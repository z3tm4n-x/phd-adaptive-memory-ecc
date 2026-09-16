"""Frozen-size tuning/test driver. Trial identity is independent of batching."""
import argparse, hashlib, itertools, json, multiprocessing as mp, os, platform, subprocess, time
from pathlib import Path
import numpy as np
from scipy.stats import beta
from reference import ROOT,config,packed,accepted
import engine

def init_worker():
    global PACKED,CFG
    CFG=config();PACKED=accepted.args(packed())

def candidates(c):
    out=[];U=c['periods_seconds']
    for a in range(len(U)):out.append([2,a,a,0,0,0,0])
    for a,b in itertools.product(range(len(U)),repeat=2):out.append([3,a,b,0,0,0,0])
    t=c['tuning']
    for ms,cap,growth,zero in itertools.product(t['pa_dom_ms'],t['pa_dom_cap'],t['pa_dom_growth'],t['pa_dom_zero_mode']):
        out.append([4,0,0,ms,cap,growth,zero])
    return np.array(out,dtype=float)

def batch(job):
    mode,case,begin,end,policies=job;seed=CFG['simulation']['tuning_seed' if mode=='tune' else 'validation_seed']
    rows=np.zeros((end-begin,len(policies),12));hashes=[];stream_counts=[]
    for j,trial in enumerate(range(begin,end)):
        stream=engine.stream(seed,case,trial,CFG);hashes.append(stream[4]);stream_counts.append([stream[6],len(stream[2])])
        for k,policy in enumerate(policies):
            # No fallback; exceptions terminate with exact seed/case/trial/policy.
            try:rows[j,k]=engine.run(*stream[:4],policy,PACKED,CFG['executor']['latch_before_commit_seconds'])[0]
            except Exception as error:
                raise RuntimeError(f'{mode=} {case=} {trial=} {policy.tolist()=}') from error
    return begin,rows,np.array(hashes,dtype='S64'),np.array(stream_counts)

def upper(k,n,alpha=.05):return 1. if k==n else float(beta.ppf(1-alpha,k+1,n-k))

def run(mode,workers,batch_size):
    c=config();output=ROOT/'outputs';output.mkdir(exist_ok=True)
    n=c['simulation']['tuning_trials' if mode=='tune' else 'validation_trials']
    selected={} if mode=='tune' else json.loads((output/'selected_policies.json').read_text())
    run_info=dict(mode=mode,trials=n,workers=workers,batch_size=batch_size,python=platform.python_version(),numpy=np.__version__,git_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),start_unix=time.time())
    for case,name in enumerate(c['cases']):
        policies=candidates(c) if mode=='tune' else np.array(selected[name]['policies'])
        path=output/f'{mode}_{name}.npz'
        rows=np.zeros((n,len(policies),12));hashes=np.empty(n,'S64');counts=np.zeros((n,2),int)
        jobs=[(mode,case,start,min(n,start+batch_size),policies) for start in range(0,n,batch_size)]
        start_time=time.perf_counter();done=0
        with mp.Pool(workers,initializer=init_worker) as pool:
            for begin,a,h,s in pool.imap_unordered(batch,jobs):
                rows[begin:begin+len(a)]=a;hashes[begin:begin+len(a)]=h;counts[begin:begin+len(a)]=s
                done+=len(a)
                if done%500<batch_size or done==n:print(f'{mode} {name}: {done}/{n}, {time.perf_counter()-start_time:.1f}s',flush=True)
        assert rows[:,:,11].sum()==0
        np.savez_compressed(path,rows=rows,event_sha256=hashes,stream_counts=counts,policies=policies)
        if mode=='tune':
            options=[];selection=[[0,0,0,0,0,0,0],[1,0,0,0,0,0,0]]
            for kind in (2,3,4):
                indices=np.flatnonzero(policies[:,0]==kind);scores=[]
                for j in indices:
                    k=int(rows[:,j,0].sum());up=upper(k,n);survive=rows[:,j,0]==0
                    resource=float(rows[survive,j,7].mean()) if survive.any() else float('inf')
                    scores.append((up>c['epsilon'][0],resource if up<=c['epsilon'][0] else up,j,up,resource,k))
                best=min(scores);j=best[2];selection.append(policies[j].tolist())
                options.append(dict(kind=kind,policy=policies[j].tolist(),risk_upper=best[3],surviving_resource=best[4],failures=best[5],no_tuning_feasible=best[0]))
            selected[name]=dict(policies=selection,selection=options)
            (output/'selected_policies.json').write_text(json.dumps(selected,indent=2)+'\n',newline='\n')
        run_info[name]=dict(seconds=time.perf_counter()-start_time,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
    run_info['elapsed_seconds']=time.time()-run_info['start_unix']
    (output/f'{mode}_manifest.json').write_text(json.dumps(run_info,indent=2)+'\n',newline='\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['tune','test']);p.add_argument('--workers',type=int,default=4);p.add_argument('--batch-size',type=int,default=20)
    a=p.parse_args();run(a.mode,a.workers,a.batch_size)

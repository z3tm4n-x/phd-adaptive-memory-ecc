"""Postprocessing only: no model/policy selection; replay and archive checks."""
from pathlib import Path
import argparse,csv,hashlib,json,platform,subprocess,sys,importlib.metadata as md
import numpy as np
from experiment import HERE,model,buffers,stream,event_hash,execute,POLICIES,NAMES,summarize,verify_prereg
from prepare import csvwrite,sha

def dump(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw-results',type=Path,required=True);ap.add_argument('--prereg',required=True);a=ap.parse_args()
    verify_prereg(a.prereg);out=HERE/'outputs';out.mkdir(exist_ok=True)
    _,p,_=model();buf=buffers(p);allrows=[];allpairs=[];audit=[];rawmanifest=[];runs=[]
    for case in ['growth','peak','typical']:
        path=a.raw_results/(case+'_trials.npz')
        with np.load(path) as archive:z={k:archive[k] for k in archive.files}
        samples=z['samples'];utc=int(z['utc_index'])
        w=next(w for w in json.loads((HERE/'selected_windows.json').read_text())['windows'] if case in w['labels'])
        run=json.loads((a.raw_results/(case+'_run.json')).read_text());assert sha(path)==run['trial_file_sha256']
        assert samples.shape==(20000,5,8) and np.all(np.isfinite(samples)) and run['computational_failures']==0
        for i in range(20000):
            ev=stream(w['nu_array_s-1'],utc,i)
            assert event_hash(ev)==z['event_hashes'][i] and len(ev[0])==z['event_counts'][i]
        replay=[0,1,2,19999]
        for i in replay:
            ev=stream(w['nu_array_s-1'],utc,i)
            for j,policy in enumerate(POLICIES):np.testing.assert_array_equal(execute(ev,p,policy,buf)[0][:8],samples[i,j])
        rows,pairs=summarize(samples,case)
        # Same-code summary reproduction must match original CSV bytes exactly.
        for suffix,data in [('policies',rows),('paired',pairs)]:
            csvwrite(out/(case+'_'+suffix+'.csv'),data)
            assert sha(out/(case+'_'+suffix+'.csv'))==sha(a.raw_results/(case+'_'+suffix+'.csv'))
        # Independent aggregate arithmetic (not a second controller implementation).
        for j,row in enumerate(rows):
            alive=[int(samples[i,j,1]) for i in range(20000) if samples[i,j,0]==0]
            assert row['first_Ecap']==sum(int(samples[i,j,0]) for i in range(20000))
            assert abs(row['passes_survivor_mean']-sum(alive)/len(alive))<1e-10
        joint=np.all(samples[:,:2,0]==0,axis=1)
        npair=sum(int(v) for v in joint);assert npair==pairs[0]['both_survive']
        counts=z['event_counts'];mu=w['exposure']
        assert abs(counts.mean()-mu)<6*np.sqrt(mu/len(counts))
        audit.append(dict(case=case,all_event_hashes_regenerated=20000,exact_trial_replays=replay,policy_replays=20,
            mean_events=float(counts.mean()),variance_events=float(counts.var(ddof=1)),expected_events=mu,aggregate_checks=True))
        rawmanifest.append(dict(path=str(path.resolve()),sha256=sha(path),bytes=path.stat().st_size,
            arrays={k:dict(shape=z[k].shape,dtype=str(z[k].dtype),sha256=hashlib.sha256(z[k].tobytes()).hexdigest()) for k in z}))
        runs.append(run);allrows+=rows;allpairs+=pairs
        dump(out/(case+'_run.json'),run)
    csvwrite(out/'policy_summary.csv',allrows);csvwrite(out/'paired_summary.csv',allpairs)
    journal=[]
    for r in allrows:
        journal.append({k:r[k] for k in ['case','policy','first_Ecap','trials','F_hat','F95_low','F95_high','F95_upper','survivors','passes_survivor_mean','passes_survivor95_low','passes_survivor95_high']})
    csvwrite(out/'journal_table.csv',journal)
    dump(out/'raw_results_manifest.json',rawmanifest);dump(out/'reproduction_checks.json',audit)
    dump(out/'environment.json',dict(python=sys.version,platform=platform.platform(),processor=platform.processor(),
        packages={k:md.version(k) for k in ['numpy','scipy','numba','llvmlite','h5py','matplotlib','psutil']},
        prereg=a.prereg,threads='OPENBLAS_NUM_THREADS=1; 3 independent case processes',
        jit='original numba njit(cache=True), fastmath=False; Windows short TEMP/g16jit cache',
        source_bytecode_policy='PYTHONDONTWRITEBYTECODE=1; NUMBA_CACHE_DIR outside repository'))
    # All base files checked as raw Git blobs: no CRLF normalization in this test.
    base='7b83f643efb37541547d7d93a65ba2f43acd43fd';root=HERE.parents[1]
    tree=subprocess.check_output(['git','ls-tree','-r',base],cwd=root,text=True).splitlines()
    tracked=[(x.split('\t',1)[1],x.split('\t',1)[0].split()[2]) for x in tree]
    paths='\n'.join(x[0] for x in tracked)+'\n'
    current=subprocess.check_output(['git','hash-object','--no-filters','--stdin-paths'],input=paths,cwd=root,text=True).splitlines()
    changed=[p for (p,b),c in zip(tracked,current) if b!=c];eol=[]
    assert len(current)==len(tracked)
    for name in changed:
        canonical=subprocess.check_output(['git','show',base+':'+name],cwd=root)
        actual=(root/name).read_bytes()
        assert actual.replace(b'\r\n',b'\n')==canonical.replace(b'\r\n',b'\n'),name
        eol.append(dict(path=name,canonical_sha256=hashlib.sha256(canonical).hexdigest(),checkout_sha256=sha(root/name)))
    dump(out/'preservation.json',dict(base=base,files_checked=len(tracked),raw_blob_mismatch_count=len(changed),
        checkout_EOL_only=eol,non_EOL_mismatches=[],
        git_status_note='Ten legacy CSVs were dirty immediately after checkout because tracked CRLF conflicts with attributes; their raw blobs equal base. Additionally 25 other files have checkout-only newline conversion. No historical content edited or staged.'))
    # Exactly the predeclared growth illustration; all completed observations shown.
    tr=list(csv.DictReader((a.raw_results/'growth_illustration.csv').open()));csvwrite(out/'growth_illustration.csv',tr)
    import matplotlib;matplotlib.use('Agg')
    matplotlib.rcParams['svg.hashsalt']='RE-INTERNAL-COUNT-GOES16-VALIDATION-01'
    import matplotlib.pyplot as plt
    w=next(w for w in json.loads((HERE/'selected_windows.json').read_text())['windows'] if 'growth' in w['labels'])
    t=np.array([float(r['time_end_s']) for r in tr]);counts=np.array([float(r['own_count']) for r in tr]);tau=np.array([float(r['next_period_s']) for r in tr])
    fig,axes=plt.subplots(3,1,figsize=(10,7),sharex=True,layout='constrained',height_ratios=[1,1,1.2])
    axes[0].stairs(w['nu_array_s-1'],np.arange(13)*5,color='#235789',linewidth=2);axes[0].set_ylabel('Array intensity, s⁻¹')
    axes[1].vlines(t/60,0,counts,color='#278074',linewidth=.65);axes[1].plot(t/60,counts,'.',color='#278074',markersize=1.4);axes[1].set_ylabel('Completed own count')
    good=tau>0;axes[2].step(np.r_[0,t[good]/60],np.r_[float(tr[0]['period_s']),tau[good]],where='post',color='#ac542b',linewidth=.8)
    axes[2].set_ylabel('Next period, s');axes[2].set_xlabel('Minutes since 2024-10-10 13:00 UTC')
    axes[2].set_yscale('log');axes[2].set_yticks([1,2,5,10,20,100,300],labels=['1','2','5','10','20','100','300'])
    axes[2].set_ylim(.8,450)
    terminal=(tau>0)&(t+tau>3600)
    if np.any(terminal):axes[2].annotate('Terminal partial action',xy=(t[terminal][-1]/60,tau[terminal][-1]),xytext=(42,100),arrowprops={'arrowstyle':'->'},fontsize=9)
    for ax in axes:ax.grid(alpha=.2);ax.set_xlim(0,60)
    rr=runs[0]['illustration_result']
    if rr[0]:
        for ax in axes:ax.axvline(rr[5]/60,color='crimson',linestyle='--',label='First E_cap')
    fig.suptitle('Growth profile / Proposed — fixed seed 2026091602, trial 0\n'+('First E_cap marked; control trace stops there' if rr[0] else 'No E_cap in this illustrative trial; no trajectory selection'))
    fig.savefig(out/'growth_profile.png',dpi=160);fig.savefig(out/'growth_profile.svg',metadata={'Date':None});plt.close(fig)
    svg=out/'growth_profile.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    dump(out/'output_hashes.json',{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='output_hashes.json'})
    print(json.dumps(dict(runs=runs,policy=allrows,paired=allpairs),indent=2))
if __name__=='__main__':main()

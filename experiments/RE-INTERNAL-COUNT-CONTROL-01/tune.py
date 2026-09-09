"""Finite PA-DOM adaptation tuning, using pilot streams only."""
from pathlib import Path
import csv,json,time
import numpy as np
from scipy.stats import beta
from core import load_config,build_model
from simulate import pack,batch
ROOT=Path(__file__).resolve().parent

def binomial_upper(k,n,alpha=.05):
    return 1.0 if k==n else float(beta.ppf(1-alpha,k+1,n-k))

def run(dwells=None):
    (ROOT/'cache').mkdir(exist_ok=True)
    cfg=load_config();seed=cfg['simulation']['pilot_seed'];rows=[];selected=[]
    candidates=[[4,2,2,ms,cap,growth,zero] for ms in [.01,.02,.04,.08,.12,.2,.3,.5,1.]
                for cap in [5.,20.,100.,300.] for growth in [3.,10000.] for zero in [0,1]]
    # Targeted pilot refinement of the coarse Ms=0.12..0.20 gap.
    candidates += [[4,2,2,ms,cap,3.,1] for ms in [.13,.14,.15,.16,.17,.18,.19] for cap in [5.,20.,100.,300.]]
    for d in (dwells or cfg['environment']['mean_dwell_seconds']):
        t=time.perf_counter();p=pack(build_model(cfg,d,False))
        # Same independent physical streams across candidates; own counters.
        chunks=[]
        for start in range(0,len(candidates),12):
            path=ROOT/'cache'/f'pilot_{d}_{start}.npz'
            if path.exists(): chunk=np.load(path)['samples']
            else:
                chunk=batch(p,500,seed,candidates[start:start+12]);np.savez_compressed(path,samples=chunk)
            chunks.append(chunk)
            print('screen',d,start+len(chunk[0]),'/',len(candidates),flush=True)
        r=np.concatenate(chunks,axis=1)
        table=[]
        for j,c in enumerate(candidates):
            k=int(r[:,j,0].sum());alive=r[:,j,0]==0
            table.append(dict(dwell=d,stage='screen500',candidate=j,Ms=c[3],cap=c[4],growth=c[5],zero_mode=c[6],n=500,failures=k,risk=k/500,upper=binomial_upper(k,500),passes_survive=(float(r[alive,j,1].mean()) if alive.any() else None)))
        eligible=[x for x in table if x['upper']<=.1]
        # Refine the lowest-cost pilot-eligible candidates. No validation
        # observations or outcomes participate in this selection.
        shortlist=sorted(eligible,key=lambda x:x['passes_survive'])[:12]
        ids=list(dict.fromkeys(x['candidate'] for x in shortlist))
        if not ids: raise RuntimeError('no safe pilot analogue; expand only within the fixed target model')
        refined=batch(p,cfg['simulation']['pilot_trials'],seed,[candidates[j] for j in ids])
        refinements=[]
        for j,idx in enumerate(ids):
            c=candidates[idx];n=len(refined);k=int(refined[:,j,0].sum());alive=refined[:,j,0]==0
            x=dict(dwell=d,stage='refine2000',candidate=idx,Ms=c[3],cap=c[4],growth=c[5],zero_mode=c[6],n=n,failures=k,risk=k/n,upper=binomial_upper(k,n),passes_survive=float(refined[alive,j,1].mean()))
            refinements.append(x)
        safe=[x for x in refinements if x['upper']<=.1]
        if not safe: raise RuntimeError('no refined analogue under upper<=0.1')
        chosen=min(safe,key=lambda x:(x['passes_survive'],x['upper'],x['candidate']))
        selected.append(dict(dwell=d,policy=candidates[chosen['candidate']],pilot=chosen))
        rows+=table+refinements
        (ROOT/'cache'/f'tuning_{d}.json').write_text(json.dumps(dict(rows=table+refinements,selected=selected[-1],candidates=candidates)))
        print('D',d,'chosen',selected[-1],'seconds',time.perf_counter()-t,flush=True)
    (ROOT/'outputs').mkdir(exist_ok=True)
    with (ROOT/'outputs'/'analogue_tuning.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (ROOT/'outputs'/'selected_analogue.json').write_text(json.dumps(dict(pilot_seed=seed,validation_used=False,candidates=candidates,selected=selected),indent=2))
    return selected
if __name__=='__main__':
    import sys
    run([float(sys.argv[1])] if len(sys.argv)>1 else None)

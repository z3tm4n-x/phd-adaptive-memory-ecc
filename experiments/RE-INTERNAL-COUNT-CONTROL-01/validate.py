"""Held-out full-array evaluation; training data never enter these estimates."""
from __future__ import annotations
import csv,json,math,time
from pathlib import Path
import numpy as np
from scipy.stats import beta
from numba import njit
from core import load_config,build_model
from simulate import pack,batch,run_trace,_choose,_observe
ROOT=Path(__file__).resolve().parent
NAMES=['proposed','count_disabled','Fixed','Precomputed','PA_DOM_adaptation']
TRACE_FIELDS=['time_start','period','time_end','own_correction_count','prior_high_probability','posterior_high_probability','prior_pending_mean','posterior_pending_mean','slack_before','slack_after','expected_value_increment','interval_pair_reward','potential_before','auxiliary_likelihood','next_period','sum_conditional_pair_rewards','actual_pending_diagnostic_NOT_INPUT']

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def mean_ci(x):
    n=len(x);m=float(np.mean(x));se=float(np.std(x,ddof=1)/math.sqrt(n)) if n>1 else math.nan
    return m,m-1.96*se,m+1.96*se

@njit(cache=True)
def _benchmark(repeats,counts,initial,slack0,kernels,transition,H,J,constant,coefficient,first,second,ticks,tick,words,dwell,low,high):
    checksum=0.
    for trial in range(repeats):
        q=initial.copy();s=slack0;remaining=len(constant)-1
        for count in counts:
            if remaining<=0: break
            a,s,_,_,_=_choose(q,s,remaining,H,J,constant,coefficient,first,second,ticks,tick,words,dwell,low,high)
            remaining-=min(remaining,ticks[a])
            if remaining>0:q,_=_observe(q,a,int(count),True,kernels,transition)
            checksum+=q[0]
    return checksum


def run():
    (ROOT/'cache').mkdir(exist_ok=True)
    cfg=load_config();settings=json.loads((ROOT/'outputs'/'selected_analogue.json').read_text())
    rows=[];paired=[];bench=[];n=cfg['simulation']['validation_trials'];seed0=cfg['simulation']['validation_seed']
    for di,dwell in enumerate(cfg['environment']['mean_dwell_seconds']):
        start=time.perf_counter();model=build_model(cfg,dwell,False);p=pack(model)
        chosen=next(x['policy'] for x in settings['selected'] if x['dwell']==dwell)
        policies=[[0,2,2,0,0,0,0],[1,2,2,0,0,0,0],[2,2,2,0,0,0,0],[3,3,2,0,0,0,0],chosen]
        chunks=[]
        for first_trial in range(0,n,2000):
            count=min(2000,n-first_trial);seed=seed0+di*100000+first_trial
            r=batch(p,count,seed,policies);chunks.append(r)
            print('heldout',dwell,first_trial+count,'/',n,flush=True)
        samples=np.concatenate(chunks,axis=0)
        np.savez_compressed(ROOT/'cache'/f'validation_{dwell}.npz',samples=samples,policies=np.array(policies),seed=seed0+di*100000)
        for j,name in enumerate(NAMES):
            k=int(samples[:,j,0].sum());alive=samples[:,j,0]==0
            lo=0. if k==0 else float(beta.ppf(.025,k,n-k+1));hi=1. if k==n else float(beta.ppf(.975,k+1,n-k))
            family_upper=1. if k==n else float(beta.ppf(1-.05/15,k+1,n-k))
            m,ml,mh=mean_ci(samples[alive,j,1])
            rows.append(dict(dwell=dwell,policy=name,epsilon=.1,trials=n,failures=k,F_estimate=k/n,F_CI95_low=lo,F_CI95_high=hi,F_family95_upper=family_upper,
                 complete_passes_stop_mean=float(samples[:,j,1].mean()),passes_given_survival=m,passes_given_survival_CI95_low=ml,passes_given_survival_CI95_high=mh,
                 busy_seconds_stop_mean=float(samples[:,j,2].mean()),busy_seconds_given_survival=float(samples[alive,j,2].mean()),
                 reads_stop_mean=float(samples[:,j,3].mean()),writes_stop_mean=float(samples[:,j,4].mean()),updates_given_survival=float(samples[alive,j,6].mean()),
                 guarantee=('analytic_plus_controlled_error' if j<=1 else 'deterministic_bracket' if j<=3 else 'heldout_binomial_only')))
        for j in range(1,len(NAMES)):
            both=(samples[:,0,0]==0)&(samples[:,j,0]==0)
            diff=samples[both,j,1]-samples[both,0,1];m,lo,hi=mean_ci(diff)
            riskdiff=samples[:,0,0]-samples[:,j,0];rd,rl,rh=mean_ci(riskdiff)
            paired.append(dict(dwell=dwell,comparator=NAMES[j],joint_survivors=int(both.sum()),passes_saved_mean=m,passes_saved_CLT95_low=lo,passes_saved_CLT95_high=hi,
                               proposed_minus_comparator_F=rd,risk_difference_CLT95_low=rl,risk_difference_CLT95_high=rh))
        # A concrete *own* count/action history, generated after policy freezing.
        result,trace=run_trace(p,12345)
        with (ROOT/'outputs'/f'trace_{dwell}.csv').open('w',newline='') as f:
            writer=csv.writer(f);writer.writerow(TRACE_FIELDS);writer.writerows(trace)
        # Batched, compiled, warmed timings; neither JIT compilation nor
        # simulation/event generation is counted as online controller time.
        counts=trace[:,3].astype(np.int64)
        bargs=(counts,p.initial,p.slack,p.kernels,p.transition,p.H,p.J,p.constant,p.coefficient,p.first,p.second,p.ticks,p.tick,p.words,p.dwell,p.low,p.high)
        _benchmark(1,*bargs)
        timings=[]
        for repeat in range(7):
            t=time.perf_counter();_benchmark(100,*bargs);timings.append((time.perf_counter()-t)/(100*len(counts)))
        rom=sum(x.nbytes for x in [p.kernels,p.transition,p.H,p.J,p.constant,p.coefficient,p.first,p.second,p.periods,p.ticks,p.initial])
        bench.append(dict(dwell=dwell,offline_build_seconds=model.build_seconds,online_update_median_seconds=float(np.median(timings)),online_update_max_batch_mean_seconds=float(max(timings)),
                          packed_arrays_bytes=int(rom),live_two_belief_buffers_bytes=2*len(p.initial)*8,live_scalar_workspace_upper_bytes=256,
                          uncompressed_reference_value_bytes=model.value.nbytes,trace_complete_passes=int(result[1]),trace_first_passage=bool(result[0])))
        write_csv(ROOT/'outputs'/'comparison.csv',rows);write_csv(ROOT/'outputs'/'paired_comparison.csv',paired);write_csv(ROOT/'outputs'/'controller_cost.csv',bench)
        print('finished',dwell,'seconds',time.perf_counter()-start,flush=True)
        for row in rows[-5:]:print(row['policy'],row['F_estimate'],row['passes_given_survival'],flush=True)
    return rows,paired,bench
if __name__=='__main__':run()

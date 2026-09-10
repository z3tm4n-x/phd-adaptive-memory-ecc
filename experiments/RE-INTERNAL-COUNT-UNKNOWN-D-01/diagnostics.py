"""Lossless set/budget traces and host-controller resource measurements."""
from __future__ import annotations
import csv,json,math,time
import numpy as np
from numba import njit
from model import ROOT,build_bank,load_config,choose,observe,retained,controller_args
from known_reference import build_known
from simulate import trace_run

COLUMNS=['time_s','previous_period_s','own_count','D_cell_mask_before','D_cell_mask_after','next_period_s',
         'slack_min','slack_max','completed_passes','physical_pending_words_diagnostic_only',
         'local_previous_set_period','local_refined_set_period','PrH_D3000','PrH_D30','last_blocking_node','knownD_slack_unused_for_unknown',
         'remaining_risk_potential_min','remaining_risk_potential_max']

def hull(mask,rates):
    ids=[j for j in range(len(rates)-1) if int(mask)&(1<<j)]
    return (float(1/rates[ids[-1]+1]),float(1/rates[ids[0]]),len(ids)) if ids else (None,None,0)

@njit(cache=True)
def timing_loop(n,kernels,reward,T,J,V,q0,s0,rates,ticks,threshold,tick,W,lo,hi):
    checksum=0.
    for i in range(n):
        q=q0.copy();s=s0.copy();logs=np.zeros(len(q));rej=np.zeros(len(q),np.bool_)
        q=observe(q,logs,rej,2,i%2,kernels,threshold,True)
        active=retained(rej)
        a,s,_=choose(q,s,active,35990,reward,T,J,V,ticks,tick,W,rates,lo,hi,2)
        checksum+=a+s[0]
    return checksum

def main():
    b=build_bank();cfg=b.cfg;out=ROOT/'outputs';excerpts=[];effects=[];traces=[]
    for D in cfg['simulation']['dwell_seconds']:
        k=build_known(cfg,D)
        for kind in [0,1]:
            r,tr=trace_run(b,k,D,cfg['simulation']['trace_seed'],kind)
            name=f'trace_{D}_{"learning" if kind==0 else "frozen"}.csv'
            with (out/name).open('w',newline='') as f:
                writer=csv.writer(f);writer.writerow(COLUMNS);writer.writerows(tr)
            changes=np.flatnonzero(tr[:,3]!=tr[:,4]);actionchanges=np.flatnonzero((tr[:,10]>=0)&(tr[:,10]!=tr[:,11]))
            traces.append(dict(dwell=D,policy='learning' if kind==0 else 'frozen',seed=cfg['simulation']['trace_seed'],
                               failure=bool(r[0]),passes=int(r[1]),set_changes=len(changes),local_action_changes=len(actionchanges),file=name))
            for ix in actionchanges:
                row=tr[ix];before=hull(row[3],b.rates);after=hull(row[4],b.rates)
                effects.append(dict(dwell=D,row=int(ix),time=row[0],count=int(row[2]),D_before_lower=before[0],D_before_upper=before[1],
                    D_after_lower=after[0],D_after_upper=after[1],cells_before=before[2],cells_after=after[2],
                    previous_set_period=row[10],refined_set_period=row[11],slack_min=row[6],risk_potential_max=row[17]))
            for ix in sorted(set([0,len(tr)-1]+list(changes[:4])+list(actionchanges[:4]))):
                if ix<0:continue
                row=tr[ix];rr=dict(zip(COLUMNS,row));rr.update(dwell=D,policy=kind,row=ix);excerpts.append(rr)
    if effects:
        with (out/'local_information_action_effect.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(effects[0]));w.writeheader();w.writerows(effects)
    with (out/'trace_excerpt.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(excerpts[0]));w.writeheader();w.writerows(excerpts)
    (out/'trace_summary.json').write_text(json.dumps(traces,indent=2)+'\n')
    cc=cfg['controller'];args=(b.kernels,b.reward,b.transition,b.pending,b.value,b.initial,b.slack,b.rates,b.ticks,
        math.log(cc['continuous_transfer_factor']/cc['beta'])+cc['test_log_margin'],cc['time_tick_seconds'],cfg['memory']['words'],
        cfg['environment']['b_low'],cfg['environment']['b_high'])
    timing_loop(1,*args);samples=[]
    for _ in range(7):
        t=time.perf_counter();timing_loop(10000,*args);samples.append((time.perf_counter()-t)/10000)
    memory=dict(probabilities_and_moments_bytes=b.initial.nbytes,second_filter_buffer_bytes=b.initial.nbytes,
        slack_and_likelihood_scores_bytes=2*b.slack.nbytes,rejection_and_active_flags_bytes=2*len(b.rates),
        kernel_tables_bytes=b.kernels.nbytes,value_tables_bytes=b.value.nbytes,
        reward_transition_pending_bytes=b.reward.nbytes+b.transition.nbytes+b.pending.nbytes,
        build_seconds=b.build_seconds,host_update_choice_seconds=samples,median_host_seconds=float(np.median(samples)),
        minimum_idle_window_seconds=min(b.periods)-cfg['memory']['pass_seconds'],hardware_WCET_claim=False,
        scaling='working O(M); observation O(M), choice O(M |U|), value tables O(M H/tick); fixed M=33, independent of W')
    (out/'controller_cost.json').write_text(json.dumps(memory,indent=2)+'\n')
    print(json.dumps(dict(traces=traces,controller=memory,local_effect_examples=effects[:5]),indent=2),flush=True)

if __name__=='__main__':main()

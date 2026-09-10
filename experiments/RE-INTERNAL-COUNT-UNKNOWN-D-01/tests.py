"""Independent physical and algebraic falsification checks, not a review PASS."""
from __future__ import annotations
import json,math,time,copy
import numpy as np
from scipy.linalg import expm
from model import (ROOT,load_config,build_bank,observe,choose,retained,controller_args,
                   action_delta,moments)
from small_reference import small_config,evaluate
from simulate import batch,stream,trace_run,pack_args,run
from known_reference import build_known


def dummy_known():
    # The known-D policy is NOT invoked in small tests; shapes satisfy a common
    # compiled interface only. Production diagnostics always use build_known.
    return (np.zeros((1,1,26,26)),np.zeros((1,2,2)),np.zeros((1,2,2)),
            np.zeros((1,4)),np.zeros((1,4)),np.zeros(26),0.,0.)


def explicit_scan(bank,ts,ws,bs,learning=True):
    """Chronologically merge EVERY word reset and bit event; no lazy helpers."""
    c=bank.cfg;W=c['memory']['words'];P=c['memory']['pass_seconds'];tick=c['controller']['time_tick_seconds']
    H=c['horizon_seconds'];total=int(round(H/tick));now=0;ei=0;passes=0;masks=[0]*W
    q=bank.initial;s=bank.slack.copy();logs=np.zeros(len(q));rej=np.zeros(len(q),bool);active=np.ones(len(q),bool)
    threshold=math.log(c['controller']['continuous_transfer_factor']/c['controller']['beta'])+c['controller']['test_log_margin']
    counts=[]
    while now<total:
        rem=total-now;a,s,_=choose(q,s,active,rem,*controller_args(bank));tau=bank.periods[a]
        t=now*tick;end=min(H,t+tau);start=t+tau-P;events=[]
        for w in range(W):
            reset=start+(w+1)*P/W
            if reset<=end+1e-13:events.append((reset,0,w,0))
        while ei<len(ts) and ts[ei]<end-1e-12:
            events.append((ts[ei],1,int(ws[ei]),int(bs[ei])));ei+=1
        events.sort();count=0
        for e,kind,w,bit in events:
            if kind==0:
                count+=bool(masks[w]);masks[w]=0
            else:
                masks[w]^=1<<bit
                if masks[w].bit_count()>1:return True,passes,e,counts
        if t+tau>H+1e-10:return False,passes,H,counts
        passes+=1;counts.append(count);now+=int(bank.ticks[a])
        if now<total:
            q=observe(q,logs,rej,a,count,bank.kernels,threshold,learning)
            active=retained(rej) if learning else active
    return False,passes,H,counts


def main():
    started=time.perf_counter();cfg=load_config();b=build_bank(cfg);records=[]
    def record(name,**kw):records.append(dict(test=name,passed=True,**kw))
    # Independent moments via 6x6 block exponential of the integrated-rate PGF.
    error=0.
    for D in [30,100,300,1000,3000]:
        a=1/D;Q=np.array([[-a,a],[a,-a]]);B=np.diag([cfg['environment']['b_low'],cfg['environment']['b_high']]);Z=np.zeros((2,2))
        A=np.block([[Q,B,Z],[Z,Q,2*B],[Z,Z,Q]])
        for h in [.01125632,.2,1,20,300]:
            E=expm(A*h);f,s=moments(h,a,*np.diag(B));ff=E[:2,2:4].sum(axis=1);ss=E[:2,4:6].sum(axis=1)
            error=max(error,float(np.max(abs(f-ff)/(1+ff))),float(np.max(abs(s-ss)/(1+ss))))
    assert error<1e-9;record('integrated_rate_moments_independent_block_exponential',max_scaled_error=error)
    q=b.initial;logs=np.zeros(33);rej=np.zeros(33,bool);rng=np.random.default_rng(616)
    max_identity=0.;max_martingale=0.;max_mean=0.
    for step in range(100):
        a=int(rng.integers(12));count=int(rng.integers(2));rem=int(rng.integers(3001,36001));dt=min(rem,int(b.ticks[a]));s0=np.full(33,.03)
        # All branches are explicitly included, no conditioning on physical survival.
        nexts=[];ells=[];branchlogs=[]
        for y in [0,1]:
            raw=np.einsum('ji,jik->jk',q[:,:4],b.kernels[:,a,y]);ell=raw[:,:4].sum(axis=1)
            nexts.append(raw/ell[:,None]);ells.append(ell);branchlogs.append(logs+np.log(ell))
        for j in range(33):
            delta,one,val=action_delta(q,j,a,rem,b.reward,b.transition,b.pending,b.value,b.ticks,.1,
                                       cfg['memory']['words'],b.rates,cfg['environment']['b_low'],cfg['environment']['b_high'])
            ev=0.
            for y in [0,1]:
                qq=nexts[y][j];vv=b.value[j,rem-dt]
                v=(qq[0]+qq[2])*vv[0]+(qq[1]+qq[3])*vv[1]+qq[4]*vv[2]+qq[5]*vv[3]
                ev+=ells[y][j]*(v+s0[j]-delta)
            max_identity=max(max_identity,abs(one+ev-val-s0[j]))
        oldmix=np.exp(logs-logs.max()).mean();oldE=oldmix/np.exp(logs-logs.max())
        expected=np.zeros(33)
        for y in [0,1]:
            ll=branchlogs[y];ee=np.exp(ll-ll.max()).mean()/np.exp(ll-ll.max());expected+=ells[y]*ee
        max_martingale=max(max_martingale,float(np.max(abs(expected-oldE)/(1+oldE))))
        q=observe(q,logs,rej,a,count,b.kernels,math.log(1.064/.005)+.001,False)
        max_mean=max(max_mean,float(q[:,4:].sum(axis=1).max()))
        assert np.max(abs(q[:,:4].sum(axis=1)-1))<1e-12
    assert max_identity<1e-12 and max_martingale<1e-10
    assert max_mean<=cfg['environment']['b_high']*cfg['memory']['pass_seconds']/2+1e-12
    record('whole_observation_tree_potential_identity',checks=3300,max_residual=max_identity)
    record('likelihood_ratio_one_step_martingale_identity',checks=3300,max_relative_residual=max_martingale)
    record('unbounded_pending_first_moment_bound',maximum=max_mean)
    assert not rej.any();record('frozen_set_is_not_posterior_reweighted_or_shrunk')
    assert np.array_equal(retained(np.array([True,True,False])),[False,True,True])
    assert retained(np.array([True,False,True])).all()
    assert not retained(np.ones(33,bool)).any()
    a,ss,_=choose(b.initial,b.slack,np.zeros(33,bool),36000,*controller_args(b))
    assert a==2 and np.array_equal(ss,b.slack)
    record('closed_cell_elimination_and_empty_set_no_budget_reset')
    qq1=observe(b.initial,np.zeros(33),np.zeros(33,bool),2,1,b.kernels,100.,False)
    qq2=observe(b.initial,np.zeros(33),np.zeros(33,bool),2,100000,b.kernels,100.,False)
    assert np.array_equal(qq1,qq2);record('binary_coarsening_is_explicit_not_an_extra_channel')
    # True physical small reference; production parameters are not substituted.
    sc=small_config(cfg);small=build_bank(sc,[.1,1/3,1.]);known=dummy_known();exact=[]
    for i,D in enumerate([1.,3.,10.]):
        data=batch(small,known,D,100000,cfg['simulation']['small_oracle_seed']+i*1000000,[[0,0,0,0],[1,0,0,0]])
        for k,learning in enumerate([True,False]):
            r=evaluate(small,D,learning);exact.append(r);f=data[:,k,0].mean();se=math.sqrt(r['F_upper']*(1-r['F_upper'])/len(data))
            assert abs(f-r['F_upper'])<5*se+1e-10
            assert r['mass_residual']<1e-12 and r['F_upper']<sc['epsilon']
            record('small_killed_physical_vs_actual_events',D=D,learning=learning,trials=len(data),F_exact=r['F_upper'],F_MC=float(f),standard_error=se,nodes=r['nodes'])
    discrepancies=0
    for seed in range(200):
        ts,ws,bs=stream(565600+seed,sc['horizon_seconds'],3.,sc['environment']['b_low'],sc['environment']['b_high'],2)
        for kind in [0,1]:
            trace=np.empty((40,18));state=np.full(2,-1,np.int8)
            r=run(ts,ws,bs,kind,.12,5.,3.,*pack_args(small,known,3.),state,np.empty(2),np.empty(2,np.int32),np.empty(2,np.int32),trace,True)
            f,p,t,counts=explicit_scan(small,ts,ws,bs,kind==0)
            if bool(r[0])!=f or r[1]!=p or abs(r[5]-t)>1e-10 or counts!=trace[:int(r[-1]),2].astype(int).tolist():discrepancies+=1
    assert discrepancies==0;record('explicit_all_word_chronology_vs_lazy_scanner',paths=400,discrepancies=discrepancies)
    # Reproduce published controller-action witnesses with extra known-D input.
    known=build_known(cfg,300.);r,tr=trace_run(b,known,300.,12345,5)
    witnesses=[]
    for time0,count,nextperiod in [(116.,0,2.),(118.,0,10.),(828.,22,1.)]:
        ix=np.flatnonzero(abs(tr[:,0]-time0)<1e-9)
        assert len(ix)==1;ix=int(ix[0]);assert tr[ix,2]==count and tr[ix+1,1]==nextperiod
        witnesses.append([time0,count,nextperiod])
    record('known_D_adapter_reproduces_published_RES003_action_witnesses',witnesses=witnesses)
    out=dict(status='ENGINEERING_CHECKS_COMPLETED_NOT_SCIENTIFIC_REVIEW',seconds=time.perf_counter()-started,tests=records)
    (ROOT/'outputs'/'small_physical_oracle.json').write_text(json.dumps(exact,indent=2)+'\n')
    (ROOT/'outputs'/'tests.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2),flush=True);return out

if __name__=='__main__':main()

"""Targeted independent oracles and mutation-sensitive checks; no SR verdict."""
from __future__ import annotations
import copy,json,math,time
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from scipy.stats import beta
import core
from exact_oracle import ExactOracle
from simulate import pack,batch,args,_run,_stream,_choose,_observe
ROOT=Path(__file__).resolve().parent


def check(name,condition,**details):
    if not condition: raise AssertionError(f'{name}: {details}')
    return dict(test=name,passed=True,**details)


def direct_small(times,words,bits,p,epsilon,enabled=True):
    """Explicit chronological resets of EVERY small word, not lazy resets."""
    cfg=p.cfg;w=cfg['memory']['words'];P=cfg['memory']['pass_seconds'];H=cfg['horizon_seconds']
    q=p.initial;s=epsilon-p.error['whole_horizon_delta']-float(q@p.value[-1])
    state=np.full(w,-1);t=0.;event=0;passes=0;observations=[]
    while t<H-1e-10:
        a,s,_=p.choose(int(round(t/.1)),q,s);tau=p.periods[a];end=t+tau;start=end-P
        reset_times=start+(np.arange(w)+1)*P/w;nextword=0;count=0
        while True:
            te=times[event] if event<len(times) else math.inf
            tr=reset_times[nextword] if nextword<w else math.inf
            if min(te,tr)>min(end,H)+1e-12: break
            if te<tr:
                j=words[event];bit=bits[event]
                if state[j]==bit: state[j]=-1
                elif state[j]<0: state[j]=bit
                else: return True,passes,te,observations
                event+=1
            else:
                if state[nextword]>=0: count+=1;state[nextword]=-1
                nextword+=1
        if end>H+1e-12: break
        passes+=1;observations.append(count)
        if end<H-1e-12: q,_=p.observe(q,a,count,enabled)
        t=end
    return False,passes,H,observations


def run():
    rows=[];cfg=core.load_config();t0=time.perf_counter()
    # Independent block matrix for integrated-intensity first/second moments.
    largest=0.
    for dwell in [30.,300.,3000.]:
        b=np.array([cfg['environment']['b_low'],cfg['environment']['b_high']]);Q=np.array([[-1,1],[1,-1]])/dwell
        G=np.zeros((6,6))
        for j in range(3): G[2*j:2*j+2,2*j:2*j+2]=Q
        G[:2,2:4]=np.diag(b);G[2:4,4:]=2*np.diag(b)
        for dt in [.01,.2,1,30,300]:
            E=expm(G*dt);m1,m2=core.moments(dt,dwell,*b)
            exact=np.column_stack([E[:2,2:4].sum(1),E[:2,4:].sum(1)])
            found=np.column_stack([m1,m2]);err=float(np.max(np.abs(found-exact)/(1+np.abs(exact))))
            largest=max(largest,err)
    rows.append(check('moments_independent_6state_exponential',largest<2e-10,max_scaled_error=largest))
    # Actual-memory oracle stress model, explicitly not a production scenario.
    small=copy.deepcopy(cfg);small['memory']['words']=2;small['memory']['pass_seconds']=.12
    small['environment']['b_low']=.04;small['environment']['b_high']=.45;small['horizon_seconds']=6.
    eps=.19;dwell=3.;m=core.build_model(small,dwell,False);oracle=ExactOracle(small,dwell);p=pack(m,eps)
    exacts=[oracle.evaluate(m,eps,en) for en in [True,False]]
    for en,r in zip([True,False],exacts):
        rows.append(check('joint_killed_oracle_'+str(en),abs(r['mass_residual'])<1e-12 and r['first_passage']<=eps,
                          first_passage=r['first_passage'],nodes=r['exact_tree_nodes'],mass_residual=r['mass_residual']))
    samples=batch(p,100000,12038017,[[0,2,2,0,0,0,0],[1,2,2,0,0,0,0]])
    for j,en in enumerate([True,False]):
        k=int(samples[:,j,0].sum());n=len(samples);se=math.sqrt(exacts[j]['first_passage']*(1-exacts[j]['first_passage'])/n)
        rows.append(check('small_event_simulator_vs_joint_oracle_'+str(en),abs(k/n-exacts[j]['first_passage'])<6*se,
                          trials=n,events=k,estimate=k/n,exact=exacts[j]['first_passage'],standard_error=se))
    # The explicit reset implementation shares the policy but NO lazy state code.
    discrepancies=0
    for seed in range(22310,22410):
        ts,ws,bs=_stream(seed,6.,3.,.04,.45,2,32)
        for en in [True,False]:
            ref=direct_small(ts,ws,bs,m,eps,en);trace=np.empty((100,17))
            out=_run(ts,ws,bs,0 if en else 1,2,2,0.,0.,0.,0,*args(p),np.full(2,-1,np.int8),np.empty(2),np.empty(2,np.int32),np.empty(2,np.int32),trace,True)
            discrepancy=(bool(out[0])!=ref[0] or out[1]!=ref[1] or abs(out[5]-ref[2])>1e-10 or list(trace[:int(out[8]),3].astype(int))!=ref[3])
            discrepancies+=discrepancy
    rows.append(check('explicit_all_word_reset_vs_lazy_simulator',discrepancies==0,paths=200,discrepancies=int(discrepancies)))
    # Physical same-bit cancellation vs first distinct-bit passage, under Fixed.
    def explicit_events(ts,ws,bs,first=2):
        tr=np.empty((100,17))
        out=_run(np.array(ts,float),np.array(ws,np.int32),np.array(bs,np.int8),2,first,first,0.,0.,0.,0,*args(p),
                 np.full(2,-1,np.int8),np.empty(2),np.empty(2,np.int32),np.empty(2,np.int32),tr,True)
        return out,tr[:int(out[8])]
    r,tr=explicit_events([.1,.2],[0,0],[3,3])
    rows.append(check('same_bit_toggle_not_a_correction',r[0]==0 and tr[0,3]==0,first_count=float(tr[0,3])))
    r,_=explicit_events([.1,.2,.3],[0,0,0],[3,4,4])
    rows.append(check('first_passage_cannot_be_erased_by_later_toggle',r[0]==1 and abs(r[5]-.2)<1e-12))
    r,tr=explicit_events([.97],[0],[3])
    rows.append(check('no_free_global_reset_at_pass_end',r[0]==0 and tr[0,3]==0 and tr[0,16]==1 and tr[1,3]==1,
                      first_count=float(tr[0,3]),pending_at_end=float(tr[0,16]),second_count=float(tr[1,3])))
    # Exact killed projection differs from auxiliary observation by <= the
    # deliberately pessimistic repeated-word probability upper bound.
    a=2;actual=oracle.initial@oracle.kernel(1.).sum(0);lost=1-actual.sum()
    joint=np.einsum('i,cij->cj',oracle.initial,oracle.kernel(1.)).reshape(3,2,4).sum(2)
    aux=(m.initial@m.kernels[a]).reshape(33,2,13).sum(2)
    pad=np.zeros_like(aux);pad[:3]=joint;tv=.5*(np.abs(aux-pad).sum()+lost)
    one=float(m.initial@m.reward[a])
    rows.append(check('actual_vs_auxiliary_joint_count_mode_coupling',tv<=one+1e-12,total_variation=float(tv),pair_bound=one))
    # Production state, decision, normalization, and Bellman-potential identity.
    largest_identity=0.;largest_affine=0.;choice_disagree=0
    for d in [30,300,3000]:
        model=core.build_model(cfg,d,False);packed=pack(model);L=13
        rng=np.random.default_rng(741+d)
        for test in range(200):
            q=rng.dirichlet(np.ones(26));rem=int(rng.integers(1,36001));s=float(rng.random()*.05)
            a,snew,D=model.choose(36000-rem,q,s)
            aa,ss,dd,rr,vv=_choose(q,s,rem,packed.H,packed.J,packed.constant,packed.coefficient,packed.first,packed.second,packed.ticks,packed.tick,packed.words,packed.dwell,packed.low,packed.high)
            choice_disagree+=a!=aa or abs(snew-ss)>1e-10
            dt=min(rem,int(model.ticks[a]));R=rem-dt
            if model.ticks[a]<=rem:
                reward=float(q@model.reward[a]);future=0.
                for y in range(33):
                    un=q@model.kernels[a,y];prob=un.sum()
                    if prob>0: future+=float(un@model.value[R])+prob*snew
                residual=reward+future-float(q@model.value[rem])-s
            else:
                residual=float(q@core.reward_vector(rem*.1,cfg,d))+snew-float(q@model.value[rem])-s
            largest_identity=max(largest_identity,abs(residual))
        for k in range(L):
            for z in range(2):
                expected=packed.constant[:,z]+k*packed.coefficient[:,z]
                largest_affine=max(largest_affine,float(np.max(np.abs(expected-model.value[:,z*L+k]))))
        rows.append(check('production_numeric_reserve_'+str(d),model.error['arithmetic']['covered'],bound=model.error['arithmetic']['total_bound'],reserved=model.error['arithmetic']['reserve']))
        q=model.initial
        q0,_=model.observe(q,2,0,False);qbig,_=model.observe(q,2,999999,False)
        rows.append(check('count_disabled_does_not_receive_numeric_count_'+str(d),np.array_equal(q0,qbig)))
    rows.append(check('compiled_action_matches_reference',choice_disagree==0,comparisons=600,disagreements=int(choice_disagree)))
    rows.append(check('whole_horizon_potential_one_step_identity',largest_identity<1e-11,max_residual=largest_identity))
    rows.append(check('compressed_value_affine_in_pending_count',largest_affine<1e-10,max_error=largest_affine))
    report=dict(status='ENGINEERING_CHECKS_COMPLETED_NOT_SCIENTIFIC_REVIEW',seconds=time.perf_counter()-t0,tests=rows)
    (ROOT/'outputs'/'tests.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));return report
if __name__=='__main__':run()

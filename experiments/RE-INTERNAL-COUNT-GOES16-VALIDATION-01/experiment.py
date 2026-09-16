"""NHPP adapter around unmodified RES-003; no GOES data enters its controller."""
from pathlib import Path
import argparse, hashlib, json, sys, time, subprocess, platform
from datetime import datetime
import numpy as np
from scipy.stats import beta
from prepare import HERE, sha, dump, csvwrite
OLD=HERE.parent/'RE-INTERNAL-COUNT-CONTROL-01'
sys.path.insert(0,str(OLD))
import core
import simulate as sim

NAMES=['Proposed','Count-disabled','Fixed','Precomputed','PA-DOM']
POLICIES=[[0,2,2,0,0,0,0],[1,2,2,0,0,0,0],[2,2,2,0,0,0,0],[3,3,2,0,0,0,0],[4,2,2,.15,20,3,1]]
TRACE=['time_start_s','period_s','time_end_s','own_count','prior_qH','posterior_qH','prior_pending_mean','posterior_pending_mean','slack_before','slack_after','D','reward','potential','likelihood','next_period_s','sum_reward','physical_pending_NOT_INPUT']

def stream(rates,utc_index,trial,seed=2026091601,words=524288,bits=32):
    """SeedSequence tuple is batch/order invariant; UTC key is Unix 5-minute index."""
    r=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,int(utc_index),int(trial)])))
    ts=[]
    for i,rate in enumerate(rates):
        k=r.poisson(float(rate)*300)
        ts.append(i*300+300*np.sort(r.random(k)))
    times=np.concatenate(ts).astype('<f8')
    locations=r.integers(0,words,size=len(times),dtype=np.int32).astype('<i4')
    bits_arr=r.integers(0,bits,size=len(times),dtype=np.int8)
    return times,locations,bits_arr
def event_hash(events):
    h=hashlib.sha256()
    for a in events: h.update(a.tobytes())
    return h.hexdigest()
def buffers(p):return (np.full(p.words,-1,np.int8),np.empty(p.words),np.empty(p.words,np.int32),np.empty(p.words,np.int32))
def execute(events,p,policy,buf=None,record=False):
    if buf is None:buf=buffers(p)
    k,a,b,ms,cap,growth,zero=policy
    audit=record or k<=1
    trace=np.empty((18001 if audit else 0,17))
    result=sim._run(*events,int(k),int(a),int(b),ms,cap,growth,int(zero),*sim.args(p),*buf,trace,audit)
    if not np.all(np.isfinite(result)):raise ArithmeticError('nonfinite simulation result')
    if audit:
        tr=trace[:int(result[8])]
        if not np.all(np.isfinite(tr)):raise ArithmeticError('nonfinite controller trace')
        if np.any(tr[:,13]<=0):raise ArithmeticError('invalid observation likelihood')
        if np.any(tr[:,5]<-1e-12) or np.any(tr[:,5]>1+1e-12):raise ArithmeticError('invalid posterior mode probability')
        if record:return result,tr
    return result,None
def model():
    cfg=core.load_config();m=core.build_model(cfg,300,cache=False);p=sim.pack(m,.1)
    floor=float(m.initial@m.value[-1])+m.error['whole_horizon_delta']
    assert abs(floor-.07667519552414697)<1e-12 and abs(m.error['whole_horizon_delta']-.0002196041093111929)<1e-15 and p.slack>0
    selected=json.loads((OLD/'outputs/selected_analogue.json').read_text())
    assert next(x['policy'] for x in selected['selected'] if x['dwell']==300)==POLICIES[4]
    return m,p,dict(floor=floor,delta=m.error['whole_horizon_delta'],s0=p.slack,backup=float(m.initial@m.value[-1]),
                    accepted_SR_arithmetic_bound=.000143018263177913,numeric_reserve=.0002,
                    guarantee_domain='original CTMC only; not GOES profile')

def cp(k,n,alpha=.05):
    if n<=0:return 0.,1.
    return (0. if k==0 else float(beta.ppf(alpha/2,k,n-k+1)),1. if k==n else float(beta.ppf(1-alpha/2,k+1,n-k)))
def upper(k,n,alpha=.05):return 1. if k==n else float(beta.ppf(1-alpha,k+1,n-k))
def eb(x,alpha=.05,low=12.,high=18000.):
    """Two-sided empirical Bernstein: two applications of Maurer-Pontil Thm 4."""
    x=np.asarray(x,float);n=len(x)
    if n<2:return low,high
    if np.min(x)<low or np.max(x)>high:raise ValueError('bound domain violated')
    log=np.log(4/alpha)
    radius=np.sqrt(2*np.var(x,ddof=1)*log/n)+7*(high-low)*log/(3*(n-1))
    return max(low,float(x.mean()-radius)),min(high,float(x.mean()+radius))
def risk_difference(a,b,alpha=.05):
    n=len(a);plus=int(np.sum((a==1)&(b==0)));minus=int(np.sum((a==0)&(b==1)))
    lp,up=cp(plus,n,alpha/2);lm,um=cp(minus,n,alpha/2)
    return plus,minus,lp-um,up-lm
def gain_interval(a,b,alpha=.05):
    ap,au=eb(a,alpha/2);bp,bu=eb(b,alpha/2)
    return 1-au/bp,1-ap/bu
def summarize(samples,label):
    rows=[];paired=[];n=len(samples);alpha=.05/12
    if not np.all(np.isfinite(samples)):raise ArithmeticError('computational failures: no complete-sample inference')
    for j,name in enumerate(NAMES):
        k=int(samples[:,j,0].sum());live=samples[:,j,0]==0;x=samples[live,j,1];lo,hi=cp(k,n);ml,mh=eb(x)
        fl,fu=cp(k,n,alpha)
        rows.append(dict(case=label,policy=name,trials=n,first_Ecap=k,F_hat=k/n,F95_low=lo,F95_high=hi,F95_upper=upper(k,n),
            primary_family_low=fl if j<2 else '',primary_family_upper=fu if j<2 else '',survivors=int(live.sum()),
            passes_survivor_mean=float(x.mean()) if len(x) else '',passes_survivor95_low=ml,passes_survivor95_high=mh,
            passes_stop_mean=float(samples[:,j,1].mean()),busy_stop_mean_s=float(samples[:,j,2].mean()),
            reads_stop_mean=float(samples[:,j,3].mean()),writes_stop_mean=float(samples[:,j,4].mean()),
            partial_reads_stop_mean=float((samples[:,j,3]-samples[:,j,1]*2097152).mean()),
            partial_writes_stop_mean=float((samples[:,j,4]-samples[:,j,1]*2097152).mean()),computational_failures=0))
    for j in [1,4]:
        a=samples[:,0,0];b=samples[:,j,0];live=(a==0)&(b==0);x=samples[live,0,1];y=samples[live,j,1]
        plus,minus,dl,du=risk_difference(a,b);_,_,fdl,fdu=risk_difference(a,b,alpha)
        gl,gu=gain_interval(x,y);fgl,fgu=gain_interval(x,y,alpha);pl,pu=eb(y-x,low=-17988,high=17988)
        paired.append(dict(case=label,comparator=NAMES[j],both_survive=int(live.sum()),proposed_only_Ecap=plus,comparator_only_Ecap=minus,both_Ecap=int(np.sum((a==1)&(b==1))),
             proposed_minus_comparator_risk=float((a-b).mean()),risk_diff95_low=dl,risk_diff95_high=du,
             primary_family_risk_diff_low=fdl if j==1 else '',primary_family_risk_diff_high=fdu if j==1 else '',
             proposed_passes_on_J=float(x.mean()) if len(x) else '',comparator_passes_on_J=float(y.mean()) if len(y) else '',
             saved_passes_on_J=float((y-x).mean()) if len(x) else '',saved_passes95_low=pl,saved_passes95_high=pu,
             G_J=1-float(x.mean()/y.mean()) if len(x) else '',G95_low=gl,G95_high=gu,
             primary_family_G_low=fgl if j==1 else '',primary_family_G_high=fgu if j==1 else ''))
    return rows,paired

def fixed300(rates):
    # Exact rational arithmetic on the declared binary64 rates and P.
    # Word j checks at 300*k-d_j, d_j=P*(W-1-j)/W. Include both edges.
    from fractions import Fraction as F
    from decimal import Decimal, localcontext, ROUND_CEILING
    W=524288;P=F(.18874368);r=[F(float(v)) for v in rates]
    assert len(r)==12 and min(r)>=0
    d=P*(W-1)/(2*W);d2=P*P*(W-1)*(2*W-1)/(6*W*W)
    a=300*300-600*d+d2;b=2*(300*d-d2)
    squares=a*r[0]**2+d2*r[-1]**2
    for old,new in zip(r[:-1],r[1:]):squares+=a*new**2+b*old*new+d2*old**2
    q=min(F(1),F(31,64*W)*squares)
    coarse=min(F(1),F(31,64*W)*max(r)**2*300*3600)
    with localcontext() as c:
        c.prec=60;c.rounding=ROUND_CEILING
        dec=Decimal(q.numerator)/Decimal(q.denominator)
        return dict(period_s=300,upper_decimal_ceiling=str(dec),upper=float(np.nextafter(float(dec),np.inf)),
                    exact_numerator=str(q.numerator),exact_denominator=str(q.denominator),coarse_max_rate_upper=float(coarse),
                    status='SUFFICIENT' if q<=F(1,10) else 'NOT_ESTABLISHED',
                    argument='distinct-bit pair union bound on every actual word-check gap, including initial and terminal gaps; exact rational sum')

def verify_prereg(sha_id):
    subprocess.run(['git','merge-base','--is-ancestor',sha_id,'HEAD'],cwd=HERE,check=True)
    for name in ['prepare.py','experiment.py','check.py','config.json','PREREGISTRATION.md','selected_windows.json','derived_rates.csv','input_manifest.json']:
        p=HERE/name
        rel=p.relative_to(HERE.parents[1]).as_posix()
        blob=subprocess.check_output(['git','show',sha_id+':'+rel],cwd=HERE)
        if hashlib.sha256(blob).hexdigest()!=sha(p):raise ValueError('prereg drift: '+str(p))
    mf=json.loads((HERE/'input_manifest.json').read_text(encoding='utf-8'))
    for path,digest in mf['pipeline_hashes'].items():
        if sha(HERE.parents[1]/path)!=digest:raise ValueError('upstream drift: '+path)

def run_case(a):
    verify_prereg(a.prereg);cfg=json.loads((HERE/'config.json').read_text());n=cfg['trials_per_unique_window']
    w=next(x for x in json.loads((HERE/'selected_windows.json').read_text())['windows'] if a.case in x['labels'])
    utc=int(datetime.fromisoformat(w['utc']).timestamp())//300
    a.out.mkdir(parents=True,exist_ok=True);start=time.perf_counter();m,p,cert=model();buf=buffers(p)
    samples=np.full((n,5,8),np.nan);hashes=[];counts=[];failures=[]
    for i in range(n):
        ev=stream(w['nu_array_s-1'],utc,i);h=event_hash(ev);hashes.append(h);counts.append(len(ev[0]))
        for j,policy in enumerate(POLICIES):
            try:
                result,_=execute(ev,p,policy,buf);samples[i,j]=result[:8]
                assert event_hash(ev)==h
            except Exception as exc:
                failures.append(dict(trial=i,policy=NAMES[j],event_sha256=h,error=repr(exc)))
                buf=buffers(p)
        if (i+1)%1000==0:print(a.case,i+1,'/',n,flush=True)
    np.savez_compressed(a.out/(a.case+'_trials.npz'),samples=samples,event_hashes=np.array(hashes),event_counts=np.array(counts),utc_index=utc)
    dump(a.out/(a.case+'_failures.json'),failures)
    if not failures:
        rows,paired=summarize(samples,a.case);csvwrite(a.out/(a.case+'_policies.csv'),rows);csvwrite(a.out/(a.case+'_paired.csv'),paired)
    # Exactly one predeclared illustration, never searched for a pleasing trace.
    ev=stream(w['nu_array_s-1'],utc,0,2026091602);result,tr=execute(ev,p,POLICIES[0],record=True)
    csvwrite(a.out/(a.case+'_illustration.csv'),[dict(zip(TRACE,r)) for r in tr])
    dump(a.out/(a.case+'_run.json'),dict(case=a.case,prereg=a.prereg,utc=w['utc'],trials=n,computational_failures=len(failures),
         seconds=time.perf_counter()-start,trial_file_sha256=sha(a.out/(a.case+'_trials.npz')),certificate=cert,
         fixed300=fixed300(w['nu_array_s-1']),illustration_result=result.tolist(),illustration_event_hash=event_hash(ev),
         python=platform.python_version(),numpy=np.__version__,peak_memory_bytes=__import__('psutil').Process().memory_info().peak_wset))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--case',choices=['growth','peak','typical'],required=True);ap.add_argument('--prereg',required=True);ap.add_argument('--out',type=Path,required=True)
    run_case(ap.parse_args())

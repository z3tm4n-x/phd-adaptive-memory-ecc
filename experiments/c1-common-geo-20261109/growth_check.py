"""Test bin integrals against the theorist's one-sided growth class, including holes."""
import argparse
from decimal import Decimal, ROUND_CEILING
import gzip
import json
import math
from pathlib import Path
import numpy as np
from cadence import samples, EPOCH
from coverage import (CAP, environment, goes_observed, sepem_series, write_or_check)
from minute_sources import selected
from prior import HERE, activate, EXPERIMENTS


def selection(cadence):
    contenders=[('SEPEM 5min',cadence['SEPEM']['nu_slope_s_inv2']['slope'])]
    for key,by_dt in cadence['native'].items():
        for dt,metrics in by_dt.items():
            result=metrics['nu_slope_s_inv2']
            if result:contenders.append((key+' '+dt,result['slope']))
    winner,slope=max(contenders,key=lambda item:item[1])
    value=(2*Decimal.from_float(slope)).quantize(Decimal('0.000000001'),rounding=ROUND_CEILING)
    return winner,slope,value


def exact_and_construction(times,averages,dt,R,g,b,full_T=None):
    """All finite bins in chronological order. Unknown intervals retain their exposure."""
    ok=np.isfinite(averages)
    m=np.maximum(averages[ok]-b,0.); t=np.asarray(times)[ok]
    if not len(t):return {'bins':0,'status':'no measured bins'}
    if np.any(np.diff(t)<dt):raise ValueError('Overlapping bins in this reconstruction')
    gap=np.r_[t[0] if full_T else 0,np.diff(t)-dt]
    if (gap<0).any():raise ValueError('Negative gap')
    # With free startup the first mean may already be high. On a hole drop to
    # max(0,z-gG), then rise to z. This explicitly pays the gap integral.
    prev=np.r_[R,m[:-1]]
    z=np.minimum(m,prev+g*gap)
    z[0]=m[0]
    gap_area=(z+np.maximum(0.,z-g*gap))*np.minimum(gap,z/g)/2
    endpoint=2*m-z
    slopes=(endpoint-z)/dt
    crest=float(np.max(endpoint)); sharp=float(np.max(slopes))
    # Forward reachability as specified in #196/186, from U(0)=R.
    U=R; worst=-math.inf
    for G,mean in zip(gap.tolist(),m.tolist()):
        U=min(R,U+g*G)
        upper_mean=U+g*dt/2 if U+g*dt<=R else R-(R-U)**2/(2*g*dt)
        worst=max(worst,mean-upper_mean)
        Y=math.sqrt(2*g*dt*mean) if mean<=g*dt/2 else mean+g*dt/2
        U=min(R,U+g*dt,Y)
    result={'bins':len(m),'exact_max_mean_minus_reachable_s_inv':worst,
            'exact_feasible':bool(worst<=1e-14 and np.max(m)<=R),
            'constructed_max_excess_s_inv':crest,'constructed_max_slope_s_inv2':sharp,
            'constructed_feasible':crest<=R and sharp<=g+2e-16,
            'witness_excess_on_gaps':math.fsum(gap_area),'observed_excess':dt*math.fsum(m)}
    if full_T:
        assert int(t[-1])+dt<=full_T
        result['terminal_gap_s']=int(full_T-t[-1]-dt)
        result['constructed_full_S1']=b*full_T+result['observed_excess']+result['witness_excess_on_gaps']
        result['within_exposure_quota']=result['constructed_full_S1']<=float(CAP)
    return result


def run(previous,minutes,gc,sc):
    prev=activate(previous)
    cadence=json.loads((HERE/'cadence.json').read_text(encoding='utf-8'))
    winner,slope,g=selection(cadence)
    env,T,F=environment();R=float(env['B']-env['b']);b=float(env['b'])
    nu,_,_,_,_=sepem_series(sc,prev)
    profiles={'SEPEM_archive':exact_and_construction(np.arange(len(nu))*300,nu,300,R,float(g),b)}
    rates,_,_,info=goes_observed(gc,prev)
    for d,name in enumerate(('East','West')):
        profiles['GOES_composite_5min_'+name]=exact_and_construction(np.arange(len(rates))*300,rates[:,d],
                                                                     300,R,float(g),b,int(T))
    with gzip.open(EXPERIMENTS/'t67-goes-growth/outputs/file_audits.json.gz','rt',encoding='utf-8') as f:
        known=json.load(f)
    # Signature boundaries matter for observed-difference selection; the feasibility
    # recursion here never resets, including at a boundary or repeated rise.
    ids={q:i for i,q in enumerate(sorted({r['signature'] for r in known}))}
    signatures={r['name']:ids[r['signature']] for r in known}
    for s in (16,18,19):
        t,v,_,_=samples(selected(),minutes/'folded',60,s,signatures,info)
        for d,name in enumerate(('East','West')):
            profiles[f'G{s}_1min_{name}']=exact_and_construction(t,v[:,d],60,R,float(g),b,int(T))
    return {'g_s_inv2':str(g),'selection_source':winner,'s_obs_s_inv2':slope,'R_s_inv':R,
            'delta_g_s_inv2':1e-9,'r0':'any in [0,R], hidden; clean initialized memory','profiles':profiles}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('previous','minutes','goes-cache','sepem-cache'):p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('--check',action='store_true');args=p.parse_args()
    result=run(args.previous,args.minutes,args.goes_cache,args.sepem_cache)
    write_or_check(HERE/'growth.json',result,args.check)
    print('g',result['g_s_inv2'],[(k,v['exact_feasible'],v['constructed_feasible']) for k,v in result['profiles'].items()])

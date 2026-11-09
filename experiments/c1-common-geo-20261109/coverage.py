"""Exposure and peak tests on the common reference array; no zero filling of GOES."""
import argparse
from fractions import Fraction as F
import gzip
import json
import math
from pathlib import Path
import numpy as np
from prior import HERE, EXPERIMENTS, activate

CAP = F(187464)


def environment():
    import fixed
    env = fixed.environment()
    return env, fixed.T, CAP-env['b']*fixed.T


def sepem_series(cache,previous):
    import sepem
    bands,_,_=sepem.verified_arrays(cache,None)
    info=json.loads((previous/'sepem.json').read_text(encoding='utf-8'))
    h=bands[:,1,0]+bands[:,1,1]; solar=np.maximum(h-info['H_p10'],0.)
    rate=info['background_per_s']+(1+info['HI_to_H'])*solar
    return rate,h,solar,bands,info


def sepem_check(cache,windows,previous):
    import sepem
    env,T,quota=environment()
    nu,h,solar,bands,info=sepem_series(cache,previous)
    width=int(T)//300
    with np.load(windows) as data:
        s1=data['S1'];s2=data['S2']
    assert s1.size==len(nu)-width+1 and np.isfinite(s1).all()
    i=int(np.argmax(s1))
    direct=300*math.fsum(nu[i:i+width])
    assert math.isclose(direct,float(s1[i]),rel_tol=2e-15)
    assert math.isclose(300*math.fsum(float(v)**2 for v in nu[i:i+width]),s2[i],rel_tol=2e-15)
    upper2=env['b']**2*T+(env['B']+env['b'])*quota
    common_R=float(T*upper2)/s1**2
    high=np.flatnonzero(nu[:len(s1)]>float((env['B']+env['b'])/2))
    # The reconstruction subtracts one H floor, not individual channel floors.
    # Allocate surviving H excess in proportion to the two simultaneous raw bands.
    ratio=np.divide(solar,h,out=np.zeros_like(h),where=h>0)
    components={}
    for name,excess in [('H_low',bands[:,1,0]*ratio),('H_high',bands[:,1,1]*ratio),
                        ('LET_exclusive',info['HI_to_H']*solar)]:
        prefix=np.r_[0.,np.cumsum(excess,dtype=np.float64)]
        amount=300*(prefix[width:]-prefix[:-width])
        j=int(np.argmax(amount))
        old=env['rates']['solar'][name]
        components[name]={'old_peak':str(old),'old_exposure':str(old*env['tau']),
          'diagnostic_excess_peak':float(np.max(excess)),
          'diagnostic_largest_window_exposure':300*math.fsum(excess[j:j+width]),
          'approximately_maximizing_start':sepem.stamp(j)}
    return {'windows':len(s1),'above_T141':int(np.count_nonzero(s1>float(env['S1']))),
            'above_187463':int(np.count_nonzero(s1>187463)),'above_cap':int(np.count_nonzero(s1>float(CAP))),
            'max_S1_by_fsum':direct,'max_S1_start':sepem.stamp(i),'max_S2':float(np.max(s2)),
            'peak_s_inv':float(np.max(nu)),'above_B_bins':int(np.count_nonzero(nu>float(env['B']))),
            'high_starts':[sepem.stamp(j) for j in high],'max_r0_zero_g_necessary_s_inv2':2*(float(np.max(nu))-float(env['b']))/300,
            'component_diagnostics':components,'positive_exposure_quota':str(quota),
            'class_ratio':float(T*upper2/CAP**2),'R_on_window_S1':{'range':[float(common_R.min()),float(common_R.max())],
                'quantiles':sepem.empirical(common_R)}}


def goes_observed(cache,previous):
    import goes_profile as g
    with gzip.open(previous/'goes-sources.json.gz','rt',encoding='utf-8') as stream:
        source=json.load(stream)
    summary=json.loads((previous/'goes.json').read_text(encoding='utf-8'))
    cube,sats,_,_=g.composite(cache,source['receipt']['folded'])
    rates=np.empty(sats.shape,dtype='float64')
    for d,direction in enumerate(('East','West')):
        ref=summary['directions'][direction]
        h=cube[:,d,0]+cube[:,d,1]
        rates[:,d]=summary['background_s_inv']+(1+summary['HI_to_H'])*np.maximum(h-ref['proton_p10_per_s'],0.)
        assert np.isfinite(rates[:,d]).sum()==ref['covered_bins']
    return rates,sats,cube[:,:,4],summary


def goes_check(cache,previous):
    env,T,quota=environment()
    rates,_,_,info=goes_observed(cache,previous)
    result={}
    for d,direction in enumerate(('East','West')):
        ref=info['directions'][direction]; observed=rates[:,d][np.isfinite(rates[:,d])]
        s1=F.from_float(300*math.fsum(observed))
        assert math.isclose(float(s1),ref['S1_observed'],rel_tol=1e-14)
        actual=300*len(observed);gap=T-actual; excess=s1-env['b']*actual
        allowance=quota-excess
        result[direction]={'covered_bins':len(observed),'covered_s':actual,
            'S1_obs':float(s1),'S2_obs':ref['S2_observed_s_inv'],'observed_excess':float(excess),
            'calendar_holes_s':info['calendar_duration_s']-actual,
            'unobserved_terminal_s':int(T)-info['calendar_duration_s'],'unobserved_over_T_s':int(gap),
            'allowed_unobserved_total':float(CAP-s1),'allowed_unobserved_excess':float(allowance),
            'allowed_mean_excess_s_inv':float(allowance/gap),'peak_only_excess_ceiling':float((env['B']-env['b'])*gap),
            'above_B_bins':int(np.count_nonzero(observed>float(env['B']))),'peak_obs':float(observed.max())}
    return result


def write_or_check(path,data,check):
    text=json.dumps(data,default=str,indent=2,ensure_ascii=False)+'\n'
    if check:
        if path.read_text(encoding='utf-8')!=text:raise SystemExit('Mismatch: '+path.name)
    else:path.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('previous','sepem-cache','windows','goes-cache'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--check',action='store_true');args=p.parse_args();prev=activate(args.previous)
    env,T,quota=environment()
    result={'D':38*524288,'T_s':int(T),'b_s_inv':str(env['b']),'B_s_inv':str(env['B']),
        'old_S1':str(env['S1']),'S1_cap':str(CAP),'bT':str(env['b']*T),'F_r':str(quota),
        'S2_upper':str(env['b']**2*T+(env['B']+env['b'])*quota),
        'SEPEM':sepem_check(args.sepem_cache,args.windows,prev),'GOES':goes_check(args.goes_cache,prev)}
    write_or_check(HERE/'coverage.json',result,args.check)
    print('Checked SEPEM windows and GOES masks',result['SEPEM']['windows'],result['GOES']['West']['allowed_unobserved_excess'])

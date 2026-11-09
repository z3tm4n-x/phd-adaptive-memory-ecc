"""Independent moment sums on the identified windows, and edge checks on both catalogues."""
import argparse
from datetime import datetime
from fractions import Fraction as F
from math import fsum, isclose
from pathlib import Path

import numpy as np

from fixed import read
import sepem


def verify_sepem(cache, windows):
    source=read(sepem.HERE/'sepem.json')
    bands,_,_=sepem.verified_arrays(cache,None)
    h=bands[:,1,0]+bands[:,1,1]
    series=source['background_per_s']+(1+source['HI_to_H'])*np.maximum(h-source['H_p10'],0.)
    width=source['T_s']//sepem.STEP
    with np.load(windows) as saved:
        assert set(saved.files)=={'S1','S2','k','R'}
        arrays={key:saved[key] for key in saved.files}
    for key in ('S1','S2','k'):
        assert int(np.argmax(arrays[key]))==source['maxima'][key]['start_bin']
    assert len(arrays['R'])==len(series)-width+1==source['window_count']
    assert np.array_equal(arrays['R'],source['T_s']*max(arrays['S2'])/arrays['S1']**2)
    for i in {0,273,850000,len(arrays['R'])-1,*(v['start_bin'] for v in source['maxima'].values())}:
        v=series[i:i+width]
        s1=sepem.STEP*fsum(v)
        s2=sepem.STEP*fsum(float(x)**2 for x in v)
        values=s1,s2,source['T_s']*s2/s1**2
        for key,val in zip(('S1','S2','k'),values):
            assert isclose(arrays[key][i],val,rel_tol=4e-15)
    tiny=[1.,1.,2.,1.,2.,1.]
    _,ext,_=sepem.sliding(np.array(tiny),2)
    combos=[tuple(map(F,tiny[i:i+2])) for i in range(len(tiny)-1)]
    for key,fn in [('S1',sum),('S2',lambda x:sum(a*a for a in x)),
                   ('k',lambda x:2*sum(a*a for a in x)/sum(x)**2)]:
        val=[fn(x) for x in combos]
        assert (ext[key][0],ext[key][3])==(val.index(max(val)),val.count(max(val)))
    runs=sepem.positive_runs(np.array([1.,2.,5.,np.nan,12.,14.]),19)
    assert [(r[0],r[1],r[4]) for r in runs]==[(19,21,20),(23,24,23)]
    print('PASS: independent SEPEM sums, all extrema, R column, ties, gap and global rise indices')


def verify_goes(cache):
    import goes_profile as g
    import gzip
    import json
    data=read(g.HERE/'goes.json')
    with gzip.open(g.HERE/'goes-sources.json.gz','rt',encoding='utf-8') as f:
        sources=json.load(f)
    with gzip.open(g.HERE/'goes-events.json.gz','rt',encoding='utf-8') as f:
        events=json.load(f)
    receipt=sources['receipt']; urls={r['url'] for r in receipt['folded']}
    missing=set(receipt['errors'])
    assert urls.isdisjoint(missing)
    assert urls|missing==set(sources['index']['selected_daily']+[sources['index']['special']])
    assert sum(v['files'] for v in sources['signatures'].values())==len(urls)
    # Build the same selector in reverse priority, overwriting overlaps only with valid data.
    rates=np.full((g.NBINS,2),np.nan)
    seen=np.zeros((g.NBINS,2),dtype=np.int8)
    for rec in sorted(receipt['folded'],key=lambda r:r['satellite'],reverse=True):
        with np.load(cache/'derived'/(rec['name']+'.npz')) as obs:
            idx=obs['index'];v=obs['values']; keep=(idx>=0)&(idx<g.NBINS)
            for d in range(2):
                h=v[:,d,0]+v[:,d,1];ok=keep&np.isfinite(h)
                rates[idx[ok],d]=h[ok];seen[idx[ok],d]=rec['satellite']
    for d,direction in enumerate(('East','West')):
        row=data['directions'][direction]
        observed=rates[np.isfinite(rates[:,d]),d]
        reconstructed=data['background_s_inv']+(1+data['HI_to_H'])*np.maximum(observed-np.quantile(observed,.1),0.)
        s1=g.DT*fsum(reconstructed);s2=g.DT*fsum(float(x)**2 for x in reconstructed)
        assert isclose(s1,row['S1_observed'],rel_tol=1e-14) and isclose(s2,row['S2_observed_s_inv'],rel_tol=1e-14)
        assert row['covered_bins']*g.DT+row['missing_s']==g.NBINS*g.DT
        for sat,n in row['selected_bins_by_satellite'].items():
            assert n==np.count_nonzero(seen[:,d]==int(sat))
        for e in events[direction]:
            start=int((datetime.fromisoformat(e['onset'])-g.FIRST).total_seconds())//g.DT
            stop=int((datetime.fromisoformat(e['end'])-g.FIRST).total_seconds())//g.DT
            assert stop>=start and 0<=e['covered_rate_s']<=e['calendar_span_s']
            rises=([e['initial_rise']] if e['initial_rise'] else [])+e['repeated_rises']
            for a,b,left,right,j,slope in rises:
                assert start<=a<=j<b<stop and right>left and slope>0 and np.all(np.isfinite(rates[a:b+1,d]))
    assert data['calendar_duration_s']<data['required_T_s'] and data['full_decades']==0
    assert data['k_class'] is None and data['R'] is None
    print('PASS: GOES source coverage, independent selection and sums, event edges and missing decades')


def verify_response(path):
    """Direct quadrature on one measured spectrum, independent of the basis kernel."""
    from scipy.integrate import quad
    import goes_profile as g
    src=g.sgps.read(path)
    _,values,_=g.fold(path)
    i,d=np.unravel_index(np.nanargmax(values[:,:,0]+values[:,:,1]),values.shape[:2])
    sensor=1-d if src.yaw[i]==0 else d
    spec=src.corrected[i,d]
    energy=src.energy[sensor]; left,right=src.lower[sensor,0],src.upper[sensor,-1]
    tab=g.transport.RangeTable(); rho=3
    threshold=tab.inverse(rho+tab.range(5.))
    # Split at all response/transport branches before adaptive integration.
    knots=np.unique(np.r_[5.,10.,30.,energy,tab.energy,tab.inverse(rho),
        tab.inverse(rho+tab.range(np.r_[.001,5.,g.transport.sigma_module.zero_crossing_low(g.transport.POINTS),
                                         g.transport.SIGMA_E,tab.energy])),right])
    points=knots[(knots>5.)&(knots<right)]
    def flux(e):
        return np.interp(np.log(e),np.log(energy),spec[:13])
    def folded(e):
        residual=tab.residual(np.array([e]),rho)
        return 4*np.pi*g.transport.BITS*flux(e)*g.transport.sigma(residual)[0]
    def integrate(fun,lo,hi):
        return quad(fun,lo,hi,points=points[(points>lo)&(points<hi)],limit=400,epsabs=2e-15,epsrel=1e-9)[0]
    valid=np.all(np.isfinite(src.corrected),axis=2)
    gap,_,_=g.response.gap_bridge(src.corrected,valid)
    tail=gap[i,d]+spec[13]
    high_tail=4*np.pi*g.transport.BITS*tail*g.transport.sigma(tab.residual(np.array([500.]),rho))[0]
    expected=[integrate(folded,max(5.,left),threshold),integrate(folded,threshold,right)+high_tail,
              integrate(flux,10.,right)+tail,4*np.pi*(integrate(flux,30.,right)+tail)]
    for j,expected_value in enumerate(expected):
        measured=values[i,d,j]
        if j<2 or np.isfinite(measured):
            assert isclose(measured,expected_value,abs_tol=2e-14,rel_tol=2e-9),(measured,expected_value)
    print('PASS: direct CSDA/proton spectral integrals',path.name)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sepem-cache',type=Path);parser.add_argument('--windows',type=Path)
    parser.add_argument('--goes-cache',type=Path);parser.add_argument('--response-file',type=Path);args=parser.parse_args()
    if bool(args.sepem_cache)!=bool(args.windows):parser.error('SEPEM requires the cache and window file together')
    if not (args.sepem_cache or args.goes_cache or args.response_file):parser.error('Select an archive')
    if args.sepem_cache:verify_sepem(args.sepem_cache,args.windows)
    if args.goes_cache:verify_goes(args.goes_cache)
    if args.response_file:verify_response(args.response_file)


if __name__=='__main__':main()

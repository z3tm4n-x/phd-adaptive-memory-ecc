"""The theorist's prepaid positive-variation quota on the frozen PR423 reconstructions."""
import argparse
from fractions import Fraction as F
import gzip
import json
import math
from pathlib import Path
import numpy as np
from observations import DT,T,WIDTH,HERE,save,setup
from strict import dates,G_MAIN


def maxima(rows,values,j,label):
    """Compare in exact binary units and keep the earliest maximizing start."""
    best=rows.get(label)
    if best is None or values>best[0]:rows[label]=[values,j,1]
    elif values==best[0]:best[2]+=1


def sepem_windows(m,width):
    bits=53-math.frexp(float(m[m>0].min()))[1]
    unit=1<<bits
    levels=[int(math.ldexp(float(val),bits)) for val in m]
    up=[0]+[max(0,y-x) for x,y in zip(levels,levels[1:])]
    total=sum(up[:width]);n=len(m)-width+1
    columns=np.empty((n,3),dtype=np.float64);records={}
    for j in range(n):
        z=levels[j]-up[j]
        lower=z+total; aligned=z+2*total
        left=levels[j-1]+up[j-1]+2*total if j else aligned
        columns[j]=(lower/unit,aligned/unit,left/unit if j else np.nan)
        maxima(records,lower,j,'bin_lower')
        maxima(records,aligned,j,'aligned_reconstruction')
        if j:maxima(records,left,j,'left_limit_reconstruction')
        if j+1<n:total+=up[j+width]-up[j]
    out={key:{'value_s_inv':val/unit,'exact_fraction':str(F(val,unit)),
        'index':idx,'start_or_limit_utc':dates(idx),'stop_or_limit_utc':dates(idx+width),'ties':ties}
         for key,(val,idx,ties) in records.items()}
    return columns,out


def event_parts(m,events,index,width,left_limit):
    label=np.full(len(m),-1,dtype=np.int16)
    first=np.zeros(len(m),dtype=bool)
    for j,e in enumerate(events):
        a=e['start_bin'];b=e['stop_bin']
        assert np.all(label[a:b]<0)
        label[a:b]=j
        r=e['initial_positive_run']
        if r:first[r[0]+1:r[1]+1]=True
    up=np.r_[0.,np.maximum(0.,np.diff(m))]
    prev=np.r_[-1,label[:-1]]
    within=(label>=0)&(label==prev);outside=(label<0)&(prev<0)
    masks={'first_rise_within_event':within&first,'repeated_rises_within_event':within&~first,
           'outside_catalogue':outside,'cross_catalogue_boundary':~within&~outside}
    sl=slice(index,index+width)
    parts={k:2*math.fsum(up[sl][mask[sl]]) for k,mask in masks.items()}
    parts['left_charge']=float(m[index-1]+up[index-1] if left_limit else m[index]-up[index])
    parts['sum']=math.fsum(parts.values())
    return parts


def sepem_result(sc,old,export):
    from coverage import sepem_series
    from sepem import empirical
    with gzip.open(old/'sepem-events.json.gz','rt',encoding='utf-8') as f:events=json.load(f)
    nu,_,_,_,info=sepem_series(sc,old);m=nu-info['background_per_s']
    data,rec=sepem_windows(m,WIDTH)
    for key,left in [('aligned_reconstruction',False),('left_limit_reconstruction',True)]:
        r=rec[key];parts=event_parts(m,events,r['index'],WIDTH,left)
        assert math.isclose(parts['sum'],r['value_s_inv'],rel_tol=2e-15)
        r['pieces_at_maximum']=parts
    i=np.arange(len(data))
    starts=np.array([e['start_bin'] for e in events]);stops=np.array([e['stop_bin'] for e in events])
    counts=np.searchsorted(starts,i+WIDTH)-np.searchsorted(starts,i)
    residual=np.searchsorted(starts,i)-np.searchsorted(stops,i,side='right')
    right=np.searchsorted(starts,i+WIDTH)-np.searchsorted(stops,i+WIDTH,side='right')
    assert (residual>=0).all() and (right>=0).all()
    if export:np.savez_compressed(export,bin_lower=data[:,0],aligned=data[:,1],left_limit=data[:,2],catalogue_starts=counts)
    return {'bins':len(m),'windows':len(data),'maxima':rec,'quantiles':{
        'bin_lower':empirical(data[:,0]),'aligned':empirical(data[:,1]),'left_limit':empirical(data[1:,2])},
        'catalogued_starts_range':[int(counts.min()),int(counts.max())],'catalogued_starts_median':float(np.median(counts)),
        'windows_with_active_event_at_left':int(np.sum(residual>0)),'windows_with_active_event_at_right':int(np.sum(right>0)),
        'total_events':len(events),'events_with_repeated_rises':sum(bool(e['repeated_positive_runs']) for e in events)}


def profile_J(t,v,dt,b,g,events):
    ok=np.isfinite(v)
    t=np.asarray(t)[ok];m=v[ok]-b
    assert len(t) and np.all(m>=0) and t[0]>=0 and t[-1]+dt<=T
    gap=np.r_[t[0],np.diff(t)-dt]; assert np.all(gap>=0)
    z=np.minimum(m,np.r_[m[0],m[:-1]+g*gap[1:]])
    intra=2*(m-z);rise_holes=np.minimum(z,g*gap)
    start=float(z[0]-rise_holes[0])
    gap_area=(z+np.maximum(0.,z-g*gap))*np.minimum(gap,z/g)/2
    dif=np.r_[0.,np.maximum(0.,np.diff(m))]
    catalogue=np.full(len(t),-1,dtype=int);end_status={}
    from cadence import stamp
    for j,e in enumerate(events):
        a,zend=np.searchsorted(t,[stamp(e['onset']),stamp(e['end'])])
        catalogue[a:zend]=j
        reason=e['end_status']
        end_status[reason]=end_status.get(reason,0)+1
    prior=np.r_[-1,catalogue[:-1]]
    same=(catalogue>=0)&(prior==catalogue)
    outside=(catalogue<0)&(prior<0)
    rec=start+math.fsum(rise_holes)+math.fsum(intra)
    return {'valid_bins':len(m),'covered_s':len(m)*dt,'unobserved_s':T-len(m)*dt,
        'leading_gap_s':int(t[0]),'terminal_gap_s':int(T-t[-1]-dt),
        'interior_gaps':int((gap[1:]>0).sum()),'interior_gap_s':int(np.sum(gap[1:])),
        'bin_lower_s_inv':float(m[0])+math.fsum(dif),
        'lower_initial_mean':float(m[0]),'lower_adjacent_increments':math.fsum(dif[gap==0]),
        'lower_increments_across_holes':math.fsum(dif[gap>0]),
        'lower_increment_event_parts':{'within_catalogued_event':math.fsum(dif[same]),
            'outside_catalogue':math.fsum(dif[outside]),'catalogue_boundaries':math.fsum(dif[~same&~outside])},
        'reconstruction_J_s_inv':rec,'reconstruction_initial_level':start,
        'reconstruction_rises_on_holes':math.fsum(rise_holes),'reconstruction_rises_in_measured_bins':math.fsum(intra),
        'reconstruction_excess_integral_on_holes':math.fsum(gap_area),'peak_excess':float(max(2*m-z)),
        'max_slope':float(max(intra)/dt),'catalogue_end_status':end_status}


def goes_result(gc,mc,old):
    from coverage import goes_observed
    from minute_sources import selected
    from cadence import samples
    from prior import EXPERIMENTS
    rates,_,_,info=goes_observed(gc,old);b=info['background_s_inv']
    with gzip.open(old/'goes-events.json.gz','rt',encoding='utf-8') as f:events=json.load(f)
    out={}
    for d,n in enumerate(('East','West')):
        out['composite_5min_'+n]=profile_J(np.arange(len(rates))*DT,rates[:,d],DT,b,G_MAIN,events[n])
    with gzip.open(EXPERIMENTS/'t67-goes-growth/outputs/file_audits.json.gz','rt',encoding='utf-8') as f:audit=json.load(f)
    lut={s:i for i,s in enumerate(sorted({r['signature'] for r in audit}))}
    sig={r['name']:lut[r['signature']] for r in audit}
    for s in (16,18,19):
        t,v,_,_=samples(selected(),mc/'folded',60,s,sig,info)
        for d,n in enumerate(('East','West')):
            out[f'G{s}_1min_'+n]=profile_J(t,v[:,d],60,b,G_MAIN,events[n])
    return out


def run(args):
    common,old=setup(args.common,args.previous)
    s=sepem_result(args.sepem_cache,old,args.export_windows)
    goes=goes_result(args.goes_cache,args.minutes,old)
    maxima={k:F(v['exact_fraction']) for k,v in s['maxima'].items() if k!='bin_lower'}
    maxima.update({k:F.from_float(v['reconstruction_J_s_inv']) for k,v in goes.items()})
    key=max(maxima,key=maxima.get);top=maxima[key];quota=F(math.ceil(1000*top),1000)
    assert 0<=quota-top<F(1,1000)
    for v in goes.values():
        v['allowance_beyond_bin_lower']=float(quota)-v['bin_lower_s_inv']
        v['headroom_after_reconstruction']=float(quota)-v['reconstruction_J_s_inv']
    return {'g_nominal_s_inv2':G_MAIN,'winner':key,'largest_reconstructed_J_s_inv':float(top),
            'quota_exact':str(quota),'quota_s_inv':float(quota),'SEPEM':s,'GOES':goes}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('common','previous','sepem-cache','goes-cache','minutes'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--export-windows',type=Path);p.add_argument('--check',action='store_true');args=p.parse_args()
    result=run(args);save('variation.json',result,args.check)
    print(result['winner'],result['largest_reconstructed_J_s_inv'],result['quota_s_inv'])

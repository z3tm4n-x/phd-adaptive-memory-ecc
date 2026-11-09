"""Strict adjacent-pair coverage and exact reachability of every full SEPEM decade."""
import argparse
from datetime import datetime,timedelta,timezone
import gzip
import json
import math
from pathlib import Path
import numpy as np
from observations import HERE,DT,T,WIDTH,setup,save

G_MAIN=0.004392116
G_STRICT=0.000036055
START=datetime(1974,7,1,tzinfo=timezone.utc)


def sections(mask):
    edges=np.diff(np.r_[False,mask,False].astype(np.int8))
    return list(zip(np.flatnonzero(edges==1).tolist(),np.flatnonzero(edges==-1).tolist()))


def dates(i,start=START):
    return (start+timedelta(seconds=int(i)*DT)).isoformat().replace('+00:00','Z')


def window_coverage(n,width,pairs):
    count=n-width+1
    diff=np.zeros(count+1,dtype=np.int64)
    if pairs:
        i,j=np.asarray(pairs,dtype=np.int64).T
        left=np.maximum(0,j-width+1); right=np.minimum(i,count-1)
        ok=left<=right
        np.add.at(diff,left[ok],1);np.add.at(diff,right[ok]+1,-1)
    invalid=np.cumsum(diff[:-1])>0
    return invalid


def conflict_pairs(m,time,dt,R,g):
    """Latest incompatible predecessor per bin; a window fails exactly if it contains such a pair."""
    a=g*dt
    if np.any((m<0)|(m>R)) or np.any(np.diff(time)<dt):raise ValueError('Out-of-domain input')
    Y=np.where(m<=a/2,np.sqrt(2*a*m),m+a/2)
    Y=np.minimum(R,Y)
    # Least starting level that can produce mean m. The square-root form is
    # only active when the rising envelope reaches R before the end of the bin.
    L=np.where(m <= R-a/2,m-a/2,R-np.sqrt(2*a*(R-m))).clip(min=0.)
    U=R; bad=[];margin_min=math.inf;prev_end=int(time[0]) if len(time) else 0
    for j,(t,lower,y) in enumerate(zip(time.tolist(),L.tolist(),Y.tolist())):
        U=min(R,U+g*(t-prev_end))
        if U<lower:
            for i in range(j-1,-1,-1):
                elapsed=t-int(time[i])-dt
                if g*elapsed>=R:break
                separation=lower-(float(Y[i])+g*elapsed)
                if separation>0:
                    if separation<1e-12:raise ArithmeticError('Resolve marginal pair with directed arithmetic')
                    margin_min=min(margin_min,separation)
                    bad.append((i,j));break
            else:raise ArithmeticError('Missing predecessor')
            if not bad or bad[-1][1]!=j:raise ArithmeticError('No predecessor found')
        U=min(R,U+a,y);prev_end=t+dt
    return bad,None if not bad else margin_min


def native_counts(cadence):
    totals={};peaks={};detail={}
    for key,versions in cadence['native'].items():
        for dt,metrics in versions.items():
            val=metrics['strict_nu_slope_s_inv2']
            n=val['pairs'] if val else 0
            detail.setdefault(key,{})[dt]=n;totals[dt]=totals.get(dt,0)+n
            if val and (dt not in peaks or val['slope']>peaks[dt]['slope']):
                peaks[dt]={**val,'instrument_direction':key}
    return {'files_1min':cadence['minute_files'],'strict_pairs':totals,'breakdown':detail,'maxima':peaks}


def analyze_sepem(nu,g,R,b):
    m=nu-b;time=np.arange(len(m),dtype=np.int64)*DT
    bad,_=conflict_pairs(m,time,DT,R,g)
    adjacent=np.flatnonzero(np.diff(m)>g*DT)
    simple=window_coverage(len(m),WIDTH,[(int(i),int(i+1)) for i in adjacent])
    exact=window_coverage(len(m),WIDTH,bad)
    assert not np.any(simple&~exact)
    count=len(exact)
    return {'g_s_inv2':g,'adjacent_pairs_total':len(m)-1,'adjacent_violations':len(adjacent),
        'bad_bin_pairs_latest':len(bad),'window_count':count,'windows_with_adjacent_violation':int(simple.sum()),
        'windows_failing_exact':int(exact.sum()),'windows_passing_exact':int(count-exact.sum()),
        'windows_failing_only_exact':int((exact&~simple).sum()),
        'ranges_valid_starts_inclusive':[[dates(lo),dates(hi-1),hi-lo] for lo,hi in sections(~exact)],
        'ranges_invalid_starts_inclusive':[[dates(lo),dates(hi-1),hi-lo] for lo,hi in sections(exact)]}


def analyze_goes(rates,sats,strict,b,R,g,info):
    out={}
    for d,name in enumerate(('East','West')):
        v=rates[:,d]
        for mask_name,mask in [('screened',np.isfinite(v)),('strict_selected',strict[:,d]==1)]:
            good=mask&np.isfinite(v);t=np.flatnonzero(good).astype(np.int64)*DT
            m=v[good]-b
            bad,margin=conflict_pairs(m,t,DT,R,g)
            adj=(np.diff(t)==DT)&(np.diff(m)>g*DT)
            out[name+'_'+mask_name]={'covered_bins':len(t),'covered_s':len(t)*DT,'unobserved_to_T_s':T-len(t)*DT,
                'adjacent_violations':int(adj.sum()),'latest_conflict_pairs':len(bad),'compatible_bins':not bad,
                'smallest_reported_conflict_margin_s_inv':margin,
                'first_conflict_utc':[[int(t[bad[0][0]]),int(t[bad[0][1]])]] if bad else []}
    return out


def run(args):
    common,old=setup(args.common,args.previous)
    from coverage import environment,sepem_series,goes_observed
    env,_,_=environment();b=float(env['b']);R=float(env['B']-env['b'])
    c=json.loads((common/'cadence.json').read_text(encoding='utf-8'))
    n=native_counts(c)
    assert n['strict_pairs']=={'1min':0,'5min':787} and math.ceil(2*n['maxima']['5min']['slope']*1e9)/1e9==G_STRICT
    nu,_,_,_,_=sepem_series(args.sepem_cache,old)
    v,sats,st,info=goes_observed(args.goes_cache,old)
    result={'strict_native':n,'SEPEM':{},'GOES':{}}
    for label,g in [('nominal',G_MAIN),('strict5',G_STRICT)]:
        result['SEPEM'][label]=analyze_sepem(nu,g,R,b)
        result['GOES'][label]=analyze_goes(v,sats,st,b,R,g,info)
    assert result['SEPEM']['strict5']['adjacent_violations']==174
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('common','previous','sepem-cache','goes-cache'):p.add_argument('--'+k,required=True,type=Path)
    p.add_argument('--check',action='store_true');args=p.parse_args()
    result=run(args);save('strict.json',result,args.check)
    print(result['SEPEM']['strict5'])

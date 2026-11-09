"""Strict adjacent-pair coverage and exact reachability of every full SEPEM decade."""
import argparse
from datetime import datetime,timezone
import gzip
import json
import math
from pathlib import Path
import numpy as np
from observations import DT,T,WIDTH,G_MAIN,G_STRICT,START,dates,setup,save


def sections(mask):
    edges=np.diff(np.r_[False,mask,False].astype(np.int8))
    return list(zip(np.flatnonzero(edges==1).tolist(),np.flatnonzero(edges==-1).tolist()))


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


def analyze_goes(rates,strict,b,R,g):
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
                'first_conflict_utc':[datetime.fromtimestamp(1483228800+int(t[i]),timezone.utc).isoformat()
                                      for i in bad[0]] if bad else []}
    return out


def segment_witness(m,R,g):
    """Linear in each bin, with downward jumps at bin edges; all inequalities exact."""
    from fractions import Fraction as F
    half=F(str(g))*DT/2
    bits=53-math.frexp(float(m[m>0].min()))[1]
    den=math.lcm(1<<bits,half.denominator,R.denominator)
    unit=den//(1<<bits)
    x=[int(math.ldexp(float(v),bits))*unit for v in m]
    cap=int(R*den);step=int(half*den)
    a=[];last=x[0]
    for v in x:
        a.append(max(0,2*v-cap,v-step,min(last,v)))
        last=v
    pos=0;initial=None;prev_peak=cap
    for j,v in enumerate(x):
        z=min(a[j],2*v-a[j+1]) if j+1<len(a) else a[j]
        ascent=2*(v-z);peak=z+ascent
        assert 0<=z<=prev_peak and 0<=ascent<=2*step and peak<=cap
        if initial is None:initial=z
        pos+=ascent;prev_peak=peak
    return F(initial+pos,den)


def strict_joint(nu,b,R,windows):
    out=[]
    for x,y,count in windows:
        i=int((datetime.fromisoformat(x)-START).total_seconds())//DT
        j=int((datetime.fromisoformat(y)-START).total_seconds())//DT+WIDTH
        J=segment_witness(nu[i:j]-b,R,G_STRICT)
        out.append({'start':dates(i),'end_exclusive':dates(j),'windows':count,
                    'variation_whole_segment_s_inv':float(J),'exact':str(J)})
    return out


def native_check(old,minutes,cache,b,R,n):
    from prior import EXPERIMENTS
    from cadence import samples,iso
    from minute_sources import selected
    from variation import profile_J
    with gzip.open(old/'goes-events.json.gz','rt',encoding='utf-8') as f:events=json.load(f)
    with gzip.open(EXPERIMENTS/'t67-goes-growth/outputs/file_audits.json.gz','rt',encoding='utf-8') as f:audit=json.load(f)
    with gzip.open(old/'goes-sources.json.gz','rt',encoding='utf-8') as f:five=json.load(f)['receipt']['folded']
    by_name={r['name']:r['signature'] for r in audit}
    by_name.update({r['name']:r['signature'] for r in five})
    ids={s:i for i,s in enumerate(sorted(set(by_name.values())))}
    signatures={k:ids[v] for k,v in by_name.items()}
    info=json.loads((old/'goes.json').read_text(encoding='utf-8'))
    results={}
    for dt,rows,folder in [(60,selected(),minutes/'folded'),(300,five,cache/'derived')]:
        for sat in sorted({r['satellite'] for r in rows}):
            t,v,st,sig=samples(rows,folder,dt,sat,signatures,info)
            for d,name in enumerate(('East','West')):
                strict=st[:,d]&np.isfinite(v[:,d])
                adj=strict[1:]&strict[:-1]&(np.diff(t)==dt)&(sig[1:]==sig[:-1])
                idx=np.flatnonzero(adj)
                expected=n['breakdown'][f'G{sat}_{name}'][f'{dt//60}min']
                assert len(idx)==expected
                sample={'strict_bins':int(strict.sum()),'strict_adjacent_pairs':len(idx),'maximum_s_inv2':None}
                if strict.any():
                    sample['first_strict_utc']=iso(t[strict][0]);sample['last_strict_end_utc']=iso(t[strict][-1]+dt)
                    witness=profile_J(t[strict],v[strict,d],dt,b,G_STRICT,events[name])
                    sample['strict_completion']={k:witness[k] for k in ('reconstruction_J_s_inv','max_slope','peak_excess',
                                              'leading_gap_s','terminal_gap_s','reconstruction_excess_integral_on_holes')}
                    sample['strict_completion']['total_S1']=float(b*T+dt*math.fsum(v[strict,d]-b)
                                                             +witness['reconstruction_excess_integral_on_holes'])
                    assert witness['max_slope']<=G_STRICT and witness['peak_excess']<=R
                if len(idx):
                    j=idx[np.argmax(v[idx+1,d]-v[idx,d])]
                    sample.update(maximum_s_inv2=float(max(0.,(v[j+1,d]-v[j,d])/dt)),from_utc=iso(t[j]),to_utc=iso(t[j+1]))
                for label,mask in [('screened',np.isfinite(v[:,d])),('strict',strict)]:
                    m=v[mask,d]-b
                    if len(m):
                        bad,_=conflict_pairs(m,t[mask],dt,R,G_STRICT)
                        sample[label+'_conflict_pairs']=len(bad)
                results[f'G{sat}_{name}_{dt//60}min']=sample
    return results


def run(args):
    common,old=setup(args.common,args.previous)
    from coverage import environment,sepem_series,goes_observed
    env,_,_=environment();b=float(env['b']);R=float(env['B']-env['b'])
    c=json.loads((common/'cadence.json').read_text(encoding='utf-8'))
    n=native_counts(c)
    assert n['strict_pairs']=={'1min':0,'5min':787} and math.ceil(2*n['maxima']['5min']['slope']*1e9)/1e9==G_STRICT
    nu,_,_,_,_=sepem_series(args.sepem_cache,old)
    v,_,st,_=goes_observed(args.goes_cache,old)
    result={'strict_native':n,'SEPEM':{},'GOES':{}}
    for label,g in [('nominal',G_MAIN),('strict5',G_STRICT)]:
        result['SEPEM'][label]=analyze_sepem(nu,g,R,b)
        result['GOES'][label]=analyze_goes(v,st,b,R,g)
    assert result['SEPEM']['strict5']['adjacent_violations']==174
    result['strict_joint_witnesses']=strict_joint(nu,b,env['B']-env['b'],result['SEPEM']['strict5']['ranges_valid_starts_inclusive'])
    result['native_replay']=native_check(old,args.minutes,args.goes_cache,b,R,n)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('common','previous','sepem-cache','goes-cache','minutes'):p.add_argument('--'+k,required=True,type=Path)
    p.add_argument('--check',action='store_true');args=p.parse_args()
    result=run(args);save('strict.json',result,args.check)
    print(result['SEPEM']['strict5'])

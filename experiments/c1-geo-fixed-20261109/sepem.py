"""C1 SEPEM v2: every bin-aligned full decade, with exact extrema of the binary64 reconstruction."""
import argparse
import csv
from datetime import datetime, timedelta, timezone
from fractions import Fraction
import gzip
import hashlib
import json
from math import frexp, ldexp
from pathlib import Path
import sys
import zipfile
import numpy as np

HERE=Path(__file__).resolve().parent
EXP=HERE.parent
T141=EXP/'t141-radiation-chain'
T123=EXP/'tNN-sepem-profiles'
START=datetime(1974,7,1,tzinfo=timezone.utc)
STEP=300
T=315576000
PERC=(.1,.25,.5,.75,.9)


def stamp(i):
    return (START+timedelta(seconds=int(i)*STEP)).isoformat().replace('+00:00','Z')


def rows(path):
    with path.open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))


def digest(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def verified_arrays(cache,archive):
    receipt=json.loads((T141/'outputs/profile-provenance.json').read_text(encoding='utf-8'))['input']
    if archive:
        with zipfile.ZipFile(archive) as z, z.open('SEPEM_H_reference.txt') as s:
            if hashlib.file_digest(s,'sha256').hexdigest()!=receipt['fingerprint']['raw_sha256']:
                raise ValueError('Different SEPEM H reference file')
    if not (cache/'bands.npy').exists():
        if not archive: raise ValueError('Supply --archive to build the T141 cache')
        cache=cache.resolve()
        if cache.is_relative_to(EXP.parent): raise ValueError('Use an external cache directory')
        cache.mkdir(parents=True,exist_ok=True)
        raw=cache/'SEPEM_H_reference.txt'
        import shutil
        with zipfile.ZipFile(archive) as z, z.open(raw.name) as src, raw.open('wb') as dst:
            shutil.copyfileobj(src,dst)
        sys.path.insert(0,str(T141)); from profiles import build_cache
        build_cache(raw,cache,False)
    manifest=json.loads((cache/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['fingerprint']==receipt['fingerprint']
    for name,sha in receipt['arrays_sha256'].items():
        if digest(cache/name)!=sha: raise ValueError('Cache content differs: '+name)
    return np.load(cache/'bands.npy',mmap_mode='r'),np.load(cache/'flux30.npy',mmap_mode='r'),receipt


def empirical(x):
    return {str(p):float(np.quantile(x,p,method='inverted_cdf')) for p in PERC}


def positive_runs(series,offset):
    delta=np.diff(series)
    positive=delta>0
    edges=np.diff(np.r_[False,positive,False].astype(np.int8))
    runs=[]
    for a,b in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)):
        j=int(a+np.argmax(delta[a:b]))
        runs.append([int(offset+a),int(offset+b),float(series[a]),float(series[b]),int(offset+j),float(delta[j]/STEP)])
    return runs


def event_catalog(nu,solar,flux30):
    events=[]
    for e in rows(T123/'outputs/events.csv'):
        a=int(e['start_index']); b=int(e['stop_index_exclusive'])
        values=nu[a:b]; peak=a+int(np.argmax(values)); runs=positive_runs(values,a)
        excess=solar[a:b]
        events.append(dict(id=e['event_id'],start=e['start_utc'],stop=e['end_exclusive_utc'],
            start_bin=a,stop_bin=b,peak_utc=stamp(peak),duration_s=(b-a)*STEP,peak_per_s=float(nu[peak]),
            proton_fluence_above30_cm2=float(flux30[a:b].sum()*STEP),
            excess_inversions=float(excess.sum()*STEP),S1_total=float(values.sum()*STEP),
            S2_total=float(values@values*STEP),initial_positive_run=runs[0] if runs else None,
            repeated_positive_runs=runs[1:],max_upward_bin_slope_per_s2=float(max([r[5] for r in runs],default=0)),
            quality='RDS reconstructed; no per-bin quality mask; rates averaged over 300 s'))
    return events


def sliding(nu,width):
    # A common binary unit represents every stored rate exactly. Only comparisons
    # of the three maxima require exact arithmetic. Output columns are binary64.
    bits=53-frexp(float(np.min(nu)))[1]
    z=[int(ldexp(float(v),bits)) for v in nu]
    unit=1<<bits
    first=sum(z[:width]); second=sum(v*v for v in z[:width])
    count=len(z)-width+1
    cols=np.empty((count,3),dtype='float64')
    extrema={k:None for k in ('S1','S2','k')}
    for i in range(count):
        cols[i]=(STEP*first/unit,STEP*second/unit**2,width*second/first**2)
        for key in extrema:
            best=extrema[key]
            if best is None:
                cmp=1
            elif key=='S1': cmp=first-best[1]
            elif key=='S2': cmp=second-best[2]
            else: cmp=second*best[1]**2-best[2]*first**2
            if cmp>0: extrema[key]=[i,first,second,1]
            elif cmp==0: best[3]+=1
        if i+1<count:
            old,new=z[i],z[i+width]
            first+=new-old; second+=(new-old)*(new+old)
    whole_first=sum(z);whole_second=sum(v*v for v in z)
    whole={'duration_s':len(z)*STEP,'S1':STEP*whole_first/unit,'S2_s_inv':STEP*whole_second/unit**2,
           'profile_k':len(z)*whole_second/whole_first**2}
    return cols,extrema,whole


def compute(cache,archive,export=None):
    bands,flux30,receipt=verified_arrays(cache,archive)
    info=next(x for x in rows(T141/'outputs/profile-background.csv') if x['shield_g_cm2']=='3.0')
    total=bands[:,1,:].sum(axis=1); floor=float(info['floor_s_inv']); b=float(info['cosrad_b_s_inv'])
    assert np.quantile(total,.1)==floor
    hi_factor=1+float(info['HI_to_H_assumed']); solar=hi_factor*np.maximum(total-floor,0.)
    nu=b+solar; width=T//STEP
    assert len(nu)==4365792 and stamp(len(nu))=='2016-01-01T00:00:00Z'
    cols,extrema,whole=sliding(nu,width)
    ratio=T*cols[extrema['S2'][0],1]/np.square(cols[:,0])
    ceiling=float(Fraction(width*extrema['S2'][2],extrema['S1'][1]**2))
    assert np.isclose(ceiling,ratio[extrema['S1'][0]]) and ceiling>=1 and np.all(cols[:,2]>=1)
    if export:
        # Row i starts START + i*300 s. k and R are supplied explicitly.
        np.savez_compressed(export,S1=cols[:,0],S2=cols[:,1],k=cols[:,2],R=ratio)
    maxima={}
    for key,(i,_,_,ties) in extrema.items():
        maxima[key]={'start_bin':i,'start_utc':stamp(i),'stop_utc_exclusive':stamp(i+width),
            'exact_ties':ties,'S1':float(cols[i,0]),'S2_s_inv':float(cols[i,1]),
            'profile_k':float(cols[i,2]),'R':float(ratio[i])}
    windows=rows(T141/'outputs/cycle-windows.csv'); tested=0
    for r in windows:
        if r['shield_g_cm2']!='3.0': continue
        date=datetime(int(r['start_year']),1,1,tzinfo=timezone.utc)
        i=int((date-START).total_seconds())//STEP
        assert np.isclose(cols[i,1],float(r['S2_H_HI_proxy_plus_background_s_inv']),rtol=2e-8)
        assert np.isclose(cols[i,0],b*T+hi_factor*float(r['H_solar_N']),rtol=2e-8)
        tested+=1
    assert tested==31
    events=event_catalog(nu,solar,flux30)
    peak=int(np.argmax(nu))
    slopes=np.diff(nu)/STEP
    ascent=int(np.argmax(slopes))
    whole.update(peak_s_inv=float(nu[peak]), peak_utc=stamp(peak),
                 max_upward_bin_slope_s_inv2=float(slopes[ascent]), upward_from_utc=stamp(ascent),
                 upward_to_utc=stamp(ascent+1))
    starts=np.array([e['start_bin'] for e in events]); ix=np.arange(len(cols))
    counts=np.searchsorted(starts,ix+width)-np.searchsorted(starts,ix)
    assert len(events)==131
    result={'configuration':'SEPEM RDS v2.00; T141 primary CSDA, Al 3 g/cm2, full38 reference; HI proxy synchronous with solar H',
        'covered_interval':[stamp(0),stamp(len(nu))],'dt_s':STEP,'T_s':T,'whole_archive':whole,'window_count':len(cols),
        'window_step_s':STEP,'maxima':maxima,'k_class':ceiling,'R_quantiles':empirical(ratio),
        'R_range':[float(np.min(ratio)),float(np.max(ratio))],
        'event_start_counts_per_window':{'quantiles':empirical(counts),'range':[int(np.min(counts)),int(np.max(counts))]},
        'number_of_events':len(events),'event_quantiles':{key:empirical([e[key] for e in events]) for key in
          ('duration_s','peak_per_s','proton_fluence_above30_cm2','excess_inversions','max_upward_bin_slope_per_s2')},
        'event_ranges':{key:[min(e[key] for e in events),max(e[key] for e in events)] for key in
          ('duration_s','peak_per_s','proton_fluence_above30_cm2','excess_inversions','max_upward_bin_slope_per_s2')},
        'repeat_count_range':[min(len(e['repeated_positive_runs']) for e in events),
                              max(len(e['repeated_positive_runs']) for e in events)],
        'rise_fields':['first_bin','last_bin','first_rate_s_inv','last_rate_s_inv','steepest_left_bin','steepest_slope_s_inv2'],
        'H_p10':floor,'background_per_s':b,'HI_to_H':hi_factor-1,'checked_T141_Jan1_windows':tested,
        'source_cache':receipt,'physical_class_ceiling':None}
    return result,events


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',required=True,type=Path);parser.add_argument('--archive',type=Path)
    parser.add_argument('--export-windows',type=Path);parser.add_argument('--check',action='store_true')
    args=parser.parse_args();result,events=compute(args.cache,args.archive,args.export_windows)
    for name,value in [('sepem.json',result),('sepem-events.json.gz',events)]:
        if name.endswith('.gz'):
            payload=(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode()
            data=gzip.compress(payload,compresslevel=9,mtime=0)
        else:
            data=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
        path=HERE/name
        if args.check:
            saved=path.read_bytes()
            unpack=gzip.decompress if name.endswith('.gz') else lambda s:s
            if unpack(saved)!=unpack(data): raise SystemExit('Mismatch: '+name)
        else: path.write_bytes(data)
    print(result['window_count'],result['k_class'],result['R_quantiles'])


if __name__=='__main__': main()

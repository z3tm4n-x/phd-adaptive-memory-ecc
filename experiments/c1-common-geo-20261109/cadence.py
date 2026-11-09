"""One response and one background floor per direction at both GOES cadences."""
import argparse
from datetime import datetime, timedelta, timezone
import gzip
import json
from pathlib import Path
import numpy as np

from coverage import sepem_series, write_or_check
from minute_sources import selected
from prior import HERE, EXPERIMENTS, activate

EPOCH=datetime(2017,1,1,tzinfo=timezone.utc)
L=0.001


def iso(seconds):
    return (EPOCH+timedelta(seconds=int(seconds))).isoformat().replace('+00:00','Z')


def stamp(text):
    return int((datetime.fromisoformat(text)-EPOCH).total_seconds())


def hlevel(x):
    # Historical T67 H_l applied to this reconstruction of full nu.
    return np.where(x<=L,x/L,1.+np.log(np.maximum(x,L)/L))


def extreme(t,nu,strict,connected,delta,h=False):
    idx=np.flatnonzero(connected&np.isfinite(nu[:-1])&np.isfinite(nu[1:]))
    if not len(idx):return None
    x=hlevel(nu) if h else nu
    changes=(x[idx+1]-x[idx])/delta
    j=int(idx[np.argmax(changes)])
    return {'pairs':len(idx),'from_utc':iso(t[j]),'to_utc':iso(t[j+1]),'from_s_inv':float(nu[j]),
            'to_s_inv':float(nu[j+1]),'slope':float(max(0.,(x[j+1]-x[j])/delta)),
            'both_strict':bool(strict[j] and strict[j+1])}


def metrics(t,nu,strict,signature,dt):
    pairs=(np.diff(t)==dt)&(signature[:-1]==signature[1:])
    return {'nu_slope_s_inv2':extreme(t,nu,strict,pairs,dt),
            'H_l_slope_s_inv':extreme(t,nu,strict,pairs,dt,True),
            'strict_nu_slope_s_inv2':extreme(t,nu,strict,pairs&strict[:-1]&strict[1:],dt)}


def rises(events,t,nu,strict,sig,dt):
    out=[]
    for event in events:
        a,b=np.searchsorted(t,[stamp(event['onset']),stamp(event['end'])])
        if a==b:continue
        v=nu[a:b];good=(np.diff(v)>0)&(np.diff(t[a:b])==dt)&(sig[a:b-1]==sig[a+1:b])
        edges=np.diff(np.r_[False,good,False].astype(np.int8))
        runs=[]
        for start,end in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)):
            pos=start+np.argmax(np.diff(v[start:end+1]))
            runs.append({'start_utc':iso(t[a+start]),'end_utc':iso(t[a+end]),
                'start_s_inv':float(v[start]),'end_s_inv':float(v[end]),'steepest_from_utc':iso(t[a+pos]),
                'steepest_slope_s_inv2':float((v[pos+1]-v[pos])/dt),
                'both_strict_at_steepest':bool(strict[a+pos] and strict[a+pos+1])})
        if runs:
            out.append({'onset':event['onset'],'catalog_peak':event['peak_catalog'],'rise_count':len(runs),
                'first_observed':runs[0],'strongest_repeated':max(runs[1:],key=lambda r:r['steepest_slope_s_inv2'],default=None)})
    return out


def match(t,nu,strict,sig,t5,v5,s5,sig5):
    # Five actual consecutive minutes from the same device/direction; a common
    # pair of neighbouring blocks is required for all three reported maxima.
    starts=np.flatnonzero((t%300==0)&(np.arange(len(t))+4<len(t)))
    starts=starts[(t[starts+4]==t[starts]+240)&(sig[starts]==sig[starts+4])]
    native=np.searchsorted(t5,t[starts])
    has=native<len(t5);native=native[has];starts=starts[has]
    has=t5[native]==t[starts];native=native[has];starts=starts[has]
    chunks=starts[:,None]+np.arange(5)
    vals=nu[chunks];flags=np.all(strict[chunks],axis=1)
    ok=np.all(np.isfinite(vals),axis=1)&np.isfinite(v5[native])
    average=np.mean(vals,axis=1)
    common=(np.diff(t[starts])==300)&(sig[starts[:-1]]==sig[starts[1:]])&(sig5[native[:-1]]==sig5[native[1:]])
    common&=ok[:-1]&ok[1:]
    pairs=np.flatnonzero(common)
    if not len(pairs):return {'matched_pairs':0}
    native_val=extreme(t[starts],v5[native],s5[native],common,300)
    mean_val=extreme(t[starts],average,flags,common,300)
    one=np.zeros(len(t)-1,dtype=bool)
    for offset in range(9):one[starts[pairs]+offset]=True
    minute=extreme(t,nu,strict,one,60)
    return {'matched_pairs':len(pairs),'minute':minute,'mean_five_minutes':mean_val,'native_five_minutes':native_val,
        'max_abs_native_minus_mean_s_inv':float(np.max(np.abs(v5[native][ok]-average[ok]))),
        'minute_to_mean_maximum_ratio':minute['slope']/mean_val['slope'] if mean_val['slope']>0 else None}


def samples(rows,loc,dt,satellite,signatures,info):
    dates=[]; rates=[]; strict=[]; signatures_out=[]
    for r in sorted((r for r in rows if r['satellite']==satellite),key=lambda r:r['name']):
        with np.load(loc/(r['name']+'.npz')) as src:
            time=src['index']*dt;v=src['values']
        dates.append(time)
        h=v[:,:,0]+v[:,:,1]
        floors=[info['directions'][n]['proton_p10_per_s'] for n in ('East','West')]
        rates.append(info['background_s_inv']+(1+info['HI_to_H'])*np.maximum(h-floors,0))
        strict.append(v[:,:,4]==1)
        signatures_out.append(np.full(len(time),signatures[r['name']],dtype=np.int32))
    t=np.concatenate(dates);order=np.argsort(t)
    assert np.all(np.diff(t[order])>0)
    return t[order],np.concatenate(rates)[order],np.concatenate(strict)[order],np.concatenate(signatures_out)[order]


def decisive_quality(result,minutes,mc):
    import goes_profile as g
    choices=[(m['1min']['nu_slope_s_inv2']['slope'],k,m['1min']['nu_slope_s_inv2'])
             for k,m in result['native'].items() if '1min' in m and m['1min']['nu_slope_s_inv2']]
    _,key,best=max(choices)
    sat,direction=key.split('_')
    date=best['from_utc'][:10].replace('-','')
    record=next(r for r in minutes if r['satellite']==int(sat[1:]) and r['date']==date)
    path=mc/'raw'/record['name']; src=g.sgps.read(path)
    details=[]
    with g.ReadOnlyNC(path) as f:
        for when in (best['from_utc'],best['to_utc']):
            i=int(np.searchsorted(src.time,EPOCH.timestamp()+stamp(when)))
            d=('East','West').index(direction);sensor=1-d if src.yaw[i]==0 else d
            flags={}
            for name in ('DiffDQFerrSum','IntDQFerrSum','DiffValidL1bSamplesInAvg','IntValidL1bSamplesInAvg'):
                v=g.sgps.clean(f.array(name),f.attrs(name))[i,sensor]
                flags[name]=np.asarray(v).tolist()
            details.append({'utc':when,'yaw':float(src.yaw[i]),'sensor':sensor,'native_flags':flags})
    return {'name':record['name'],'sha256':record['sha256'],'direction':direction,'bins':details}


def run(previous,mc,gc,sc):
    prev=activate(previous)
    info=json.loads((prev/'goes.json').read_text(encoding='utf-8'))
    with gzip.open(prev/'goes-events.json.gz','rt',encoding='utf-8') as f:events=json.load(f)
    with gzip.open(prev/'goes-sources.json.gz','rt',encoding='utf-8') as f:five=json.load(f)['receipt']['folded']
    with gzip.open(EXPERIMENTS/'t67-goes-growth/outputs/file_audits.json.gz','rt',encoding='utf-8') as f:audit=json.load(f)
    sigs={r['name']:r['signature'] for r in audit}
    sigs.update({r['name']:r['signature'] for r in five})
    lookup={s:i for i,s in enumerate(sorted(set(sigs.values())))}
    sigs={name:lookup[s] for name,s in sigs.items()}
    minute=selected()
    receipt=json.loads((mc/'receipt.json').read_text(encoding='utf-8'))
    assert not receipt['errors'] and set(receipt['ok'])=={r['name'] for r in minute}
    result={'level_s_inv':L,'minute_files':len(minute),'native':{},'matched':{},'event_rises':{}}
    for sat in sorted({r['satellite'] for r in minute}):
        t,v,st,sig=samples(minute,mc/'folded',60,sat,sigs,info)
        t5,v5,s5,sig5=samples(five,gc/'derived',300,sat,sigs,info)
        for d,direction in enumerate(('East','West')):
            key=f'G{sat}_{direction}'
            result['native'][key]={'1min':metrics(t,v[:,d],st[:,d],sig,60),'5min':metrics(t5,v5[:,d],s5[:,d],sig5,300)}
            result['matched'][key]=match(t,v[:,d],st[:,d],sig,t5,v5[:,d],s5[:,d],sig5)
            result['event_rises'][key]={'1min':rises(events[direction],t,v[:,d],st[:,d],sig,60),
                                         '5min':rises(events[direction],t5,v5[:,d],s5[:,d],sig5,300)}
    # G17 is part of the five-minute passport; T67 selected no minute G17 series.
    t5,v5,s5,sig5=samples(five,gc/'derived',300,17,sigs,info)
    for d,direction in enumerate(('East','West')):
        key=f'G17_{direction}'
        result['native'][key]={'5min':metrics(t5,v5[:,d],s5[:,d],sig5,300)}
    nu,_,_,_,_=sepem_series(sc,prev)
    import sepem
    sec0=int((sepem.START-EPOCH).total_seconds());grid=sec0+np.arange(len(nu))*300
    adjacent=np.ones(len(nu)-1,dtype=bool)
    result['SEPEM']={'nu_slope_s_inv2':extreme(grid,nu,np.zeros(len(nu),bool),adjacent,300),
        'H_l_slope_s_inv':extreme(grid,nu,np.zeros(len(nu),bool),adjacent,300,True),'quality':'No per-bin strict flag in RDS v2'}
    result['decisive_raw_quality']=decisive_quality(result,minute,mc)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('previous','minutes','goes-cache','sepem-cache'):p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('--check',action='store_true');args=p.parse_args()
    result=run(args.previous,args.minutes,args.goes_cache,args.sepem_cache)
    catalog=result.pop('event_rises');packet=(json.dumps(catalog,separators=(',',':'))+'\n').encode()
    catfile=HERE/'event-rises.json.gz'
    if args.check:
        if gzip.decompress(catfile.read_bytes())!=packet:raise SystemExit('Mismatch: '+catfile.name)
    else:catfile.write_bytes(gzip.compress(packet,compresslevel=9,mtime=0))
    write_or_check(HERE/'cadence.json',result,args.check)
    print('Cadence pairs',sum(r['matched_pairs'] for r in result['matched'].values()),'G19 West',result['matched']['G19_West'])

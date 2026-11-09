"""C1 GOES SGPS: measured coverage, CSDA folds, and observed-support moments."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,timedelta
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
from time import monotonic
from urllib.parse import urlsplit
import h5py
import numpy as np
from scipy.io import netcdf_file
from numpy.polynomial.legendre import leggauss
from goes_inventory import get, CUTOFF
from sepem import positive_runs, empirical

HERE=Path(__file__).resolve().parent; EXP=HERE.parent
sys.path.insert(0,str(EXP/'t67-goes-growth')); import sgps, response, archive
sys.path.insert(0,str(EXP/'tNN-sepem-profiles')); import transport
DT=300; T=315576000
FIRST=datetime(2017,1,1,tzinfo=timezone.utc)
STOP=datetime.strptime(CUTOFF,'%Y%m%d').replace(tzinfo=timezone.utc)
NBINS=int((STOP-FIRST).total_seconds())//DT


def iso(i):
    return (FIRST+timedelta(seconds=int(i)*DT)).isoformat().replace('+00:00','Z')


class ReadOnlyNC:
    """Same raw (unpacked) variable/attribute interface as T67 PyFile."""
    def __init__(self,path):
        self.hdf=h5py.is_hdf5(path)
        self.ds=h5py.File(path,'r') if self.hdf else netcdf_file(path,'r',mmap=False,maskandscale=False)
    def __enter__(self):return self
    def __exit__(self,*args):self.ds.close()
    def names(self):return list(self.ds.keys() if self.hdf else self.ds.variables)
    def attrs(self,name=None):
        obj=self.ds if name is None else (self.ds[name] if self.hdf else self.ds.variables[name])
        out={}
        for k,v in (obj.attrs if self.hdf else obj._attributes).items():
            if isinstance(v,np.ndarray) and v.size==1: v=v.item()
            out[k]=v.decode('utf-8') if isinstance(v,(bytes,np.bytes_)) else v
        return out
    def array(self,name):
        obj=self.ds[name] if self.hdf else self.ds.variables[name]
        return np.asarray(obj[...],dtype=float)


sgps.open_nc=ReadOnlyNC
KERNELS={}


def kernel(src,sensor):
    energy=src.energy[sensor]; edges=(src.lower[sensor,0],src.upper[sensor,-1]); key=tuple(energy)+tuple(edges)
    if key in KERNELS:return KERNELS[key]
    table=transport.RangeTable(); rho=3
    residual_knots=np.r_[.001,5,transport.sigma_module.zero_crossing_low(transport.POINTS),transport.SIGMA_E,table.energy]
    incident=table.inverse(rho+table.range(residual_knots))
    cuts=np.unique(np.r_[edges,energy,5,10,30,table.energy,incident,table.inverse(rho)])
    cuts=cuts[(cuts>=5)&(cuts>=edges[0])&(cuts<=edges[1])]
    z,w=leggauss(24); a,b=cuts[:-1,None],cuts[1:,None]
    e=((a+b+(b-a)*z)/2).ravel(); weights=((b-a)*w/2).ravel()
    # Energy below 5 MeV incident stops in this column; flux integrals start at 10/30.
    assert table.range(5)<rho
    residual=table.residual(e,rho); sig=transport.sigma(residual)
    basis=np.column_stack([response.NS['reconstruct_on_grid'](energy,q,*edges,e) for q in np.eye(13)])
    assert np.all(np.isfinite(basis))
    full38=4*math.pi*transport.BITS
    low=full38*(basis.T@(weights*sig*(residual<5)))
    high=full38*(basis.T@(weights*sig*(residual>=5)))
    f10=basis.T@(weights*(e>=10)); f30=basis.T@(weights*(e>=30))
    tail=float(transport.sigma(np.array([table.residual(np.array([500.]),rho)[0]]))[0])
    assert table.residual(np.array([390.]),rho)[0]>transport.SIGMA_E[-1]
    KERNELS[key]=(low,high,f10,f30,full38*tail)
    return KERNELS[key]


def fold(path):
    src=sgps.read(path); assert src.cadence==DT
    f=src.corrected; valid=np.all(np.isfinite(f),axis=2)
    gap,fallback,_=response.gap_bridge(f,valid); tail=gap+f[:,:,13]
    out=np.full((len(src.time),2,6),np.nan)
    for d in range(2):
        for yaw in (0,2):
            sensor=1-d if yaw==0 else d
            lo,hi,f10,f30,sigma_tail=kernel(src,sensor)
            active=np.r_[np.flatnonzero(lo+hi>0),13]
            mask=valid[:,d]&(src.yaw==yaw)&np.all(src.screened[:,d][:,active],axis=1)
            ff=f[mask,d,:13]; ft=tail[mask,d]
            out[mask,d,0]=ff@lo;out[mask,d,1]=ff@hi+sigma_tail*ft
            out[mask,d,2]=ff@f10+ft;out[mask,d,3]=4*math.pi*(ff@f30+ft)
            out[mask,d,4]=np.all(src.strict[mask,d],axis=1)&(f[mask,d,12]>0)&(f[mask,d,13]>0)
            out[mask,d,5]=fallback[mask,d]
            # Fluence uses additional low-energy channels and has its own coverage.
            flux_ok=np.all(src.screened[mask,d][:,np.r_[np.flatnonzero(f10>0),13]],axis=1)
            out[np.flatnonzero(mask)[~flux_ok],d,2:4]=np.nan
    ids=np.rint((src.time-FIRST.timestamp())/DT).astype(np.int64)
    if np.any(np.abs(src.time-(FIRST.timestamp()+ids*DT))>.01): raise ValueError('Off-grid SGPS starts')
    return ids,out,src.audit


def download_one(job):
    url,raw,local=job; name=urlsplit(url).path.rsplit('/',1)[-1]
    try:
        path=local.get(name,raw/name)
        if not path.exists():
            data=get(url)
            if not (data.startswith(b'CDF') or data.startswith(b'\x89HDF')): raise ValueError('not a NetCDF file')
            tmp=raw/(name+'.partial');tmp.write_bytes(data);tmp.replace(path)
        return url,path,None
    except (ValueError,OSError) as e: return url,None,str(e)


def process(index,cache,local_root,limit=None,retry_missing=False,frozen=None):
    raw=cache/'raw'; raw.mkdir(parents=True,exist_ok=True)
    derived=cache/'derived'; derived.mkdir(exist_ok=True)
    local={p.name:p for p in local_root.rglob('*sgps*.nc')} if local_root else {}
    urls=[index['special']]+index['selected_daily']; urls=urls[:limit] if limit else urls
    pinned=json.loads((EXP/'t67-goes-growth/outputs/source_manifest.json').read_text(encoding='utf-8'))
    historic={r['name']:r['sha256'] for v in pinned.values() if isinstance(v,list) for r in v
              if isinstance(r,dict) and 'name' in r and 'sha256' in r}
    errors={}; manifest=[]; start=monotonic()
    if frozen:
        historic.update({r['name']:r['sha256'] for r in frozen['folded']})
        errors=frozen['errors'].copy()
        urls=[u for u in urls if u not in errors]
    if retry_missing:
        previous=json.loads((cache/'receipt.json').read_text(encoding='utf-8'))
        allowed=set(urls)
        manifest=[r for r in previous['folded'] if r['url'] in allowed]
        done={r['url'] for r in manifest}
        urls=[u for u in urls if u not in done]
        errors={u:e for u,e in previous['errors'].items() if u in allowed}
    # Keep downloads bounded while folding in the main thread (HDF libraries need not be thread-safe).
    for batch in range(0,len(urls),48):
        with ThreadPoolExecutor(max_workers=8) as pool:
            jobs=[(url,raw,local) for url in urls[batch:batch+48]]
            for url,path,error in pool.map(download_one,jobs):
                if error: errors[url]=error; continue
                name=path.name; compact=derived/(name+'.npz'); passport=derived/(name+'.json')
                try:
                    with path.open('rb') as stream: sha=hashlib.file_digest(stream,'sha256').hexdigest()
                    if name in historic and sha!=historic[name]: raise ValueError('Source differs from pinned checksum')
                    saved=json.loads(passport.read_text(encoding='utf-8')) if passport.exists() else {}
                    if frozen or not (compact.exists() and saved.get('sha256')==sha and saved.get('fold_version')==1):
                        ids,values,audit=fold(path)
                        np.savez_compressed(compact,index=ids,values=values)
                        saved={k:audit[k] for k in ('name','sha256','bytes','signature','satellite','records','first_start_utc','last_end_utc','quality','processing','lut_match','g19_P7_P8C_test_period')}
                        saved['fold_version']=1;passport.write_text(json.dumps(saved,ensure_ascii=False,default=str),encoding='utf-8')
                    manifest.append({'url':url,'name':name,'sha256':sha,'signature':saved['signature'],'satellite':saved['satellite']})
                    errors.pop(url,None)
                except (OSError,ValueError,KeyError,AssertionError,TypeError) as e: errors[url]=str(e)
        print(f'GOES {min(batch+48,len(urls))}/{len(urls)}; folded {len(manifest)}, incomplete {len(errors)}; {monotonic()-start:.0f}s',flush=True)
        checkpoint=cache/'receipt.partial.json'
        checkpoint.write_text(json.dumps({'folded':sorted(manifest,key=lambda r:r['url']),'errors':errors},ensure_ascii=False),encoding='utf-8')
        checkpoint.replace(cache/'receipt.json')
    return manifest,errors


def composite(cache,manifest):
    # Priority is independent of values; count overlap before selecting one valid input.
    cube=np.full((NBINS,2,6),np.nan); sats=np.zeros((NBINS,2),dtype=np.int8); overlaps=np.zeros((NBINS,2),dtype=np.int8)
    coverage={}
    for rec in sorted(manifest,key=lambda r:(r['satellite'],r['name'])):
        with np.load(cache/'derived'/(rec['name']+'.npz')) as src:
            idx=src['index']; ok=(idx>=0)&(idx<NBINS); idx=idx[ok]; values=src['values'][ok]
        for d in range(2):
            valid=np.isfinite(values[:,d,0]); where=idx[valid];v=values[valid,d]
            overlaps[where,d]+=1
            key=f"G{rec['satellite']}_{('East','West')[d]}"
            row=coverage.setdefault(key,{'valid_bins_before_selection':0,'first_bin':None,'last_bin':None})
            row['valid_bins_before_selection']+=len(where)
            if len(where):
                first,last=int(where.min()),int(where.max())
                row['first_bin']=first if row['first_bin'] is None else min(first,row['first_bin'])
                row['last_bin']=last if row['last_bin'] is None else max(last,row['last_bin'])
            take=sats[where,d]==0
            sats[where[take],d]=rec['satellite'];cube[where[take],d]=v[take]
    for row in coverage.values():
        first,last=row.pop('first_bin'),row.pop('last_bin')
        row['first_valid_utc']=iso(first) if first is not None else None
        row['last_valid_stop_utc']=iso(last+1) if last is not None else None
    return cube,sats,overlaps,coverage


def catalog(cache):
    path=cache/'official-catalog.html'
    if not path.exists():path.write_bytes(get(archive.CATALOGUE))
    table=archive.Table();table.feed(path.read_text(encoding='utf-8',errors='replace'))
    events=[]
    for row in table.rows:
        if len(row)<3: continue
        try:
            onset=datetime.strptime(row[0],'%Y %m/%d %H%M').replace(tzinfo=timezone.utc)
            peak=datetime.strptime(row[1],'%Y %m/%d %H%M').replace(tzinfo=timezone.utc)
            if FIRST<=onset<STOP:
                events.append({'onset':onset.isoformat(),'peak_catalog':peak.isoformat(),'peak_pfu':float(row[2].replace(',',''))})
        except ValueError:continue
    pinned=json.loads((EXP/'t67-goes-growth/outputs/source_manifest.json').read_text(encoding='utf-8'))
    old={(e['onset_utc'],e['peak_utc']) for e in pinned['events'] if e['kind']=='NOAA_catalogue'}
    current={(e['onset'],e['peak_catalog']) for e in events}
    if not old<=current:
        raise ValueError('NOAA catalogue no longer reproduces pinned T67 rows; audit changed dates.')
    warnings={e['onset_utc'] for e in pinned['events'] if e.get('catalogue_date_warning')}
    for e in events:
        e['T67_catalog_date_warning']=e['onset'] in warnings
    return sorted(events,key=lambda e:e['onset']),hashlib.sha256(path.read_bytes()).hexdigest()


def observed_events(official,values,rate):
    result=[]
    for j,event in enumerate(official):
        index=lambda t:int((datetime.fromisoformat(t)-FIRST).total_seconds())//DT
        a=index(event['onset']); peak=index(event['peak_catalog'])
        until=index(official[j+1]['onset']) if j+1<len(official) else NBINS
        stop=min(until,NBINS); reason='next_event_or_archive_end'; quiet=0
        if not a<=peak<stop:
            reason='catalog_peak_outside_onset_interval'
        for i in range(peak if a<=peak<stop else stop,stop):
            if not np.isfinite(values[i,2]): stop=i;reason='missing_after_catalog_peak';break
            quiet=quiet+1 if values[i,2]<10 else 0
            if quiet==6: stop=i-5;reason='six_bins_below_10_pfu';break
        part=rate[a:stop]; seen=np.isfinite(part); flux=values[a:stop,3]
        if not np.all(seen): reason+='; internal holes'
        runs=positive_runs(part,a)  # np.diff at a hole is NaN, so cannot link slopes across it.
        result.append({**event,'end':iso(stop),'end_status':reason,'calendar_span_s':(stop-a)*DT,
            'covered_rate_s':int(seen.sum())*DT,'peak_rate':float(np.nanmax(part)) if seen.any() else None,
            'peak_rate_time':iso(a+np.nanargmax(part)) if seen.any() else None,
            'observed_S1':float(np.nansum(part))*DT if seen.any() else None,
            'observed_S2':float(np.nansum(part**2))*DT if seen.any() else None,
            'fluence30_observed_cm2':float(np.nansum(flux))*DT if np.any(np.isfinite(flux)) else None,
            'fluence30_covered_s':int(np.isfinite(flux).sum())*DT,'initial_rise':runs[0] if runs else None,'repeated_rises':runs[1:],
            'max_observed_upward_slope_s_inv2':max((r[5] for r in runs),default=None)})
    return result


def passport_by_signature(cache,manifest):
    """Retain the processing contract and DQ statistics for each distinct source signature."""
    signatures={}
    for rec in manifest:
        p=json.loads((cache/'derived'/(rec['name']+'.json')).read_text(encoding='utf-8'))
        item=signatures.setdefault(p['signature'],{'processing':p['processing'],'files':0,'records':0,
                    'files_failed_lut':0,'g19_test_files':0,'quality':{}})
        item['files']+=1
        item['records']+=p['records']
        item['files_failed_lut']+=not p['lut_match']
        item['g19_test_files']+=p['g19_P7_P8C_test_period']
        for flag,e in p['quality'].items():
            q=item['quality'].setdefault(flag,{'flagged':0,'missing':0,'meaning':e['meaning']})
            q['flagged']+=e['flagged'];q['missing']+=e['missing']
    return signatures


def summarize(cache,index,receipt):
    cube,sats,overlap,counts=composite(cache,receipt['folded']);official,catsha=catalog(cache)
    import csv
    with (EXP/'t141-radiation-chain/outputs/profile-background.csv').open(encoding='utf-8') as f:
        model=next(r for r in csv.DictReader(f) if r['shield_g_cm2']=='3.0')
    b=float(model['cosrad_b_s_inv']);factor=1+float(model['HI_to_H_assumed']); out={}; all_events={}
    for d,name in enumerate(('East','West')):
        ok=sats[:,d]>0; values=cube[:,d]; h=values[:,0]+values[:,1]
        if not ok.any():out[name]={'covered_bins':0,'moments':None}; all_events[name]=[];continue
        floor=float(np.quantile(h[ok],.1));rate=b+factor*np.maximum(h-floor,0)
        s1=float(np.nansum(rate))*DT;s2=float(np.nansum(rate**2))*DT;tobs=int(ok.sum())*DT
        atpeak=int(np.nanargmax(rate))
        slopes=np.diff(rate)/DT; atup=int(np.nanargmax(slopes))
        out[name]={'covered_bins':int(ok.sum()),'covered_s':tobs,'missing_s':NBINS*DT-tobs,
                   'first_valid_utc':iso(np.flatnonzero(ok)[0]),'last_valid_stop_utc':iso(np.flatnonzero(ok)[-1]+1),
                   'proton_p10_per_s':floor,'S1_observed':s1,'S2_observed_s_inv':s2,'k_observed_exposure':tobs*s2/s1**2,
                   'peak_rate_s_inv':float(rate[atpeak]),'peak_rate_utc':iso(atpeak),
                   'max_upward_bin_slope_s_inv2':float(slopes[atup]),'upward_from_utc':iso(atup),'upward_to_utc':iso(atup+1),
                   'strict_bins_within_screened':int(np.nansum(values[:,4])),'fallback_tail_bins':int(np.nansum(values[:,5])),
                   'overlap_bins':int(np.sum(overlap[:,d]>=2)),
                   'selected_bins_by_satellite':{str(s):int(np.sum(sats[:,d]==s)) for s in (16,17,18,19)}}
        all_events[name]=observed_events(official,values,rate)
        events=all_events[name]
        out[name]['event_end_status_counts']=dict(Counter(e['end_status'] for e in events))
        out[name]['catalogued_events_with_a_valid_rate']=sum(e['covered_rate_s']>0 for e in events)
        out[name]['event_support_statistics']={}
        for key in ('calendar_span_s','peak_rate','fluence30_observed_cm2','max_observed_upward_slope_s_inv2'):
            sample=[e[key] for e in events if e[key] is not None and e['covered_rate_s']>0]
            if sample: out[name]['event_support_statistics'][key]={'count':len(sample),'range':[min(sample),max(sample)],
                                                                'quantiles':empirical(sample)}
    summary={'config':'GOES SGPS, conditional directional primary CSDA Al 3 g/cm2, T141 full38 and synchronous HI proxy',
        'interval':[iso(0),iso(NBINS)],'calendar_duration_s':NBINS*DT,'required_T_s':T,'full_decades':0,
        'k_class':None,'R':None,'window_maxima':None,'archive_k_complete_calendar':None,
        'selected_daily_files':len(index['selected_daily']),'folded_files':len(receipt['folded']),'file_failures':len(receipt['errors']),
        'unverified_indexes':index['unverified_indexes'],'official_catalog_sha256':catsha,'official_events':len(official),
        'availability_per_sat_direction':counts,'directions':out,'background_s_inv':b,'HI_to_H':factor-1,
        'rise_fields':['first_bin','last_bin','first_rate_s_inv','last_rate_s_inv','steepest_left_bin','steepest_slope_s_inv2']}
    assert summary['calendar_duration_s'] < T
    return summary,all_events


def report(s,events,sources):
    out=['# GOES. Что покрывают измерения ГСО','',
         "Интегралы полной частоты и её квадрата собраны раздельно для East и West за 01.01.2017–09.11.2026 UTC. "
         f"Календарь содержит {s['calendar_duration_s']} с при требуемых {T} с. "
         "Полных десятилетий — **0**. Максимумы по десятилетиям, k класса и квантили R здесь не определены. "
         "[Условия реконструкции](GOES-CONFIG.md) · [Паспорт T67](../t67-goes-growth/SOURCES.md).",'',
         f"Обработано {s['folded_files']} из {s['selected_daily_files']+1} выбранных файлов. "
         f"Файлов с открытой ошибкой получения или обработки — {s['file_failures']}. "
         f"Число различных паспортов прибора и алгоритма — {len(sources['signatures'])}. "
         "URL, даты, продукт, версия, исходный SHA-256, паспорт алгоритма, таблицы энергий, ошибки чтения и флаги качества "
         "сохранены в [манифесте](goes-sources.json.gz). День с файлом всё ещё может содержать пропуски после проверки качества.",'',
         '| Направление | Первое измерение UTC | Конец последнего бина UTC | Покрыто, с | Пропуски, с | S₁ на покрытии | S₂ на покрытии, с⁻¹ | k на покрытии |',
         '|---|---|---|---:|---:|---:|---:|---:|']
    for name,r in s['directions'].items():
        out.append(f"|{name}|{r['first_valid_utc']}|{r['last_valid_stop_utc']}|{r['covered_s']}|{r['missing_s']}|"
                   f"{r['S1_observed']:.6f}|{r['S2_observed_s_inv']:.6f}|{r['k_observed_exposure']:.6f}|")
    out.extend(['','Показатель k на покрытии равен T_obs S₂,obs/S₁,obs². Длительность T_obs есть сумма пригодных бинов, в том числе разнесённых во времени.',
                '', '| Направление | Пик ν, с⁻¹ и время UTC | Максимальный рост соседних средних, с⁻² и начало пары | Перекрытия, бины | Строгое качество, бины | Модель хвоста с подстановкой, бины |',
                '|---|---|---|---:|---:|---:|'])
    for name,r in s['directions'].items():
        out.append(f"|{name}|{r['peak_rate_s_inv']:.9g} · {r['peak_rate_utc']}|"
                   f"{r['max_upward_bin_slope_s_inv2']:.9g} · {r['upward_from_utc']}|{r['overlap_bins']}|"
                   f"{r['strict_bins_within_screened']}|{r['fallback_tail_bins']}|")
    out.extend(['','Перекрытие означает присутствие как минимум двух пригодных спутников в том же направлении. В интеграл вошёл один спутник по заранее принятому порядку. Поправка за межприборную калибровку принята равной единице, а сферическое 4π продолжение направленного потока условно. Для G18 сохраняется температурная оговорка T67. Для тестового периода G19 исключены затронутые каналы.',
                '', '| Спутник и направление | Пригодные бины до выбора | Бины в сумме | Первое пригодное начало | Последний пригодный конец |','|---|---:|---:|---|---|'])
    for key,r in sorted(s['availability_per_sat_direction'].items()):
        sat,d=key.split('_')
        out.append(f"|{key}|{r['valid_bins_before_selection']}|{s['directions'][d]['selected_bins_by_satellite'][sat[1:]]}|"
                   f"{r['first_valid_utc'] or '—'}|{r['last_valid_stop_utc'] or '—'}|")
    out.extend(['','## Каталог событий','',
        f"В версии каталога NOAA перечислено {s['official_events']} начал от 2017 года до отсечения. "
        f"Последнее доступное каталожное начало — {events['East'][-1]['onset']}. "
        "Версия воспроизводит все 46 исторических пар начала и пика T67. Длинный интервал между 04 и 25 января 2025 года помечен предупреждением источника. "
        "Завершение, пиковая частота, флюенс >30 МэВ и положительные подъёмы имеют раздельные признаки покрытия. "
        "Первый наблюдаемый подъём после пропуска может начинаться позже физического. "
        "[Каталог с повторными подъёмами](goes-events.json.gz) · [Исходный каталог NOAA](https://www.ngdc.noaa.gov/stp/space-weather/interplanetary-data/solar-proton-events/SEP%20page%20code.html).",
        '', '| Направление | События с данными | Конец по шести бинам, без внутренних дыр | Медиана наблюдаемого пика, с⁻¹ | Медиана наблюдаемого флюенса, см⁻² |',
        '|---|---:|---:|---:|---:|'])
    for name,r in s['directions'].items():
        stats=r['event_support_statistics']
        out.append(f"|{name}|{r['catalogued_events_with_a_valid_rate']}|{r['event_end_status_counts'].get('six_bins_below_10_pfu',0)}|"
                   f"{stats['peak_rate']['quantiles']['0.5']:.8g}|{stats['fluence30_observed_cm2']['quantiles']['0.5']:.8g}|")
    out.extend(['','Распределения и диапазоны доступны в [численных результатах](goes.json). Секунды покрытия каждого флюенса указаны в каталоге событий.',
        '', '## Что требуется для календарной оценки', '',
        'Пусть G — суммарная длительность пропусков, Y₁ и Y₂ — интегралы ν и ν² по ним. Тогда S₁=S₁,obs+Y₁, S₂=S₂,obs+Y₂ и Y₂≥Y₁²/G при G>0. В модели с постоянным фоном b≥0 также Y₁≥bG. Если независимо установлен физический верх B≥ν, добавляются условия Y₁≤BG и Y₂≤(b+B)Y₁−bBG. Без такого верха пики в пропусках и внутри пятиминутного бина не имеют конечной оценки из этих измерений. При переходе к десятилетию вообще возможен лишь тривиальный физический диапазон k класса от 1 без установленного конечного верха. Для расчёта показателей за весь календарный срок нужны границы Y₁,Y₂ даже при известном общем времени наблюдения.',
        '', 'Для расширения на GOES-13/15 нужны датированный интервал до 2017 года, согласованные энергетические каналы, отклик и проверка межприборной калибровки на перекрытии. Для периода до регулярных SGPS остаются многолетние разрывы. [Контраст LEO и вход SEPEM](ARCHIVES.md).',''])
    return '\n'.join(out)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--index',required=True,type=Path);p.add_argument('--cache',required=True,type=Path)
    p.add_argument('--local',type=Path);p.add_argument('--limit',type=int);p.add_argument('--fold',action='store_true')
    p.add_argument('--retry-missing',action='store_true');p.add_argument('--check',action='store_true');args=p.parse_args()
    index=json.loads(args.index.read_text(encoding='utf-8'))
    frozen=None
    if args.fold and args.check:
        with gzip.open(HERE/'goes-sources.json.gz','rt',encoding='utf-8') as stream:
            known=json.load(stream)
        if known['index']!=index:raise SystemExit('GOES inventory differs from issued input')
        frozen=known['receipt']
    if args.fold or args.retry_missing:process(index,args.cache,args.local,args.limit,args.retry_missing,frozen)
    if args.limit:return
    receipt=json.loads((args.cache/'receipt.json').read_text(encoding='utf-8'))
    receipt['folded'].sort(key=lambda r:r['url'])
    folded={r['url'] for r in receipt['folded']}
    assert folded|set(receipt['errors'])==set(index['selected_daily']+[index['special']])
    summary,events=summarize(args.cache,index,receipt)
    sources={'index':index,'receipt':receipt,'signatures':passport_by_signature(args.cache,receipt['folded'])}
    report_text=report(summary,events,sources)
    report_file=HERE/'GOES.md'
    if args.check:
        if report_file.read_text(encoding='utf-8')!=report_text:raise SystemExit('Mismatch: GOES.md')
    else:
        report_file.write_text(report_text,encoding='utf-8',newline='\n')
    for name,data in [('goes.json',summary),('goes-events.json.gz',events),('goes-sources.json.gz',sources)]:
        pretty=not name.endswith('.gz')
        content=(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2 if pretty else None,
                            separators=(',',': ') if pretty else (',',':'))+'\n').encode()
        if name.endswith('.gz'):content=gzip.compress(content,compresslevel=9,mtime=0)
        target=HERE/name
        if args.check:
            unpack=gzip.decompress if name.endswith('.gz') else lambda s:s
            if unpack(target.read_bytes())!=unpack(content):raise SystemExit('Mismatch: '+name)
        else:target.write_bytes(content)
    print(json.dumps(summary['directions'],indent=2))


if __name__=='__main__':main()

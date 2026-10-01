"""Repo-native scientific figures and compact audit tables (no resampling inputs)."""
from __future__ import annotations
import csv
from datetime import datetime,timezone
import gzip
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from analyze import write_csv, stamp

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.hashsalt':'t67-fixed',
                     'axes.spines.top':False,'axes.spines.right':False})
COLORS=['#1762a4','#bd4d17']


def table(path):
    op=gzip.open if str(path).endswith('.gz') else open
    with op(path,'rt',newline='') as f:
        return list(csv.DictReader(f))


def save(fig,path):
    fig.savefig(path.with_suffix('.png'),dpi=170,bbox_inches='tight',metadata={'Software':'T67'})
    fig.savefig(path.with_suffix('.svg'),bbox_inches='tight',metadata={'Date':None})
    plt.close(fig)


def broken(time,values,mask,signature,cadence):
    """Do not draw a line over a missing bin or processing boundary."""
    x=time.astype('datetime64[s]')
    y=values.copy()
    y[~mask]=np.nan
    edge=np.r_[False,(np.diff(time)!=cadence)|(signature[1:]!=signature[:-1])]
    # Insert NaN separators; retain both edge observations instead of deleting one.
    outx,outy=[],[]
    for i in range(len(x)):
        if edge[i]:
            outx.append(x[i]);outy.append(np.nan)
        outx.append(x[i]);outy.append(y[i])
    return np.asarray(outx),np.asarray(outy)


def make_figures(manifest,series_dir,out):
    groups={}
    for sat in (16,18,19):
        for cad in (60,300):
            path=series_dir/f'g{sat}_{cad}.npz'
            if path.exists():
                with np.load(path) as z: groups[sat,cad]={k:z[k] for k in z.files}
    metrics=table(out/'growth_metrics.csv.gz')
    summaries=table(out/'series_summary.csv.gz')
    authors={s:e['id'] for e in manifest['events'] for s in e.get('author_dates',[])}
    author_rows=[r for r in metrics if r['event_id'] in set(authors.values()) and r['series']=='main_loglog'
                 and r['mask']=='screened' and r['level_label'].startswith('abs_')]
    write_csv(out/'author_points.csv',author_rows)
    cadrows=[]
    for sat in (16,18,19):
        if (sat,60) not in groups or (sat,300) not in groups: continue
        one,five=groups[sat,60],groups[sat,300]
        positions=np.searchsorted(one['time'],five['time'])
        complete=(positions+4<len(one['time']))
        rows=np.flatnonzero(complete)
        ind=positions[rows,None]+np.arange(5)
        keep=np.all(one['time'][ind]==five['time'][rows,None]+np.arange(5)*60,axis=1)
        rows,ind=rows[keep],ind[keep]
        for d,direction in enumerate(('E','W')):
            valid=np.all(one['complete'][ind,d],axis=(1,2)) & np.all(five['complete'][rows,d],axis=1)
            for name in ('core_only','main_loglog'):
                a=np.mean(one[name][ind,d],axis=1);b=five[name][rows,d]
                m=valid&np.isfinite(a)&np.isfinite(b)&(b>=1e-4)
                if not np.any(m):continue
                rel=np.abs(a[m]-b[m])/b[m]
                cadrows.append({'satellite':sat,'direction':direction,'series':name,'pairs':int(np.sum(m)),
                                'native_5m_level_floor_s-1':1e-4,'median_absolute_relative_difference':float(np.median(rel)),
                                'p99_absolute_relative_difference':float(np.quantile(rel,.99)),
                                'max_absolute_relative_difference':float(np.max(rel)),
                                'status':'descriptive; full source seconds; 5m reconstruction vs mean of 1m reconstructions'})
    write_csv(out/'cadence_consistency.csv',cadrows)
    fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for ax,(day,sat) in zip(axs.flat,[('2024-06-08',16),('2024-11-21',16),('2025-11-11',19),('2026-01-19',19)]):
        zero=stamp(day+'T00:00:00+00:00')
        for cad in (60,300):
            if (sat,cad) not in groups:continue
            g=groups[sat,cad];m=(g['time']>=zero-12*3600)&(g['time']<zero+48*3600)
            for d,direction in enumerate(('E','W')):
                x,y=broken(g['time'][m],g['main_loglog'][m,d],g['screened'][m,d],g['signature'][m],cad)
                ax.plot(x,y,color=COLORS[d],alpha=.5 if cad==60 else 1,lw=.65 if cad==60 else 1.25,
                        linestyle='-' if cad==60 else '--',label=f'{direction}, {cad//60} мин')
        for level in (.001,.01,.1):ax.axhline(level,color='#888888',lw=.65,ls=':')
        ax.set(yscale='log',ylim=(1e-7,1),title=f'{day} · GOES-{sat}',ylabel='Модельные инверсии массива, с⁻¹')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m\n%H:%M'))
        ax.grid(alpha=.14);ax.legend(ncol=2,fontsize=8)
    fig.suptitle('R0-A: протонный отклик 32 data bits × 2¹⁹, 10 мм Al\nScreened; минутные и пятиминутные бины, не непрерывная граница',fontsize=13)
    save(fig,out/'author_events')
    rho=table(out/'rho_candidates.csv')
    fig,ax=plt.subplots(figsize=(8.3,5),layout='constrained')
    disjoint=table(out/'time_disjoint_holdout.csv')
    for holdout,label in (('False','Основная подвыборка'),('True','Отложенные без пересечения')):
        for cad,color in ((60,COLORS[0]),(300,COLORS[1])):
            pool=rho if holdout=='False' else disjoint
            found=[r for r in pool if r['holdout']==holdout and r['mask']=='screened' and int(r['cadence_s'])==cad and int(r['window_s'])==cad and r.get('rho_observed_s-1')]
            rows=[max([r for r in found if r['level_s-1']==level],key=lambda r:float(r['rho_observed_s-1'])) for level in sorted({r['level_s-1'] for r in found})]
            rows.sort(key=lambda r:float(r['level_s-1']))
            ax.plot([float(r['level_s-1']) for r in rows],[float(r['rho_observed_s-1']) for r in rows],
                    marker='o' if holdout=='False' else 's',ls='-' if holdout=='False' else '--',color=color,
                    label=f'{label}, {cad//60} мин')
    ax.axhline(1/300,color='#555555',ls=':',label='1/300 с⁻¹: ориентир e за 5 мин выше l')
    ax.set(xscale='log',yscale='log',xlabel='Порог l для модельного отклика, с⁻¹',ylabel='Максимум ΔHₗ/Δt по бинам, с⁻¹',
           title='Наблюдаемые требования к росту ≠ проектная верхняя граница')
    ax.grid(alpha=.2);ax.legend(fontsize=8)
    save(fig,out/'growth_thresholds')
    # Strongest screened native increment: inspect measured P6/P7 beside its
    # model, not just a selected attractive author example.
    cases=[r for r in rho if r['mask']=='screened' and r['level_s-1']=='0.001' and r['cadence_s']=='60' and r['window_s']=='60']
    if cases:
        case=max(cases,key=lambda r:float(r['rho_observed_s-1']))
        sat=int(case['satellite']);center=stamp(case['start_utc'])
        fig,axs=plt.subplots(2,1,figsize=(10,7),sharex=True,layout='constrained')
        for cad in (60,300):
            g=groups[sat,cad];m=(g['time']>=center-1800)&(g['time']<=center+1800)
            for d,direction in enumerate(('E','W')):
                for c,name in ((6,'P6'),(7,'P7')):
                    if cad!=60:continue
                    x,y=broken(g['time'][m],g['flux'][m,d,c],g['flux_screened'][m,d,c],g['signature'][m],cad)
                    axs[0].plot(x,y,color=COLORS[d],ls='-' if c==6 else '--',label=f'{direction} {name}')
                x,y=broken(g['time'][m],g['main_loglog'][m,d],g['screened'][m,d],g['signature'][m],cad)
                axs[1].plot(x,y,color=COLORS[d],ls='-' if cad==60 else '--',label=f'{direction}, {cad//60} мин')
        axs[0].set(ylabel='Измеренный поток\nпротоны/(см²·ср·с·МэВ)',yscale='log')
        axs[1].set(ylabel='Модельные инверсии\nмассива, с⁻¹',yscale='log',xlabel='UTC; метки начала бинов')
        axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        for ax in axs:
            ax.axvspan(datetime.fromtimestamp(center,timezone.utc),datetime.fromtimestamp(center+60,timezone.utc),color='#dddddd',alpha=.6)
            ax.grid(alpha=.15);ax.legend(ncol=4,fontsize=8)
        fig.suptitle(f"Наибольшее screened ΔH при l=0,001 с⁻¹ · GOES-{sat}\n{case['start_utc']} → {case['end_utc']}; измерение и модель разделены",fontsize=11)
        save(fig,out/'decisive_growth')
    return {'figures':['author_events','growth_thresholds','decisive_growth']}

"""New four-shield, disjoint-band RDS calculation and conditional chronology.

Raw and full derived series remain OUTSIDE Git. No download; input hash required.
No old 200000-mission campaign is repeated. The new 20000 draws test explicit
full-rate composition, off-mask time, population and unknown-tail sensitivities.
"""
import argparse
import csv
import json
import inspect
import math
import os
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd
from scipy.special import logsumexp

from chain import (HERE,ROOT,SEPEM,CFG,BITS,T,transport,digest,write_csv,write_json,load_module)
from calculate import component_rates

analysis=load_module('t141_pinned_event_statistics',SEPEM/'analysis.py')
N_ROWS=4365792
DT=300
RAW_SHA='012b8a375ded951fef9bd9268e20a97556a8a7ebc171dd8b7d0763141a41fa50'
ENERGY=transport.ENERGY
RHO=CFG['shield_g_cm2']


class BandResponse:
    def __init__(self,order=24):
        self.slopes=np.arange(-14.,8.0001,.02)
        self.bands=np.r_[5.,ENERGY,289.2,500.,1000.,3000.,10000.]
        self.kernels={}
        for i,rho in enumerate(RHO):
            e,w,_,residual=transport.quadrature(transport.RangeTable(),rho,order=order)
            for k,keep in enumerate((residual<5.,residual>=5.)):
                for j,(lo,hi) in enumerate(zip(self.bands[:-1],self.bands[1:])):
                    q=(e>=lo)&(e<hi)&keep&(w>0)
                    if not q.any():continue
                    anchor=int(np.clip(np.searchsorted(ENERGY,(lo+hi)/2)-1,0,len(ENERGY)-2))
                    self.kernels[i,k,j]=logsumexp(
                        self.slopes[:,None]*np.log(e[q]/ENERGY[anchor])+np.log(w[q]),axis=1)

    def calculate(self,f):
        if f.ndim!=2 or f.shape[1]!=11 or not np.isfinite(f).all() or np.any(f<=0):
            raise ValueError('11 positive finite RDS H channels required')
        slopes=np.diff(np.log(f),axis=1)/np.diff(np.log(ENERGY))
        if slopes.min()<self.slopes[0] or slopes.max()>self.slopes[-1]:
            raise ValueError('Unsupported spectral slope; no silent clipping')
        out=np.zeros((len(f),len(RHO),2))
        fluence30=np.zeros(len(f))
        for j,(lo,hi) in enumerate(zip(self.bands[:-1],self.bands[1:])):
            anchor=int(np.clip(np.searchsorted(ENERGY,(lo+hi)/2)-1,0,len(ENERGY)-2))
            s=slopes[:,anchor].copy();amp=f[:,anchor].copy()
            if lo>=ENERGY[-1]:
                s=np.minimum(slopes[:,-1],-2.)
                amp=f[:,-1]*np.exp(s*np.log(ENERGY[anchor]/ENERGY[-1]))
            for i in range(len(RHO)):
                for k in range(2):
                    key=i,k,j
                    if key in self.kernels:
                        out[:,i,k]+=amp*np.exp(np.interp(s,self.slopes,self.kernels[key]))*BITS*4*math.pi
            low=max(lo,30.)
            if low<hi:
                v=s+1;span=np.log(hi/low)
                ratio=np.full_like(v,span)
                far=np.abs(v)>1e-10
                ratio[far]=np.expm1(v[far]*span)/v[far]
                fluence30+=amp*low*np.exp(s*np.log(low/ENERGY[anchor]))*ratio*4*math.pi
        return out,fluence30


def build_cache(raw,cache,reuse):
    # Normalize '..' lexically before the Windows missing-path resolve fallback.
    cache=Path(os.path.abspath(cache))
    if ROOT==cache.resolve() or ROOT in cache.resolve().parents:
        raise ValueError('Full RDS derivatives must remain outside Git')
    cache.mkdir(parents=True,exist_ok=True)
    fingerprint={'raw_sha256':RAW_SHA,'kernel_code_sha256':__import__('hashlib').sha256(inspect.getsource(BandResponse).encode()).hexdigest(),
                 'transport_sha256':digest(SEPEM/'transport.py'),
                 'sigma_sha256':digest(transport.SIGMA_PATH),'sigma_module_sha256':digest(transport.SIGMA_MODULE),
                 'config_sha256':digest(HERE/'config.json'),
                 'pstar_sha256':digest(SEPEM/'inputs/nist_pstar_al.csv')}
    if digest(raw)!=RAW_SHA:raise ValueError('RDS raw hash mismatch')
    if reuse:
        saved=json.loads((cache/'manifest.json').read_text())
        if saved['fingerprint']!=fingerprint:raise ValueError('Stale cache fingerprint')
        for name,sha in saved['arrays_sha256'].items():
            if digest(cache/name)!=sha:raise ValueError('Changed cache array')
    else:
        response=BandResponse();offset=0
        print('T141 new four-shield kernels ready',flush=True)
        rates=np.lib.format.open_memmap(cache/'bands.npy',mode='w+',dtype='float64',shape=(N_ROWS,4,2))
        flux=np.lib.format.open_memmap(cache/'flux30.npy',mode='w+',dtype='float64',shape=(N_ROWS,))
        for chunk in pd.read_csv(raw,skiprows=1,header=None,chunksize=50000):
            values=chunk.iloc[:,1:].to_numpy(dtype=float)
            end=offset+len(values)
            if end>N_ROWS:raise ValueError('Unexpected RDS length')
            rates[offset:end],flux[offset:end]=response.calculate(values)
            offset=end
            if offset%1000000==0:print(f'T141 RDS {offset}/{N_ROWS}',flush=True)
        if offset!=N_ROWS:raise ValueError('Truncated RDS')
        rates.flush();flux.flush()
        saved={'fingerprint':fingerprint,'n':N_ROWS,'dt_s':DT,
               'arrays_sha256':{n:digest(cache/n) for n in ('bands.npy','flux30.npy')},
               'lookup_relative_upper':math.expm1(.02**2*np.max(np.log(response.bands[1:]/response.bands[:-1]))**2/32),
               'lookup_scope':'positive discrete quadrature only; not response/transport/physical uncertainty'}
        write_json(cache/'manifest.json',saved)
    return np.load(cache/'bands.npy',mmap_mode='r'),np.load(cache/'flux30.npy',mmap_mode='r'),saved


def statistics(bands,intervals,remove_floor=True):
    total=np.asarray(bands.sum(axis=1))
    floor=float(np.quantile(total,.1)) if remove_floor else 0.
    solar=np.maximum(total-floor,0.)
    # Remove scalar baseline proportionally, preserving low+high exactly.
    components=np.asarray(bands)*np.divide(solar,total,out=np.zeros_like(total),where=total>0)[:,None]
    mask=np.zeros(len(total),bool)
    events=[]
    for a,b in intervals:
        mask[a:b]=True
        x=components[a:b];y=solar[a:b];gram=x.T@x*DT
        integral=x.sum(axis=0)*DT
        events.append([DT*(b-a),float(y.sum()*DT),float(y@y*DT),float(y.max()),
                       float(integral[0]),float(integral[1]),float(gram[0,0]),float(gram[1,1]),float(2*gram[0,1])])
    off=solar[~mask]
    return np.asarray(events),dict(floor_s_inv=floor,off_mean_s_inv=float(off.mean()),
        off_mean_square_s_inv2=float(off@off/len(off)),off_peak_s_inv=float(off.max()),
        off_duration_s=len(off)*DT,off_N=float(off.sum()*DT),off_S2_s_inv=float(off@off*DT),
        total_S2_s_inv=float(solar@solar*DT),total_N=float(solar.sum()*DT)),solar


def mission_values(counts,events,off,b,c):
    """Whole events packed without overlap; remaining time uses off-mask moments.

    This defines a realizable conditional chronology with HI=c-1 times H.
    It is NOT claimed to be the future solar-cycle chronology. The same draw
    supplies peak, N and S2; their marginal quantiles are never multiplied.
    """
    occupied=counts@events[:,0]
    quiet=T-occupied
    if np.any(quiet<0):raise ValueError('Sampled events cannot fit declared nonoverlap chronology')
    n=counts@events[:,1]+quiet*off['off_mean_s_inv']
    s2=counts@events[:,2]+quiet*off['off_mean_square_s_inv2']
    peak=np.maximum(np.max((counts>0)*events[None,:,3],axis=1),off['off_peak_s_inv'])
    return dict(N=b*T+c*n,S2=b*b*T+2*b*c*n+c*c*s2,peak=b+c*peak,
                solar_N=n,solar_S2=s2,quiet=quiet)


def qsummary(samples):
    q=analysis.quantile_order_interval(samples)
    return {'q90':q['estimate'],'MC95_low':q['lower'],'MC95_high':q['upper']}


def main(raw,cache,out,reuse):
    started=time.perf_counter()
    out.mkdir(parents=True,exist_ok=True)
    bands,flux,meta=build_cache(raw,cache,reuse)
    raw3=np.asarray(bands[:,1].sum(axis=1))
    intervals=analysis.detect_events(raw3)
    intervals=[(a,b) for a,b in intervals if a>0 and b<N_ROWS and flux[a:b].sum()*DT>1e5]
    saved=list(csv.DictReader((SEPEM/'outputs/events.csv').open(encoding='utf-8')))
    saved_intervals=[(int(r['start_index']),int(r['stop_index_exclusive'])) for r in saved]
    if intervals!=saved_intervals:raise ValueError('Nominal event segmentation changed: explicit review required')
    pop=json.loads((ROOT/'experiments/t127-cy62167-pdi/outputs/population.json').read_text())
    means=[pop['filtered_count_per_10_Julian_years'],92.5548,pop['actual_cycle_expected_per_10_Julian_years']]
    # Poisson splitting into labelled empirical events gives one shared draw for all shields.
    draws={mean:np.random.Generator(np.random.PCG64(CFG['profile_seed'])).poisson(
        mean/len(intervals),size=(CFG['profile_missions'],len(intervals))) for mean in means}
    event_rows=[];background_rows=[];mission_rows=[];sens=[];cycle=[];seg=[];shape_rows=[]
    basis={}
    for i,rho in enumerate(RHO):
        ev,off,solar=statistics(bands[:,i],intervals)
        rates=component_rates(rho)
        b=sum(rates['background'].values())
        r=rates['solar']['LET_exclusive']/(rates['solar']['H_low']+rates['solar']['H_high'])
        c=1+r
        basis[rho]=dict(b=b,HI_to_H_assumed=r,**off)
        background_rows.append(dict(shield_g_cm2=rho,cosrad_b_s_inv=b,HI_to_H_assumed=r,**off))
        for j,(a,z) in enumerate(intervals):
            v=ev[j]
            event_rows.append(dict(shield_g_cm2=rho,event=j+1,start_index=a,stop_index=z,
                duration_s=v[0],H_solar_N=v[1],H_solar_S2_s_inv=v[2],H_solar_peak_s_inv=v[3],
                H_low_N=v[4],H_high_N=v[5],H_low_S2_s_inv=v[6],H_high_S2_s_inv=v[7],
                twice_low_high_s_inv=v[8],H_shape=v[2]/(v[1]*v[3]),
                HI_proxy_S2_s_inv=r*r*v[2],twice_H_HI_proxy_s_inv=2*r*v[2]))
        for mean,counts in draws.items():
            v=mission_values(counts,ev,off,b,c)
            q=qsummary(v['S2'])
            mission_rows.append(dict(shield_g_cm2=rho,mean_events=mean,missions=len(counts),
                background_s_inv=b,HI_to_H_assumed=r,
                N_mean=float(v['N'].mean()),N_q90=float(np.quantile(v['N'],.9,method='inverted_cdf')),
                peak_q90_s_inv=float(np.quantile(v['peak'],.9,method='inverted_cdf')),
                S2_q90_s_inv=q['q90'],S2_MC95_low_s_inv=q['MC95_low'],S2_MC95_high_s_inv=q['MC95_high'],
                maximum_occupied_fraction=float(1-v['quiet'].min()/T),
                physical_joint_q90=None,status='CONDITIONAL_PACKED_EMPIRICAL_MODEL; no physical quantile'))
            # Fixed COSRAD scalar peak and N, varied TOTAL shape only. We do
            # not multiply sampled marginal peak/fluence quantiles. r is
            # calculated from the very same complete mission draw.
            hpeak=(v['peak']-b)/c
            rmission=v['solar_S2']/(hpeak*v['solar_N'])
            if np.any(rmission>1+1e-10):raise ValueError('Invalid mission shape')
            rq=float(np.quantile(rmission,.9,method='inverted_cdf'))
            p_design=sum(rates['solar'].values());n_design=CFG['cosrad_Teff_s']*p_design
            for label,shape in [('universal',1.),('sample_max',float(rmission.max())),('sample_q90',rq)]:
                shape_rows.append(dict(shield_g_cm2=rho,mean_events=mean,shape_choice=label,shape=shape,
                    fixed_background_s_inv=b,fixed_solar_peak_s_inv=p_design,fixed_solar_N=n_design,
                    S2_s_inv=b*b*T+2*b*n_design+shape*p_design*n_design,
                    status='same fixed scalar inputs; shape transfer ASSUMPTION; no joint physical Pi claim'))
        mean=means[-1];counts=draws[mean];v=mission_values(counts,ev,off,b,c)
        candidates={'nominal':v['S2']}
        for mult in (0.,2.):
            candidates[f'HI_to_H_x{mult:g}']=mission_values(counts,ev,off,b,1+r*mult)['S2']
        for kappa in (2.,10.):
            candidates[f'subbin_solar_S2_x{kappa:g}']=b*b*T+2*b*c*v['solar_N']+c*c*kappa*v['solar_S2']
        raw_ev,raw_off,_=statistics(bands[:,i],intervals,False)
        candidates['no_p10_subtraction']=mission_values(counts,raw_ev,raw_off,b,c)['S2']
        empty_off={**off,'off_mean_s_inv':0.,'off_mean_square_s_inv2':0.,'off_peak_s_inv':0.}
        candidates['omit_outside_mask_DIAGNOSTIC_ONLY']=mission_values(counts,ev,empty_off,b,c)['S2']
        # Sensitivity to unknown overlap of distinct event histories; Cauchy cap.
        overlap_cap=(counts@np.sqrt(ev[:,2]))**2-counts@ev[:,2]
        for fraction in (.01,1.):
            candidates[f'interevent_Cauchy_fraction_{fraction:g}']=v['S2']+c*c*fraction*overlap_cap
        # Rare unobserved population is a parameter, never estimated by MC CI.
        j=int(np.argmax(ev[:,2]));largest=ev[j]
        for prob in (.01,.1,.2):
            rare=np.random.Generator(np.random.PCG64(CFG['profile_seed']+77)).poisson(-math.log1p(-prob),len(counts))
            if np.any(rare*largest[0]>v['quiet']):raise ValueError('Rare event does not fit')
            k=10.
            dn=rare*(k*largest[1]-off['off_mean_s_inv']*largest[0])
            ds=rare*(k*k*largest[2]-off['off_mean_square_s_inv2']*largest[0])
            candidates[f'rare_p{prob:g}_amplitude10']=v['S2']+2*b*c*dn+c*c*ds
        for name,a in candidates.items():
            qs=qsummary(a)
            sens.append(dict(shield_g_cm2=rho,case=name,mean_events=mean,S2_q90_s_inv=qs['q90'],
                ratio_to_nominal=qs['q90']/qsummary(v['S2'])['q90'],
                kind='model sensitivity; parameter ranges not confidence bounds'))
        # Fixed Julian 10-year windows, yearly starts; overlapping/descriptive only.
        start=np.datetime64('1974-07-01T00:00:00','s')
        width=T//DT
        cumulative_n=np.r_[0,np.cumsum(solar,dtype=float)]*DT
        cumulative_s=np.r_[0,np.cumsum(solar*solar,dtype=float)]*DT
        for year in range(1975,2007):
            a=int((np.datetime64(f'{year}-01-01','s')-start).astype(int)//DT);z=a+width
            if z>N_ROWS:continue
            n=cumulative_n[z]-cumulative_n[a];s=cumulative_s[z]-cumulative_s[a]
            cycle.append(dict(shield_g_cm2=rho,start_year=year,duration_s=T,
                H_solar_N=n,H_solar_S2_s_inv=s,S2_H_HI_proxy_plus_background_s_inv=b*b*T+2*b*c*n+c*c*s,
                selected_event_starts=sum(a<=lo<z for lo,_ in intervals),
                status='overlapping observed windows; NOT independent future missions'))
    for threshold,gap in [(10,24),(5,24),(20,24),(10,12),(10,48)]:
        ints=analysis.detect_events(raw3,multiplier=threshold,merge_hours=gap)
        ints=[(a,b) for a,b in ints if a>0 and b<N_ROWS and flux[a:b].sum()*DT>1e5]
        ev,off,_=statistics(bands[:,1],ints)
        counts=np.random.Generator(np.random.PCG64(CFG['profile_seed'])).poisson(means[-1]/len(ints),
            (CFG['profile_missions'],len(ints)))
        b=basis[3.]['b'];c=1+basis[3.]['HI_to_H_assumed']
        v=mission_values(counts,ev,off,b,c)
        seg.append(dict(threshold=threshold,merge_hours=gap,events=len(ints),
            empirical_per_10y=len(ints)*T/(N_ROWS*DT),mean_count_assumed=means[-1],
            S2_q90_s_inv=qsummary(v['S2'])['q90'],off_S2_s_inv=off['off_S2_s_inv'],
            status='fixed count assumption despite different extracted populations; diagnostic'))
    write_csv(out/'profile-events.csv',event_rows)
    write_csv(out/'profile-background.csv',background_rows)
    write_csv(out/'profile-missions.csv',mission_rows)
    write_csv(out/'profile-sensitivity.csv',sens)
    write_csv(out/'cycle-windows.csv',cycle)
    write_csv(out/'segmentation.csv',seg)
    write_csv(out/'shape-transfer.csv',shape_rows)
    # Historical pure-H archive check; production profiles are a new convolution.
    reference=np.array([float(r['S2_s-1']) for r in saved])
    fresh,_off,_solar=statistics(bands[:,1],intervals,False)
    rel=float(np.max(np.abs(fresh[:,2]-reference)/reference))
    if rel>1e-4:raise ValueError('New H response disagrees with pinned event moments')
    write_json(out/'profile-provenance.json',dict(
        input=meta,code_sha256=digest(Path(__file__)),conditions_sha256=digest(HERE/'conditions.json'),
        shared_code_sha256={n:digest(HERE/n) for n in ('chain.py','calculate.py','config.json')},
        analysis_code_sha256=digest(SEPEM/'analysis.py'),python=platform.python_version(),
        numpy=np.__version__,pandas=pd.__version__,scipy=__import__('scipy').__version__,
        random_generator='PCG64',seed=CFG['profile_seed'],missions_per_case=CFG['profile_missions'],
        nominal_events=len(intervals),legacy_event_S2_max_relative_difference=rel,
        spectral_bands_are_not_pure_mechanism_labels=True,
        HI_time_model='r times H excess, r from COSRAD peak ratio; a transfer assumption, not measured ions',
        calendar='whole empirical events packed disjointly into T; remaining time uses off-mask moments',
        rare_tail_coverage=None,physical_joint_quantile=None,
        compact_inputs_sha256={str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in
            [SEPEM/'outputs/events.csv',ROOT/'experiments/t127-cy62167-pdi/outputs/population.json']},
        outputs_sha256={p.name:digest(p) for p in out.glob('*.csv') if p.name.startswith('profile-') or p.name in ('cycle-windows.csv','segmentation.csv','shape-transfer.csv')}))
    print(f'T141 profiles: {len(intervals)} events; {len(mission_rows)} new model rows; {time.perf_counter()-started:.1f}s',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--raw',type=Path,required=True,help='existing SEPEM_H_reference.txt')
    parser.add_argument('--cache',type=Path,required=True,help='outside Git')
    parser.add_argument('--reuse-cache',action='store_true')
    parser.add_argument('--out',type=Path,default=HERE/'outputs')
    a=parser.parse_args();main(a.raw,a.cache,a.out,a.reuse_cache)

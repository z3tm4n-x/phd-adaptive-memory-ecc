"""T150 addressed comparison on the immutable T141 response and checked cache."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T141 = ROOT/'experiments/t141-radiation-chain'
sys.path.insert(0, str(T141))
import profiles as source
from chain import digest, write_csv, write_json
from moments import gram_moments, assemble, pack, q90, overflow_bound, shape_transfer, rolling_moments

T = source.T
DT = source.DT
SEED = 2026101301  # paired with accepted T141; no new large sampling campaign
MISSIONS = 20000
CASES = [('full',1.,1.,1.), ('no_low',0.,1.,1.), ('low_half',.5,1.,1.),
         ('low_double',2.,1.,1.), ('LET_zero',1.,0.,1.), ('LET_half',1.,.5,1.),
         ('H_geometry_half',1.,1.,.5), ('H_geometry_double',1.,1.,2.)]


def event_stats(x, intervals):
    mask = np.zeros(len(x), bool)
    ns, gs, ds = [], [], []
    for a,z in intervals:
        mask[a:z] = True
        n,g = gram_moments(x[a:z], DT)
        ns.append(n); gs.append(g); ds.append((z-a)*DT)
    off = x[~mask]
    n,g = gram_moments(off, 1.)
    return np.array(ds), np.array(ns), np.array(gs), mask, n/len(off), g/len(off)


def scenario(bparts, pparts, x, ion_ratio, low, ion, geometry):
    # The ion proxy is frozen BEFORE low-energy response changes. Recomputing
    # ion_ratio from the modified H would confound two changes.
    transform = np.array([[geometry*low,0.], [0.,geometry],
                          [ion*ion_ratio,ion*ion_ratio]])
    weights = transform.sum(axis=0)
    b = bparts['H_low']*geometry*low+bparts['H_high']*geometry+bparts['LET_exclusive']*ion
    peak = pparts['H_low']*geometry*low+pparts['H_high']*geometry+pparts['LET_exclusive']*ion
    return transform, weights, b, peak


def main(raw, cache, out):
    started = time.perf_counter()
    out.mkdir(parents=True,exist_ok=True)
    # This only reads/validates T141 raw/cache; no new response convolution.
    bands, flux, cache_meta = source.build_cache(raw,cache,True)
    nominal = list(csv.DictReader((T141/'outputs/profile-missions.csv').open(encoding='utf-8')))
    evold = list(csv.DictReader((source.SEPEM/'outputs/events.csv').open(encoding='utf-8')))
    intervals = [(int(r['start_index']), int(r['stop_index_exclusive'])) for r in evold]
    means = sorted(set(float(r['mean_events']) for r in nominal))
    draws = {mu:np.random.Generator(np.random.PCG64(SEED)).poisson(mu/len(intervals),
                    size=(MISSIONS,len(intervals))) for mu in means}
    shapes=[]; mission=[]; events=[]; windows=[]; decompositions=[]; overflows=[]
    moments_rows=[]; sensitivities=[]; numerical_checks=[]; rolling_rows=[]
    for i,rho in enumerate(source.RHO):
        rates = source.component_rates(rho)
        bparts, pparts = rates['background'], rates['solar']
        h = np.asarray(bands[:,i])
        ht = h.sum(axis=1)
        baseline = np.quantile(ht,.1)
        x = h*np.maximum(0.,ht-baseline)[:,None]/ht[:,None]
        ratio = pparts['LET_exclusive']/(pparts['H_low']+pparts['H_high'])
        duration, en, eg, mask, on, og = event_stats(x, intervals)
        for mu in means:
            overflows.append(dict(shield_g_cm2=rho, mean_events=mu,
                max_event_duration_s=float(duration.max()), **overflow_bound(mu,duration.max(),T),
                rule='overflow -> +infinity S2 and exceedance; no rejection or resampling'))
        for case, low, ion, geometry in CASES:
            transform,w,b,p = scenario(bparts,pparts,x,ratio,low,ion,geometry)
            y = x@w
            n = en@w
            g = np.einsum('i,nij,j->n',w,eg,w)
            peak = np.array([y[a:z].max() for a,z in intervals])
            off = dict(mean=float(on@w), mean_square=float(w@og@w), peak=float(y[~mask].max()))
            fixed_n = source.CFG['cosrad_Teff_s']*p
            fixed_f = b*T+fixed_n
            rect = shape_transfer(b,p,fixed_n,1.,T)
            shape_base = dict(shield_g_cm2=rho, response_case=case, background_s_inv=b,
                              solar_peak_s_inv=p, F_solar=fixed_n, F=fixed_f)
            shapes.append(dict(**shape_base, mean_events=None, choice='rectangle', r=1.,
                S2_s_inv=rect,G_ideal=T*rect/fixed_f**2,
                basis='conditional common scalar envelope; not a physical Pi=.1 quantile'))
            for mu,counts in draws.items():
                v = pack(counts,duration,n,g,peak,off,b,T)
                est,loq,hiq = q90(v['S2'])
                rq = q90(v['r'])[0]
                j = np.argsort(v['S2'],kind='stable')[math.ceil(.9*len(counts))-1]
                if v['overflow'][j]:
                    raise ValueError('q90 is infinite under declared overflow model')
                G = np.full(len(counts),np.inf)
                valid=~v['overflow']
                G[valid] = T*v['S2'][valid]/v['F'][valid]**2
                mission.append(dict(shield_g_cm2=rho,response_case=case,mean_events=mu,
                    S2_q90_s_inv=est,MC95_low_s_inv=loq,MC95_high_s_inv=hiq,
                    same_draw_F=float(v['F'][j]),same_draw_peak_s_inv=float(v['peak'][j]),
                    same_draw_solar_shape=float(v['r'][j]),G_ideal_same_draw=float(G[j]),
                    G_ideal_q90=q90(G)[0],r_q90=rq,r_sample_max=float(v['r'].max()),
                    overflow_count=int(v['overflow'].sum()),
                    physical_quantile=None,scope='fixed empirical model; F/peak/G at the S2 order-statistic draw'))
                for choice,r in [('model_r_q90',rq),('model_r_max',float(v['r'].max()))]:
                    val = shape_transfer(b,p,fixed_n,r,T)
                    shapes.append(dict(**shape_base,mean_events=mu,choice=choice,r=r,
                        S2_s_inv=val,G_ideal=T*val/fixed_f**2,
                        basis='fixed COSRAD b/p/F; transfer of empirical shape is ASSUMPTION'))
                if case == 'full':
                    prev=next(r for r in nominal if float(r['shield_g_cm2'])==rho and float(r['mean_events'])==mu)
                    delta=abs(est-float(prev['S2_q90_s_inv']))/est
                    assert delta < 1e-11
                    numerical_checks.append(dict(check='T141_nominal_q90',rho=rho,mu=mu,relative_delta=delta))
                if mu==means[-1] and case in ('full','no_low'):
                    n2=counts[j]@en+(T-counts[j]@duration)*on
                    g2=np.einsum('n,nij->ij',counts[j],eg)+(T-counts[j]@duration)*og
                    n3=transform@n2;g3=transform@g2@transform.T
                    a=assemble(b,T,n3,g3)
                    assert np.isclose(a['S2'],est,rtol=3e-14)
                    decompositions.append(dict(shield_g_cm2=rho,response_case=case,
                        draw_index=int(j),mean_events=mu,**a,
                        H_low_S2=g3[0,0],H_high_S2=g3[1,1],LET_S2=g3[2,2],
                        twice_low_high=2*g3[0,1],twice_low_LET=2*g3[0,2],twice_high_LET=2*g3[1,2]))
            if case in ('full','no_low'):
                er = g/(n*peak)
                for j,(a,z) in enumerate(intervals):
                    events.append(dict(shield_g_cm2=rho,response_case=case,event=j+1,
                        start_index=a,stop_index=z,solar_N=n[j],solar_S2_s_inv=g[j],
                        solar_peak_s_inv=peak[j],r=float(er[j]),
                        status='observed binned transformed history; not future bound'))
                # Fixed Julian ten-year windows, annual starts, with ALL bins.
                cn=np.r_[0.,np.cumsum(y)]*DT;cs=np.r_[0.,np.cumsum(y*y)]*DT
                origin=np.datetime64('1974-07-01T00:00:00','s')
                for year in range(1975,2007):
                    a=int((np.datetime64(f'{year}-01-01','s')-origin).astype(int)//DT)
                    z=a+T//DT
                    if z>len(y):continue
                    N=cn[z]-cn[a];S=cs[z]-cs[a];P=y[a:z].max()
                    full=b*b*T+2*b*N+S;F=b*T+N
                    windows.append(dict(shield_g_cm2=rho,response_case=case,start_year=year,
                        F=F,S2_s_inv=full,peak_s_inv=b+P,solar_N=N,solar_S2_s_inv=S,
                        r=S/(N*P),G_ideal=T*full/F**2,
                        status='overlapping full-history windows; not independent missions'))
                nr,gr=gram_moments(x,DT)
                parts=assemble(b,len(x)*DT,transform@nr,transform@gr@transform.T)
                moments_rows.append(dict(shield_g_cm2=rho,response_case=case,
                    duration_s=len(x)*DT,**parts,baseline_H_s_inv=float(baseline)))
                wn,ws,wp=rolling_moments(y,T//DT,DT)
                wr=ws/(wp*wn);j=int(np.argmax(wr))
                rolling_rows.append(dict(shield_g_cm2=rho,response_case=case,windows=len(wr),
                    step_s=DT,duration_s=T,r_min=float(wr.min()),r_median=float(np.median(wr)),
                    r_max=float(wr[j]),r_max_start_index=j,
                    same_window_F=float(b*T+wn[j]),same_window_S2_s_inv=float(b*b*T+2*b*wn[j]+ws[j]),
                    same_window_peak_s_inv=float(b+wp[j]),
                    max_S2_s_inv=float(np.max(b*b*T+2*b*wn+ws)),
                    status='all starts on the full unmasked binned history; overlapping descriptive windows'))
                del wn,ws,wp,wr
            if case=='full':
                mu=means[-1];counts=draws[mu]
                v=pack(counts,duration,n,g,peak,off,b,T)
                base=v['S2'];nom=q90(base)[0]
                for k in (2.,10.):
                    a=b*b*T+2*b*v['solar_N']+k*v['solar_S2']
                    sq,slo,shi=q90(a)
                    sensitivities.append(dict(shield_g_cm2=rho,case=f'subbin_S2_x{k:g}',
                        S2_q90_s_inv=sq,MC95_low_s_inv=slo,MC95_high_s_inv=shi,ratio_to_full=sq/nom,
                        basis='subbin variance assumption; F preserved, true peak can increase'))
                overlap=(counts@np.sqrt(g))**2-counts@g
                for k in (.01,1.):
                    a=base+k*overlap
                    sq,slo,shi=q90(a)
                    sensitivities.append(dict(shield_g_cm2=rho,case=f'overlap_Cauchy_{k:g}',
                        S2_q90_s_inv=sq,MC95_low_s_inv=slo,MC95_high_s_inv=shi,ratio_to_full=sq/nom,
                        basis='Cauchy interevent term at frozen first/off-mask moments; not a generated timeline'))
                j=int(np.argmax(g))
                for probability in (.01,.1,.2):
                    extra=np.random.Generator(np.random.PCG64(SEED+77)).poisson(-math.log1p(-probability),MISSIONS)
                    aug_counts=np.column_stack((counts,extra))
                    v2=pack(aug_counts,np.r_[duration,duration[j]],np.r_[n,10*n[j]],
                        np.r_[g,100*g[j]],np.r_[peak,10*peak[j]],off,b,T)
                    sq,slo,shi=q90(v2['S2'])
                    sensitivities.append(dict(shield_g_cm2=rho,case=f'rare_p{probability:g}_amplitude10',
                        S2_q90_s_inv=sq,MC95_low_s_inv=slo,MC95_high_s_inv=shi,ratio_to_full=sq/nom,
                        basis='unobserved-tail parameter; same overflow rule; not estimated frequency'))
        print(f'T150 common history done: {rho:g} g/cm2',flush=True)
    segmentation=[]
    h=np.asarray(bands[:,1]);ht=h.sum(axis=1);x=h*np.maximum(0.,ht-np.quantile(ht,.1))[:,None]/ht[:,None]
    rates=source.component_rates(3.);ratio=rates['solar']['LET_exclusive']/sum(rates['solar'][k] for k in ('H_low','H_high'))
    b=sum(rates['background'].values());y=x.sum(axis=1)*(1+ratio)
    for threshold,gap in [(10,24),(5,24),(20,24),(10,12),(10,48)]:
        ints=source.analysis.detect_events(ht,multiplier=threshold,merge_hours=gap)
        ints=[(a,z) for a,z in ints if a>0 and z<len(y) and flux[a:z].sum()*DT>1e5]
        ds,ns,gs,mask,on,og=event_stats(x,ints);w=np.repeat(1+ratio,2)
        pk=np.array([y[a:z].max() for a,z in ints]);off=dict(mean=on@w,mean_square=w@og@w,peak=y[~mask].max())
        for mode,mu in [('fixed_event_count',means[-1]),
                        ('count_scaled_with_segmentation',means[-1]*len(ints)/len(intervals))]:
            counts=np.random.Generator(np.random.PCG64(SEED)).poisson(mu/len(ints),(MISSIONS,len(ints)))
            v=pack(counts,ds,ns@w,np.einsum('i,nij,j->n',w,gs,w),pk,off,b,T)
            sq,slo,shi=q90(v['S2'])
            segmentation.append(dict(threshold=threshold,merge_hours=gap,events=len(ints),
                population_rule=mode,mean_events=mu,S2_q90_s_inv=sq,MC95_low_s_inv=slo,MC95_high_s_inv=shi,
                overflow_count=int(v['overflow'].sum()),**overflow_bound(mu,ds.max(),T)))
    outputs={'shape-transfer.csv':shapes,'mission-model.csv':mission,'event-shapes.csv':events,
        'window-shapes.csv':windows,'square-decomposition.csv':decompositions,
        'overflow.csv':overflows,'archive-moments.csv':moments_rows,
        'tail-and-bin-sensitivity.csv':sensitivities,'segmentation.csv':segmentation,
        'window-all-starts.csv':rolling_rows}
    for name,rows in outputs.items():write_csv(out/name,rows)
    count=len(intervals);mu=means[-1];tail95=1-.05**(1/count)
    needed=-math.log(.9)/mu
    statistical=dict(Pi_event='P[S2_model(T)>s] <= .1; includes infinite overflow outcomes',
        horizon_s=T,missions=MISSIONS,seed=SEED,means=means,
        event_max_order_statistic=dict(assumption='iid event shapes, stationary population; NOT established',
            events=count,confidence=.95,tail_probability_upper=tail95,
            probability_any_future_shape_above_archive_max_upper=1-math.exp(-mu*tail95),
            sufficient_event_tail_for_mission_exceedance_point1=needed,
            iid_events_needed_for_95pct_tolerance=math.ceil(math.log(.05)/math.log1p(-needed)),
            warning='this is occurrence of an uncovered event, not itself proof of S2 exceedance'),
        physical_S2_q90=None,physical_shape_bound=None,physical_Gcert=None,
        numerical_checks=numerical_checks)
    write_json(out/'statistics.json',statistical)
    inputs=[T141/'outputs/contract.json',T141/'outputs/profile-provenance.json',
        T141/'outputs/profile-missions.csv',T141/'outputs/profile-events.csv',
        source.SEPEM/'outputs/events.csv',source.SEPEM/'outputs/analysis_summary.json',
        T141/'chain.py',T141/'calculate.py',T141/'profiles.py',T141/'config.json',
        source.SEPEM/'analysis.py',source.SEPEM/'transport.py']
    write_json(out/'radiation-provenance.json',dict(task=150,
        base='a69fe3df97eac5a509f65446395891e71a8e9553',T141_sha='ea789fc4b4d69699696d66a41b2738099d4154bb',
        plan_sha='faf2f82d0158e32fcdd54264d5c93a29b852f645',cache=cache_meta,
        code_sha256={n:digest(HERE/n) for n in ('radiation.py','moments.py')},
        input_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in inputs},
        output_sha256={n:digest(out/n) for n in [*outputs,'statistics.json']},
        python=sys.version.split()[0],numpy=np.__version__,scipy=__import__('scipy').__version__))
    print(f'T150 radiation calculation finished in {time.perf_counter()-started:.1f}s',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True)
    p.add_argument('--cache',type=Path,required=True);p.add_argument('--out',type=Path,default=HERE/'outputs')
    a=p.parse_args();main(a.raw,a.cache,a.out)

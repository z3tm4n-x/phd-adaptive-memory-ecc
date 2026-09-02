#!/usr/bin/env python3
from __future__ import annotations
import csv,json,math,sys,hashlib
from pathlib import Path
import numpy as np
from direct_floor_killtest import *
HERE=Path(__file__).resolve().parent; TASK2=HERE.parent/'RE-GOES19-PROTON-RATE-01'

def mods():
    if str(TASK2) not in sys.path: sys.path.insert(0,str(TASK2))
    from goes19_adapter import load_directory
    from rate_pipeline import reconstruct_goes,low_energy_extension,high_energy_gap_bridge,trap_weights
    from sigma_model import load_experimental_points,sigma_hat,zero_crossing_low
    from sigma_closure import load_pub,sigma_phys
    return locals()
def cent(a): return np.where(np.all(np.isfinite(a),axis=-1),np.mean(a,axis=-1),np.nan)
def q(a,p): return float(np.nanquantile(np.asarray(a,float),p))
def write(path,rows):
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def sha(p):
    h=hashlib.sha256();
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def calc(goes,a):
    m=mods(); z=np.load(a.transport); E=np.asarray(z['energy_mev'],float); shields=np.asarray(z['shield_mm'],float); P=np.asarray(z['primary'],float); S=np.asarray(z['secondary'],float)
    if tuple(shields.tolist())!=SHIELDS_MM: raise ValueError('shield grid')
    exp=m['load_experimental_points'](a.sigma_csv); pe,ps=m['load_pub'](a.published_csv)
    sig={'main_loglog':m['sigma_hat'](E,exp,'main_loglog'),'published_rpp_fluka_digitized':m['sigma_phys'](E,pe,ps,exp)}
    sigh={'main_loglog':float(m['sigma_hat'](np.array([600.]),exp,'main_loglog')[0]),'published_rpp_fluka_digitized':float(m['sigma_phys'](np.array([600.]),pe,ps,exp)[0])}
    pts=load_multiplicity_points(a.multiplicity_csv,a.false_mcu_csv); mm={}
    for v in MULTIPLICITY_VARIANTS:
        for low in LOW_SCENARIOS: mm[v,low]=multiplicity_on_grid(E,pts,v,low)
    J,_=m['reconstruct_goes'](goes,E); J*=FOUR_PI
    L,_=m['low_energy_extension'](goes,E,m['zero_crossing_low'](exp),2.); L*=FOUR_PI; inp=J+L
    gap,*_=m['high_energy_gap_bridge'](goes); tw=m['trap_weights'](E); lm=E<.9
    res={}; bit={}; lowfrac={}
    for di,dmm in enumerate(shields):
        od=[]
        for d in range(2):
            v=goes.valid[:,d]; x=np.full((len(goes.times),len(E)),np.nan); x[v]=inp[v,d]@P[di].T+inp[v,d]@S[di].T; od.append(x)
        for sm in SIGMA_MODELS:
            hb=N_BITS*FOUR_PI*sigh[sm]*(gap+goes.p11); rb=np.full((len(goes.times),2),np.nan); lb=np.full_like(rb,np.nan)
            re={k:np.full_like(rb,np.nan) for k in mm}; rm={k:np.full_like(rb,np.nan) for k in mm}
            for d in range(2):
                v=goes.valid[:,d]; dens=N_BITS*od[d][v]*sig[sm][None,:]; rb[v,d]=dens@tw+hb[v,d]; lb[v,d]=dens@(tw*lm)
                for k,(pm,kb) in mm.items():
                    re[k][v,d]=dens@(tw/kb)+hb[v,d]/kb[-1]; rm[k][v,d]=dens@(tw*pm/kb)+hb[v,d]*pm[-1]/kb[-1]
            bc=cent(rb); lc=cent(lb); bit[sm,float(dmm)]=bc; lowfrac[sm,float(dmm)]=lc/np.maximum(bc,1e-300)
            for k in mm:
                ev=cent(re[k]); mu=cent(rm[k]); res[sm,k[0],k[1],float(dmm)]={'r_bit':bc,'r_event':ev,'r_multi':mu,'q_M':mu/np.maximum(ev,1e-300),'tau_s':1/np.maximum(mu,1e-300),'lowfrac':lowfrac[sm,float(dmm)]}
    return {'E':E,'shields':shields,'pts':pts,'mm':mm,'res':res,'bit':bit,'lowrep':low_conservative_probability(pts)}

def summary(goes,C):
    out=[]
    for (sm,mv,low,d),r in C['res'].items():
        M=r['r_multi']; E=r['r_event']; B=r['r_bit']; i=int(np.nanargmax(M)); med=float(np.nanmedian(M)); p95=q(M,.95); p99=q(M,.99); mx=float(M[i]); hz=float(np.nansum(M*300));
        out.append({'sigma_model':sm,'multiplicity_variant':mv,'low_energy_scenario':low,'shield_mm':d,'valid_5min_intervals':int(np.sum(np.isfinite(M))),'q_M_period_event_weighted':float(np.nansum(M*300)/np.nansum(E*300)),'q_M_time_median':float(np.nanmedian(r['q_M'])),'r_M_background_median_s-1':med,'r_M_p95_s-1':p95,'r_M_p99_s-1':p99,'r_M_peak_s-1':mx,'peak_timestamp_utc':goes.times[i].isoformat(),'tau_D_upper_background_s':1/max(med,1e-300),'tau_D_upper_p95_s':1/max(p95,1e-300),'tau_D_upper_p99_s':1/max(p99,1e-300),'tau_D_upper_peak_s':1/max(mx,1e-300),'expected_upper_multi_events_valid_period':hz,'F_D_upper_valid_period':nhpp_floor(hz),'E_lt_0p9_bit_fraction_period':float(np.nansum(B*r['lowfrac']*300)/np.nansum(B*300)),'bit_rate_background_median_s-1':float(np.nanmedian(B))})
    return out

def horizons(goes,C):
    out=[]
    for (sm,mv,low,d),r in C['res'].items():
        x=r['r_multi']; med=float(np.nanmedian(x)); p95=q(x,.95); p99=q(x,.99)
        for lab,sec in HORIZONS:
            for reg,rate in [('background_median_constant',med),('p95_constant',p95),('p99_constant',p99)]:
                h=rate*sec; out.append({'sigma_model':sm,'multiplicity_variant':mv,'low_energy_scenario':low,'shield_mm':d,'regime':reg,'horizon':lab,'duration_s':sec,'hazard_upper':h,'F_D_upper':nhpp_floor(h),'window_start_utc':'','window_end_utc':''})
            h,i=max_contiguous_hazard(x,sec//300); en=None if i is None else i+sec//300-1
            out.append({'sigma_model':sm,'multiplicity_variant':mv,'low_energy_scenario':low,'shield_mm':d,'regime':'max_actual_contiguous_window','horizon':lab,'duration_s':sec,'hazard_upper':h,'F_D_upper':nhpp_floor(h) if np.isfinite(h) else np.nan,'window_start_utc':'' if i is None else goes.times[i].isoformat(),'window_end_utc':'' if en is None else goes.times[en].isoformat()})
        h=float(np.nansum(x*300)); out.append({'sigma_model':sm,'multiplicity_variant':mv,'low_energy_scenario':low,'shield_mm':d,'regime':'full_valid_Jan_Feb_exposure','horizon':'Jan-Feb-valid','duration_s':int(np.sum(np.isfinite(x))*300),'hazard_upper':h,'F_D_upper':nhpp_floor(h),'window_start_utc':goes.times[0].isoformat(),'window_end_utc':goes.times[-1].isoformat()})
    return out

def sens(S):
    by={(r['sigma_model'],r['multiplicity_variant'],r['low_energy_scenario'],float(r['shield_mm'])):r for r in S}
    def diffs(kind):
        v=[]
        for sm in SIGMA_MODELS:
          for d in SHIELDS_MM:
            for met in ['q_M_period_event_weighted','r_M_background_median_s-1','r_M_p99_s-1','r_M_peak_s-1']:
              if kind=='false': a=by[sm,'nominal_logE_linear','low_energy_conservative',d]; b=by[sm,'false_mcu_aware_logE_linear','low_energy_conservative',d]
              elif kind=='raw': a=by[sm,'nominal_logE_linear','low_energy_conservative',d]; b=by[sm,'raw_nearest_observed','low_energy_conservative',d]
              else: continue
              if float(a[met])>0:v.append(float(b[met])/float(a[met])-1)
        return {'min_relative':min(v),'max_relative':max(v),'max_abs_relative':max(abs(x) for x in v)}
    sv=[]; lv=[]
    for mv in MULTIPLICITY_VARIANTS:
      for d in SHIELDS_MM:
       for met in ['r_M_background_median_s-1','r_M_p99_s-1','r_M_peak_s-1']:
        a=by['main_loglog',mv,'low_energy_conservative',d]; b=by['published_rpp_fluka_digitized',mv,'low_energy_conservative',d]; sv.append(float(b[met])/float(a[met])-1)
    for sm in SIGMA_MODELS:
      for mv in MULTIPLICITY_VARIANTS:
       for d in SHIELDS_MM:
        for met in ['r_M_background_median_s-1','r_M_p99_s-1','r_M_peak_s-1']:
         a=by[sm,mv,'K1_only',d]; b=by[sm,mv,'low_energy_conservative',d]
         if float(a[met])>0: lv.append(float(b[met])/float(a[met])-1)
    R=lambda v:{'min_relative':min(v),'max_relative':max(v),'max_abs_relative':max(abs(x) for x in v)}
    return {'false_mcu_aware_vs_nominal':diffs('false'),'raw_nearest_vs_nominal':diffs('raw'),'published_sigma_vs_main':R(sv),'low_conservative_vs_K1_only':R(lv)}

def classify(H):
    x=[r for r in H if r['multiplicity_variant']=='nominal_logE_linear' and r['low_energy_scenario']=='low_energy_conservative' and r['regime']=='max_actual_contiguous_window']; mh=max(float(r['hazard_upper']) for r in x if np.isfinite(float(r['hazard_upper'])))
    if mh>=1: return 'B',{'max_nominal_actual_window_hazard':mh,'natural_relevance_scale':'hazard>=1 => F_D_upper>=0.632','reason':'At least one requested actual reporting window has upper NHPP hazard >=1; direct risk cannot be dismissed without W/geometry.'}
    return 'C',{'max_nominal_actual_window_hazard':mh,'reason':'No order-one upper hazard, but no accepted future F_A threshold is available to prove irrelevance.'}

def model_rows(C):
    rows=[]
    for (mv,low),(p,k) in C['mm'].items():
      for e,pp,kk in zip(C['E'],p,k): rows.append({'energy_mev':f'{e:.9g}','multiplicity_variant':mv,'low_energy_scenario':low,'p_K_ge_2':f'{pp:.12g}','Kbar':f'{kk:.12g}','energy_zone':'below_0p9' if e<.9 else ('above_186_hold' if e>186 else 'measured_support_interpolated'),'low_conservative_representative_p':f"{C['lowrep']:.12g}"})
    return rows

def time_series(goes,C,path):
    fields=['timestamp_utc','valid_pair','multiplicity_variant','low_energy_scenario']; keys=[]
    for sm in SIGMA_MODELS:
      for d in C['shields']:
        tag=('main' if sm=='main_loglog' else 'phys')+f'_d{d:g}'.replace('.','p'); keys.append((sm,float(d),tag)); fields += [tag+'_'+x for x in ['r_bit_s-1','r_event_reconstructed_s-1','r_M_reconstructed_s-1','q_M','tau_D_upper_s','E_lt_0p9_bit_fraction']]
    with Path(path).open('w',newline='',encoding='utf-8') as f:
      w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
      for i,t in enumerate(goes.times):
        row={'timestamp_utc':t.isoformat(),'valid_pair':int(goes.valid[i,0] and goes.valid[i,1]),'multiplicity_variant':'nominal_logE_linear','low_energy_scenario':'low_energy_conservative'}
        for sm,d,tag in keys:
          r=C['res'][sm,'nominal_logE_linear','low_energy_conservative',d]
          for suf,key in [('r_bit_s-1','r_bit'),('r_event_reconstructed_s-1','r_event'),('r_M_reconstructed_s-1','r_multi'),('q_M','q_M'),('tau_D_upper_s','tau_s'),('E_lt_0p9_bit_fraction','lowfrac')]:
            v=r[key][i];row[tag+'_'+suf]='' if not np.isfinite(v) else f'{v:.10e}'
        w.writerow(row)

def report(S,H,V,code,D,Se,C):
    by={(r['sigma_model'],r['multiplicity_variant'],r['low_energy_scenario'],float(r['shield_mm'])):r for r in S}; lines=['# '+TASK_ID,'','This is a pre-W conservative kill test. `K>=2` is not an ECC failure statement; the only retained inequality is `p_D(E,W) <= P(K>=2|E)`.','',f"For E<0.9 MeV the conservative representative scenario uses P(K>=2)={C['lowrep']:.6g}, the maximum raw observed value over 0.9-3 MeV; this is not a confidence bound.",'','## Nominal results','','|sigma|Al mm|q_M period|r_M median s^-1|r_M p99 s^-1|r_M peak s^-1|tau background|tau peak|E<0.9 bit fraction|peak|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for sm in SIGMA_MODELS:
      for d in SHIELDS_MM:
        r=by[sm,'nominal_logE_linear','low_energy_conservative',d];lines.append(f"|{sm}|{d:g}|{r['q_M_period_event_weighted']:.4%}|{r['r_M_background_median_s-1']:.4e}|{r['r_M_p99_s-1']:.4e}|{r['r_M_peak_s-1']:.4e}|{r['tau_D_upper_background_s']:.4g}s|{r['tau_D_upper_peak_s']:.4g}s|{r['E_lt_0p9_bit_fraction_period']:.3%}|{r['peak_timestamp_utc']}|")
    hb={(r['sigma_model'],float(r['shield_mm']),r['horizon']):r for r in H if r['multiplicity_variant']=='nominal_logE_linear' and r['low_energy_scenario']=='low_energy_conservative' and r['regime']=='max_actual_contiguous_window'}
    lines += ['','## Maximum actual-window F_D^upper','','|sigma|Al mm|5min|1h|24h|7d|','|---|---:|---:|---:|---:|---:|']
    for sm in SIGMA_MODELS:
      for d in SHIELDS_MM:
        v=[float(hb[sm,d,h]['F_D_upper']) for h in ['5min','1h','24h','7d']]; lines.append(f'|{sm}|{d:g}|{v[0]:.4%}|{v[1]:.4%}|{v[2]:.4%}|{v[3]:.4%}|')
    lines += ['','## Sensitivity','',f'False-MCU: `{json.dumps(Se["false_mcu_aware_vs_nominal"])}`',f'Raw observed interpolation: `{json.dumps(Se["raw_nearest_vs_nominal"])}`',f'Sigma model: `{json.dumps(Se["published_sigma_vs_mail"])}`',f'Low-energy multiplicity: `{json.dumps(Se["low_conservative_vs_K1_only"])}`','','## Answers','','1. `q_M` is spectrum-weighted under the energy integral and is reconstructed, not a measured sigma_k.','2. Absolute `r_M(t,d)` is stored in `weighted_parent_event_rate.csv` for the nominal conservative branch.','3. `tau_D^upper=1/r_M` is reported for background, p95, p99 and peak.','4. NHPP `F_D^upper` is swept over 5 min, 1 h, 6 h, 24 h, 7 d, 30 d and the valid Jan-Feb exposure.','5. Geometry/W/M1 is necessary if disposition B, because only W can reduce `P(K>=2|E)` to the true direct probability.','','## Validation','',f"Task-2 bit-rate reconstruction max rel: `{V['main_bit_rate_reconstruction_max_rel']:.3e}`",f"Multiplicity invariants: `{V['multiplicity_invariants_pass']}`",f"Nonnegative rates: `{V['nonnegative_rates_pass']}`",'',f'## Disposition: **{code}**','',D['reason'],'','No ECC, F_A or T_scrub calculation was performed.']
    return '\n'.join(lines)+'\n'

def run(a):
    a.out.mkdir(parents=True,exist_ok=True); m=mods(); goes=m['load_directory'](a.goes_dir); C=calc(goes,a); S=summary(goes,C); H=horizons(goes,C); Se=sens(S)
    frozen={}
    with a.task2_rate_csv.open(encoding='utf-8',newline='') as f:
      for r in csv.DictReader(f): frozen[r['timestamp_utc']]=r
    rr=[]
    for d in C['shields']:
      tag=f'd{float(d):g}'.replace('.','p')+'_lambda_central_s-1'; arr=C['bit']['main_loglog',float(d)]
      for i,t in enumerate(goes.times):
        if np.isfinite(arr[i]) and frozen[t.isoformat()].get(tag,''):
          y=float(frozen[t.isoformat()][tag]);rr.append(abs(arr[i]-y)/max(abs(y),1e-300))
    V={'task_id':TASK_ID,'starting_commit':STARTING_COMMIT,'goes_radar_pipeline_changed':False,'main_bit_rate_reconstruction_max_rel':max(rr),'multiplicity_invariants_pass':all(np.all((p>=0)&(p<=1)&(k>=1)&(k+1e-12>=1+p)) for p,k in C['mm'].values()),'nonnegative_rates_pass':all(np.nanmin(r['r_multi'])>=0 and np.nanmin(r['r_event'])>=0 for r in C['res'].values()),'controlled_goes_valid_intervals':int(np.sum(goes.valid[:,0]&goes.valid[:,1]))}
    if not(V['main_bit_rate_reconstruction_max_rel']<2e-6 and V['multiplicity_invariants_pass'] and V['nonnegative_rates_pass']): raise SystemExit(V)
    code,D=classify(H); V['disposition']=code;V['decision_diagnostics']=D;V['sensitivity_diagnostics']=Se
    write(a.out/'multiplicity_model.csv',model_rows(C));time_series(goes,C,a.out/'weighted_parent_event_rate.csv');write(a.out/'direct_floor_summary.csv',S);write(a.out/'direct_floor_horizon_sweep.csv',H);(a.out/'validation.json').write_text(json.dumps(V,indent=2)+'\n');(a.out/'REPORT.md').write_text(report(S,H,V,code,D,Se,C))
    print(json.dumps({'disposition':code,'decision':D,'sensitivity':Se},indent=2))

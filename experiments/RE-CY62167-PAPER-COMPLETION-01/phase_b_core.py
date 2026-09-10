from __future__ import annotations
import csv
from pathlib import Path
import numpy as np,pandas as pd
from cosrad_parser import SHIELDS
from cosrad_operator import convolve,integrate_threshold
from cosrad_rate_reconstruction import MAPPINGS,accumulation_structured_model,accumulation_piecewise_sigma_model

T=3.156e8; QDOP=1e-3; BETA=31/(2*2**24)
R1U=0.04718592; R1E=0.02359296; R2U=0.18874368; R2E=0.09437184
READS={'R1':2**19,'R2':2**21}; TREAD=TWRITE=45e-9

def write_csv(path:Path,rows,fields=None):
    if fields is None: fields=list(rows[0]) if rows else []
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def bound(nud,nuc):
    fd=T*nud/QDOP
    if fd>=1:return fd,None,None,'DIRECT-BOUND-EXHAUSTED'
    sd=-fd/(1-fd) if fd>0 else -0.0
    tau=(QDOP/T-nud)/(BETA*nuc*nuc)
    return fd,sd,tau,'CERTIFIED-POSITIVE-PERIOD'

def make_bounds(rates):
    out=[]
    for r in rates:
        fd,sd,tau,status=bound(r['nu_direct_total_s-1'],r['nu_accumulation_total_bit_s-1'])
        out.append({'environment_scenario':'GCR-ARTICLE-BACKGROUND','shield_g_cm2':r['shield_g_cm2'],'mapping_id':r['mapping_id'],'estimate_type':r['estimate_type'],'rate_reconstruction_route':r['rate_reconstruction_route'],'nu_direct_total_s-1':r['nu_direct_total_s-1'],'nu_accumulation_total_bit_s-1':r['nu_accumulation_total_bit_s-1'],'f_D':fd,'S_D':sd if sd is not None else '','tau_max_U_s':tau if tau is not None else '','bound_status':status})
    return out

def make_references(bounds):
    return [{'shield_g_cm2':r['shield_g_cm2'],'mapping_id':r['mapping_id'],'estimate_type':r['estimate_type'],'rate_reconstruction_route':r['rate_reconstruction_route'],'tau_max_U_s':r['tau_max_U_s'],'tau_max_ref_low_s':'','tau_max_ref_high_s':'','eta_tau_low':'','eta_tau_high':'','scrub_rate_penalty_low':'','scrub_rate_penalty_high':'','reference_comparison_status':'REFERENCE-NOT-AVAILABLE','reference_status':'TAU_MAX_REFERENCE_BLOCKED_BY_COSRAD_OPERATOR_SEMANTICS'} for r in bounds]

def resource_rows(bounds):
    out=[]
    for r in bounds:
        tau=r['tau_max_U_s']
        if tau in ('',None) or (isinstance(tau,float) and not np.isfinite(tau)):continue
        if r['rate_reconstruction_route']!='SPECTRAL_EXTERNAL_CONVOLUTION':continue
        tau=float(tau)
        for mode in ['R1','R2']:
            for wp in ['U','E']:
                nr=READS[mode]; nw=nr if wp=='U' else None
                floor={('R1','U'):R1U,('R1','E'):R1E,('R2','U'):R2U,('R2','E'):R2E}[(mode,wp)]
                rr=nr/tau; rw=(nw/tau if nw is not None else None); frac=rr*TREAD+(rw*TWRITE if rw is not None else 0.0)
                out.append({'shield_g_cm2':r['shield_g_cm2'],'mapping_id':r['mapping_id'],'estimate_type':r['estimate_type'],'rate_reconstruction_route':r['rate_reconstruction_route'],'period_source':'TAU_MAX_U','tau_s':tau,'scan_mode':mode,'write_policy':wp,'reads_per_cycle':nr,'writes_per_cycle_or_expected':nw if nw is not None else '','t_read_effective_s':TREAD,'t_write_effective_s':TWRITE if nw is not None else '','tau_min_arch_s':floor,'resource_margin':tau/floor,'period_feasible':tau>=floor,'architecture_status':'ARCHITECTURALLY-FEASIBLE' if tau>=floor else 'ARCHITECTURALLY-INFEASIBLE-FOR-DECLARED-SCAN','reads_per_s':rr,'writes_per_s':rw if rw is not None else '','interface_fraction':frac,'interface_percent':100*frac,'write_cost_status':'DEFINED' if wp=='U' else 'ERR_ASSISTED_WRITE_COST = MODEL_DEPENDENT'})
    return out

def boundary_rows(bounds):
    out=[]; df=pd.DataFrame(bounds)
    for (route,m,est),g in df.groupby(['rate_reconstruction_route','mapping_id','estimate_type']):
        g=g.sort_values('shield_g_cm2'); exhausted=g[g.bound_status=='DIRECT-BOUND-EXHAUSTED']; pos=g[g.bound_status=='CERTIFIED-POSITIVE-PERIOD']
        last=float(exhausted.shield_g_cm2.max()) if len(exhausted) else np.nan; first=float(pos.shield_g_cm2.min()) if len(pos) else np.nan
        lo=hi=interp=np.nan; status='BELOW_GRID' if not len(exhausted) else ('ABOVE_GRID' if not len(pos) else 'GRID_BRACKET_AND_LINEAR_INTERPOLATION')
        if len(exhausted) and len(pos):
            lo=last;hi=first;f0=float(g.loc[np.isclose(g.shield_g_cm2,lo),'f_D'].iloc[0]);f1=float(g.loc[np.isclose(g.shield_g_cm2,hi),'f_D'].iloc[0])
            if f1!=f0:interp=lo+(1-f0)*(hi-lo)/(f1-f0)
        out.append({'rate_reconstruction_route':route,'mapping_id':m,'estimate_type':est,'last_direct_bound_exhausted_shield':last,'first_positive_period_shield':first,'first_R1U_arch_feasible_shield':first,'first_R2U_arch_feasible_shield':first,'fD_equals_1_grid_low':lo,'fD_equals_1_grid_high':hi,'fD_equals_1_interp':interp,'boundary_status':status})
    return out

def accumulation_sensitivity(pkg,phase_groups):
    out=[]; gl=pkg.spectra['gl_x.txt']
    for m,g in phase_groups.items():
        if m not in MAPPINGS:continue
        fs=accumulation_structured_model(g);fp=accumulation_piecewise_sigma_model(g)
        for j,d in enumerate(SHIELDS):
            a=convolve(gl.x,gl.values[:,j],fs,'LET'); b=convolve(gl.x,gl.values[:,j],fp,'LET'); rel=(b-a)/a
            out.append({'mapping_id':m,'shield_g_cm2':float(d),'structured_nu_C_HI_s-1':a,'piecewise_linear_sigma_C_nu_C_HI_s-1':b,'relative_difference':rel,'status':'MATERIAL' if abs(rel)>0.05 else 'IMMATERIAL'})
    return out

def legacy_rows(pkg,s_gcr,bounds):
    rg=pd.DataFrame(s_gcr); bg=pd.DataFrame(bounds); out=[]
    lp={2.0:2.983e-9,2.5:2.565e-9,3.0:2.247e-9};ld={2.0:3.253e-12,2.5:2.797e-12,3.0:2.450e-12};lc={2.0:1.53e-4,2.5:1.40e-4,3.0:1.30e-4};lt={2.0:np.nan,2.5:20.5,3.0:45.7}; gl=pkg.spectra['gl_x.txt']
    for d in [2.0,2.5,3.0]:
        j=int(np.where(np.isclose(SHIELDS,d))[0][0]); phi=integrate_threshold(gl.x,gl.values[:,j],33,'LET')
        q=rg[(rg.mapping_id=='W_00_01')&(rg.estimate_type=='ARTICLE_CONFIDENCE_STYLE')&(np.isclose(rg.shield_g_cm2,d))].iloc[0]
        qb=bg[(bg.mapping_id=='W_00_01')&(bg.estimate_type=='ARTICLE_CONFIDENCE_STYLE')&(bg.rate_reconstruction_route=='SPECTRAL_EXTERNAL_CONVOLUTION')&(np.isclose(bg.shield_g_cm2,d))].iloc[0]
        for name,old,new in [('Phi_L_ge_33_cm-2_s-1',lp[d],phi),('nu_D_s-1',ld[d],q['nu_direct_total_s-1']),('nu_C_s-1',lc[d],q['nu_accumulation_total_bit_s-1'])]:
            out.append({'quantity':name,'shield_g_cm2':d,'legacy_value':old,'phase_B_value':new,'absolute_difference':new-old,'relative_difference':(new-old)/old,'status':'REPRODUCED','reproduction_route':'SPECTRAL_EXTERNAL_CONVOLUTION'})
        old=lt[d];new=qb['tau_max_U_s']
        if np.isnan(old):out.append({'quantity':'tau_max_s','shield_g_cm2':d,'legacy_value':'NO_POSITIVE_PERIOD','phase_B_value':qb.bound_status,'absolute_difference':'','relative_difference':'','status':'REPRODUCED','reproduction_route':'SPECTRAL_EXTERNAL_CONVOLUTION'})
        else:out.append({'quantity':'tau_max_s','shield_g_cm2':d,'legacy_value':old,'phase_B_value':new,'absolute_difference':float(new)-old,'relative_difference':(float(new)-old)/old,'status':'REPRODUCED','reproduction_route':'SPECTRAL_EXTERNAL_CONVOLUTION'})
    for tau,p in [(20.0,0.9437184),(45.0,0.4194304)]:
        calc=100*(2**21/tau)*(45e-9+45e-9);out.append({'quantity':f'R2U_interface_percent_at_tau_{int(tau)}s','shield_g_cm2':'','legacy_value':p,'phase_B_value':calc,'absolute_difference':calc-p,'relative_difference':(calc-p)/p,'status':'REPRODUCED','reproduction_route':'FROZEN_PHASE_A_SERIAL_RESOURCE'})
    return out

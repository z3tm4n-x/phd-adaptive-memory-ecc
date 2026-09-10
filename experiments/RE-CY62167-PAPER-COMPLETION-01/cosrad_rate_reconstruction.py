from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import nnls
from cosrad_parser import SHIELDS,THRESHOLDS,Package
from cosrad_operator import convolve,kernel_g,integrate_threshold

N_BITS=2**24
SIGMA_SAT=2.6e-7; WEIBULL_L0=0.15; WEIBULL_W=70.0; WEIBULL_H=1.2
ACS_SIGMA=1.0904848941775637e-3
PROTON_E0_MEV=10.0
PROTON_BIT_SIGMA_CM2=8e-14
PROTON_GEOMETRIC_FACTOR=0.5
PROTON_ASSUMPTION_STATUS='DECLARED PROTON COMPARATOR ASSUMPTION'
MAPPINGS=['W_01_02','W_00_01','W_00_11']

def sigma_bit(L):
    a=np.asarray(L,float); out=np.zeros_like(a); m=a>WEIBULL_L0
    out[m]=SIGMA_SAT*(1.0-np.exp(-((a[m]-WEIBULL_L0)/WEIBULL_W)**WEIBULL_H)); return out

def load_phase_a(path:Path|str):
    df=pd.read_csv(path)
    return {m:g.sort_values('LET_MeV_cm2_mg').reset_index(drop=True) for m,g in df.groupby('mapping_id')}

def direct_point_model(group):
    if int(group['N_direct_events'].sum())==0:
        return lambda L: np.zeros_like(np.asarray(L,float))
    g=group.set_index('LET_MeV_cm2_mg')
    y42=float(g.loc[42.0,'sigma_direct_point_cm2']); y57=float(g.loc[57.0,'sigma_direct_point_cm2'])
    return lambda L: np.interp(np.asarray(L,float),[33.,42.,57.],[0.,y42,y57],left=0.,right=y57)

def direct_legacy_step_model(group):
    y57=float(group.loc[np.isclose(group.LET_MeV_cm2_mg,57.0),'sigma_direct_point_cm2'].iloc[0])
    return lambda L: np.where(np.asarray(L,float)>=33.,y57,0.)

def direct_acs_model(L): return np.where(np.asarray(L,float)>=33.,ACS_SIGMA,0.)

def accumulation_structured_model(group):
    L=group.LET_MeV_cm2_mg.to_numpy(float)
    sig=group.sigma_accumulation_point_cm2.to_numpy(float)
    r=sig/(N_BITS*sigma_bit(L))
    def f(q):
        a=np.asarray(q,float); rr=np.interp(a,L,r,left=r[0],right=r[-1]); return N_BITS*sigma_bit(a)*rr
    return f

def accumulation_piecewise_sigma_model(group):
    L=group.LET_MeV_cm2_mg.to_numpy(float); y=group.sigma_accumulation_point_cm2.to_numpy(float)
    return lambda q: np.interp(np.asarray(q,float),L,y,left=y[0],right=y[-1])

def event_sigma_model(group):
    L=group.LET_MeV_cm2_mg.to_numpy(float); y=group.sigma_event_cm2.to_numpy(float)
    return lambda q: np.interp(np.asarray(q,float),L,y,left=y[0],right=y[-1])

def proton_acc_rate(spectrum,j):
    sig_total=N_BITS*PROTON_BIT_SIGMA_CM2*PROTON_GEOMETRIC_FACTOR
    return convolve(spectrum.x,spectrum.values[:,j],lambda E:np.where(E>=PROTON_E0_MEV,sig_total,0.0),'E')

def spectral_rows(pkg:Package,phase_groups,environment='GCR'):
    let_spec=pkg.spectra['gl_x.txt' if environment=='GCR' else 'sl_x.txt']
    p_spec=pkg.spectra['gp_x.txt' if environment=='GCR' else 'sp_x.txt']
    rows=[]
    for m in MAPPINGS:
        g=phase_groups[m]; acc=accumulation_structured_model(g); pdir=direct_point_model(g)
        for est in (['POINT'] if m=='W_01_02' else ['POINT','ARTICLE_CONFIDENCE_STYLE']):
            dmodel=pdir if est=='POINT' else direct_acs_model
            dname='POINT-DATA-INTERPOLATED' if est=='POINT' and m!='W_01_02' else ('REGISTERED-CLUSTER-ZERO-POINT' if est=='POINT' else 'ARTICLE-CONFIDENCE-STYLE-STEP')
            for j,d in enumerate(SHIELDS):
                nd_hi=(ACS_SIGMA*integrate_threshold(let_spec.x,let_spec.values[:,j],33.0,'LET') if est=='ARTICLE_CONFIDENCE_STYLE' else convolve(let_spec.x,let_spec.values[:,j],dmodel,'LET'))
                nc_hi=convolve(let_spec.x,let_spec.values[:,j],acc,'LET')
                nc_p=proton_acc_rate(p_spec,j)
                rows.append({'environment_scenario':'GCR_ONLY' if environment=='GCR' else 'SEP_PEAK_ONLY','shield_g_cm2':float(d),'mapping_id':m,'estimate_type':est,'direct_model':dname,'nu_direct_HI_s-1':nd_hi,'nu_direct_proton_registered_s-1':0.0,'nu_direct_total_s-1':nd_hi,'nu_accumulation_HI_bit_s-1':nc_hi,'nu_accumulation_proton_bit_s-1':nc_p,'nu_accumulation_total_bit_s-1':nc_hi+nc_p,'rate_reconstruction_route':'SPECTRAL_EXTERNAL_CONVOLUTION'})
    return rows

def _basis_grid(): return np.geomspace(WEIBULL_L0,900.0,3000)
def _basis_matrix(grid,thresholds=THRESHOLDS): return np.column_stack([kernel_g(grid,t) for t in thresholds])
def _basis_response_vector(pkg,environment,j): return np.array([pkg.responses[(environment,float(t))].ion_rate[j] for t in THRESHOLDS],float)

def basis_models(phase_groups):
    grid=_basis_grid(); B=_basis_matrix(grid); cond=float(np.linalg.cond(B)); specs={}; diag=[]; approx=[]
    for m in MAPPINGS:
        g=phase_groups[m]
        target=accumulation_structured_model(g)(grid); peak=max(float(target.max()),1e-300)
        coef=np.linalg.lstsq(B,target,rcond=None)[0]; pred=B@coef
        specs[(m,'ACCUMULATION','POINT_RESIDUAL')]=coef
        err=float(np.max(np.abs(pred-target))/peak); rmse=float(np.sqrt(np.mean((pred-target)**2))/peak)
        approx.append({'mapping_id':m,'target_kind':'ACCUMULATION','estimate_type':'POINT_RESIDUAL','basis_method':'SIGNED-LEAST-SQUARES','max_abs_fraction_of_peak':err,'rmse_fraction_of_peak':rmse,'prediction_min_fraction_of_peak':float(pred.min()/peak),'coefficient_l1_fraction_of_peak':float(np.sum(np.abs(coef))/peak),'approximation_status':'APPROXIMATION-SMALL' if err<0.01 else 'APPROXIMATION-MATERIAL','coefficients_by_threshold':json.dumps({str(t):float(c) for t,c in zip(THRESHOLDS,coef)},sort_keys=True)})
        diag.append({'mapping_id':m,'target_kind':'ACCUMULATION','estimate_type':'POINT_RESIDUAL','method':'SIGNED-LEAST-SQUARES-DIAGNOSTIC','max_abs_fraction_of_peak':err,'rmse_fraction_of_peak':rmse,'prediction_min_fraction_of_peak':float(pred.min()/peak),'below33_max_abs_fraction_of_peak':float(np.max(np.abs((pred-target)[grid<33]))/peak),'coefficient_l1_fraction_of_peak':float(np.sum(np.abs(coef))/peak),'coefficient_max_fraction_of_peak':float(np.max(np.abs(coef))/peak),'basis_matrix_condition_number':cond,'max_GCR_response_cancellation_factor':np.nan,'operational_use':'ACCEPTED_FOR_ACCUMULATION_BASIS_ROUTE' if err<0.01 else 'DIAGNOSTIC_ONLY'})
        for est in (['POINT'] if m=='W_01_02' else ['POINT','ARTICLE_CONFIDENCE_STYLE']):
            target=(direct_point_model(g)(grid) if est=='POINT' else direct_acs_model(grid)); peak=float(target.max()) if np.max(target)>0 else 1.0
            if np.max(target)==0:
                coef=np.zeros(len(THRESHOLDS)); pred=np.zeros_like(grid); method='EXACT_ZERO_REGISTERED_CLUSTER_POINT'
            else:
                use=np.where(THRESHOLDS>=33)[0]; csmall,_=nnls(B[:,use],target); coef=np.zeros(len(THRESHOLDS)); coef[use]=csmall; pred=B@coef; method='SUPPORT-PRESERVING-NNLS; DIRECT BASIS THRESHOLDS >=33 ONLY'
            specs[(m,'DIRECT',est)]=coef
            err=float(np.max(np.abs(pred-target))/peak) if peak else 0.; rmse=float(np.sqrt(np.mean((pred-target)**2))/peak) if peak else 0.
            approx.append({'mapping_id':m,'target_kind':'DIRECT','estimate_type':est,'basis_method':method,'max_abs_fraction_of_peak':err,'rmse_fraction_of_peak':rmse,'prediction_min_fraction_of_peak':(float(pred.min()/peak) if np.max(target)>0 else np.nan),'coefficient_l1_fraction_of_peak':(float(np.sum(np.abs(coef))/peak) if np.max(target)>0 else np.nan),'approximation_status':'APPROXIMATION-SMALL' if err<0.01 else ('EXACT-ZERO' if np.max(target)==0 else 'BASIS-TARGET-APPROXIMATION-INADEQUATE'),'coefficients_by_threshold':json.dumps({str(t):float(c) for t,c in zip(THRESHOLDS,coef) if abs(c)>0},sort_keys=True)})
            if np.max(target)>0:
                cs=np.linalg.lstsq(B,target,rcond=None)[0]; ps=B@cs
                err2=float(np.max(np.abs(ps-target))/peak); rm2=float(np.sqrt(np.mean((ps-target)**2))/peak)
                diag.append({'mapping_id':m,'target_kind':'DIRECT','estimate_type':est,'method':'SIGNED-LEAST-SQUARES-DIAGNOSTIC','max_abs_fraction_of_peak':err2,'rmse_fraction_of_peak':rm2,'prediction_min_fraction_of_peak':float(ps.min()/peak),'below33_max_abs_fraction_of_peak':float(np.max(np.abs((ps-target)[grid<33]))/peak),'coefficient_l1_fraction_of_peak':float(np.sum(np.abs(cs))/peak),'coefficient_max_fraction_of_peak':float(np.max(np.abs(cs))/peak),'basis_matrix_condition_number':cond,'max_GCR_response_cancellation_factor':np.nan,'operational_use':'DIAGNOSTIC_ONLY; DIRECT_SIGNED_LS_REJECTED_FOR_RATE_RECONSTRUCTION'})
    return specs,approx,diag

def basis_rows(pkg,phase_groups,environment='GCR'):
    specs,approx,diag=basis_models(phase_groups)
    rows=[]
    for m in MAPPINGS:
        for est in (['POINT'] if m=='W_01_02' else ['POINT','ARTICLE_CONFIDENCE_STYLE']):
            dc=specs[(m,'DIRECT',est)]; ac=specs[(m,'ACCUMULATION','POINT_RESIDUAL')]
            for j,d in enumerate(SHIELDS):
                R=_basis_response_vector(pkg,environment,j)
                nd=float(dc@R); nc_hi=float(ac@R)
                nd=max(nd,0.0); nc_hi=max(nc_hi,0.0)
                p_spec=pkg.spectra['gp_x.txt' if environment=='GCR' else 'sp_x.txt']; nc_p=proton_acc_rate(p_spec,j)
                rows.append({'environment_scenario':'GCR_ONLY' if environment=='GCR' else 'SEP_PEAK_ONLY','shield_g_cm2':float(d),'mapping_id':m,'estimate_type':est,'direct_model':'COSRAD-BASIS-RECONSTRUCTED','nu_direct_HI_s-1':nd,'nu_direct_proton_registered_s-1':0.0,'nu_direct_total_s-1':nd,'nu_accumulation_HI_bit_s-1':nc_hi,'nu_accumulation_proton_bit_s-1':nc_p,'nu_accumulation_total_bit_s-1':nc_hi+nc_p,'rate_reconstruction_route':'BASIS_RESPONSE_RECONSTRUCTION_STABILITY_GATED'})
    for rec in diag:
        m=rec['mapping_id']; kind=rec['target_kind']; est=rec['estimate_type']
        if kind=='ACCUMULATION': coef=specs[(m,'ACCUMULATION','POINT_RESIDUAL')]
        else:
            grid=_basis_grid(); B=_basis_matrix(grid); g=phase_groups[m]
            target=direct_point_model(g)(grid) if est=='POINT' else direct_acs_model(grid)
            coef=np.linalg.lstsq(B,target,rcond=None)[0]
        fac=[]
        for j in range(9):
            R=_basis_response_vector(pkg,'GCR',j); den=abs(float(coef@R)); num=float(np.sum(np.abs(coef*R))); fac.append(num/max(den,1e-300))
        rec['max_GCR_response_cancellation_factor']=max(fac)
    return rows,approx,diag

from __future__ import annotations
import numpy as np
from cosrad_parser import SHIELDS,Package
from cosrad_operator import dense_spectrum
from cosrad_rate_reconstruction import event_sigma_model,direct_point_model

SUPPORT=np.array([5.2,15.,17.,22.,27.,29.,33.,42.,57.])

def _barycentric_weights(L):
    L=np.asarray(L,float); W=np.zeros((len(L),len(SUPPORT)))
    for k,x in enumerate(L):
        if x<=SUPPORT[0]:W[k,0]=1;continue
        if x>=SUPPORT[-1]:W[k,-1]=1;continue
        hi=int(np.searchsorted(SUPPORT,x)); lo=hi-1
        a=(x-SUPPORT[lo])/(SUPPORT[hi]-SUPPORT[lo]); W[k,lo]=1-a;W[k,hi]=a
    return W

def event_weights(pkg:Package,phase_groups,environment='GCR'):
    spec=pkg.spectra['gl_x.txt' if environment=='GCR' else 'sl_x.txt']; rows=[]
    for m,g in phase_groups.items():
        if m not in ('W_01_02','W_00_01','W_00_11'):continue
        evt=event_sigma_model(g)
        frac_direct=(g.N_direct_events.to_numpy(float)/g.N_events.to_numpy(float))
        for j,d in enumerate(SHIELDS):
            L,phi=dense_spectrum(spec.x,spec.values[:,j],'LET',n=20000)
            rate_density=phi*evt(L); W=_barycentric_weights(L)
            lambdas=np.array([np.trapezoid(rate_density*W[:,k],L) for k in range(len(SUPPORT))])
            total=float(lambdas.sum())
            for k,s in enumerate(SUPPORT):
                ld=float(lambdas[k]*frac_direct[k]); lr=float(lambdas[k]-ld)
                rows.append({'environment_scenario':'GCR_ONLY' if environment=='GCR' else 'SEP_PEAK_ONLY','shield_g_cm2':float(d),'mapping_id':m,'LET_support_MeV_cm2_mg':float(s),'lambda_registered_event_s-1':float(lambdas[k]),'lambda_direct_registered_s-1':ld,'lambda_residual_event_s-1':lr,'weight_fraction':float(lambdas[k]/total) if total else 0.0,'event_rate_total_s-1':total,'status':'DIAGNOSTIC_ONLY; TAU_MAX_REFERENCE_BLOCKED_BY_COSRAD_OPERATOR_SEMANTICS'})
    return rows

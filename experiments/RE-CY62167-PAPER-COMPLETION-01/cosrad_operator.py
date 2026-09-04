from __future__ import annotations
import numpy as np
from cosrad_parser import THRESHOLDS,SHIELDS,Package

DENSE_N=20000

def kernel_g(L,L0):
    a=np.asarray(L,float); out=np.zeros_like(a)
    m=a>=L0; out[m]=np.exp(-10.0*L0/a[m]); return out

def _loglog_interp(x,y,grid):
    x=np.asarray(x,float); y=np.asarray(y,float); grid=np.asarray(grid,float)
    p=x>0; x=x[p]; y=y[p]
    if len(x)<2:return np.zeros_like(grid)
    idx=np.searchsorted(x,grid,side='right')-1; idx=np.clip(idx,0,len(x)-2)
    x0=x[idx];x1=x[idx+1];y0=y[idx];y1=y[idx+1]
    out=np.zeros_like(grid)
    both=(y0>0)&(y1>0)
    if np.any(both):
        a=(np.log(grid[both])-np.log(x0[both]))/(np.log(x1[both])-np.log(x0[both]))
        out[both]=np.exp((1-a)*np.log(y0[both])+a*np.log(y1[both]))
    if np.any(~both):
        a=(grid[~both]-x0[~both])/(x1[~both]-x0[~both])
        out[~both]=(1-a)*y0[~both]+a*y1[~both]
    out[(grid<x.min())|(grid>x.max())]=0.0
    return out

def dense_spectrum(x,phi,unit_kind='LET',n=DENSE_N):
    x=np.asarray(x,float); phi=np.asarray(phi,float)
    if unit_kind=='LET':
        x=x/1000.0; phi=phi*1000.0
    positive_x=x[x>0]
    grid=np.geomspace(positive_x.min(),x.max(),n)
    return grid,_loglog_interp(x,phi,grid)

def convolve(x,phi,target,unit_kind='LET',n=DENSE_N):
    g,p=dense_spectrum(x,phi,unit_kind,n)
    return float(np.trapezoid(p*np.asarray(target(g),float),g))

def integrate_threshold(x,phi,threshold,unit_kind='LET',n=DENSE_N):
    x=np.asarray(x,float); phi=np.asarray(phi,float)
    if unit_kind=='LET':
        x=x/1000.0; phi=phi*1000.0
    lo=max(float(threshold),float(x[x>0].min()))
    if lo>=x.max(): return 0.0
    grid=np.geomspace(lo,float(x.max()),n)
    p=_loglog_interp(x,phi,grid)
    return float(np.trapezoid(p,grid))

def let_unit_invariance(x,phi,target):
    X=np.asarray(x,float); y=np.asarray(phi,float)
    gx=np.geomspace(X[X>0].min(),X.max(),DENSE_N)
    px=_loglog_interp(X,y,gx)
    iX=float(np.trapezoid(px*np.asarray(target(gx/1000.0),float),gx))
    L=X/1000.0; phiL=1000.0*y
    gl=np.geomspace(L[L>0].min(),L.max(),DENSE_N)
    pl=_loglog_interp(L,phiL,gl)
    iL=float(np.trapezoid(pl*np.asarray(target(gl),float),gl))
    rel=0.0 if iX==iL==0 else abs(iX-iL)/max(abs(iX),abs(iL),1e-300)
    return iX,iL,rel

def operator_closure(pkg:Package):
    rows=[]
    for env,specname in [('GCR','gl_x.txt'),('SEP','sl_x.txt')]:
        s=pkg.spectra[specname]
        for t in THRESHOLDS:
            r=pkg.responses[(env,float(t))]
            for j,d in enumerate(SHIELDS):
                spectral=convolve(s.x,s.values[:,j],lambda L,t=t:kernel_g(L,t),'LET')
                cosrad=float(r.ion_rate[j])
                rel=(spectral-cosrad)/cosrad if cosrad!=0 else (0.0 if spectral==0 else np.inf)
                rows.append({'environment':env,'threshold_MeV_cm2_mg':float(t),'shield_g_cm2':float(d),'spectral_integral_ion_s-1':spectral,'cosrad_ion_see_s-1':cosrad,'relative_difference':rel,'absolute_relative_difference':abs(rel),'closure_status':'PASS' if np.isfinite(rel) and abs(rel)<=0.05 else 'SPECTRAL_OPERATOR_NOT_CLOSED'})
    return rows

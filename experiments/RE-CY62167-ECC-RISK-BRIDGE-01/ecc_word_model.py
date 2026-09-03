"""Exact SEC data-word first-passage model for RE-CY62167-ECC-RISK-BRIDGE-01."""
from __future__ import annotations
import math
import numpy as np
from scipy.linalg import expm

N_DATA=32

def transient_generator(n:int=N_DATA)->np.ndarray:
    return np.array([[-float(n),float(n)],[1.0,-float(n)]],float)

def log_clean_survival(mu, n:int=N_DATA):
    """log survival from clean word through integrated per-bit exposure mu.

    Exact for generator Q(mu)=Q0*dmu. Stable eigen-form, no endpoint-occupancy approximation.
    """
    x=np.asarray(mu,float)
    if np.any(x<0): raise ValueError('mu must be nonnegative')
    b=math.sqrt(n); e=np.exp(-2*b*x)
    inner=.5*(1+b)+.5*(1-b)*e
    out=(-n+b)*x+np.log(inner)
    # The closed form cancels O(x) terms; use the exact Taylor series of log S
    # at small exposure to retain the O(x^2) first-passage probability.
    small=x<1e-3
    if np.any(small):
        c2=(-n*n+n)/2
        c3=(n**3-n**2)/3
        c4=-n**4/4+n**3/3-n**2/12
        c5=n**5/5-n**4/3+2*n**3/15
        c6=-n**6/6+n**5/3-17*n**4/90+n**3/45
        xs=x[small] if x.ndim else x
        ys=xs*xs*(c2+xs*(c3+xs*(c4+xs*(c5+xs*c6))))
        if x.ndim: out=np.array(out,copy=True);out[small]=ys
        else: out=ys
    return float(out) if np.ndim(out)==0 else out

def clean_survival(mu,n:int=N_DATA):
    return np.exp(log_clean_survival(mu,n))

def clean_failure(mu,n:int=N_DATA):
    return -np.expm1(log_clean_survival(mu,n))

def pair_failure(mu,n:int=N_DATA):
    x=np.asarray(mu,float);y=(n*(n-1)/2.0)*x*x
    return float(y) if y.ndim==0 else y

def transient_expm(mu,n:int=N_DATA):
    return expm(transient_generator(n)*float(mu))

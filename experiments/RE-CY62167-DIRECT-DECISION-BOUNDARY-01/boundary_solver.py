"""Monotone boundary solvers and exact tau=1 batch evaluator.

The tau=1 evaluator is an algebraic vectorization of the frozen bridge's 16-phase
CYCLIC-SEQUENTIAL scrub calculation.  It does not change the reliability model.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np

@dataclass(frozen=True)
class RootResult:
    theta: float | None
    status: str
    bracket_low: float
    bracket_high: float
    tolerance: float


def bisect_monotone(func, target, lo=0.0, hi=1.0, tol=1e-4, increasing=True):
    """Bracketed bisection for a monotone scalar response."""
    flo, fhi = float(func(lo)), float(func(hi))
    if increasing:
        if flo > target:
            return RootResult(None, "ALWAYS_INFEASIBLE", lo, lo, tol)
        if fhi <= target:
            return RootResult(None, "ALWAYS_FEASIBLE", hi, hi, tol)
    else:
        if flo < target:
            return RootResult(None, "ALWAYS_INFEASIBLE", lo, lo, tol)
        if fhi >= target:
            return RootResult(None, "ALWAYS_FEASIBLE", hi, hi, tol)
    a, b = float(lo), float(hi)
    while b - a > tol:
        m = 0.5 * (a + b); fm = float(func(m))
        if (fm > target) == increasing:
            b = m
        else:
            a = m
    return RootResult(0.5 * (a + b), "FINITE", a, b, tol)


def monotonicity_violations(values, atol=1e-10):
    x = np.asarray(values, float)
    return np.where(np.diff(x) < -float(atol))[0]


def probability_to_hazard(F):
    F = np.asarray(F, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return -np.log1p(-np.clip(F, 0.0, 1.0))


def hazard_to_probability(H):
    return -np.expm1(-np.maximum(np.asarray(H, float), 0.0))


def piecewise_hazard_interpolant(theta, anchor_theta, anchor_probability):
    """Monotone local interpolation used only for action-transition roots.

    Scalar feasibility-loss and 2-D energy boundaries are exact-corrected with the
    frozen tau=1 evaluator; this interpolant is retained for tau>1 action transitions
    and is validated against exact frozen-model representative cases.
    """
    t = float(theta); at = np.asarray(anchor_theta, float); ap = np.asarray(anchor_probability, float)
    if np.any(np.diff(at) <= 0):
        raise ValueError("anchor_theta must increase")
    if t <= at[0]: return float(ap[0])
    if t >= at[-1]: return float(ap[-1])
    j = int(np.searchsorted(at, t) - 1)
    x = (t - at[j]) / (at[j+1] - at[j])
    h = probability_to_hazard(ap[[j,j+1]])
    if not np.isfinite(h[0]):
        return 1.0
    if not np.isfinite(h[1]):
        h[1] = max(float(h[0]) + 50.0, -math.log(1e-12))
    return float(hazard_to_probability(h[0] + x * (h[1]-h[0])))


def tau1_risk_batch(direct_rate, acc_bit_rate, log_clean_survival,
                    n_words=524288, n_data_bits=2**24, bin_seconds=300.0, phases=16):
    """Exact vectorized tau=1 specialization of frozen cyclic-sequential semantics.

    Returns mapping window label -> (F_product, F_dependence_upper, valid_mask), each
    probability array shaped [batch, sliding_window_start].
    """
    dr=np.asarray(direct_rate,float); ac=np.asarray(acc_bit_rate,float)
    if dr.ndim==1: dr=dr[None,:]
    if ac.ndim==1: ac=ac[None,:]
    if dr.shape != ac.shape: raise ValueError("rate arrays must have equal shape")
    K,N=dr.shape; rb=ac/float(n_data_bits)
    rs=np.nan_to_num(rb,nan=0.0); rn=np.concatenate([rs[:,1:],rs[:,-1:]],axis=1)
    phase_grid=(np.arange(phases)+0.5)/phases
    windows={"5min":1,"1h":12,"6h":72,"24h":288,"7d":2016}
    def rollsum(a,B):
        c=np.concatenate([np.zeros((a.shape[0],1)),np.cumsum(a,axis=1)],axis=1)
        return c[:,B:]-c[:,:-B]
    def valid(B):
        ok=np.isfinite(rb[0]).astype(int); c=np.r_[0,np.cumsum(ok)]
        return (c[B:]-c[:-B])==B
    acc={B:[np.zeros((K,N-B+1)),np.zeros((K,N-B+1)),valid(B)] for B in windows.values()}
    for phi in phase_grid:
        C=299.0*log_clean_survival(rs)+log_clean_survival(rs*(1-phi)+rn*phi)
        for B,(sl,sf,v) in acc.items():
            full=rollsum(C,B)
            rlast=rs[:,B-1:]; rnext=rn[:,B-1:]
            full=full-log_clean_survival(rlast*(1-phi)+rnext*phi)
            ls=log_clean_survival(rs[:,:N-B+1]*phi)+full+log_clean_survival(rlast*(1-phi))
            ls[:,~v]=np.nan; fw=-np.expm1(ls)
            sl+=np.nan_to_num(ls); sf+=np.nan_to_num(fw)
    out={}
    for label,B in windows.items():
        sl,sf,v=acc[B]; ml=sl/phases; mf=sf/phases; ml[:,~v]=np.nan; mf[:,~v]=np.nan
        logS=n_words*ml; Fp=-np.expm1(logS); U=np.minimum(1.0,n_words*mf)
        hd=rollsum(np.nan_to_num(dr,nan=0.0)*bin_seconds,B); hd[:,~v]=np.nan
        Ft=-np.expm1(logS-hd); Ut=1-np.exp(-hd)*(1-U)
        out[label]=(Ft,Ut,v)
    return out


def summarize_probability(arr, statistic):
    x=np.asarray(arr,float)
    if statistic == "max": return float(np.nanmax(x))
    q={"median":0.5,"p95":0.95,"p99":0.99}[statistic]
    return float(np.nanquantile(x,q))

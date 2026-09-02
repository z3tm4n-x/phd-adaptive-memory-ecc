#!/usr/bin/env python3
"""Multiplicity interface and CLI entrypoint for the bounded direct-floor kill test."""
from __future__ import annotations
import argparse,csv,json,math
from dataclasses import dataclass
from pathlib import Path
import numpy as np

TASK_ID='RE-CY62167-DIRECT-FLOOR-KILLTEST-01'
STARTING_COMMIT='3474bf5d1773fe481bfd0a3d9013c12cb06dbabd'
N_BITS=16_777_216
FOUR_PI=4.0*math.pi
SHIELDS_MM=(0.,1.,2.,3.,5.,7.,10.)
SIGMA_MODELS=('main_loglog','published_rpp_fluka_digitized')
MULTIPLICITY_VARIANTS=('nominal_logE_linear','raw_nearest_observed','false_mcu_aware_logE_linear')
LOW_SCENARIOS=('K1_only','low_energy_conservative')
HORIZONS=(('5min',300),('1h',3600),('6h',21600),('24h',86400),('7d',604800),('30d',2592000))

@dataclass(frozen=True)
class MultiplicityPoint:
    energy_mev:float; n_events:float; n_bitflips:float; n_multi:float
    raw_p_multi:float; raw_kbar:float; false_pair_temporal_ind3:float
    corrected_p_multi:float; corrected_kbar:float

def _f(x): return 0.0 if x is None or not str(x).strip() else float(x)

def load_multiplicity_points(multiplicity_csv:Path,false_csv:Path):
    false={}
    with Path(false_csv).open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            e=float(r['energy_mev'])
            if e<=5.: false[e]=false.get(e,0.)+_f(r.get('false_N2_IND3_temporal'))
    out=[]
    with Path(multiplicity_csv).open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            e=float(r['energy_mev']); ne=float(r['N_events']); nb=float(r['N_bitflips'])
            c=json.loads(r['multiplicity_counts']); n1=float(c.get('1',0)); nm=ne-n1
            p=nm/ne; k=nb/ne; fp=min(false.get(e,0.),nm)
            ce=ne+fp; cp=max(0.,nm-fp)/ce; ck=nb/ce
            if not (0<=cp<=p+1e-15 and 1<=ck<=k+1e-15): raise ValueError(f'false-MCU correction {e}')
            out.append(MultiplicityPoint(e,ne,nb,nm,p,k,fp,cp,ck))
    out.sort(key=lambda x:x.energy_mev)
    if not out or out[0].energy_mev!=0.9 or out[-1].energy_mev!=186.: raise ValueError('multiplicity support')
    return tuple(out)

def low_conservative_probability(points):
    return max(p.raw_p_multi for p in points if .9<=p.energy_mev<=3.)

def multiplicity_on_grid(E,points,variant,low_scenario):
    if variant not in MULTIPLICITY_VARIANTS or low_scenario not in LOW_SCENARIOS: raise ValueError('scenario')
    E=np.asarray(E,float); xp=np.array([p.energy_mev for p in points])
    if variant=='false_mcu_aware_logE_linear':
        pp=np.array([p.corrected_p_multi for p in points]); kk=np.array([p.corrected_kbar for p in points])
    else:
        pp=np.array([p.raw_p_multi for p in points]); kk=np.array([p.raw_kbar for p in points])
    p=np.full_like(E,pp[-1]); k=np.full_like(E,kk[-1]); mid=(E>=xp[0])&(E<=xp[-1])
    if variant=='raw_nearest_observed':
        idx=np.argmin(abs(np.log(E[mid])[:,None]-np.log(xp)[None,:]),axis=1); p[mid]=pp[idx]; k[mid]=kk[idx]
    else:
        p[mid]=np.interp(np.log(E[mid]),np.log(xp),pp); k[mid]=np.interp(np.log(E[mid]),np.log(xp),kk)
    low=E<xp[0]
    if low_scenario=='K1_only': p[low]=0.; k[low]=1.
    else:
        pl=low_conservative_probability(points); p[low]=pl; k[low]=1.+pl
    if np.any((p<0)|(p>1)|(k<1)|(k+1e-12<1+p)): raise ValueError('multiplicity invariant')
    return p,k

def nhpp_floor(hazard):
    h=np.asarray(hazard,float); y=-np.expm1(-np.maximum(h,0)); return float(y) if y.ndim==0 else y

def max_contiguous_hazard(rate_s,n_bins,dt_s=300.):
    x=np.asarray(rate_s,float)
    if n_bins<=0 or n_bins>len(x): return float('nan'),None
    ok=np.isfinite(x); cs=np.r_[0.,np.cumsum(np.where(ok,x*dt_s,0.))]; cc=np.r_[0,np.cumsum(ok.astype(int))]
    s=cs[n_bins:]-cs[:-n_bins]; n=cc[n_bins:]-cc[:-n_bins]; good=n==n_bins
    if not np.any(good): return float('nan'),None
    z=np.where(good,s,-np.inf); i=int(np.argmax(z)); return float(z[i]),i

def main():
    from killtest_run import run
    p=argparse.ArgumentParser()
    for name in ('goes-dir','transport','sigma-csv','published-csv','multiplicity-csv','false-mcu-csv','task2-rate-csv','out'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(); run(a)

if __name__=='__main__': main()

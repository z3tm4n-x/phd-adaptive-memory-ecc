"""GOES-19 SGPS L2 5-minute adapter for RE-GOES19-PROTON-RATE-01.

No temporal averaging, smoothing, or outlier rejection is performed.  Instrument
fill values create missing rows; DQF metadata are retained as flags rather than
silently deleting otherwise reported L2 averages.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import h5py
import numpy as np

CHANNELS=("P1","P2A","P2B","P3","P4","P5","P6","P7","P8A","P8B","P8C","P9","P10")
OLD_LO=np.array([1.02,1.90,2.31,3.40,5.84,11.64])
OLD_HI=np.array([1.86,2.30,3.34,6.48,11.00,23.27])
CORR_LO=np.array([0.92,1.80,2.20,3.30,6.30,12.4])
CORR_HI=np.array([1.80,2.20,3.20,6.20,11.7,23.3])
CORR=np.array([0.656,0.688,0.708,0.625,0.618,0.753])
EPOCH=datetime(2000,1,1,12,tzinfo=timezone.utc)


def sha256(path: Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def dec(v):
    if isinstance(v,(bytes,np.bytes_)):return v.decode(errors='replace')
    if isinstance(v,np.ndarray):return v.tolist()
    if isinstance(v,np.generic):return v.item()
    return v


def _fill_to_nan(ds):
    a=np.asarray(ds[...],dtype=float)
    fill=float(np.asarray(ds.attrs.get('_FillValue',[-1e31])).ravel()[0])
    a[(~np.isfinite(a)) | (a <= fill/2) | (a<0)] = np.nan
    return a


@dataclass
class GoesData:
    times: list[datetime]
    version: np.ndarray
    yaw: np.ndarray
    flux: np.ndarray       # [T, direction(E=0,W=1), channel], cm^-2 sr^-1 s^-1 MeV^-1
    uncert: np.ndarray
    p11: np.ndarray        # [T, direction], cm^-2 sr^-1 s^-1 above 500 MeV
    p11_uncert: np.ndarray # same units; quadrature random+systematic error reported by L2
    valid: np.ndarray      # [T,direction] all 13 differential channels valid and yaw resolved
    quality_any: np.ndarray
    effective: np.ndarray  # [direction,channel] MeV, direction-specific P8-P9 retained
    lower: np.ndarray
    upper: np.ndarray
    files: list[dict]
    audit: dict


def load_directory(root: str|Path)->GoesData:
    root=Path(root); paths=sorted(root.glob('*.nc'))
    if len(paths)!=59: raise ValueError(f'expected 59 GOES files, found {len(paths)}')
    times=[];versions=[];yaws=[];fluxes=[];uncs=[];p11s=[];p11uncs=[];valids=[];quals=[];filemeta=[]
    ref_energy=None; calibration_actions=set(); global_luts=set(); missing_rows=[]
    algo_versions={}; dqf_totals={nm:{'positive_elements':0,'sample_sum':0} for nm in ('DiffDQFdtcSum','DiffDQFerrSum','DiffDQFoobSum')}
    for path in paths:
        m=re.search(r'_d(\d{8})_v([\d-]+)\.nc$',path.name)
        if not m: raise ValueError(path.name)
        with h5py.File(path,'r') as f:
            title=dec(f.attrs.get('title')); platform=dec(f.attrs.get('platform')); level=dec(f.attrs.get('processing_level'))
            inst=dec(f.attrs.get('instrument')); cadence=dec(f.attrs.get('time_coverage_resolution'))
            if platform!='g19' or level!='Level 2' or 'SGPS' not in inst or cadence!='PT5M':
                raise ValueError(f'unexpected product identity in {path.name}')
            av=tuple(int(x) for x in np.asarray(f.attrs['algorithm_version']).ravel()); algo_versions[av]=algo_versions.get(av,0)+1
            lut=dec(f.attrs.get('L1b_LUT_Filenames','')); global_luts.add(lut)
            t=[EPOCH+timedelta(seconds=float(x)) for x in np.asarray(f['time'][...])]
            yaw=np.asarray(f['yaw_flip_flag'][...],dtype=np.uint8)
            raw=_fill_to_nan(f['AvgDiffProtonFlux'])*1000.0 # per-keV -> per-MeV
            unc=_fill_to_nan(f['AvgDiffProtonFluxUncert'])*1000.0
            p11=_fill_to_nan(f['AvgIntProtonFlux'])
            p11unc=_fill_to_nan(f['AvgIntProtonFluxUncert']) if 'AvgIntProtonFluxUncert' in f else np.full_like(p11,np.nan)
            lo=np.asarray(f['DiffProtonLowerEnergy'][...],float)/1000.0
            hi=np.asarray(f['DiffProtonUpperEnergy'][...],float)/1000.0
            eff=np.asarray(f['DiffProtonEffectiveEnergy'][...],float)/1000.0
            # Detect whether vendor P1-P5 correction has already been applied from energy bounds.
            old=np.allclose(lo[:, :6],OLD_LO[None,:],rtol=0,atol=0.011) and np.allclose(hi[:, :6],OLD_HI[None,:],rtol=0,atol=0.011)
            corrected=np.allclose(lo[:, :6],CORR_LO[None,:],rtol=0,atol=0.011) and np.allclose(hi[:, :6],CORR_HI[None,:],rtol=0,atol=0.011)
            if old:
                raw[:,:,:6]*=CORR[None,None,:]; unc[:,:,:6]*=CORR[None,None,:]
                lo[:,:6]=CORR_LO;hi[:,:6]=CORR_HI;eff[:,:6]=np.sqrt(CORR_LO*CORR_HI)
                calibration_actions.add('P1-P5 multiplicative correction applied once to old bounds')
            elif corrected:
                calibration_actions.add('P1-P5 already corrected; no multiplicative correction applied')
            else:
                raise ValueError(f'P1-P5 bounds neither known original nor corrected: {path.name}')
            energy_tuple=(lo.copy(),hi.copy(),eff.copy())
            if ref_energy is None: ref_energy=energy_tuple
            else:
                for a,b in zip(ref_energy,energy_tuple):
                    if not np.array_equal(a,b): raise ValueError(f'energy metadata changed at {path.name}')
            for nm in ('DiffDQFdtcSum','DiffDQFerrSum','DiffDQFoobSum'):
                if nm in f:
                    qa=np.asarray(f[nm][...]); qfill=f[nm].attrs.get('_FillValue',np.iinfo(qa.dtype).max); qv=qa[qa!=qfill]
                    dqf_totals[nm]['positive_elements'] += int(np.count_nonzero(qv>0)); dqf_totals[nm]['sample_sum'] += int(qv.sum())
            # DQF *sum* arrays count valid 1-s samples carrying specific flags; they are
            # retained in audit and are not themselves treated as an invalid 5-min average.
            # quality_any below marks only the L2 bitmask saying invalid L1b DQFs were
            # explicitly ignored for averaging. Fill values remain the hard invalidation.
            q=np.zeros(raw.shape[:2],dtype=bool)
            if 'DiffProtonIgnoredL1bDQFs' in f:
                a=np.asarray(f['DiffProtonIgnoredL1bDQFs'][...]);fill=f['DiffProtonIgnoredL1bDQFs'].attrs.get('_FillValue',255)
                q |= np.any((a!=fill)&(a!=0),axis=2)
            # map physical East/West. sensor 0 (-X)=W, sensor1(+X)=E upright; inverted reverses.
            out=np.full_like(raw,np.nan);outu=np.full_like(unc,np.nan);outp=np.full_like(p11,np.nan);outpu=np.full_like(p11unc,np.nan);outq=np.ones_like(q,dtype=bool)
            valid=np.zeros(raw.shape[:2],dtype=bool)
            for i,y in enumerate(yaw):
                if y==0:
                    out[i,0]=raw[i,1]; out[i,1]=raw[i,0]; outu[i,0]=unc[i,1];outu[i,1]=unc[i,0];outp[i,0]=p11[i,1];outp[i,1]=p11[i,0];outpu[i,0]=p11unc[i,1];outpu[i,1]=p11unc[i,0];outq[i,0]=q[i,1];outq[i,1]=q[i,0]
                elif y==2:
                    out[i,0]=raw[i,0]; out[i,1]=raw[i,1]; outu[i,0]=unc[i,0];outu[i,1]=unc[i,1];outp[i,0]=p11[i,0];outp[i,1]=p11[i,1];outpu[i,0]=p11unc[i,0];outpu[i,1]=p11unc[i,1];outq[i,0]=q[i,0];outq[i,1]=q[i,1]
                else:
                    continue
                valid[i]=np.all(np.isfinite(out[i]),axis=1)
            for i,ok in enumerate(valid):
                if not np.all(ok): missing_rows.append({'timestamp':t[i].isoformat(),'file':path.name,'east_valid':bool(ok[0]),'west_valid':bool(ok[1]),'missing_cells':int(np.sum(~np.isfinite(out[i])))})
            times.extend(t);versions.extend([f'{av[0]}.{av[1]}']*len(t));yaws.extend(yaw.tolist());fluxes.append(out);uncs.append(outu);p11s.append(outp);p11uncs.append(outpu);valids.append(valid);quals.append(outq)
            filemeta.append({
                'name':path.name,'sha256':sha256(path),'date':m.group(1),'file_version':m.group(2),'algorithm_version':f'{av[0]}.{av[1]}',
                'date_created':dec(f.attrs.get('date_created')),'L1b_LUT_Filenames':lut,'ExpectedLUTNotFound':int(np.asarray(f['ExpectedLUTNotFound'][()])),
                'title':title,'platform':platform,'processing_level':level,'instrument':inst,'time_coverage_resolution':cadence,
            })
    F=np.concatenate(fluxes);U=np.concatenate(uncs);P=np.concatenate(p11s);PU=np.concatenate(p11uncs);V=np.concatenate(valids);Q=np.concatenate(quals);yaw=np.asarray(yaws,dtype=np.uint8);versions=np.asarray(versions)
    # timestamp/cadence assertions
    sec=np.array([x.timestamp() for x in times]);diff=np.diff(sec)
    if len(times)!=16992 or not np.all(diff==300): raise ValueError('time coverage/cadence mismatch')
    # version-boundary discontinuity diagnostic: one-step jump at 2026-01-13 00:00 versus local adjacent-log-change population.
    boundary=datetime(2026,1,13,tzinfo=timezone.utc);ib=times.index(boundary)
    version_check=[]
    for d,name in enumerate(('E','W')):
        for c,ch in enumerate(CHANNELS):
            x=F[:,d,c]
            local=np.arange(max(1,ib-288),min(len(x),ib+288))
            pair=np.log(np.maximum(x[local],1e-300))-np.log(np.maximum(x[local-1],1e-300))
            pair=pair[np.isfinite(pair)&(x[local]>0)&(x[local-1]>0)]
            if x[ib]>0 and x[ib-1]>0 and pair.size:
                jump=abs(float(np.log(x[ib]/x[ib-1])));q99=float(np.quantile(np.abs(pair),.99));ratio=jump/max(q99,1e-300)
            else: jump=q99=ratio=float('nan')
            version_check.append({'direction':name,'channel':ch,'boundary_log_jump_abs':jump,'local_abs_log_change_p99':q99,'jump_to_local_p99_ratio':ratio})
    audit={
      'satellite':'GOES-19','instrument':'SEISS/SGPS','product':'L2 5-minute Flux Averages','processing_level':'Level 2','timestamp_semantics':'timestamp at start of averaging period','cadence_seconds':300,
      'time_start':times[0].isoformat(),'time_end':times[-1].isoformat(),'n_timestamps':len(times),'directions':['East','West'],
      'native_units':'protons/(cm^2 sr keV s)','internal_units':'protons/(cm^2 sr MeV s)','channels':list(CHANNELS),
      'algorithm_versions':{'.'.join(map(str,k)):v for k,v in algo_versions.items()},'version_boundary':'2026-01-13T00:00:00+00:00','energy_metadata_constant_across_version_boundary':True,
      'yaw_counts':{str(int(k)):int(v) for k,v in zip(*np.unique(yaw,return_counts=True))},'L1b_LUT_Filenames':sorted(global_luts),
      'calibration_actions':sorted(calibration_actions),'dqf_valid_sample_flag_totals':dqf_totals,'missing_direction_rows':int(np.sum(~V)),'timestamps_with_any_missing_direction':int(np.sum(~np.all(V,axis=1))),
      'missing_rows':missing_rows,'quality_flagged_direction_rows':int(np.sum(Q)),'version_boundary_checks':version_check,
      'calibration_note':'GOES-19 provisional ReadMe vendor P1-P5 revised energy bounds/geometric factors; correction factors applied only when old bounds detected.',
    }
    # energy arrays direction order E,W; ref source arrays are sensor W,E in upright, so swap.
    lo0,hi0,ef0=ref_energy
    lower=np.stack([lo0[1],lo0[0]]);upper=np.stack([hi0[1],hi0[0]]);effective=np.stack([ef0[1],ef0[0]])
    audit['energy_channels'] = [
        {
            'channel': ch,
            'east': {'lower_mev': float(lower[0,i]), 'upper_mev': float(upper[0,i]), 'effective_mev': float(effective[0,i])},
            'west': {'lower_mev': float(lower[1,i]), 'upper_mev': float(upper[1,i]), 'effective_mev': float(effective[1,i])},
        }
        for i, ch in enumerate(CHANNELS)
    ]
    audit['quality_flag_semantics'] = {
        'DiffProtonIgnoredL1bDQFs': 'bit mask indicating invalid L1b DQFs ignored by the L2 averaging algorithm; retained as a per-direction warning flag, not used by this study as an automatic L2-average rejection criterion',
        'DiffDQFdtcSum': 'count of valid contributing 1-s samples carrying dead-time-correction-threshold flag',
        'DiffDQFerrSum': 'count of valid contributing 1-s samples carrying dynamic-error-threshold flag',
        'DiffDQFoobSum': 'count of valid contributing 1-s samples carrying out-of-band-contamination-threshold flag',
        'hard_invalidation': 'fill/nonfinite differential flux or unresolved yaw state; no time interpolation is performed',
    }
    audit['calibration_status'] = {
        'maturity': 'GOES-19 SGPS provisional product',
        'P1_P5_vendor_revision': 'revised bounds/geometric factors applied exactly once when legacy bounds are detected',
        'operational_L2_note': 'NOAA provisional ReadMe states corrected Level-2 one- and five-minute flux products are planned/replacement pending; supplied files retain legacy bounds, so this study applies the published multiplicative corrections once',
    }
    return GoesData(times,versions,yaw,F,U,P,PU,V,Q,effective,lower,upper,filemeta,audit)


def reconstruct_on_grid(channel_energy, channel_flux, support_lo, support_hi, grid):
    """Piecewise-linear interpolation in log(E), linear in J; handles reported zeros.

    Constant extension is used only from the first/last effective energy to the
    corresponding measured channel support edge. Outside measured differential
    support the result is NaN/unsupported, not silently treated as measured zero.
    """
    e=np.asarray(channel_energy,float);j=np.asarray(channel_flux,float);g=np.asarray(grid,float)
    if not np.all(np.isfinite(j)): return np.full_like(g,np.nan)
    out=np.full_like(g,np.nan)
    m=(g>=support_lo)&(g<=support_hi)
    if not np.any(m):return out
    lg=np.log(g[m]);le=np.log(e)
    out[m]=np.interp(lg,le,j,left=j[0],right=j[-1])
    out[m]=np.maximum(out[m],0.0)
    return out

"""Input-only preparation. Never executes a GOES policy or consumes trial seeds."""
from pathlib import Path
import argparse, csv, hashlib, json, sys, subprocess, platform, time
from datetime import datetime, timedelta, timezone
import numpy as np
import h5py

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
UP = HERE.parent / 'RE-GOES19-PROTON-RATE-01'
sys.path.insert(0, str(UP))
from goes19_adapter import GoesData, EPOCH, CHANNELS
from rate_pipeline import reconstruct_goes, low_energy_extension, high_energy_gap_bridge, trap_weights
from sigma_model import load_experimental_points, sigma_hat, zero_crossing_low
import radar_adapter as radar

BASE = '7b83f643efb37541547d7d93a65ba2f43acd43fd'
URL = 'https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/sgps-l2-avg5m/2024/10/'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p, obj): Path(p).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
def csvwrite(p, rows):
    with Path(p).open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)
def dec(x):
    if isinstance(x, bytes): return x.decode()
    if isinstance(x, np.ndarray): return [dec(v) for v in x.tolist()]
    if isinstance(x, np.generic): return x.item()
    return x
def read_flux(f, name):
    d=f[name]; a=np.asarray(d[...],float)
    a[(~np.isfinite(a)) | (a < 0) | (a > float(d.attrs['valid_max'][0]))]=np.nan
    return a

def load_g16(raw):
    times=[]; flux=[]; unc=[]; p11=[]; pu=[]; flags=[]; val=[]; yawall=[]; meta=[]; quality=[]
    ref=None
    for day in range(8,13):
        p=Path(raw)/f'sci_sgps-l2-avg5m_g16_d202410{day:02d}_v3-0-2.nc'
        with h5py.File(p) as f:
            assert dec(f.attrs['platform'])=='g16'
            assert dec(f.attrs['processing_level'])=='Level 2'
            assert dec(f.attrs['time_coverage_resolution'])=='PT5M'
            assert list(f.attrs['algorithm_version'])==[3,2]
            assert dec(f['time'].attrs['units'])=='seconds since 2000-01-01 12:00:00 UTC'
            assert 'start of the averaging period' in dec(f['time'].attrs['long_name'])
            assert dec(f['AvgDiffProtonFlux'].attrs['units'])=='protons/(cm^2 sr keV s)'
            assert dec(f['AvgIntProtonFlux'].attrs['units'])=='protons/(cm^2 sr s)'
            assert np.all(f['IntegralProtonEffectiveEnergy'][...]==500000)
            energy=[np.asarray(f[k],float)[[1,0]]/1000 for k in
                    ('DiffProtonLowerEnergy','DiffProtonUpperEnergy','DiffProtonEffectiveEnergy')]
            if ref is None: ref=energy
            assert all(np.array_equal(a,b) for a,b in zip(ref,energy))
            # Direction swap is independently checked against the raw long_name.
            assert 'First unit (-X) looks Westward' in dec(f['DiffProtonLowerEnergy'].attrs['long_name'])
            yaw=np.asarray(f['yaw_flip_flag']); assert np.all(yaw==0), 'new yaw domain requires row-specific energy mapping'
            x=read_flux(f,'AvgDiffProtonFlux')[:,[1,0],:]*1000
            u=read_flux(f,'AvgDiffProtonFluxUncert')[:,[1,0],:]*1000
            ip=read_flux(f,'AvgIntProtonFlux')[:,[1,0]]
            iu=read_flux(f,'AvgIntProtonFluxUncert')[:,[1,0]]
            samples=np.asarray(f['DiffValidL1bSamplesInAvg'])[:,[1,0],:]
            ips=np.asarray(f['IntValidL1bSamplesInAvg'])[:,[1,0]]
            dq=np.asarray(f['DiffProtonIgnoredL1bDQFs'])[:,[1,0],:]
            iq=np.asarray(f['IntProtonIgnoredL1bDQFs'])[:,[1,0]]
            # Despite its name, raw variable LONG_NAME defines 1 as matching LUTs.
            lutok=int(np.asarray(f['ExpectedLUTNotFound']).item())==1
            valid=np.all(np.isfinite(x),axis=2)&np.isfinite(ip)&np.all((samples>0)&(samples<=301),axis=2)&(ips>0)&(ips<=301)&lutok
            q=np.any(dq!=0,axis=2)|(iq!=0)
            tt=[EPOCH+timedelta(seconds=float(s)) for s in f['time'][...]]
            assert len(tt)==288
            for i,t in enumerate(tt):
                quality.append(dict(timestamp_utc=t.isoformat(),min_differential_samples=int(samples[i].min()),min_integral_samples=int(ips[i].min()),
                                    ignored_dqf_E=int(np.bitwise_or.reduce(dq[i,0]))|int(iq[i,0]),ignored_dqf_W=int(np.bitwise_or.reduce(dq[i,1]))|int(iq[i,1]),
                                    east_valid=bool(valid[i,0]),west_valid=bool(valid[i,1]),lut_match=lutok))
            meta.append(dict(name=p.name,url=URL+p.name,sha256=sha(p),bytes=p.stat().st_size,
                attrs={k:dec(v) for k,v in f.attrs.items()},
                time_long_name=dec(f['time'].attrs['long_name']),expected_lut_indicator_semantics=dec(f['ExpectedLUTNotFound'].attrs['long_name']),
                temperature_correction_max_abs=float(np.nanmax(abs(np.asarray(f['AvgDiffProtonFlux'])-np.asarray(f['AvgDiffProtonFluxObserved']))))))
            times+=tt;flux.append(x);unc.append(u);p11.append(ip);pu.append(iu);val.append(valid);flags.append(q);yawall.extend(yaw.tolist())
    assert len(times)==1440 and np.all(np.diff([t.timestamp() for t in times])==300)
    assert times[0]==datetime(2024,10,8,tzinfo=timezone.utc) and times[-1]+timedelta(seconds=300)==datetime(2024,10,13,tzinfo=timezone.utc)
    data=GoesData(times,np.array(['3.2']*1440),np.array(yawall),np.concatenate(flux),np.concatenate(unc),np.concatenate(p11),np.concatenate(pu),
                  np.concatenate(val),np.concatenate(flags),ref[2],ref[0],ref[1],meta,{})
    return data,quality

def select_windows(times,nu):
    rows=[]
    for i in range(len(nu)-11):
        x=nu[i:i+12]
        if np.all(np.isfinite(x)) and np.all(x>=0) and (times[i+11]-times[i]).total_seconds()==3300:
            rows.append(dict(index=i,utc=times[i].isoformat(),exposure=float(300*sum(x)),growth=float(300*(sum(x[6:])-sum(x[:6])))))
    if not rows: raise ValueError('BLOCKED_INPUT: no eligible complete hour')
    chosen=[('growth',min(rows,key=lambda r:(-r['growth'],r['utc']))),('peak',min(rows,key=lambda r:(-r['exposure'],r['utc']))),
            ('typical',sorted(rows,key=lambda r:(r['exposure'],r['utc']))[(len(rows)-1)//2])]
    out={}
    for label,row in chosen:
        i=row['index']
        if i not in out: out[i]={**row,'labels':[],'nu_array_s-1':nu[i:i+12].tolist(),'end_utc':(times[i]+timedelta(hours=1)).isoformat()}
        out[i]['labels'].append(label)
    return list(out.values()),len(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--radar',type=Path,required=True);ap.add_argument('--cache',type=Path,required=True);ap.add_argument('--out',type=Path,default=HERE)
    a=ap.parse_args();a.cache.mkdir(parents=True,exist_ok=True);a.out.mkdir(parents=True,exist_ok=True);start=time.perf_counter()
    assert subprocess.check_output(['git','-C',str(a.radar),'rev-parse','HEAD'],text=True).strip()==radar.RADAR_SHA
    g,quality=load_g16(a.raw)
    matrix=a.cache/'transport_3mm.npz'
    radar.SHIELDS_MM=(3.,)
    if not matrix.exists():
        e,p,s,actions=radar.build_matrices(a.radar,192,depth_steps=48,survival_steps=128)
        np.savez_compressed(matrix,energy=e,primary=p[0],secondary=s[0]);dump(a.cache/'transport_actions.json',actions)
    z=np.load(matrix);e=z['energy'];points=load_experimental_points(HERE.parent/'RE-CY62167-PROTON-01/sigma_bit_experimental.csv')
    sig=sigma_hat(e,points,'main_loglog');ww=trap_weights(e)*sig
    J,_=reconstruct_goes(g,e);L,_=low_energy_extension(g,e,zero_crossing_low(points),2.)
    # Same numerical cutoff as original chain: 390 MeV. Native G16 P10 ends at
    # 404 MeV; 390--500 is MODELLED by the inherited bridge, not counted twice.
    gap,_,_,gamma,diag=high_energy_gap_bridge(g)
    high=float(sigma_hat(np.array([600.]),points)[0])
    primary=4*np.pi*(J+L)@z['primary'].T
    secondary=4*np.pi*(J+L)@z['secondary'].T
    perbit=(primary+secondary)@ww+4*np.pi*(gap+g.p11)*high
    perbit[~g.valid]=np.nan
    nu=524288*32*perbit.mean(axis=1)
    windows,nwindows=select_windows(g.times,nu)
    rows=[]
    for i,t in enumerate(g.times):
        fallback=(g.flux[i,:,-1]<=0)|(g.p11[i,:]<=0)
        rows.append(dict(timestamp_utc=t.isoformat(),end_utc=(t+timedelta(seconds=300)).isoformat(),
            lambda_bit_E_s_1=perbit[i,0],lambda_bit_W_s_1=perbit[i,1],lambda_bit_central_s_1=perbit[i].mean(),nu_array_s_1=nu[i],
            valid=bool(np.isfinite(nu[i])),retrospective_bridge_E=bool(fallback[0]),retrospective_bridge_W=bool(fallback[1]),
            warning_E=bool(g.quality_any[i,0]),warning_W=bool(g.quality_any[i,1])))
    csvwrite(a.out/'derived_rates.csv',rows);csvwrite(a.out/'input_quality.csv',quality)
    dump(a.out/'selected_windows.json',dict(eligible_windows=nwindows,windows=windows,selection_uses_policy_results=False))
    inputs={str(p.relative_to(REPO)).replace('\\','/'):sha(p) for p in [*UP.glob('*.py'), HERE.parent/'RE-CY62167-PROTON-01/sigma_bit_experimental.csv',* (HERE.parent/'RE-INTERNAL-COUNT-CONTROL-01').glob('*.py'),HERE.parent/'RE-INTERNAL-COUNT-CONTROL-01/config.json']}
    dump(a.out/'input_manifest.json',dict(base=BASE,retrieved_utc=datetime.now(timezone.utc).isoformat(),raw_local=str(a.raw.resolve()),files=g.files,
         pipeline_hashes=inputs,radar_sha=radar.RADAR_SHA,transport_file=str(matrix.resolve()),transport_sha256=sha(matrix),
         transport_arrays_sha256={k:hashlib.sha256(z[k].tobytes()).hexdigest() for k in z.files},
         energy_metadata=dict(direction_order=['E','W'],lower_mev=g.lower.tolist(),upper_mev=g.upper.tolist(),effective_mev=g.effective.tolist()),
         calibration='Use archived G16 temperature-corrected Avg*Flux as supplied. No G19 multiplicative correction. Retain G16 provisional caveats; not physical calibration.',
         transport_cutoff_mev=390,native_P10_upper_mev=404,bridge='Inherited P10/P11 power-law from 390 to 500; overlaps native channel support but NOT transport integral',
         bridge_diagnostic=diag,valid_bins=int(np.isfinite(nu).sum()),total_bins=1440,eligible_windows=nwindows,
         invalid_timestamps=[g.times[i].isoformat() for i in np.where(~np.isfinite(nu))[0]],
         rates_sha256=sha(a.out/'derived_rates.csv'),preparation_seconds=time.perf_counter()-start,
         python=platform.python_version(),numpy=np.__version__,h5py=h5py.__version__))
    np.savez_compressed(a.cache/'spectral_check.npz',J=J,L=L,perbit=perbit,gap=gap,p11=g.p11,energy=e,sigma=sig,primary=z['primary'],secondary=z['secondary'])
    print(json.dumps(dict(windows=windows,valid=int(np.isfinite(nu).sum()),min=float(np.nanmin(nu)),max=float(np.nanmax(nu))),indent=2))
if __name__=='__main__':main()

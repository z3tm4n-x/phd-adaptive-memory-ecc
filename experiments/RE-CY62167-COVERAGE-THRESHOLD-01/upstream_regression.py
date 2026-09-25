"""Separate historical GOES adapter + direct trapezoids; no DREG/risk imports."""
import argparse, csv, dataclasses, json, math, sys, tempfile
from pathlib import Path
import numpy as np
from input_contract import HERE, TIMES, archive_extract, reference, sources, transport, sha
sys.path.insert(0,str(HERE/'recovery/historical'))
import goes19_adapter as ga
import rate_pipeline as rp
from sigma_model import load_experimental_points, sigma_hat, zero_crossing_low

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--repo',type=Path,required=True);a=ap.parse_args()
    sources();npz=transport();ref=reference(a.repo)
    with tempfile.TemporaryDirectory() as td:
        members=archive_extract(a.archive,a.repo,td);full=ga.load_directory(td)
    ids=[i for i,t in enumerate(full.times) if t in set(TIMES)]
    if [full.times[i] for i in ids]!=TIMES:raise ValueError('selected time coverage')
    # Preserve full historical fallback-median population, no rate calculation outside H.
    gap,_,_,_,diag=rp.high_energy_gap_bridge(full)
    g=dataclasses.replace(full,times=TIMES,**{n:getattr(full,n)[ids] for n in ['version','yaw','flux','uncert','p11','p11_uncert','valid','quality_any']})
    if not g.valid.all() or not np.isfinite(g.p11).all() or (g.p11<0).any():raise ValueError('missing/invalid selected flux')
    z=np.load(npz,allow_pickle=False);E=z['energy_mev'];di=list(z['shield_mm']).index(10.)
    points=load_experimental_points(HERE/'recovery/historical/sigma_bit_experimental.csv');sigma=sigma_hat(E,points,'main_loglog')
    J,_=rp.reconstruct_goes(g,E);L,_=rp.low_energy_extension(g,E,zero_crossing_low(points),2.)
    values=[]
    for t in range(288):
        directions=[]
        for d in range(2):
            # Keep measured/low and primary/secondary separate, as original rate pipeline.
            pieces=[]
            for inp in [J[t,d],L[t,d]]:
                for matrix in [z['primary'][di],z['secondary'][di]]:
                    out=(4*math.pi*inp)@matrix.T
                    pieces.append(16777216*float(np.trapezoid(out*sigma,E)))
            pieces.append(16777216*4*math.pi*float(sigma[-1])*(float(g.p11[t,d])+float(gap[ids[t],d])))
            directions.append(math.fsum(pieces))
        values.append(math.fsum(directions)/2)
    errors=[];rows=[]
    for t,x,r in zip(TIMES,values,ref):
        y=float(r['d10_lambda_central_s-1'])
        if not(math.isfinite(x) and math.isfinite(y) and x>=0 and y>=0):raise ValueError('nonfinite/negative upstream')
        err=abs(x-y)/y if y>0 else (0. if x==0 else float('inf'))
        errors.append(err);rows.append(dict(timestamp_utc=t.isoformat(),computed_s_1=repr(x),reference_s_1=repr(y),relative_error=repr(err)))
    out=HERE/'recovery/outputs'
    with (out/'upstream_regression.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result={'pass':max(errors)<=1e-6,'rows':288,'relative_tolerance':1e-6,'zero_rule':'exact zero; no additive floor','max_relative_error':max(errors),'transport_sha256':sha(npz),'goes_members':len(members),'fallback_population':'all 16992 frozen timestamps, rates computed only for selected 288','historical_gap_diagnostic':diag,'independence':'historical goes19_adapter/rate_pipeline primitive calls; separate component transports and trapezoids; no selected_recovery or CW imports','physical_qualification':False}
    (out/'upstream_regression.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['pass','rows','max_relative_error']}))
    if not result['pass']:raise ValueError('upstream regression failed; DREG blocked')

if __name__=='__main__':main()

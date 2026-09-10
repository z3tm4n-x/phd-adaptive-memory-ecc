#!/usr/bin/env python3
"""Published-physics sigma(E) sensitivity closure for RE-GOES19-PROTON-RATE-01."""
from __future__ import annotations
import argparse, csv, json, math
from pathlib import Path
import numpy as np
from goes19_adapter import load_directory
from sigma_model import load_experimental_points, sigma_hat
from rate_pipeline import (FOUR_PI, LOW_EXTRAP_REFERENCE_GAMMA, N_BITS, SHIELDS_MM,
    calculate as calculate_reference, high_energy_gap_bridge, low_energy_extension,
    reconstruct_goes, trap_weights)

REF="main_loglog"; PHYS="published_rpp_fluka_digitized"
BANDS=(("0-3",0.,3.),("3-20",3.,20.),(">20",20.,math.inf))

def load_pub(path):
    e=[]; s=[]
    with Path(path).open(encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            if r.get("comparator")==PHYS:
                e.append(float(r["energy_mev"])); s.append(float(r["sigma_cm2_per_bit"]))
    e=np.asarray(e); s=np.asarray(s)
    if len(e)<3 or np.any(np.diff(e)<=0) or np.any(s<=0): raise ValueError("bad published curve")
    return e,s

def sigma_phys(E,pe,ps,exp):
    E=np.asarray(E,float); y=sigma_hat(E,exp,REF)
    m=(E>=pe[0])&(E<=pe[-1])
    y[m]=np.exp(np.interp(np.log(E[m]),np.log(pe),np.log(ps)))
    y[E>pe[-1]]=ps[-1]
    return y

def central(a):
    a=np.asarray(a,float); return np.where(np.all(np.isfinite(a),axis=-1),np.mean(a,axis=-1),np.nan)
def pearson(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float); m=np.isfinite(a)&np.isfinite(b)
    if m.sum()<3 or np.std(a[m])==0 or np.std(b[m])==0: return float("nan")
    return float(np.corrcoef(a[m],b[m])[0,1])
def q(x,p): return float(np.nanquantile(np.asarray(x,float),p))
def rd(new,ref): return float(new)/float(ref)-1.0

def metrics(times,x):
    i=int(np.nanargmax(x)); med=float(np.nanmedian(x)); p99=q(x,.99); mx=float(x[i])
    return {"median_s-1":med,"mean_s-1":float(np.nanmean(x)),"p99_s-1":p99,"max_s-1":mx,
        "max_timestamp_utc":times[i].isoformat(),"total_expected_flips":float(np.nansum(x*300.)),
        "p99_over_median":p99/med,"max_over_median":mx/med}

def calc(goes,transport,sigma_csv,pub_csv):
    z=np.load(transport); E=np.asarray(z["energy_mev"],float); shields=np.asarray(z["shield_mm"],float)
    P=np.asarray(z["primary"],float); S=np.asarray(z["secondary"],float)
    if tuple(shields.tolist())!=SHIELDS_MM: raise ValueError("shield grid mismatch")
    exp=load_experimental_points(sigma_csv); pe,ps=load_pub(pub_csv)
    sr=sigma_hat(E,exp,REF); sp=sigma_phys(E,pe,ps,exp); tw=trap_weights(E); wr=tw*sr; wp=tw*sp
    frozen=calculate_reference(goes,transport,sigma_csv)
    J,_=reconstruct_goes(goes,E); J*=FOUR_PI
    L,_=low_energy_extension(goes,E,float(frozen["low_sigma_zero_crossing"]),LOW_EXTRAP_REFERENCE_GAMMA); L*=FOUR_PI
    gap,*_=high_energy_gap_bridge(goes)
    hr=float(sigma_hat(np.array([600.]),exp,REF)[0]); hp=float(sigma_phys(np.array([600.]),pe,ps,exp)[0])
    p11r=N_BITS*FOUR_PI*goes.p11*hr; p11p=N_BITS*FOUR_PI*goes.p11*hp
    gapr=N_BITS*FOUR_PI*gap*hr; gapp=N_BITS*FOUR_PI*gap*hp
    shape=(len(goes.times),len(shields),2); R=np.full(shape,np.nan); Q=np.full(shape,np.nan)
    BR={n:np.full(shape,np.nan) for n,_,_ in BANDS}; BP={n:np.full(shape,np.nan) for n,_,_ in BANDS}
    for di in range(len(shields)):
        for d in range(2):
            v=goes.valid[:,d]
            out=(J[v,d]+L[v,d])@P[di].T+(J[v,d]+L[v,d])@S[di].T
            R[v,di,d]=N_BITS*(out@wr)+p11r[v,d]+gapr[v,d]
            Q[v,di,d]=N_BITS*(out@wp)+p11p[v,d]+gapp[v,d]
            for n,lo,hi in BANDS:
                m=(E>=lo) if math.isinf(hi) else ((E>=lo)&(E<hi))
                BR[n][v,di,d]=N_BITS*(out@(wr*m)); BP[n][v,di,d]=N_BITS*(out@(wp*m))
                if n==">20":
                    BR[n][v,di,d]+=p11r[v,d]+gapr[v,d]; BP[n][v,di,d]+=p11p[v,d]+gapp[v,d]
    fr=np.asarray(frozen["reference_total"],float); m=np.isfinite(fr)&np.isfinite(R)
    val={"reference_reconstruction_max_rel":float(np.max(np.abs(fr[m]-R[m])/np.maximum(np.abs(fr[m]),1e-300))),
         "energy_partition_max_rel_ref":float(np.nanmax(np.abs(sum(BR.values())-R)/np.maximum(np.abs(R),1e-300))),
         "energy_partition_max_rel_phys":float(np.nanmax(np.abs(sum(BP.values())-Q)/np.maximum(np.abs(Q),1e-300)))}
    return {"E":E,"shields":shields,"ref":R,"phys":Q,"br":BR,"bp":BP,"validation":val}

def compare(goes,R):
    rows=[]; ranks={REF:{},PHYS:{}}
    for i,mm in enumerate(R["shields"]):
        a=central(R["ref"][:,i,:]); b=central(R["phys"][:,i,:]); A=metrics(goes.times,a); B=metrics(goes.times,b)
        rat=b/np.maximum(a,1e-300); pos=np.isfinite(a)&np.isfinite(b)&(a>0)&(b>0)
        row={"shield_mm":float(mm)}
        row.update({"ref_"+k:v for k,v in A.items()}); row.update({"phys_"+k:v for k,v in B.items()})
        for k in ("median_s-1","mean_s-1","p99_s-1","max_s-1","total_expected_flips","p99_over_median","max_over_median"):
            base=k.replace("_s-1","")
            row[base+"_relative_difference"]=rd(B[k],A[k])
        row.update({"temporal_pearson":pearson(a,b),"temporal_log10_pearson":pearson(np.log10(a[pos]),np.log10(b[pos])),
            "ratio_phys_over_ref_median":q(rat,.5),"ratio_phys_over_ref_p01":q(rat,.01),"ratio_phys_over_ref_p99":q(rat,.99),
            "ratio_phys_over_ref_at_ref_peak":float(rat[int(np.nanargmax(a))]),"peak_timestamp_changed":A["max_timestamp_utc"]!=B["max_timestamp_utc"]})
        rows.append(row)
        for k in ("median_s-1","p99_s-1","max_s-1"):
            ranks[REF].setdefault(k,[]).append((A[k],float(mm))); ranks[PHYS].setdefault(k,[]).append((B[k],float(mm)))
    orders={}; changed=False
    for k in ("median_s-1","p99_s-1","max_s-1"):
        x=[m for _,m in sorted(ranks[REF][k],reverse=True)]; y=[m for _,m in sorted(ranks[PHYS][k],reverse=True)]
        orders[k]={REF:x,PHYS:y}; changed|=x!=y
    return rows,changed,orders

def energy_rows(R):
    out=[]
    for i,mm in enumerate(R["shields"]):
        for model,bands,total in ((REF,R["br"],R["ref"]),(PHYS,R["bp"],R["phys"])):
            tc=central(total[:,i,:]); tf=float(np.nansum(tc*300.))
            for n,_,_ in BANDS:
                x=central(bands[n][:,i,:]); flips=float(np.nansum(x*300.))
                out.append({"shield_mm":float(mm),"sigma_model":model,"energy_band_mev":n,"mean_rate_s-1":float(np.nanmean(x)),
                    "median_rate_s-1":float(np.nanmedian(x)),"p99_rate_s-1":q(x,.99),"total_expected_flips":flips,
                    "fraction_of_total_expected_flips":flips/tf})
    return out

def classify(rows,ranking_changed):
    peak=any(r["peak_timestamp_changed"] for r in rows)
    key=max(abs(r[k]) for r in rows for k in ("median_relative_difference","p99_relative_difference","max_relative_difference"))
    exc=max(abs(r[k]) for r in rows for k in ("p99_over_median_relative_difference","max_over_median_relative_difference"))
    corr=min(r["temporal_log10_pearson"] for r in rows)
    rs=[r[k] for r in rows for k in ("ratio_phys_over_ref_p01","ratio_phys_over_ref_p99")]; fac=max(max(rs),1/max(min(rs),1e-300))
    if ranking_changed or peak or corr<.95 or fac>=2 or exc>.5: code="C"
    elif key<=.10 and corr>=.995 and exc<=.10: code="A"
    else: code="B"
    return code,{"ranking_changed":ranking_changed,"peak_timestamp_changed":peak,"worst_key_metric_absolute_relative_difference":key,
        "worst_excursion_metric_absolute_relative_difference":exc,"minimum_log10_temporal_pearson":corr,"worst_pointwise_ratio_factor_p01_p99":fac,
        "rule":"A <=10% key/excursion and log10 corr>=0.995; C ranking/peak change, corr<0.95, >=2x ratio factor, or >50% excursion; otherwise B"}

def write_csv(path,rows):
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def make_report(rows,er,val,code,diag):
    lines=["# RE-GOES19-PROTON-RATE-01-SIGMA-CLOSURE","","## Scope","",
      "Only sigma(E) is varied. GOES, 4pi, E/W handling, RADAR, shielding grid and calibration are unchanged from `e2370c1ad2bb5e640efe5af549e0944ac1a16aa0`.","",
      "## Comparator provenance","",
      "`published_rpp_fluka_digitized` is digitized from Coronetti et al., DOI `10.1109/TNS.2021.3061209`, Fig. 3, printed p. 939 (PDF p. 3). It is the published FLUKA/nested-RPP simulated Cypress response, not experimental data.","",
      "Table III Cypress parameters: 10 um SiO2-equivalent BEOL; Qcrit=0.86 fC; nested volumes (side x thickness nm, alpha): 360x360/1, 984x360/0.057, 1612x360/0.037, 3160x360/0.007. No FLUKA/RPP model was rebuilt.","",
      "Publication model uncertainty is about +/-35% on average. Separate digitization allowance: typical +/-3 px = ~1.62% E and ~6.24% sigma; two overlapping peak markers +/-5 px = ~2.72% E and ~10.62% sigma. Pixel calibration/centres are reproducible in `digitize_published_physics.py`.","",
      "Comparator boundary policy: log-log interpolation of digitized FLUKA points inside plotted support; below the first point retain the Task-2 main_loglog boundary response; above the last point hold the published endpoint constant.","",
      "## Rate comparison","","| Al mm | median diff | mean diff | p99 diff | max diff | temporal r | log10 r | peak changed |","|---:|---:|---:|---:|---:|---:|---:|:---:|"]
    for r in rows: lines.append(f"| {r['shield_mm']:g} | {100*r['median_relative_difference']:+.2f}% | {100*r['mean_relative_difference']:+.2f}% | {100*r['p99_relative_difference']:+.2f}% | {100*r['max_relative_difference']:+.2f}% | {r['temporal_pearson']:.6f} | {r['temporal_log10_pearson']:.6f} | {'YES' if r['peak_timestamp_changed'] else 'NO'} |")
    lines += ["",f"Shielding ranking changed: **{'YES' if diag['ranking_changed'] else 'NO'}**.",f"Any peak timestamp changed: **{'YES' if diag['peak_timestamp_changed'] else 'NO'}**.",
      f"Worst change in p99/median or max/median excursion metric: **{100*diag['worst_excursion_metric_absolute_relative_difference']:.2f}%**.","",
      "## Energy decomposition","","Fractions are fractions of total expected flips over common valid 5-minute intervals.","","| Al mm | model | 0-3 MeV | 3-20 MeV | >20 MeV |","|---:|---|---:|---:|---:|"]
    d={(r['shield_mm'],r['sigma_model'],r['energy_band_mev']):r for r in er}
    for mm in sorted({r['shield_mm'] for r in er}):
        for m in (REF,PHYS):
            f=[d[(mm,m,b)]['fraction_of_total_expected_flips'] for b,_,_ in BANDS]
            lines.append(f"| {mm:g} | {m} | {100*f[0]:.3f}% | {100*f[1]:.3f}% | {100*f[2]:.3f}% |")
    lines += ["","Paper Table IV sanity context only (ISS + 100 mil Al, Cypress): Exp/RPP = 1.89e-6/2.11e-6 (0-3), 2.34e-8/7.64e-9 (3-20), 2.22e-7/2.08e-7 (>20), total 2.14e-6/2.33e-6 SEU/bit/day.","",
      "## Validation","",f"Reference reconstruction max rel error: `{val['reference_reconstruction_max_rel']:.3e}`",f"Band closure ref: `{val['energy_partition_max_rel_ref']:.3e}`",f"Band closure physics: `{val['energy_partition_max_rel_phys']:.3e}`","",
      "## Disposition","",f"**{code}**","",diag['rule'],"","No T_scrub, sigma_k, ECC/MCU/W or F_A calculation is performed."]
    return "\n".join(lines)+"\n"

def main():
    p=argparse.ArgumentParser(); p.add_argument("--goes-dir",type=Path,required=True); p.add_argument("--transport",type=Path,required=True); p.add_argument("--sigma-csv",type=Path,required=True); p.add_argument("--published-csv",type=Path,required=True); p.add_argument("--out",type=Path,required=True); a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    goes=load_directory(a.goes_dir); R=calc(goes,a.transport,a.sigma_csv,a.published_csv); rows,ch,orders=compare(goes,R); er=energy_rows(R); code,diag=classify(rows,ch)
    write_csv(a.out/"sigma_model_comparison.csv",rows); write_csv(a.out/"energy_contribution_comparison.csv",er)
    V={"task_id":"RE-GOES19-PROTON-RATE-01-SIGMA-CLOSURE","starting_commit":"e2370c1ad2bb5e640efe5af549e0944ac1a16aa0","models":[REF,PHYS],"goes_radar_pipeline_changed":False,"reference_low_spectrum_gamma":LOW_EXTRAP_REFERENCE_GAMMA,"published_source_doi":"10.1109/TNS.2021.3061209","published_model_uncertainty":"average +/-35% stated by publication; digitization error separate","numeric_validation":R["validation"],"ranking_orders":orders,"disposition":code,"disposition_diagnostics":diag}
    (a.out/"validation_sigma_closure.json").write_text(json.dumps(V,indent=2),encoding="utf-8"); (a.out/"REPORT_SIGMA_CLOSURE.md").write_text(make_report(rows,er,R["validation"],code,diag),encoding="utf-8")
    print(json.dumps({"disposition":code,"diagnostics":diag,"rows":rows},indent=2))
if __name__=="__main__": main()

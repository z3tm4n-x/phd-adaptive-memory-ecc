#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from collections import defaultdict
from decimal import Decimal as D,getcontext
from pathlib import Path

def read(p):
    with Path(p).open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def write(p,rows):
    rows=list(rows);fields=sorted({k for r in rows for k in r}) if rows else []
    with Path(p).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def union_components(xs):
    xs=sorted((D(a),D(b)) for a,b in xs if D(b)>D(a));out=[]
    for a,b in xs:
        if out and out[-1][1]==a:out[-1]=(out[-1][0],b)
        else:out.append((a,b))
    return out

def width(xs):return sum((b-a for a,b in xs),D(0))

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--dir",required=True);a=ap.parse_args();getcontext().prec=80;d=Path(a.dir)
    rc=read(d/"resource_comparison.csv");pts=read(d/"policy_points.csv");base=read(d/"baseline_actions.csv")
    pre={(r["shield"],r["epsilon"]):r for r in base if r["comparator"]=="Precomputed"}
    pg=defaultdict(list)
    for r in pts:pg[(r["label"],r["shield"],r["epsilon"],r["kind"],r.get("L_s",""),r["g_point"])].append(r)
    app=[];g1=[];groups=defaultdict(list)
    for r in rc:groups[(r["label"],r["shield"],r["epsilon"],r["L_s"])].append(r)
    for key,rows in sorted(groups.items()):
        label,shield,eps,L=key;replay=rows[0]["replay_g_min"];ps=pre[(shield,eps)];sav=[];gain=[];boundary=[]
        for r in rows:
            lo=D(r["g_lo_open"]);hi=D(r["g_hi_open"])
            if hi<=lo or r.get("replay_compatible")!="1":continue
            if r["coverage_status"]=="BOUNDARY-ENCLOSURE":boundary.append((lo,hi));continue
            if ps["status"]=="CERTIFIED" and r["delayed_status"]=="CERTIFIED" and r["pre_minus_delayed_passes"]!="" and int(r["pre_minus_delayed_passes"])>0:sav.append((lo,hi))
            if ps["status"]!="CERTIFIED" and r["delayed_status"]=="CERTIFIED":gain.append((lo,hi))
        savu=union_components(sav);gainu=union_components(gain);bu=union_components(boundary)
        app.append({"label":label,"reference_semantics":"COMPATIBLE-COMPLETION-STRESS" if label=="EARLIEST_INVALID" else "EXACT-REFERENCE-REPLAY",
            "shield":shield,"epsilon":eps,"L_s":L,"replay_g_min":replay,"precomputed_status":ps["status"],
            "positive_saving_resolved_component_count":len(savu),"positive_saving_resolved_total_g_width":str(width(savu)),
            "certifiability_gain_resolved_component_count":len(gainu),"certifiability_gain_resolved_total_g_width":str(width(gainu)),
            # Legacy CSV keys retained for byte-compatible reproduction.
            # Display labels (MINOR-R2-01 closeout):
            # boundary_enclosure_components_selected_by_representative_compatibility;
            # boundary_enclosure_total_g_width_selected_by_representative_compatibility.
            # Whole bands are selected by their representative replay_compatible flag.
            # These are NOT component counts/widths of the geometric intersection
            # with [g_min_exact, 1]; a threshold-straddling band is not clipped.
            "verified_boundary_enclosure_component_count_in_replay_domain":len(bu),"verified_boundary_enclosure_total_g_width_in_replay_domain":str(width(bu)),
            "saving_exists_for_some_replay_compatible_g":int(bool(savu)),"certifiability_gain_exists_for_some_replay_compatible_g":int(bool(gainu))})
        dk=(label,shield,eps,"Delayed",L,"1");ik=(label,shield,eps,"Ideal","","1")
        if dk not in pg or ik not in pg:raise RuntimeError(f"missing exact g=1 point {key}")
        dr=pg[dk][0];ir=pg[ik][0]
        if label!="EARLIEST_INVALID" and ps["status"]=="CERTIFIED" and dr["status"]=="CERTIFIED" and ir["status"]=="CERTIFIED":
            pp=int(ps["passes"]);dp=int(dr["passes"]);ip=int(ir["passes"]);den=pp-ip
            g1.append({"label":label,"shield":shield,"epsilon":eps,"L_s":L,"precomputed_passes":pp,"delayed_passes":dp,"ideal_passes":ip,
                "pre_minus_delayed_passes":pp-dp,"delayed_minus_ideal_passes":dp-ip,"retention":str(D(pp-dp)/D(den)) if den>0 else ""})
    write(d/"applicability_resource_summary.csv",app);write(d/"g1_endpoint_summary.csv",g1)
    exact=[r for r in app if r["reference_semantics"]=="EXACT-REFERENCE-REPLAY" and r["precomputed_status"]=="CERTIFIED"]
    stress=[r for r in app if r["reference_semantics"]=="COMPATIBLE-COMPLETION-STRESS" and r["precomputed_status"]=="CERTIFIED"]
    counts={}
    for L in ("0","300","900","1800"):
        ex=[r for r in exact if r["L_s"]==L];st=[r for r in stress if r["L_s"]==L]
        counts[L]={"complete_reference_some_saving":sum(int(r["saving_exists_for_some_replay_compatible_g"]) for r in ex),"complete_reference_denominator":len(ex),
            "missing_reference_stress_some_saving":sum(int(r["saving_exists_for_some_replay_compatible_g"]) for r in st),"missing_reference_stress_denominator":len(st)}
    print(json.dumps({"status":"PASS","applicability_rows":len(app),"g1_rows":len(g1),"counts":counts},sort_keys=True))
if __name__=="__main__":main()

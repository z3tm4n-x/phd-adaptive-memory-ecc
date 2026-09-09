#!/usr/bin/env python3
"""Build the aligned actuation-resource comparison from frozen policy-region maps."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
import pandas as pd

def findrow(gdf,mid):
    m=gdf[(gdf.g_lo_open < mid)&(mid < gdf.g_hi_open)]
    if m.empty:m=gdf[(gdf.g_lo_open <= mid+1e-12)&(mid <= gdf.g_hi_open+1e-12)]
    return None if m.empty else m.iloc[0]

def merge_sig(rows):
    out=[]
    for row,sig in rows:
        if out and out[-1][1]==sig and abs(out[-1][0]["g_hi_open"]-row["g_lo_open"])<3e-10:
            out[-1][0]["g_hi_open"]=row["g_hi_open"]
        else:out.append([row,sig])
    return [r for r,_ in out]

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",required=True);ap.add_argument("--dir",required=True)
    a=ap.parse_args();cfg=json.loads(Path(a.config).read_text());d=Path(a.dir)
    pr=pd.read_csv(d/"policy_regions.csv");base=pd.read_csv(d/"baseline_actions.csv")
    P=float(cfg["restoration"]["full_pass_duration_s"])
    premap={(r.shield,float(r.epsilon)):r for _,r in base[base.comparator=="Precomputed"].iterrows()}
    delayed=pr[pr.kind=="Delayed"];ideal=pr[pr.kind=="Ideal"];out=[]
    for key,dg in delayed.groupby(["label","shield","epsilon","L_s"],dropna=False):
        label,shield,eps,L=key
        ig=ideal[(ideal.label==label)&(ideal.shield==shield)&np.isclose(ideal.epsilon,eps)]
        if ig.empty:raise RuntimeError(f"missing Ideal regions {key}")
        pts=set(dg.g_lo_open.tolist()+dg.g_hi_open.tolist()+ig.g_lo_open.tolist()+ig.g_hi_open.tolist())
        replay=float(dg.replay_g_min.iloc[0]);pts.update([0.,1.,replay]);pts=sorted(x for x in pts if 0<=x<=1)
        pre=premap[(shield,float(eps))];tmp=[]
        for lo,hi in zip(pts[:-1],pts[1:]):
            if hi-lo<2e-12:continue
            mid=(lo+hi)/2;dr=findrow(dg,mid);ir=findrow(ig,mid)
            if dr is None or ir is None:continue
            exact=int(ir.ideal_exact_replay_available) if not pd.isna(ir.ideal_exact_replay_available) else 0
            row={"label":label,"shield":shield,"epsilon":eps,"L_s":int(L),
              "g_lo_open":lo,"g_hi_open":hi,"g_rep":mid,"replay_g_min":replay,"replay_compatible":int(mid>=replay),
              "precomputed_status":pre.status,"precomputed_passes":pre.passes if pre.status=="CERTIFIED" else np.nan,
              "delayed_status":dr.status,"delayed_passes":dr.passes,
              "ideal_status":ir.status,"ideal_passes":ir.passes,"ideal_exact_replay_available":exact,
              "pre_minus_delayed_passes":np.nan,"delayed_minus_ideal_passes":np.nan,"retention":np.nan,
              "pre_minus_delayed_occupied_s":np.nan,"pre_minus_delayed_occupancy_pp":np.nan,
              "delayed_minus_ideal_occupied_s":np.nan,"delayed_minus_ideal_occupancy_pp":np.nan}
            if pre.status=="CERTIFIED" and dr.status=="CERTIFIED":
                q=int(pre.passes)-int(dr.passes);row["pre_minus_delayed_passes"]=q
                row["pre_minus_delayed_occupied_s"]=q*P;row["pre_minus_delayed_occupancy_pp"]=q*P/6
            if exact and dr.status=="CERTIFIED" and ir.status=="CERTIFIED":
                q=int(dr.passes)-int(ir.passes);row["delayed_minus_ideal_passes"]=q
                row["delayed_minus_ideal_occupied_s"]=q*P;row["delayed_minus_ideal_occupancy_pp"]=q*P/6
            if exact and pre.status=="CERTIFIED" and dr.status=="CERTIFIED" and ir.status=="CERTIFIED":
                den=int(pre.passes)-int(ir.passes)
                if den>0:row["retention"]=(int(pre.passes)-int(dr.passes))/den
            sig=tuple("NA" if (isinstance(row[k],float) and math.isnan(row[k])) else row[k]
                      for k in ("replay_compatible","precomputed_status","precomputed_passes","delayed_status",
                                "delayed_passes","ideal_status","ideal_passes","retention"))
            tmp.append((row,sig))
        out.extend(merge_sig(tmp))
    pd.DataFrame(out).to_csv(d/"resource_comparison.csv",index=False)
    print(f"PASS resource regions={len(out)}")
if __name__=="__main__":main()

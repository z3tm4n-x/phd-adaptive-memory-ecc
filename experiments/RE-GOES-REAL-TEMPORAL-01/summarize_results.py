#!/usr/bin/env python3
from __future__ import annotations
import argparse, math
from pathlib import Path
import pandas as pd
import numpy as np


def fmt_interval(lo, hi):
    return f"({lo:.12g},{hi:.12g})"

def merge_intervals(rows):
    if not rows: return ""
    rows=sorted(rows)
    out=[]
    for lo,hi in rows:
        if out and abs(out[-1][1]-lo)<3e-10:
            out[-1]=(out[-1][0],hi)
        else: out.append((lo,hi))
    return "|".join(fmt_interval(lo,hi) for lo,hi in out)

def endpoint_row(gdf):
    # Region signature immediately below g=1; focused tests independently verify
    # the selected g=1 limiting contract, so this is a reporting projection only.
    return gdf.sort_values(["g_hi_open","g_lo_open"]).iloc[-1]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dir",required=True)
    a=ap.parse_args(); d=Path(a.dir)
    comp=pd.read_csv(d/"resource_comparison.csv")
    base=pd.read_csv(d/"baseline_actions.csv")

    app=[]; g1=[]
    for (label,shield,eps,L),g in comp.groupby(["label","shield","epsilon","L_s"],dropna=False):
        replay=float(g.replay_g_min.iloc[0])
        pre_status=str(g.precomputed_status.iloc[0])
        sav=[]; gain=[]
        for _,r in g.iterrows():
            lo=max(float(r.g_lo_open), replay); hi=float(r.g_hi_open)
            if hi <= lo+1e-14: continue
            if pre_status=="CERTIFIED" and r.delayed_status=="CERTIFIED" and not pd.isna(r.pre_minus_delayed_passes) and float(r.pre_minus_delayed_passes)>0:
                sav.append((lo,hi))
            if pre_status!="CERTIFIED" and r.delayed_status=="CERTIFIED":
                gain.append((lo,hi))
        er=endpoint_row(g)
        row={
          "label":label,"shield":shield,"epsilon":eps,"L_s":int(L),"replay_g_min":replay,
          "precomputed_status":pre_status,
          "positive_saving_open_intervals":merge_intervals(sav),
          "certifiability_gain_open_intervals":merge_intervals(gain),
          "saving_exists_for_some_replay_compatible_g":int(bool(sav)),
          "certifiability_gain_exists_for_some_replay_compatible_g":int(bool(gain)),
          "g1_delayed_status":er.delayed_status,
          "g1_pre_minus_delayed_passes":"" if pd.isna(er.pre_minus_delayed_passes) else int(er.pre_minus_delayed_passes),
          "g1_delayed_passes":"" if pd.isna(er.delayed_passes) else int(er.delayed_passes),
          "g1_ideal_passes":"" if pd.isna(er.ideal_passes) or int(er.ideal_exact_replay_available)!=1 else int(er.ideal_passes),
          "g1_retention":"" if pd.isna(er.retention) else float(er.retention),
        }
        app.append(row)
        if pre_status=="CERTIFIED" and int(er.ideal_exact_replay_available)==1:
            g1.append({
              "label":label,"shield":shield,"epsilon":eps,"L_s":int(L),
              "precomputed_passes":int(er.precomputed_passes),"delayed_passes":int(er.delayed_passes),"ideal_passes":int(er.ideal_passes),
              "pre_minus_delayed_passes":int(er.pre_minus_delayed_passes),
              "pre_minus_delayed_occupied_s":float(er.pre_minus_delayed_occupied_s),
              "pre_minus_delayed_occupancy_pp":float(er.pre_minus_delayed_occupancy_pp),
              "delayed_minus_ideal_passes":int(er.delayed_minus_ideal_passes),
              "retention":"" if pd.isna(er.retention) else float(er.retention),
            })
    pd.DataFrame(app).sort_values(["label","shield","epsilon","L_s"]).to_csv(d/"applicability_resource_summary.csv",index=False)
    pd.DataFrame(g1).sort_values(["label","shield","epsilon","L_s"]).to_csv(d/"g1_endpoint_summary.csv",index=False)
    print(f"PASS applicability rows={len(app)} g1 rows={len(g1)}")
if __name__=="__main__": main()

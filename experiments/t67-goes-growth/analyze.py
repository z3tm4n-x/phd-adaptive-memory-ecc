"""Native-bin analysis of every episode in the frozen manifest (no fitting)."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import io
import json
import platform
from pathlib import Path
import numpy as np
import archive
import growth
import selection
import sgps
from response import Response, PINNED, REPO

HERE = Path(__file__).resolve().parent


def iso(t):
    return datetime.fromtimestamp(float(t), timezone.utc).isoformat()


def stamp(s):
    return selection.dt(s).timestamp()


def write_csv(path, rows):
    rows = list(rows)
    keys = list(dict.fromkeys(k for row in rows for k in row))
    if str(path).endswith(".gz"):
        raw = Path(path).open("wb")
        stream = io.TextIOWrapper(gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0), newline="")
    else:
        raw = None
        stream = Path(path).open("w", newline="")
    with stream:
        writer = csv.DictWriter(stream, keys)
        writer.writeheader()
        writer.writerows(rows)
    if raw:
        raw.close()


def coverage(inv):
    rows, holes = [], []
    for sat in (16, 18, 19):
        for cad in (60, 300):
            all_rows = [r for r in inv["files"] if r["satellite"] == sat and r["cadence_s"] == cad]
            days = sorted({r["date"] for r in all_rows if r["selected_version"]})
            if not days:
                continue
            first, last = [datetime.strptime(s, "%Y%m%d") for s in (days[0], days[-1])]
            have = set(days)
            missing = [(first+timedelta(days=i)).strftime("%Y%m%d") for i in range((last-first).days+1)
                       if (first+timedelta(days=i)).strftime("%Y%m%d") not in have]
            rows.append({"satellite": sat, "cadence_s": cad, "first_day": days[0], "last_day": days[-1],
                         "daily_files_all_versions": len(all_rows), "unique_days": len(days), "missing_internal_days": len(missing)})
            holes.extend({"satellite":sat, "cadence_s":cad, "missing_day":s} for s in missing)
    rows.append({"satellite":16,"cadence_s":300,"first_day":"20170901","last_day":"20170930",
                 "daily_files_all_versions":1,"unique_days":30,"missing_internal_days":0,"note":"special monthly reprocessed product; 1-minute unavailable"})
    return rows, holes


def prepare_group(rows, cache, response):
    pieces, audits, signatures = [], [], {}
    for idx, row in enumerate(sorted(rows, key=lambda x:x["date"])):
        path = cache / row["name"]
        if archive.sha256(path) != row["sha256"]:
            raise ValueError("Source checksum mismatch: " + row["name"])
        src = sgps.read(path)
        model = response.calculate(src)
        key = src.signature
        if key not in signatures:
            signatures[key] = len(signatures)
        signature = signatures[key]*3 + np.nan_to_num(src.yaw, nan=1).astype(int)
        a = {"time":src.time,"signature":signature,"file_index":np.full(len(src.time),idx),
             "flux":src.flux,"flux_screened":src.screened,"flux_strict":src.strict}
        a.update({k:v for k,v in model.items() if isinstance(v,np.ndarray)})
        pieces.append(a)
        audits.append({**src.audit,"url":row["url"],"gap_diagnostics":model["gap_diagnostics"]})
    out = {k:np.concatenate([p[k] for p in pieces]) for k in pieces[0]}
    order = np.argsort(out["time"])
    out = {k:v[order] for k,v in out.items()}
    if np.any(np.diff(out["time"]) <= 0):
        raise ValueError("Duplicate or reversed bins within satellite/cadence")
    return out, audits


def series(group):
    for c,name in enumerate(sgps.CHANNELS):
        yield name, "measured_flux", group["flux"][:,:,c], {
            "reported":np.isfinite(group["flux"][:,:,c]),
            "screened":group["flux_screened"][:,:,c],
            "strict":group["flux_strict"][:,:,c]}
    for name in ("main_loglog", "linear_energy", "gap_linear_5_40", "low_hold", "core_only"):
        masks = {"reported":np.isfinite(group[name]),"screened":group["screened"]}
        if name == "main_loglog":
            masks["strict"] = group["strict"]
        elif name == "core_only":
            masks["strict"] = group["core_strict"]
        yield name,"model_inversions_s-1",group[name],masks


def main(manifest, inv, cache, out):
    out.mkdir(parents=True, exist_ok=True)
    config=json.loads((HERE/"config.json").read_text())
    archive_rows, holes=coverage(inv)
    write_csv(out/"archive_coverage.csv", archive_rows)
    write_csv(out/"archive_missing_days.csv", holes)
    # Small textual index ledger plus all filenames preserves version availability.
    (out/"archive_indexes.json").write_text(json.dumps(inv["indexes"],indent=2)+"\n")
    write_csv(out/"archive_files.csv.gz", inv["files"])
    (out/"source_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    response=Response()
    metrics, summaries, crossings, audits, union_rows, availability = [], [], [], [], [], []
    plot_cache=cache.parent/"series"
    plot_cache.mkdir(exist_ok=True)
    for sat in config["satellites"]:
        for cad in (60,300):
            files=[r for r in manifest["files"] if r["satellite"]==sat and r["cadence_s"]==cad]
            if not files:
                continue
            print(json.dumps({"stage":"parse", "satellite":sat,"cadence_s":cad,"files":len(files)}),flush=True)
            group,meta=prepare_group(files,cache,response)
            audits.extend(meta)
            t,sig=group["time"],group["signature"]
            np.savez_compressed(plot_cache/f"g{sat}_{cad}.npz",**group)
            union=np.zeros(len(t),bool)
            for event in manifest["events"]:
                a,b=stamp(event["analysis_start"]),stamp(event["analysis_end_exclusive"])
                union |= (t>=a)&(t<b)
            for direction,d in (("E",0),("W",1)):
                for mask in ("reported","screened","strict"):
                    v=union & (np.isfinite(group["main_loglog"][:,d]) if mask=="reported" else group[mask][:,d])
                    union_rows.append({"satellite":sat,"cadence_s":cad,"direction":direction,"mask":mask,
                                       "unique_retained_s":int(np.sum(v)*cad),"sum_model_inversions":float(np.sum(group["main_loglog"][v,d])*cad),
                                       "peak_model_s-1":float(np.max(group["main_loglog"][v,d])) if np.any(v) else None})
            for event in manifest["events"]:
                a,b=stamp(event["analysis_start"]),stamp(event["analysis_end_exclusive"])
                bg0=stamp(event["background_start"])
                m=(t>=a)&(t<b)
                bgm=(t>=bg0)&(t<a)
                expected=int(np.ceil(b/cad)-np.ceil(a/cad))
                expected_bg=int(np.ceil(a/cad)-np.ceil(bg0/cad))
                availability.append({"event_id":event["id"],"satellite":sat,"cadence_s":cad,
                                     "analysis_start":event["analysis_start"],"analysis_end_exclusive":event["analysis_end_exclusive"],
                                     "native_bins_present":int(np.sum(m)),"expected_bins_in_window":expected,
                                     "status":"available" if np.any(m) else "no_archive_at_event"})
                if not np.any(m):
                    continue
                et,es=t[m],sig[m]
                for name,quantity,values,masks in series(group):
                    # Alternate sigma models: the screened mask is the declared
                    # sensitivity comparison; all three masks for primary/flux.
                    for mask,valid in masks.items():
                        if name in response.models[1:] and mask!="screened":
                            continue
                        for d,direction in enumerate(("E","W")):
                            x,v=values[m,d],valid[m,d]&np.isfinite(values[m,d])
                            bg_valid=bgm&valid[:,d]&np.isfinite(values[:,d])
                            bg_count=int(np.sum(bg_valid))
                            bg=float(np.quantile(values[bg_valid,d],config["background_quantile"])) if bg_count>=expected_bg*config["background_min_coverage"] and bg_count else None
                            base={"event_id":event["id"],"holdout":event["holdout"],"satellite":sat,"cadence_s":cad,
                                  "direction":direction,"series":name,"quantity":quantity,"mask":mask}
                            summary={**base,"retained_bins":int(np.sum(v)),"expected_bins":expected,"background_bins":bg_count,
                                     "background":bg,"background_signature_count":len(set(sig[bg_valid].tolist())),
                                     "peak":float(np.max(x[v])) if np.any(v) else None,
                                     "peak_start_utc":iso(et[np.flatnonzero(v)[np.argmax(x[v])]]) if np.any(v) else None,
                                     "bin_integral":float(np.sum(x[v])*cad),
                                     "integral_units":"inversions" if quantity.startswith("model") else ("protons/(cm2 sr)" if name=="P11" else "protons/(cm2 sr MeV)")}
                            summaries.append(summary)
                            if not np.any(v):
                                continue
                            levels=[]
                            if bg is not None and bg>0:
                                levels += [(f"{k}bg",k*bg) for k in config["background_multipliers"]]
                            if quantity.startswith("model"):
                                levels += [(f"abs_{level:g}",level) for level in config["absolute_rate_levels_s-1"]]
                            for label,level in levels:
                                metric={**base,"level_label":label,"level":level}
                                ef=growth.fastest_e_fold(et,x,v,es,cad,level)
                                metric["e_completed_starts"]=ef["completed_starts"]
                                if ef["fastest"]:
                                    elapsed,i,j=ef["fastest"]
                                    metric.update({"e_min_s":elapsed,"e_start_utc":iso(et[i]),"e_end_utc":iso(et[j]),
                                                   "e_start_value":float(x[i]),"e_end_value":float(x[j]),
                                                   "e_bin_integral":float(np.sum(x[i:j])*cad)})
                                for lag in config["windows_s"]:
                                    ext=growth.window_extreme(et,x,v,es,cad,lag,level)
                                    metric[f"pairs_{lag}"]=ext["pairs"]
                                    for kind in ("h","log"):
                                        if ext.get(kind):
                                            rate,i,j=ext[kind]
                                            metric.update({f"{kind}_{lag}_s-1":rate,f"{kind}_{lag}_start":iso(et[i]),
                                                           f"{kind}_{lag}_end":iso(et[j]),f"{kind}_{lag}_x0":float(x[i]),f"{kind}_{lag}_x1":float(x[j])})
                                metrics.append(metric)
                            if name in ("main_loglog","core_only"):
                                for low,high in ((.001,.01),(.01,.1),(.001,.1)):
                                    for cr in growth.transitions(et,x,v,es,cad,low,high):
                                        i,j=cr.pop("start_index"),cr.pop("end_index")
                                        startbr,endbr=cr.pop("start_bracket"),cr.pop("end_bracket")
                                        crossings.append({**base,"low_s-1":low,"high_s-1":high,**cr,
                                                          "start_utc":iso(et[i]),"end_utc":iso(et[j]),"start_value":float(x[i]),"end_value":float(x[j]),
                                                          "previous_start_bin_utc":iso(startbr[0]),"previous_end_bin_utc":iso(endbr[0])})
                print(json.dumps({"stage":"event", "id":event["id"],"satellite":sat,"cadence_s":cad,"metrics":len(metrics)}),flush=True)
    write_csv(out/"episode_availability.csv",availability)
    write_csv(out/"series_summary.csv.gz",summaries)
    write_csv(out/"growth_metrics.csv.gz",metrics)
    write_csv(out/"transitions.csv",crossings)
    write_csv(out/"selected_union.csv",union_rows)
    (out/"file_audits.json.gz").write_bytes(gzip.compress((json.dumps(audits,ensure_ascii=False,sort_keys=True)+"\n").encode(),mtime=0))
    # Compact maximum table for every fixed absolute threshold, separate holdout.
    envelopes=[]
    for holdout in (False,True):
        for cad in (60,300):
            for mask in ("reported","screened","strict"):
                for level in config["absolute_rate_levels_s-1"]:
                    candidates=[r for r in metrics if r["holdout"]==holdout and r["cadence_s"]==cad and r["mask"]==mask and r["series"]=="main_loglog" and r["level_label"]==f"abs_{level:g}"]
                    for lag in config["windows_s"]:
                        key=f"h_{lag}_s-1"
                        found=[r for r in candidates if r.get(key) is not None]
                        if not found:
                            continue
                        r=max(found,key=lambda x:x[key])
                        envelopes.append({"holdout":holdout,"cadence_s":cad,"mask":mask,"level_s-1":level,"window_s":lag,
                                          "rho_observed_s-1":r[key],"event_id":r["event_id"],"satellite":r["satellite"],"direction":r["direction"],
                                          "start_utc":r[f"h_{lag}_start"],"end_utc":r[f"h_{lag}_end"],"start_value_s-1":r[f"h_{lag}_x0"],"end_value_s-1":r[f"h_{lag}_x1"]})
    write_csv(out/"rho_candidates.csv",envelopes)
    runtime={"python":platform.python_version(),"numpy":np.__version__,"config_sha256":archive.sha256(HERE/"config.json"),
             "upstream":{str(p.relative_to(REPO)):h for p,h in PINNED.items()},
             "events":len(manifest["events"]),"files":len(manifest["files"]),"metrics_rows":len(metrics),"crossings":len(crossings),
             "guaranteed_future_coverage":None,"confidence_level":None,"raw_temporal_interpolation":False}
    (out/"provenance.json").write_text(json.dumps(runtime,indent=2)+"\n")
    print(json.dumps(runtime),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--inventory",type=Path,required=True)
    p.add_argument("--cache",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    main(json.loads(a.manifest.read_text()),json.loads(a.inventory.read_text()),a.cache,a.out)

"""T188: frozen-input availability/format audit, never an SEP detection analysis."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import re
import statistics
import sys
import urllib.request
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def stamp(value):
    # Naive GRAINS / HIS times stay naive: no silent assignment of UTC.
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def timing(times):
    delta = [(b-a).total_seconds() for a, b in zip(times, times[1:])]
    positive = [d for d in delta if d > 0]
    med = statistics.median(positive) if positive else None
    largest = sorted(zip(delta, times, times[1:]), key=lambda x: x[0], reverse=True)[:3]
    return {
        "first": times[0].isoformat(), "last": times[-1].isoformat(),
        "rows": len(times), "duplicate_timestamps": len(times)-len(set(times)),
        "backward_steps": sum(d < 0 for d in delta),
        "positive_delta_min_s": min(positive) if positive else None,
        "positive_delta_median_s": med,
        "positive_delta_max_s": max(positive) if positive else None,
        "steps_gt_1_5_median": sum(d > 1.5*med for d in positive) if med else 0,
        "largest_steps": [{"seconds": d, "from": a.isoformat(), "to": b.isoformat()} for d,a,b in largest],
        "gap_rule_caveat": "Descriptive cadence discontinuities only; not a live-time/exposure estimate.",
    }


def parse_grains(raw):
    lines = raw.decode("utf-8-sig").splitlines()
    index = next(i for i,l in enumerate(lines) if l.startswith("# DATE TIME"))
    delimiter = "\t" if "\t" in lines[index] else ","
    headings = next(csv.reader([lines[index]], delimiter=delimiter))
    names = [x.strip().split(" - ")[0] for x in headings[1:]]
    rows = list(csv.reader(lines[index+1:], delimiter=delimiter))
    if any(len(row) != len(names)+1 for row in rows):
        raise ValueError("Unexpected GRAINS row width")
    times = [stamp(row[0]) for row in rows]
    values = [[float(x) if x.strip() else None for x in row[1:]] for row in rows]
    return lines, index, names, times, values


def audit_grains(raw):
    lines, index, names, times, values = parse_grains(raw)
    stats = timing(times)
    stats["time_scale"] = "UNKNOWN: DATE TIME without timezone; retain verbatim"
    declared_line = next(i for i,l in enumerate(lines) if l.startswith("# Number of samples"))
    stats["declared_sample_counts"] = [int(x) for x in re.split(r"[,\t]",lines[declared_line+1])]
    stats["columns"] = {}
    for i,name in enumerate(names):
        col = [r[i] for r in values]
        finite = [x for x in col if x is not None]
        pairs = [(a,b) for a,b in zip(col,col[1:]) if a is not None and b is not None]
        observed = [(j,x) for j,x in enumerate(col) if x is not None]
        drops = [{"from":times[j].isoformat(),"to":times[k].isoformat(),"before":a,"after":b,
                  "intervening_missing_rows":k-j-1}
                 for (j,a),(k,b) in zip(observed,observed[1:]) if b<a]
        stats["columns"][name] = {
            "missing": sum(x is None for x in col),
            "minimum": min(finite) if finite else None,
            "maximum": max(finite) if finite else None,
            "first": col[0], "last": col[-1],
            "decreasing_transitions": sum(b < a for a,b in pairs),
            "decreases_between_successive_observed_values":drops,
        }
    # Headers plus first 10 physical records; no reordering, deduplication or interpolation.
    sample = "\n".join(lines[:index+11]) + "\n"
    return stats, sample


HIS_TIME = re.compile(r"\(Time (\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}) \[(\d+), (\d+)\]\)")


def audit_his(raw):
    lines = raw.decode().splitlines()
    matches = [HIS_TIME.search(l) for l in lines]
    if not all(matches):
        raise ValueError("Unparsed HIS message")
    times = [datetime.strptime(m[1], "%Y/%m/%d-%H:%M:%S") for m in matches]
    def family(line):
        if "EVENT: 43915:" in line:
            return "43915_CDH_FPGA_SRAM_BRAM_" + ("FSW" if "source was FSW" in line else "FPGA")
        if "EVENT: 43904:" in line:
            return "43904_" + ("SRAM" if "HIS: SRAM" in line else "OTHER")
        raise ValueError("Unknown HIS event type")
    unique = list(dict.fromkeys(lines))
    stats = timing(times)
    stats.update({
        "time_scale": "UNKNOWN; printed seconds are not established UTC",
        "unique_exact_lines": len(unique), "exact_duplicate_extra_lines": len(lines)-len(unique),
        "raw_families": dict(Counter(map(family,lines))),
        "unique_line_families": dict(Counter(map(family,unique))),
        "printed_count_not_one_lines": [i+1 for i,l in enumerate(lines) if "Correctable 2 Errors" in l],
        "all_coarse_fields_equal_naive_seconds_since_2000": all(
            int(m[2]) == int((t-datetime(2000,1,1)).total_seconds()) for t,m in zip(times,matches)),
        "warning": "Line identity is not physical event identity. No deduplication or summation performed; OTHER and CDH may overlap. Coarse-field equality does not establish UTC, fine-time divisor or clock accuracy.",
    })
    return stats, "\n".join(lines[:10])+"\n"


def audit_hapi(raw):
    lines = raw.decode().splitlines()
    info = json.loads(lines[0].lstrip("#"))
    assert info["status"]["code"] == 1200
    assert [p["name"] for p in info["parameters"]] == ["Time", "vex_ima_bg", "vex_ima_totct"]
    assert info["parameters"][0]["units"] == "UTC"
    rows = list(csv.reader(l for l in lines[1:] if l.strip()))
    if any(len(r) != 3 for r in rows):
        raise ValueError("Unexpected HAPI row width")
    stats = timing([stamp(r[0]) for r in rows])
    stats["time_scale"] = "UTC (HAPI); interval timestamp phase UNKNOWN"
    stats["columns"] = {}
    for i,p in enumerate(info["parameters"][1:],1):
        stats["columns"][p["name"]] = {"units": p["units"], "fill": p["fill"],
                                      "fill_rows": sum(float(r[i])==float(p["fill"]) for r in rows)}
    return stats, "\n".join(lines[:11])+"\n"


def audit_epd(path, samples, vendor):
    if vendor:
        sys.path.insert(0,str(vendor))
    import numpy as np
    import cdflib
    c = cdflib.CDF(path)
    variables = ["EPOCH", "DELTA_EPOCH", "H_Rate", "H_Flux", "H_Bins_Low_Energy", "H_Bins_Width", "H_Bins_Text", "QUALITY_FLAG", "QUALITY_BITMASK"]
    attrs = {v:c.varattsget(v) for v in variables}
    assert c.varinq("EPOCH").Data_Type_Description == "CDF_TIME_TT2000"
    assert attrs["H_Rate"]["DEPEND_0"] == "EPOCH"
    assert attrs["H_Rate"]["UNITS"] == "counts / s"
    assert "Start of acquisition interval" in attrs["EPOCH"]["VAR_NOTES"]
    assert attrs["DELTA_EPOCH"]["UNITS"] == "seconds"
    epoch = c.varget("EPOCH")
    utc = cdflib.cdfepoch.to_datetime(epoch)
    delta = c.varget("DELTA_EPOCH")
    rates = c.varget("H_Rate")
    quality = c.varget("QUALITY_FLAG")
    bitmask = c.varget("QUALITY_BITMASK")
    bins = c.varget("H_Bins_Text")
    assert rates.shape == (len(epoch), len(bins))
    assert len(epoch) == len(delta) == len(quality) == len(bitmask)
    with (samples/"epd-het-sun-first10.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["epoch_tt2000_ns","utc_start","accumulation_s","quality_flag","quality_bitmask"] + ["H_Rate_counts_per_s_"+b for b in bins])
        for i in range(10):
            w.writerow([int(epoch[i]),str(utc[i])+"Z",int(delta[i]),int(quality[i]),int(bitmask[i])] + [format(float(x),".9g") for x in rates[i]])
    def plain(v):
        if isinstance(v,dict):return {k:plain(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [plain(x) for x in v]
        if isinstance(v,np.ndarray):return plain(v.tolist())
        if isinstance(v,np.generic):return v.item()
        return v
    metadata = {"global":c.globalattsget(), "variables":attrs, "H_Bins_Text":bins}
    write_json(samples/"epd-metadata.json",plain(metadata))
    differences=np.diff(epoch).astype(float)/1e9
    return {"rows":len(epoch), "utc_first":str(utc[0])+"Z", "utc_last":str(utc[-1])+"Z",
            "cadence_min_s":float(differences.min()),"cadence_median_s":float(np.median(differences)),
            "cadence_max_s":float(differences.max()),
            "accumulation_s_counts":dict(Counter(map(str,delta))),
            "quality_flag_counts":dict(Counter(map(str,quality))),
            "quality_bitmask_counts":dict(Counter(map(str,bitmask))),
            "fill_rate_cells":int(np.sum(rates==attrs["H_Rate"]["FILLVAL"])),
            "time_scale":"CDF_TIME_TT2000 converted to UTC using cdflib leap seconds; start of acquisition interval",
            "read_versions":{"cdflib":cdflib.__version__,"numpy":np.__version__},
            "scope":"One pre-event day only; not evidence of quality during the SEP or HIS exposure."}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache",type=Path,default=HERE.parents[1]/".cache"/"t188")
    p.add_argument("--out",type=Path,default=HERE/"audit")
    p.add_argument("--fetch",action="store_true",help="Fetch absent inputs from pinned URLs; never overwrite a changed cache file")
    p.add_argument("--vendor",type=Path,help="Optional directory containing cdflib 1.3.6")
    p.add_argument("--with-epd",action="store_true")
    args=p.parse_args()
    manifest=json.loads((HERE/"inputs.json").read_text(encoding="utf-8"))
    args.cache.mkdir(parents=True,exist_ok=True)
    args.out.mkdir(parents=True,exist_ok=True)
    samples=args.out/"samples"; samples.mkdir(exist_ok=True)
    verified=[]
    for entry in manifest["inputs"]:
        if not entry.get("required_for_audit"):continue
        if entry.get("reader")=="cdf" and not args.with_epd:continue
        path=args.cache/entry["local_name"]
        if not path.exists() and args.fetch:
            req=urllib.request.Request(entry["url"],headers={"User-Agent":"T188-reproducibility-audit/1.0"})
            with urllib.request.urlopen(req,timeout=60) as response:
                data=response.read()
            if sha(data)!=entry["sha256"]:
                raise ValueError("Downloaded input hash mismatch: "+entry["local_name"])
            path.write_bytes(data)
        data=path.read_bytes()
        if sha(data)!=entry["sha256"]:raise ValueError("Cached input hash mismatch: "+entry["local_name"])
        if entry.get("md5") and hashlib.md5(data).hexdigest()!=entry["md5"]:raise ValueError("Publisher MD5 mismatch")
        verified.append(entry["local_name"])
    inventory={"scope":"Availability and format only; no performance / event detection metrics", "files":{}}
    with ZipFile(args.cache/"EDAC.zip") as z:
        inventory["archive_members"]=[{"name":i.filename,"bytes":i.file_size} for i in z.infolist()]
        for name in z.namelist():
            if not name.endswith(".txt") or not ("/Solar Orbiter/" in name or "/VEX/" in name):continue
            raw=z.read(name)
            stats,sample=audit_his(raw) if "SOHIS" in name else audit_grains(raw)
            stats.update({"sha256":sha(raw),"bytes":len(raw)})
            inventory["files"][name]=stats
            (samples/(Path(name).stem+"_first10.txt")).write_text(sample,encoding="utf-8",newline="\n")
    for name in ["vex-ima-bg-20061201-20061220.csv","vex-ima-bg-20120301-20120323.csv"]:
        raw=(args.cache/name).read_bytes()
        stats,sample=audit_hapi(raw)
        stats.update({"sha256":sha(raw),"bytes":len(raw)})
        inventory["files"][name]=stats
        (samples/(Path(name).stem+"_first10.txt")).write_text(sample,encoding="utf-8",newline="\n")
    if args.with_epd:
        name="solo_L2_epd-het-sun-rates_20220904_V01.cdf"
        inventory["files"][name]=audit_epd(args.cache/name,samples,args.vendor)
    write_json(args.out/"inventory.json",inventory)
    hashes={str(f.relative_to(args.out)).replace("\\","/"):sha(f.read_bytes()) for f in sorted(samples.iterdir()) if f.is_file()}
    hashes["inventory.json"]=sha((args.out/"inventory.json").read_bytes())
    write_json(args.out/"sha256.json",hashes)
    write_json(args.out/"run.json",{"python":platform.python_version(),"platform":platform.platform(),
        "verified_inputs":verified,"reproduce_py_sha256":sha(Path(__file__).read_bytes()),
        "inputs_json_sha256":sha((HERE/"inputs.json").read_bytes()),
        "with_epd":args.with_epd,"utc_run":datetime.now(timezone.utc).isoformat()})
    print(json.dumps({"verified_inputs":len(verified),"audited_series":len(inventory["files"]),"out":str(args.out)},ensure_ascii=False))


if __name__=="__main__":
    main()

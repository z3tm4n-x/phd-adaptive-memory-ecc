"""T197: descriptive VEX2006 comparison; no UTC determination or detector scoring."""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import unittest
import urllib.request
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True,
                               allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_edac(raw):
    lines = raw.decode("utf-8-sig").splitlines()
    header = next(i for i, line in enumerate(lines) if line.startswith("# DATE TIME"))
    sep = "\t" if "\t" in lines[header] else ","
    names = next(csv.reader([lines[header]], delimiter=sep))
    if len(names) != 2 or "NDMW0D0A" not in names[1]:
        raise ValueError("Unexpected EDAC column identity")
    records = []
    for line_number, row in enumerate(csv.reader(lines[header+1:], delimiter=sep), header+2):
        if len(row) != 2:
            raise ValueError(f"EDAC width at line {line_number}")
        t = datetime.fromisoformat(row[0])
        if t.tzinfo is not None:
            raise ValueError("Time-scale contract changed: EDAC must remain naive")
        value = Decimal(row[1]) if row[1].strip() else None
        if value is not None and (not value.is_finite() or value < 0 or value != value.to_integral_value()):
            raise ValueError("Non-integral or invalid counter")
        records.append({"line": line_number, "raw_time": row[0], "raw_value": row[1],
                        "time": t, "value": None if value is None else int(value)})
    return records


def parse_ima(raw):
    lines = raw.decode("utf-8").splitlines()
    meta = json.loads(lines[0].lstrip("#"))
    params = meta["parameters"]
    if (meta["status"]["code"] != 1200 or
        [p["name"] for p in params] != ["Time", "vex_ima_bg", "vex_ima_totct"] or
        params[0]["units"] != "UTC" or params[1]["units"] != "cnts"):
        raise ValueError("IMA metadata contract changed")
    records = []
    for line_number, row in enumerate(csv.reader(lines[1:]), 2):
        if len(row) != 3:
            raise ValueError(f"IMA width at line {line_number}")
        t = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
        if t.utcoffset() != timedelta(0):
            raise ValueError("IMA timestamp is not UTC")
        val = float(row[1])
        if not math.isfinite(val):
            raise ValueError("Nonfinite IMA value")
        fill = val == float(params[1]["fill"])
        if not fill and val < 0:
            raise ValueError("Unspecified negative IMA value")
        records.append({"line": line_number, "raw_time": row[0], "raw_value": row[1],
                        "time": t.replace(tzinfo=None), "value": None if fill else val})
    return records


def check_order(records):
    if any(b["time"] < a["time"] for a, b in zip(records, records[1:])):
        raise ValueError("Backward timestamp; no automatic sorting")


def counter_intervals(records, gap_s):
    check_order(records)
    edges = []
    for a, b in zip(records, records[1:]):
        dt = (b["time"]-a["time"]).total_seconds()
        delta = None if a["value"] is None or b["value"] is None else b["value"]-a["value"]
        if delta is None:
            status = "missing_value"
        elif dt == 0:
            status = "duplicate_same_value" if delta == 0 else "duplicate_conflicting_value"
        elif delta < 0:
            status = "decrease_reset_or_rollover_unknown"
        elif dt > gap_s:
            status = "observation_gap"
        else:
            status = "valid"
        edges.append({"left": a["time"], "right": b["time"], "left_raw": a["raw_time"],
                      "right_raw": b["raw_time"], "left_line": a["line"], "right_line": b["line"],
                      "before": a["value"], "after": b["value"], "delta": delta,
                      "seconds": dt, "status": status})
    return edges


def row_bin(t, boundaries):
    if t < boundaries[0] or t >= boundaries[-1]:
        return None
    return max(0, bisect_left(boundaries, t)-1)


def interval_bins(left, right, boundaries):
    if right <= boundaries[0] or left >= boundaries[-1] or right <= left:
        return range(0)
    first = max(0, bisect_right(boundaries, left)-1)
    last = min(len(boundaries)-2, bisect_left(boundaries, right)-1)
    return range(first, last+1)


def value_stats(values):
    return {"ima_valid_rows": len(values), "ima_min_cnts": min(values) if values else None,
            "ima_median_cnts": statistics.median(values) if values else None,
            "ima_max_cnts": max(values) if values else None}


def bin_data(edac, ima, edges, boundaries):
    bins = [{"calendar_left": a.isoformat(), "calendar_right": b.isoformat(),
             "edac_rows": 0, "edac_interval_span_s": 0.0,
             "edac_increment_lower": 0, "edac_increment_upper": 0,
             "edac_increment_at_right_endpoint": 0, "excluded_edac_intervals": 0,
             "ima_rows": 0, "ima_fill_rows": 0, "ima_values": [],
             "memory_live_exposure_s": None, "ima_live_exposure_s": None,
             "joint_live_exposure_s": None, "negative_reference": "UNKNOWN"}
            for a, b in zip(boundaries, boundaries[1:])]
    for record in edac:
        index = row_bin(record["time"], boundaries)
        if index is not None:
            bins[index]["edac_rows"] += 1
    for record in ima:
        index = row_bin(record["time"], boundaries)
        if index is None:
            continue
        cell = bins[index]
        cell["ima_rows"] += 1
        if record["value"] is None:
            cell["ima_fill_rows"] += 1
        else:
            cell["ima_values"].append(record["value"])
    for edge in edges:
        indices = interval_bins(edge["left"], edge["right"], boundaries)
        if edge["seconds"] == 0 and edge["status"] != "valid":
            index = row_bin(edge["right"], boundaries)
            if index is not None:
                bins[index]["excluded_edac_intervals"] += 1
        for index in indices:
            cell = bins[index]
            if edge["status"] != "valid":
                cell["excluded_edac_intervals"] += 1
                continue
            a, b = boundaries[index:index+2]
            cell["edac_interval_span_s"] += (min(b,edge["right"])-max(a,edge["left"])).total_seconds()
            if edge["delta"] > 0:
                cell["edac_increment_upper"] += edge["delta"]
                if edge["left"] >= a and edge["right"] <= b:
                    cell["edac_increment_lower"] += edge["delta"]
        if edge["status"] == "valid":
            index = row_bin(edge["right"], boundaries)
            if index is not None:
                bins[index]["edac_increment_at_right_endpoint"] += edge["delta"]
    for cell in bins:
        values = cell.pop("ima_values")
        cell.update(value_stats(values))
        cell["edac_interval_span_s"] = round(cell["edac_interval_span_s"],6)
        cell["both_series_present_A0"] = cell["edac_interval_span_s"] > 0 and bool(values)
    return bins


def ima_blocks(records, gap_s):
    check_order(records)
    gaps = []
    for a, b in zip(records,records[1:]):
        dt = (b["time"]-a["time"]).total_seconds()
        if dt > gap_s:
            gaps.append({"from_utc":a["raw_time"],"to_utc":b["raw_time"],"seconds":dt,
                         "left_line":a["line"],"right_line":b["line"],
                         "meaning":"no intermediate returned rows; live exposure UNKNOWN"})
    blocks, block = [], []
    for record in records:
        if record["value"] is None or (block and (record["time"]-block[-1]["time"]).total_seconds()>gap_s):
            if block: blocks.append(block)
            block = []
        if record["value"] is not None:
            block.append(record)
    if block: blocks.append(block)
    intervals = [{"first_utc":b[0]["raw_time"],"last_utc":b[-1]["raw_time"],
                  "first_line":b[0]["line"],"last_line":b[-1]["line"],"rows":len(b),
                  "row_span_s":(b[-1]["time"]-b[0]["time"]).total_seconds(),
                  "live_exposure_s":None} for b in blocks]
    return intervals,gaps


def summarize_window(label, left, right, edac, ima, edges, hours):
    first_boundary = datetime.fromisoformat(hours[0]["calendar_left"])
    inside = lambda t: left < t <= right or (left == first_boundary and t == left)
    valid = [e for e in edges if e["status"]=="valid" and e["delta"]>0]
    cells = [c for c in hours if left <= datetime.fromisoformat(c["calendar_left"]) < right]
    values = [r["value"] for r in ima if inside(r["time"]) and r["value"] is not None]
    return {"window":label,"left":left.isoformat(),"right":right.isoformat(),
            "edac_rows":sum(inside(r["time"]) for r in edac),
            "edac_increment_lower":sum(e["delta"] for e in valid if e["left"]>=left and e["right"]<=right),
            "edac_increment_upper":sum(e["delta"] for e in valid if e["left"]<right and e["right"]>left),
            "edac_increment_at_right_endpoint":sum(e["delta"] for e in valid if left<e["right"]<=right),
            "hour_bins":len(cells),"hours_both_series_present_A0":sum(c["both_series_present_A0"] for c in cells),
            "hours_without_valid_ima":sum(c["ima_valid_rows"]==0 for c in cells),
            "positive_edac_hours_without_ima_A0":sum(c["edac_increment_at_right_endpoint"]>0 and c["ima_valid_rows"]==0 for c in cells),
            "joint_live_exposure_s":None,"negative_intervals":"UNKNOWN; none established",
            **value_stats(values)}


def plot_overview(out, hours, config):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.titlesize":11})
    fig, ax = plt.subplots(3,1,figsize=(13.5,8.6),sharex=True,
                           gridspec_kw={"height_ratios":[2,2,1.05]},layout="constrained")
    left=[datetime.fromisoformat(c["calendar_left"]) for c in hours]
    x=[t+timedelta(minutes=30) for t in left]
    lo=[c["edac_increment_lower"] for c in hours]
    hi=[c["edac_increment_upper"] for c in hours]
    ax[0].fill_between(x,lo,hi,step="mid",color="#227c9d",alpha=.27,label="Нижняя–верхняя сумма по интервалам")
    ax[0].plot(x,lo,color="#176785",lw=1.1,drawstyle="steps-mid",label="Нижняя сумма")
    ax[0].set_ylabel("Приращение EDAC\nза час, счёт")
    ax[0].set_ylim(bottom=-.15)
    ax[0].legend(loc="upper right",fontsize=9)
    ax[0].set_title("(a) Приращения наблюдённого счётчика; полоса — неопределённость отнесения к часу",loc="left")
    keep=[(t,c) for t,c in zip(x,hours) if c["ima_valid_rows"]]
    ax[1].vlines([t for t,c in keep],[c["ima_min_cnts"] for t,c in keep],
                  [c["ima_max_cnts"] for t,c in keep],color="#b293c2",lw=1,alpha=.8,label="Min–max имеющихся строк")
    ax[1].scatter([t for t,c in keep],[c["ima_median_cnts"] for t,c in keep],s=16,color="#71348c",label="Медиана имеющихся строк")
    ax[1].set_yscale("symlog",linthresh=1)
    ax[1].set_ylabel("IMA background, cnts\n(symlog)")
    ax[1].set_title("(b) IMA: пустые часы оставлены пустыми; cnts не преобразованы в поток",loc="left")
    ax[1].legend(loc="upper right",fontsize=9)
    # Display record presence only. The separate gray row represents unknown exposure.
    for y,key,color in [(2,"edac_rows","#176785"),(1,"ima_valid_rows","#71348c")]:
        present=[t for t,c in zip(x,hours) if c[key]>0]
        ax[2].scatter(present,[y]*len(present),marker="s",s=10,color=color)
    ax[2].axhspan(-.25,.25,color="#dddddd")
    ax[2].text(x[len(x)//2],0,"НЕ УСТАНОВЛЕНА",ha="center",va="center",fontsize=9,color="#555555")
    ax[2].set_yticks([0,1,2],["Живая экспозиция","IMA: есть строки","EDAC: есть строки"])
    ax[2].set_ylim(-.5,2.5)
    ax[2].set_title("(c) Наличие в часовом бине ≠ непрерывная экспозиция",loc="left")
    reference=list(map(datetime.fromisoformat,config["reference"]))
    window=list(map(datetime.fromisoformat,config["window"]))
    for a in ax:
        a.axvspan(*reference,color="#f4bc50",alpha=.12,zorder=-1)
        a.set_xlim(*window)
        a.grid(axis="x",alpha=.17)
    ax[-1].xaxis.set_major_locator(mdates.DayLocator())
    ax[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d"))
    ax[-1].set_xlabel("Декабрь 2006: UTC IMA; календарь EDAC наложен при допущении A0 (UTC-связь неизвестна)")
    fig.suptitle("Venus Express · полное окно 01–20 декабря 2006\nЗатенён комплекс 5/7 декабря; численная задержка UNKNOWN",fontsize=14)
    fig.supxlabel("Данные: B. Sanchez-Cano / Leicester, DOI 10.25392/leicester.data.22700146.v1 (CC BY 4.0); IMA: IRF / CDPP-AMDA / PSWS / SPIDER",fontsize=8)
    fig.savefig(out/"overview.png",dpi=160,metadata={"Software":"T197 VEX2006 audit"})
    plt.close(fig)
    return {"matplotlib":matplotlib.__version__,"numpy":np.__version__}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path,default=ROOT/".cache/t197")
    parser.add_argument("--out",type=Path,default=HERE/"outputs")
    parser.add_argument("--vendor",type=Path)
    parser.add_argument("--fetch",action="store_true")
    args=parser.parse_args()
    if args.vendor: sys.path.insert(0,str(args.vendor.resolve()))
    os.environ["MPLCONFIGDIR"] = str(ROOT/".cache/t197/matplotlib")
    config=json.loads((HERE/"inputs.json").read_text(encoding="utf-8"))
    args.cache.mkdir(parents=True,exist_ok=True)
    # Verify all bytes before making scientific outputs.
    for entry in config["inputs"]:
        path=args.cache/entry["local_name"]
        if not path.exists() and args.fetch:
            req=urllib.request.Request(entry["url"],headers={"User-Agent":"T197-reproducibility-audit/1.0"})
            with urllib.request.urlopen(req,timeout=60) as response: data=response.read()
            if digest(data)!=entry["sha256"]: raise ValueError("Downloaded input hash mismatch")
            path.write_bytes(data)
        if digest(path.read_bytes())!=entry["sha256"]: raise ValueError("Cached input hash mismatch")
    with ZipFile(args.cache/"EDAC.zip") as archive: raw_edac=archive.read(config["edac_member"])
    raw_ima=(args.cache/"vex-ima-bg-20061201-20061220.csv").read_bytes()
    edac,ima=parse_edac(raw_edac),parse_ima(raw_ima)
    start,stop=map(datetime.fromisoformat,config["window"])
    if any(not start<=r["time"]<stop for r in edac+ima): raise ValueError("Unexpected row outside frozen window")
    edges=counter_intervals(edac,config["edac_gap_threshold_s"])
    boundaries=[start+timedelta(seconds=i*config["bin_seconds"]) for i in range(int((stop-start).total_seconds()/config["bin_seconds"])+1)]
    hours=bin_data(edac,ima,edges,boundaries)
    blocks,gaps=ima_blocks(ima,config["ima_gap_threshold_s"])
    r0,r1=map(datetime.fromisoformat,config["reference"])
    windows=[("whole",start,stop),("before_reference",start,r0),("reference_complex",r0,r1),("after_reference",r1,stop)]
    summary=[summarize_window(label,a,b,edac,ima,edges,hours) for label,a,b in windows]
    positive=[e for e in edges if e["status"]=="valid" and e["delta"]>0]
    missing=[e for e in edges if e["status"]!="valid"]
    statuses=dict(Counter(e["status"] for e in edges))
    total=sum(e["delta"] for e in positive)
    if not missing and total!=edac[-1]["value"]-edac[0]["value"]: raise ValueError("Counter conservation failed")
    if sum(h["edac_increment_at_right_endpoint"] for h in hours)!=total: raise ValueError("Bin conservation failed")
    args.out.mkdir(parents=True,exist_ok=True)
    write_csv(args.out/"hourly.csv",hours,list(hours[0]))
    write_csv(args.out/"windows.csv",summary,list(summary[0]))
    export=lambda e:{k:(v.isoformat() if isinstance(v,datetime) else v) for k,v in e.items()}
    write_csv(args.out/"edac_positive_intervals.csv",[export(e) for e in positive],list(edges[0]))
    write_json(args.out/"edac_exceptions.json",[export(e) for e in missing])
    write_csv(args.out/"ima_row_blocks.csv",blocks,list(blocks[0]))
    write_json(args.out/"ima_gaps.json",gaps)
    audit={"status":"OWN RESULT; pending review","inputs_verified":2,"edac_rows":len(edac),"ima_rows":len(ima),
           "edac_member_sha256":digest(raw_edac),"edac_first":edac[0]["raw_time"],"edac_last":edac[-1]["raw_time"],
           "counter_first":edac[0]["value"],"counter_last":edac[-1]["value"],"edge_statuses":statuses,
           "positive_intervals":len(positive),"zero_intervals":sum(e["status"]=="valid" and e["delta"]==0 for e in edges),
           "increment_sum":total,"increment_sizes":dict(Counter(str(e["delta"]) for e in positive)),
           "positive_interval_width_min_s":min(e["seconds"] for e in positive),
           "positive_interval_width_max_s":max(e["seconds"] for e in positive),
           "edac_unbracketed_window_edges_s":[(edac[0]["time"]-start).total_seconds(),(stop-edac[-1]["time"]).total_seconds()],
           "ima_row_blocks":len(blocks),"ima_gaps_over_288s":len(gaps),
           "ima_duplicate_timestamps":len(ima)-len({r["time"] for r in ima}),
           "maximum_ima_gap":max(gaps,key=lambda g:g["seconds"]),
           "hours":len(hours),"hours_with_ambiguous_increment_assignment":sum(h["edac_increment_lower"]!=h["edac_increment_upper"] for h in hours),
           "hour_lower_sum":sum(h["edac_increment_lower"] for h in hours),"hour_upper_sum_not_additive":sum(h["edac_increment_upper"] for h in hours),
           "joint_exposure_s":None,"numerical_delay_s":None,"established_negative_intervals":None,
           "alignment":config["alignment"],"windows":summary}
    write_json(args.out/"summary.json",audit)
    versions=plot_overview(args.out,hours,config)
    from verify import verify
    checks=verify(args.cache,args.out,config)
    suite=unittest.defaultTestLoader.discover(str(HERE),pattern="test_reader.py")
    test_count=suite.countTestCases()
    test_result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not test_result.wasSuccessful(): raise RuntimeError("Semantic tests failed")
    checks["semantic_tests_passed"]=test_count
    write_json(args.out/"checks.json",checks)
    names=["hourly.csv","windows.csv","edac_positive_intervals.csv","edac_exceptions.json",
           "ima_row_blocks.csv","ima_gaps.json","summary.json","overview.png","checks.json"]
    write_json(args.out/"sha256.json",{n:digest((args.out/n).read_bytes()) for n in names})
    write_json(args.out/"run.json",{"python":platform.python_version(),"platform":platform.platform(),"versions":versions,
               "utc_run":datetime.now(timezone.utc).isoformat(),"reproduce_sha256":digest(Path(__file__).read_bytes()),
               "config_sha256":digest((HERE/"inputs.json").read_bytes()),"plan_sha256":digest((HERE/"PLAN.md").read_bytes()),
               "supporting_source_sha256":{n:digest((HERE/n).read_bytes()) for n in ["verify.py","test_reader.py","requirements.txt"]}})
    print(json.dumps(audit,ensure_ascii=False,indent=2))


if __name__=="__main__": main()

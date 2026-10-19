"""Separate direct reading and brute-force arithmetic; imports no production reader."""
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import json
import statistics
from zipfile import ZipFile


def verify(cache,out,config):
    for source in config["inputs"]:
        assert hashlib.sha256((cache/source["local_name"]).read_bytes()).hexdigest()==source["sha256"]
    with ZipFile(cache/"EDAC.zip") as z:
        lines=z.read(config["edac_member"]).decode().splitlines()
    start=next(i for i,x in enumerate(lines) if x.startswith("# DATE TIME"))+1
    pairs=[(datetime.fromisoformat(row[0]),int(Decimal(row[1]))) for row in csv.reader(lines[start:],delimiter="\t")]
    assert len(pairs)==25686
    assert all(0<(b[0]-a[0]).total_seconds()<=96 for a,b in zip(pairs,pairs[1:]))
    assert all(b[1]>=a[1] for a,b in zip(pairs,pairs[1:]))
    positive=[(a[0],b[0],b[1]-a[1]) for a,b in zip(pairs,pairs[1:]) if b[1]>a[1]]
    total=pairs[-1][1]-pairs[0][1]
    assert total==sum(c for a,b,c in positive)
    raw=(cache/"vex-ima-bg-20061201-20061220.csv").read_text().splitlines()
    data=[(datetime.fromisoformat(row[0].rstrip("Z")),float(row[1])) for row in csv.reader(raw[1:])]
    assert len(data)==1382 and all(v>=0 for t,v in data)
    assert all(b[0]>a[0] for a,b in zip(data,data[1:]))
    summary=json.loads((out/"summary.json").read_text())
    assert summary["increment_sum"]==total
    assert summary["positive_intervals"]==len(positive)
    with (out/"edac_positive_intervals.csv").open(newline="") as f:
        saved=list(csv.DictReader(f))
    assert [(datetime.fromisoformat(e["left"]),datetime.fromisoformat(e["right"]),int(e["delta"])) for e in saved]==positive
    expected_gaps=[(b[0]-a[0]).total_seconds() for a,b in zip(data,data[1:]) if (b[0]-a[0]).total_seconds()>288]
    assert summary["ima_gaps_over_288s"]==len(expected_gaps)
    assert summary["maximum_ima_gap"]["seconds"]==max(expected_gaps)
    with (out/"hourly.csv").open(newline="") as f: cells=list(csv.DictReader(f))
    count_convention=0
    compared=0
    positive_unpaired=0
    for row in cells:
        left,right=map(datetime.fromisoformat,[row["calendar_left"],row["calendar_right"]])
        lower=sum(v for a,b,v in positive if a>=left and b<=right)
        upper=sum(v for a,b,v in positive if a<right and b>left)
        at_right=sum(v for a,b,v in positive if left<b<=right)
        assert [int(row[k]) for k in ["edac_increment_lower","edac_increment_upper","edac_increment_at_right_endpoint"]]==[lower,upper,at_right]
        assert int(row["edac_rows"])==sum(left<t<=right for t,c in pairs)
        span=max(0,(min(right,pairs[-1][0])-max(left,pairs[0][0])).total_seconds())
        assert abs(float(row["edac_interval_span_s"])-span)<1e-6
        selected=[v for t,v in data if left<t<=right]
        assert int(row["ima_valid_rows"])==len(selected)
        if selected:
            assert float(row["ima_median_cnts"])==statistics.median(selected)
            assert float(row["ima_min_cnts"])==min(selected)
            assert float(row["ima_max_cnts"])==max(selected)
            compared+=1
        else:
            assert row["ima_median_cnts"]==""
            positive_unpaired+=at_right>0
        assert row["joint_live_exposure_s"]=="" and row["negative_reference"]=="UNKNOWN"
        count_convention+=at_right
    assert count_convention==total
    for window in summary["windows"]:
        left,right=map(datetime.fromisoformat,[window["left"],window["right"]])
        sums=[sum(v for a,b,v in positive if a>=left and b<=right),
              sum(v for a,b,v in positive if a<right and b>left)]
        assert [window["edac_increment_lower"],window["edac_increment_upper"]]==sums
        selected=[v for t,v in data if left<t<=right]
        assert window["ima_valid_rows"]==len(selected)
        assert window["ima_median_cnts"]==statistics.median(selected)
    assert compared==summary["windows"][0]["hours_both_series_present_A0"]
    assert positive_unpaired==summary["windows"][0]["positive_edac_hours_without_ima_A0"]
    return {"method":"Separate CSV/Decimal parser, direct endpoint subtraction and brute-force per-hour sums; same author, not independent review",
            "counter_net_change":total,"positive_intervals":len(positive),"all_hour_bins_checked":len(cells),
            "both_series_present_hours_A0":compared,"window_tables_checked":len(summary["windows"]),
            "ima_gap_count":len(expected_gaps),"conservation":True,"numeric_agreement":True}

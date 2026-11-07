"""Check original RATE_H metadata and repeat the comparison using CDF Epoch."""
import argparse
from collections import Counter
from datetime import date
from decimal import Decimal as D
import gzip
import json
from pathlib import Path

import cdflib
import numpy as np

from data import HERE, PROTOCOL, json_text, output, verified


def check(directory):
    lock = json.loads((HERE/"observation.json").read_text(encoding="utf-8"))
    raw = np.loadtxt(verified(directory,lock),usecols=(0,1,3))
    cdf = cdflib.CDF(verified(directory,lock["cdf_crosscheck"]))
    global_attrs = cdf.globalattsget()
    attrs = cdf.varattsget("RATE_H")
    assert global_attrs["Time_resolution"] == ["1 sec"] and attrs["units"] == "counts"
    count = cdf.varget("RATE_H")
    assert np.array_equal(count,raw[:,1])
    fill = float(global_attrs["FILLVAL"][0])
    assert not np.any(count == fill)
    epoch = cdflib.cdfepoch.to_datetime(cdf.varget("Epoch"))
    start = np.datetime64(PROTOCOL["utc_day"])
    time = (epoch-start)/np.timedelta64(1,"s")
    met_start = (date.fromisoformat(PROTOCOL["utc_day"])-date(2000,1,1)).days*86400+5
    mismatch_s = np.max(abs(time-(raw[:,0]-met_start)))
    assert mismatch_s < .001
    slots = np.floor(time+.5).astype(int)
    multiplicity = Counter(slots.tolist())
    observed = {int(i):int(x) for i,x,t,level in zip(slots,count,time,raw[:,2])
                if 0 <= t < 86400 and 0 <= i < 86400 and multiplicity[i] == 1
                and level == 1 and x >= 0 and x == int(x)}

    meta = json.loads((HERE/"forecast.json").read_text(encoding="utf-8"),parse_float=D)
    rates = {}
    with gzip.open(HERE/"forecast.rle.gz","rt",encoding="ascii") as stream:
        next(stream)
        for line in stream:
            a,b,colour,_,_ = map(int,line.split())
            if colour >= 0:
                rates.update(dict.fromkeys(range(a,b),meta["bands"][str(colour)]["proxy_Hz"]))
    confusion = Counter()
    n = N = 0
    pred = positive = negative = D(0)
    for minute in range(1440):
        seconds = range(60*minute,60*(minute+1))
        available = [i for i in seconds if i in rates]
        paired = [i for i in available if i in observed]
        if len(paired) < PROTOCOL["minimum_seconds_per_UTC_minute"]:
            continue
        whole = sum(rates[i] for i in available)
        x = sum(observed[i] for i in paired)
        y = sum(rates[i] for i in paired)
        actual = x >= len(paired)*PROTOCOL["rate_threshold_Hz"]
        forecast = whole >= len(available)*PROTOCOL["rate_threshold_Hz"]
        classification = {(True,True):"TP",(True,False):"FP",(False,True):"FN",(False,False):"TN"}
        confusion[classification[forecast,actual]] += 1
        n += len(paired)
        N += x
        pred += y
        positive += max(D(0),x-y)
        negative += max(D(0),y-x)
    primary = json.loads((HERE/"result.json").read_text(encoding="utf-8"),parse_float=D)
    summary = primary["groups"]["all"]
    assert (n,N) == (summary["exposure_s"],summary["observed_counts"])
    for k,v in (("predicted_counts",pred),("positive_residual_counts",positive),("overprediction_counts",negative)):
        assert abs(v-summary[k]) < D("0.000001")
    assert all(confusion[k] == primary["classification_minutes"][k] for k in ("TP","FP","FN","TN"))
    return {"status":"PASS", "source":lock["cdf_crosscheck"], "channel":"RATE_H",
            "cdf_data_version":global_attrs["Data_version"][0],
            "cdf_generation_date":global_attrs["Generation_date"][0],
            "cdf_variable_units":attrs["units"],"cdf_variable_description":attrs["CATDESC"],
            "cdf_time_resolution":global_attrs["Time_resolution"][0],
            "records":len(count),"counter_mismatches":0,"fill_count":0,
            "max_Epoch_vs_TXT_difference_s":round(float(mismatch_s),7),
            "replicated_common_exposure_s":n,"replicated_observed_counts":N,
            "decimal_predicted_counts":str(pred),"decimal_positive_residual_counts":str(positive),
            "decimal_overprediction_counts":str(negative),
            "classification_minutes":{k:confusion[k] for k in ("TP","FP","FN","TN")},
            "same_detector_observations":True,"independent_scientific_review":False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--check",action="store_true")
    args = parser.parse_args()
    audit = check(args.directory)
    output("archive-check.json",json_text(audit),args.check)
    print("PASS: CDF RATE_H, TXT COUNT_H, Epoch and separate Decimal exposure/count comparison.")


if __name__ == "__main__":
    main()

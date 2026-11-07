"""Score the locked RBM-H forecast on common exposure, with both residual signs."""
import argparse
import gzip
import io
import json
from datetime import datetime
from pathlib import Path

import numpy as np

from data import HERE, PROTOCOL as cfg, json_text, output, sha, verified
from forecast import DAY, DAY_LENGTH, eop_forecast, intervals, load_oem, track


def frozen_forecast(lock):
    raw = gzip.decompress((HERE/"forecast.rle.gz").read_bytes())
    meta_text = (HERE/"forecast.json").read_text(encoding="utf-8")
    meta = json.loads(meta_text)
    if not sha(raw) == meta["rle_sha256_lf"] == lock["forecast_rle_sha256_lf"]:
        raise ValueError("Forecast differs from the one sealed before unblinding")
    if sha(meta_text.encode()) != lock["forecast_meta_sha256_lf"]:
        raise ValueError("Forecast metadata differs from the sealed version")
    runs = np.loadtxt(io.BytesIO(raw),dtype=int)
    assert runs[0,0] == 0 and runs[-1,1] == DAY_LENGTH
    assert np.all(runs[:,1] > runs[:,0]) and np.array_equal(runs[:-1,1],runs[1:,0])
    states = np.repeat(runs[:,2:],runs[:,1]-runs[:,0],axis=0)
    # The unused last element is also the lookup for the sentinel -1.
    rates = np.full(cfg["legend_steps"]+1,np.nan)
    low = np.full_like(rates,np.nan)
    high = np.full_like(rates,np.nan)
    edge = np.zeros(len(rates),dtype=bool)
    for key,b in meta["bands"].items():
        i = int(key)
        rates[i],low[i] = b["proxy_Hz"],b["reading_low_Hz"]
        high[i] = np.inf if b["reading_high_Hz"] is None else b["reading_high_Hz"]
        edge[i] = b["edge_colour"]
    p = rates[states[:,0]]
    frozen_high = np.zeros(DAY_LENGTH//60,dtype=bool)
    for a,b in meta["frozen_elevated_minute_intervals"]:
        frozen_high[a:b] = True
    return p,low[states[:,1]],high[states[:,2]],edge[states[:,0]],frozen_high


def observations(path):
    with path.open(encoding="ascii") as f:
        if f.readline().lstrip("#").split() != ["TIME","COUNT_H","COUNT_Z","LVL","LON","LAT","RADIUS"]:
            raise ValueError("Unexpected MAXI TXT header")
    data = np.loadtxt(path,usecols=(0,1,3,4,5,6))
    t = data[:,0]-(DAY-datetime(2000,1,1)).total_seconds()-cfg["leap_seconds_since_epoch"]
    in_day = np.isfinite(t) & (t >= 0) & (t < DAY_LENGTH)
    slots = np.full(len(t),-1,dtype=int)
    slots[in_day] = np.floor(t[in_day]+.5).astype(int)
    in_day &= (slots >= 0) & (slots < DAY_LENGTH)
    per_slot = np.bincount(slots[in_day],minlength=DAY_LENGTH)
    unique = np.zeros(len(t),dtype=bool)
    unique[in_day] = per_slot[slots[in_day]] == 1
    ld = data[:,2] == cfg["discriminator"]
    h = data[:,1]
    good_count = np.isfinite(h) & (h >= 0) & (h == np.floor(h))
    used = unique & ld & good_count
    counts = np.full(DAY_LENGTH,np.nan)
    counts[slots[used]] = h[used]
    diagnostics = {
        "source_rows":len(t), "rows_outside_or_bad_time":int((~in_day).sum()),
        "seconds_without_time_record":int((per_slot == 0).sum()),
        "duplicate_seconds_discarded":int((per_slot > 1).sum()),
        "unique_seconds_other_LVL":int((unique & ~ld).sum()),
        "unique_LVL1_seconds_invalid_H":int((unique & ld & ~good_count).sum()),
        "valid_observation_seconds":int(used.sum()), "valid_zero_counts":int((h[used] == 0).sum()),
        "max_abs_rounding_s":round(float(np.abs(t[used]-slots[used]).max()),6) if used.any() else None,
        "LVL_counts":{str(level):int((data[:,2] == level).sum()) for level in np.unique(data[:,2])},
        "gaps_in_observed_seconds":intervals(~np.isfinite(counts)),
    }
    assert (diagnostics["seconds_without_time_record"]+diagnostics["duplicate_seconds_discarded"]
            +diagnostics["unique_seconds_other_LVL"]+diagnostics["unique_LVL1_seconds_invalid_H"]
            +diagnostics["valid_observation_seconds"]) == DAY_LENGTH
    return counts,diagnostics,t[used],data[used,3:]


def figure_minutes(counts,p,lo,hi,mask):
    valid = mask & np.isfinite(counts) & np.isfinite(p)
    def totals(x):
        return np.where(valid,x,0).reshape(-1,60).sum(axis=1)
    n = valid.reshape(-1,60).sum(axis=1)
    return n,totals(counts),totals(p),totals(lo),totals(hi)


def aggregate(minutes,chosen):
    exposure, observed, predicted, low, high = (v[chosen] for v in minutes)
    n = int(exposure.sum())
    if n == 0:
        return {"minutes":0,"exposure_s":0}
    residual = observed-predicted
    positive,negative = np.maximum(residual,0).sum(),np.maximum(-residual,0).sum()
    assert np.isclose(positive-negative,residual.sum(),atol=1e-7,rtol=1e-12)
    N = int(observed.sum())
    return {
        "minutes":int(chosen.sum()),"exposure_s":n,"observed_counts":N,
        "predicted_counts":round(float(predicted.sum()),6),
        "predicted_Hz":round(float(predicted.sum()/n),6),"observed_Hz":round(N/n,6),
        "bias_obs_minus_pred_Hz":round(float(residual.sum()/n),6),
        "weighted_MAE_Hz":round(float((positive+negative)/n),6),
        "positive_residual_counts":round(float(positive),6),
        "overprediction_counts":round(float(negative),6),
        "minutes_obs_above_point":int((residual > 0).sum()),
        "minutes_obs_below_point":int((residual < 0).sum()),
        "minutes_above_reading_envelope":int((observed > high).sum()),
        "minutes_below_reading_envelope":int((observed < low).sum()),
        "minutes_open_or_unknown_upper":int((~np.isfinite(high)).sum()),
        "conditional_Poisson_scale_Hz":round(float(np.sqrt(N)/n),8),
    }


def extreme(minutes,chosen,positive):
    n,obs,p,lo,hi = minutes
    indices = np.flatnonzero(chosen)
    if not len(indices):
        return None
    delta = (obs[indices]-p[indices])/n[indices]
    i = indices[np.argmax(delta) if positive else np.argmin(delta)]
    if (positive and obs[i] <= p[i]) or (not positive and obs[i] >= p[i]):
        return None
    def rate(x):
        return round(float(x[i]/n[i]),6) if np.isfinite(x[i]) else None
    return {"UTC":f"{i//60:02d}:{i%60:02d}","exposure_s":int(n[i]),
            "observed_counts":int(obs[i]),"observed_Hz":rate(obs),"predicted_Hz":rate(p),
            "reading_low_Hz":rate(lo),"reading_high_Hz":rate(hi),
            "obs_minus_pred_Hz":round(float((obs[i]-p[i])/n[i]),6)}


def position_check(directory,t,observed):
    finite = (np.isfinite(observed).all(axis=1) & (np.abs(observed[:,0]) <= 360)
              & (np.abs(observed[:,1]) <= 90) & (observed[:,2] > 0))
    if not finite.any():
        return {"paired_at_record_TIME":0}
    t = t[finite]
    nodes = load_oem(verified(directory,cfg["sources"]["oem"]))
    eop = eop_forecast(verified(directory,cfg["sources"]["iers"]))
    lon,lat,_,_,r,supported = track(nodes,eop,t)
    olon,olat,orr = observed[finite][supported].T
    lon,lat,r = lon[supported],lat[supported],r[supported]
    phi1,phi2 = np.radians(lat),np.radians(olat)
    h = np.sin((phi1-phi2)/2)**2+np.cos(phi1)*np.cos(phi2)*np.sin(np.radians(lon-olon)/2)**2
    angle = np.degrees(2*np.arcsin(np.sqrt(np.clip(h,0,1))))
    radial = np.abs(r-orr)
    def summary(x):
        return dict(zip(("median","p95","max"),(round(float(v),6) for v in np.percentile(x,[50,95,100]))))
    return {"paired_at_record_TIME":len(angle),"angular_separation_deg":summary(angle),
            "absolute_radius_difference_km":summary(radial)}


def score(directory,lock):
    p,lo,hi,edge,frozen_high = frozen_forecast(lock)
    counts,quality,t,coords = observations(verified(directory,lock))
    primary = figure_minutes(counts,p,lo,hi,np.ones(DAY_LENGTH,dtype=bool))
    interior = figure_minutes(counts,p,lo,hi,~edge)
    threshold = cfg["rate_threshold_Hz"]
    eligible = primary[0] >= cfg["minimum_seconds_per_UTC_minute"]
    any_obs_high = primary[1] >= threshold*primary[0]
    tp = int((eligible & frozen_high & any_obs_high).sum())
    fp = int((eligible & frozen_high & ~any_obs_high).sum())
    fn = int((eligible & ~frozen_high & any_obs_high).sum())
    tn = int((eligible & ~frozen_high & ~any_obs_high).sum())
    quality.update({
        "valid_measurements_without_map":int((np.isfinite(counts) & ~np.isfinite(p)).sum()),
        "eligible_minutes":int(eligible.sum()),"excluded_minutes":int((~eligible).sum()),
        "edge_colour_seconds_scored":int((np.isfinite(counts)&edge&np.repeat(eligible,60)).sum()),
        "valid_joint_seconds_in_excluded_minutes":int(primary[0][~eligible].sum()),
    })
    groups = {"all":aggregate(primary,eligible),
              "forecast_below_1_Hz":aggregate(primary,eligible & ~frozen_high),
              "forecast_at_least_1_Hz":aggregate(primary,eligible & frozen_high)}
    columns = ["minute_UTC_from_midnight","exposure_s","observed_counts","predicted_counts",
               "reading_low_counts","reading_high_counts_or_null","eligible","frozen_elevated"]
    lines = [json.dumps(columns)]
    for i in range(len(eligible)):
        n,x,y,l,h = (v[i] for v in primary)
        val = lambda v: round(float(v),6) if np.isfinite(v) else None
        lines.append(json.dumps([i,int(n),int(x),val(y),val(l),val(h),bool(eligible[i]),bool(frozen_high[i])],
                                allow_nan=False,separators=(",",":")))
    minute_text = "\n".join(lines)+"\n"
    result = {
        "day_UTC":cfg["utc_day"],"channel":"RBM-H","units":"counts per nominal second",
        "forecast_commit":lock["forecast_commit"],"observation_sha256":lock["sha256"],
        "minutes_sha256_lf":sha(minute_text.encode("ascii")),"quality":quality,
        "groups":groups,"classification_minutes":{"TP":tp,"FP":fp,"FN":fn,"TN":tn,
            "precision":round(tp/(tp+fp),6) if tp+fp else None,
            "recall":round(tp/(tp+fn),6) if tp+fn else None},
        "largest_underprediction":extreme(primary,eligible,True),
        "largest_overprediction":extreme(primary,eligible,False),
        "interior_colours_only":aggregate(interior,interior[0] >= cfg["minimum_seconds_per_UTC_minute"]),
        "position_diagnostic_only":position_check(directory,t,coords),
    }
    assert tp+fp+fn+tn == groups["all"]["minutes"]
    assert groups["all"]["exposure_s"] == groups["forecast_below_1_Hz"]["exposure_s"]+groups["forecast_at_least_1_Hz"]["exposure_s"]
    return result,minute_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--check",action="store_true")
    args = parser.parse_args()
    lock = json.loads((HERE/"observation.json").read_text(encoding="utf-8"))
    result,minutes = score(args.directory,lock)
    output("minutes.jsonl",minutes,args.check)
    output("result.json",json_text(result),args.check)
    print(json_text({k:result[k] for k in ("groups","classification_minutes","largest_underprediction","largest_overprediction")}))


if __name__ == "__main__":
    main()

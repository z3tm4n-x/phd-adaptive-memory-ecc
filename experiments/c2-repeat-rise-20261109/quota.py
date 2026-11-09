"""Independent reconstruction of the decade rise quota, before policy calculations."""
import argparse
import csv
import gzip
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from fractions import Fraction as F
from pathlib import Path

import numpy as np


PIN = "c0176b4837b5310378fb4218f2d549aeb4c991e9"
T = 315576000
STEP = 300
START = datetime(1974, 7, 1, tzinfo=timezone.utc)
UNIT = F(1, 1000)


def stamp(index):
    return (START + timedelta(seconds=STEP * index)).isoformat()


def use_readers(checkout):
    relative = Path("experiments/c1-common-geo-20261109")
    directory = checkout / relative
    for name in ("prior.py", "coverage.py", "cadence.py", "minute_sources.py"):
        contents = (directory / name).read_bytes().replace(b"\r\n", b"\n")
        blob = hashlib.sha1(b"blob " + str(len(contents)).encode() + b"\0" + contents).hexdigest()
        expected = subprocess.check_output(
            ["git", "-C", str(checkout), "rev-parse", f"{PIN}:{relative.as_posix()}/{name}"],
            text=True).strip()
        if blob != expected:
            raise ValueError(f"PR423 source differs: {name}")
    sys.path.insert(0, str(directory))


def sepem_windows(means, quantum_bits):
    width = T // STEP
    # Every stored excess is an integer multiple of 2^-bits. Work with exact
    # integers for all rolling sums, including initially high and cut events.
    units = np.ldexp(means, quantum_bits)
    if np.any(units != np.floor(units)):
        raise ValueError("Insufficient binary precision for the SEPEM reconstruction")
    u = [int(value) for value in units]
    def up(i):
        return max(0, u[i] - u[i-1]) if i else 0
    best = {key: (-1, 0) for key in ("registered_lower", "registered_fit", "all_phases_fit")}
    rise = sum(up(i) for i in range(width))
    bin_sum = sum(u[:width])
    area_num, area_den = bin_sum, 1
    for j in range(len(u)-width+1):
        initial = u[j]
        current = up(j)
        z = initial - current
        registered = z + 2*rise
        left = u[j-1] + up(j-1) if j else z
        for key, value in (("registered_lower", initial + rise - current),
                           ("registered_fit", registered),
                           ("all_phases_fit", max(left, z) + 2*rise)):
            if value > best[key][0]:
                best[key] = value, j
        if bin_sum * area_den > area_num:
            area_num, area_den = bin_sum, 1
        if j+width < len(u):
            next_up = up(j+width)
            # At fraction x of this bin the window integral, divided by
            # STEP, is bin_sum + d0*x + d1*x^2/2 in binary units.
            d0 = u[j+width] - next_up - z
            d1 = 2 * (next_up - current)
            if d0 > 0 and d0 + d1 < 0:
                den = -2*d1
                num = bin_sum * den + d0*d0
                if num * area_den > area_num * den:
                    area_num, area_den = num, den
            bin_sum += u[j+width] - initial
            rise += next_up - current
    out = {k: {"J_per_s":float(F(v, 1 << quantum_bits)), "units":str(v),
               "scale_bits":quantum_bits, "start_bin":j, "start_or_left_limit_utc":stamp(j)}
           for k, (v, j) in best.items()}
    out["max_excess_all_phases"] = float(F(STEP * area_num, (1 << quantum_bits) * area_den))
    return out


def event_example(means, directory):
    with (directory / "tNN-sepem-profiles/outputs/events.csv").open(encoding="utf-8") as stream:
        row = next(x for x in csv.DictReader(stream) if x["event_id"] == "E0056")
    a, b = int(row["start_index"]), int(row["stop_index_exclusive"])
    delta = np.diff(means[a:b])
    positive = delta > 0
    starts = np.flatnonzero(positive & ~np.r_[False, positive[:-1]])
    ends = np.flatnonzero(positive & ~np.r_[positive[1:], False])
    first = math.fsum(delta[starts[0]:ends[0]+1]) if len(starts) else 0.0
    total = math.fsum(delta[positive])
    return {"id":row["event_id"], "start":stamp(a), "end_exclusive":stamp(b),
            "runs":int(len(starts)), "sum_positive_per_s":total,
            "first_run_per_s":first, "repeat_runs_per_s":total-first}


def goes_series(times, rates, step, b, g):
    keep = np.isfinite(rates)
    times = times[keep]
    means = np.maximum(0, rates[keep] - b)
    gap = np.r_[times[0], np.diff(times) - step]
    assert gap.min() >= 0 and times[-1] + step <= T
    previous = np.r_[means[0], means[:-1]]
    z = np.minimum(means, previous + g * gap)
    z[0] = means[0]
    up_gap = np.minimum(z, g * gap)
    start = max(0.0, z[0] - g*gap[0])
    up_bin = 2 * (means - z)
    positive = np.maximum(np.diff(means), 0.0)
    connected = gap[1:] == 0
    # fsum avoids subtracting long prefixes in short records.
    observed = float(means[0]) + math.fsum(positive)
    reconstructed = math.fsum([start, math.fsum(up_bin), math.fsum(up_gap)])
    return {"bins":int(keep.sum()), "covered_s":step*len(means),
            "gaps_including_tail_s":T-step*len(means),
            "terminal_gap_s":int(T-times[-1]-step), "bin_lower_per_s":observed,
            "positive_adjacent_per_s":math.fsum(positive[connected]),
            "positive_across_gaps_per_s":math.fsum(positive[~connected]),
            "start_per_s":start, "rise_on_gaps_per_s":math.fsum(up_gap),
            "fit_per_s":reconstructed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("pr419", "pr423", "sepem-cache", "goes-cache", "minute-cache"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    use_readers(args.pr423)
    from prior import activate, EXPERIMENTS
    from coverage import sepem_series, goes_observed
    from cadence import samples
    from minute_sources import selected

    previous = activate(args.pr419)
    nu, _, _, _, ref = sepem_series(args.sepem_cache, previous)
    b = ref["background_per_s"]
    g = 0.004392116
    excess = np.maximum(nu - b, 0.0)
    windows = sepem_windows(excess, 53-math.frexp(b)[1])
    example = event_example(excess, EXPERIMENTS)
    rates, _, _, info = goes_observed(args.goes_cache, previous)
    records = {}
    epoch = np.arange(len(rates)) * STEP
    for col, label in enumerate(("East", "West")):
        records["GOES5_" + label] = goes_series(epoch, rates[:, col], STEP, b, g)
    with gzip.open(EXPERIMENTS / "t67-goes-growth/outputs/file_audits.json.gz", "rt",
                   encoding="utf-8") as stream:
        known = json.load(stream)
    signature = {q:i for i,q in enumerate(sorted({r["signature"] for r in known}))}
    files = {r["name"]:signature[r["signature"]] for r in known}
    for sat in (16, 18, 19):
        times, values, _, _ = samples(selected(), args.minute_cache/"folded", 60, sat, files, info)
        for col, label in enumerate(("East", "West")):
            records[f"G{sat}_1_{label}"] = goes_series(times, values[:, col], 60, b, g)
    s = windows["all_phases_fit"]
    largest = max([F(int(s["units"]), 1 << s["scale_bits"])]
                  + [F.from_float(row["fit_per_s"]) for row in records.values()])
    quota = math.ceil(largest/UNIT) * UNIT
    print(json.dumps({"PR423":PIN, "sepem_windows":len(nu)-T//STEP+1, "SEPEM":windows,
                      "event_example":example, "GOES":records, "quota_per_s":str(quota),
                      "quota_decimal":f"{float(quota):.3f}"}, indent=2))


if __name__ == "__main__":
    main()

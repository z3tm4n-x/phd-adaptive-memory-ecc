"""Paired ten-year archive replays with a GEO-wide and an archive-wide fixed policy."""
import argparse
from fractions import Fraction as F
from functools import cache
from hashlib import sha256
import json
from pathlib import Path
from runpy import run_path
import sys

import numpy as np


HERE = Path(__file__).resolve().parent
EXP = HERE.parent
PREVIOUS = EXP / "t186-volume-archive"
sys.path.insert(0, str(PREVIOUS))
from profiles import NAMES, PERIOD, goes, sepem
from replay import MODEL, T, branch_envelope, selftest

# The underlying GOES reader imports its own module named archive.
previous = run_path(str(PREVIOUS / "archive.py"))
N, ROBUST = previous["N"], previous["ROBUST"]
fixed_period, inputs_on_history = previous["fixed_period"], previous["inputs_on_history"]
series_summary, summarize = previous["series_summary"], previous["summarize"]

split_phase = run_path(str(EXP / "t525-two-phases/calculate.py"))["two_phase_risk"]
up, down = MODEL["up"], MODEL["down"]
EPS = F(1, 1000)
profiles = {"geo": MODEL["GEO"], "archive": MODEL["ARCHIVE"]}
old_sepem = json.loads((PREVIOUS / "sepem.json").read_bytes())
old_rows = old_sepem["rows"] + json.loads((PREVIOUS / "goes.json").read_bytes())["rows"]
two_phase = json.loads((EXP / "t525-two-phases/result.json").read_bytes())


def ladder_bound(rule, env):
    if rule.words == 16384:
        cost, _ = rule.cost(env, MODEL["MEAN"], rule.eta)
        return {"Q_upper": cost["q"], "s_upper": cost["s_upper"], "pct_upper": cost["pct_upper"]}
    assert rule.words == 65536
    q = sum(split_phase(rule, env))
    # #528 changes the probability in the after-stop tariff. All eligible slots
    # remain payable to T. The ordinary repair and dirty-cell tariffs use this W.
    cost = ROBUST["costs"](rule, rule.words, env, q, False)
    return {"Q_upper": up(q, 12), "s_upper": up(cost, 3), "pct_upper": up(100*cost/PERIOD, 6)}


def check_full_calendar(layout):
    words, addresses, scan, _, _ = layout
    selftest(layout)
    # The 256 KiB pass exceeds the 128 KiB predecessor's original read cap.
    for duration in (scan//2+67, scan-503, scan, scan+87):
        fixed_ns = scan+1400
        marks = tuple(np.empty(0, dtype=np.int64) for _ in range(3))
        lo, hi, _ = branch_envelope(marks, duration, fixed_ns, layout=layout)
        starts = np.arange(addresses, dtype=np.int64)
        phase = starts//4*1400+np.take([0,240,520,760], starts%4)
        assert min(phase[words:]-phase[:words]) == max(phase[words:]-phase[:words]) == scan//2
        expected = int(np.clip(duration-phase,0,100).sum())
        assert lo[0] == hi[0] == expected


@cache
def contract(kib):
    rule = MODEL["Ladder"](kib*256)
    out = {"KiB": kib, "words": rule.words, "addresses": rule.scan.addresses,
           "scan_ns": int(rule.scan.L*10**9), "top_steps": int(rule.levels[-1]/rule.scan.L),
           "thresholds": rule.counts, "classes": {}}
    for name, env in profiles.items():
        p = fixed_period(env, rule)
        floor_s = ROBUST["common_witness"](rule, rule.words, rule.words, ROBUST["WITNESSES"][name])
        quoted = MODEL["fixed_price"](rule, p, env)[1]
        stair = ladder_bound(rule, env)
        floor_quote = down(floor_s, 3)
        out["classes"][name] = {
            "period_ns": int(p*10**9), "fixed_Q_upper": quoted["physical_Q_upper"],
            "fixed_s_upper": quoted["s_upper"], "fixed_pct_upper": quoted["pct_upper"],
            "fixed_read_floor_s": floor_quote, "fixed_read_floor_pct": down(100*floor_s/PERIOD, 6),
            "ladder": stair, "class_ratio_lower": down(F(floor_quote)/F(stair["s_upper"]), 6),
        }
        assert F(quoted["physical_Q_upper"]) <= EPS and F(stair["Q_upper"]) <= EPS
        if kib == 64:
            old = old_sepem["class_prices"][name]
            assert old["fixed_best_necessary_s"] == floor_quote and old["fixed_registered_period_ns"] == p*10**9
            assert quoted == old["fixed_candidate"] and stair["s_upper"] == old["ladder"]["s_upper"]
    geo = out["classes"]["geo"]
    assert geo["period_ns"] == {64:259704200, 256:86429000}[kib]
    if kib == 256:
        assert geo["fixed_read_floor_s"] == two_phase["best_fixed_s_lower"]
        assert geo["fixed_s_upper"] == two_phase["sufficient_fixed_candidate_s_upper"]
        assert geo["ladder"]["s_upper"] == two_phase["price_s_upper"]
        assert geo["ladder"]["Q_upper"] == two_phase["stop_upper_also_bounds_physical_Q"]
    return out


def array_hash(a):
    return sha256(a.astype("<i8", copy=False).tobytes()).hexdigest()


def one_history(h, kib, reps):
    idx = NAMES.index(h.name)
    old = old_rows[idx]
    assert h.meta == old["history"] and h.name == old["name"]
    cfg = contract(kib)
    w, a, scan = cfg["words"], cfg["addresses"], cfg["scan_ns"]
    layout = (w, a, scan, cfg["top_steps"], np.array(cfg["thresholds"], dtype=np.int64))
    rule = MODEL["Ladder"](w)
    periods = {"ladder": 0, **{k:v["period_ns"] for k,v in cfg["classes"].items()}}
    records = {k:[] for k in periods}
    stats = {k:[] for k in periods}
    hashes = sha256()
    parents = []
    for rep in range(reps):
        ticks, words, bits, count = h.draw(idx, rep, w)
        parents.append(count)
        marks = (ticks, words, bits)
        for t in marks:
            hashes.update(len(t).to_bytes(8, "little"))
            hashes.update(t.astype("<i8", copy=False).tobytes())
        for name, period in periods.items():
            lo, hi, stat = branch_envelope(marks, T, period, layout=layout)
            assert np.all(lo <= hi) and 0 <= lo[0] <= hi[0] <= T
            records[name].append((lo, hi))
            stats[name].append(stat)
    arrays = {k:np.asarray(v, dtype=np.int64) for k,v in records.items()}
    digest = {k:array_hash(v) for k,v in arrays.items()}
    if kib == 64 and reps == N:
        assert hashes.hexdigest() == old["marks_sha256"]
        assert digest["ladder"] == old["sample_sha256"]["ladder"]
        assert digest["archive"] == old["sample_sha256"]["fixed_all_archives"]
    env = inputs_on_history(h.meta)
    stair = ladder_bound(rule, env)
    result = {}
    for name, array in arrays.items():
        summary = summarize(array, np.asarray(stats[name]), periods[name], a, scan)
        if name == "ladder":
            summary["analytic"] = stair
        else:
            p = F(periods[name], 10**9)
            fixed = MODEL["fixed_price"](rule, p, env)[1]
            floor_s = F(cfg["classes"][name]["fixed_read_floor_s"])
            mean = arrays["ladder"][:,:,0].astype(float).mean(axis=0)/10**9
            summary.update(
                analytic={k:fixed[k] for k in ("physical_Q_upper","s_upper","pct_upper")},
                floor_over_sample_ladder=[float(floor_s)/mean[1], float(floor_s)/mean[0]],
                floor_over_history_upper_lower=down(floor_s/F(stair["s_upper"]), 6),
                paired_difference_s=series_summary(array[:,0,0]-arrays["ladder"][:,1,0],
                                                    array[:,1,0]-arrays["ladder"][:,0,0], 10**9))
        result[name] = summary
    return {"name": h.name, "history": h.meta, "replications": reps, "parents_mean": float(np.mean(parents)),
            "marks_sha256": hashes.hexdigest(), "sample_sha256": digest, "policies": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--kib", type=int, choices=(64,256), required=True)
    parser.add_argument("--part", choices=("sepem","goes","all"), default="all")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    cfg = contract(args.kib)
    check_full_calendar((cfg["words"],cfg["addresses"],cfg["scan_ns"],cfg["top_steps"],
                         np.array(cfg["thresholds"],dtype=np.int64)))
    if args.pilot:
        pilot = one_history(sepem(args.cache), args.kib, 2)
        print("two paired seeds:", {k:v["busy_s"]["mean"] for k,v in pilot["policies"].items()})
        return
    for part in ("sepem","goes"):
        if args.part not in (part,"all"):
            continue
        histories = [sepem(args.cache)] if part == "sepem" else goes(args.cache)
        rows = []
        for h in histories:
            rows.append(one_history(h, args.kib, N))
            print(args.kib, h.name, rows[-1]["policies"]["ladder"]["busy_s"]["mean"], flush=True)
        obj = {"contract":cfg,"rows":rows}
        path = HERE / f"{part}-{args.kib}.json"
        if args.check:
            assert json.loads(path.read_bytes()) == obj
        else:
            path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+"\n",
                            encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

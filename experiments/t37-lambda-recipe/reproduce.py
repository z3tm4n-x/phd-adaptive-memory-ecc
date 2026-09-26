"""T37 descriptive audit only. No raw download, transport or reliability model.

Inputs are read from immutable Git blobs at config.base_sha, not modified
working copies. Default: run tests and compare with committed summary.json.
--write: regenerate ONLY this task's summary.json. Python 3.11+, stdlib + Git.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def truth(s):
    if s in ("1", "True", "true"):
        return True
    if s in ("0", "False", "false"):
        return False
    raise ValueError(f"Unknown boolean: {s!r}")


def stamp(s):
    t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None or t.microsecond:
        raise ValueError("Expected whole seconds and explicit timezone")
    return int(t.timestamp())


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat()


def numeric(s):
    # A missing serialized rate is not a physical zero. frame() still rejects
    # a nonfinite rate when the upstream mask claims that the row is valid.
    return float(s) if s.strip() else math.nan


def frame(times, versions, values, valid, step):
    if not (len(times) == len(versions) == len(values) == len(valid)):
        raise ValueError("Length mismatch")
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("Duplicate or nonincreasing timestamps")
    if any(t % step for t in times):
        raise ValueError("Timestamps off UTC grid")
    rows = []
    for t, version, x, ok in zip(times, versions, values, valid):
        if ok and (not math.isfinite(x) or x < 0):
            raise ValueError("Invalid value marked valid")
        rows.append((t, version, x, bool(ok)))
    return rows


def aggregate(rows, source_step, target_step):
    if target_step < source_step or target_step % source_step:
        raise ValueError("Aggregation requires an integer number of source bins")
    groups = {}
    for row in rows:
        key = row[0] // target_step * target_step
        groups.setdefault(key, []).append(row)
    result = []
    for t, group in sorted(groups.items()):
        expected = list(range(t, t + target_step, source_step))
        complete = [r[0] for r in group] == expected
        ok = complete and all(r[3] for r in group) and len({r[1] for r in group}) == 1
        value = math.fsum(r[2] for r in group) / len(group) if ok else math.nan
        result.append((t, group[0][1], value, ok))
    return result


def describe(rows, step):
    good = [r for r in rows if r[3]]
    pairs = [(a, b) for a, b in zip(rows, rows[1:])
             if a[3] and b[3] and b[0] - a[0] == step and a[1] == b[1]]
    increasing = [(a, b) for a, b in pairs if b[2] > a[2]]
    witness = None
    if increasing:
        a, b = max(increasing, key=lambda p: p[1][2] - p[0][2])
        witness = {"from_bin_start_utc": iso(a[0]), "to_bin_start_utc": iso(b[0]),
                   "from_value": a[2], "to_value": b[2], "version": a[1],
                   "positive_increment": b[2] - a[2],
                   "increment_divided_by_step_s": (b[2] - a[2]) / step}
    values = [r[2] for r in good]
    peak = max(good, key=lambda r: r[2]) if good else None
    return {"bin_s": step, "bins_present": len(rows), "valid_bins": len(good),
            "invalid_bins": len(rows) - len(good), "eligible_adjacent_pairs": len(pairs),
            "increasing_pairs": len(increasing),
            "min": min(values) if values else None,
            "median": statistics.median(values) if values else None,
            "max": peak[2] if peak else None,
            "max_bin_start_utc": iso(peak[0]) if peak else None,
            "max_positive_increment": witness,
            "zero_growth_when_pairs_but_no_increase": bool(pairs) and not increasing}


def source_tables(config):
    tables = {}
    for path, expected in config["source_hashes"].items():
        raw = subprocess.check_output(["git", "show", config["base_sha"] + ":" + path], cwd=ROOT)
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ValueError(f"Source hash mismatch: {path}")
        payload = gzip.decompress(raw) if path.endswith(".gz") else raw
        tables[Path(path).name] = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    return tables


def audit(config):
    frozen = {"cadence_s": 300, "aggregate_s": 3600,
              "historical_array_bits": 16777216, "g16_shield_mm": 3, "g19_shield_mm": 1,
              "policies": ["published_valid", "screened"]}
    if any(config[k] != v for k, v in frozen.items()):
        raise ValueError("Configuration no longer describes these frozen source products")
    tab = source_tables(config)
    g16 = tab["derived_rates.csv"]
    quality = tab["input_quality.csv"]
    g19 = tab["proton_rate_5min.csv"]
    fallback = {r["timestamp_utc"] for r in tab["fallback_rows.csv.gz"]
                if truth(r["historical_direction_median_fallback"])}
    if [r["timestamp_utc"] for r in quality] != [r["timestamp_utc"] for r in g16]:
        raise ValueError("G16 quality/rate timestamp mismatch")
    if not fallback <= {r["timestamp_utc"] for r in g19}:
        raise ValueError("G19 fallback timestamp missing from source")
    result = {"base_sha": config["base_sha"], "source_sha256": config["source_hashes"],
              "meaning": config["numeric_meaning"], "unit": "bit inversions / bit / s",
              "growth_unit": "bit inversions / bit / s^2 (difference of bin means divided by bin spacing)",
              "confidence_interval": None, "future_upper_bound": None, "series": {}}
    for name, rows in [("GOES16_3mm", g16), ("GOES19_1mm", g19)]:
        is16 = name.startswith("GOES16")
        times = [stamp(r["timestamp_utc"]) for r in rows]
        versions = ["3.2" if is16 else r["algorithm_version"] for r in rows]
        valid, warned, retro, incomplete = [], [], [], []
        for i, r in enumerate(rows):
            q = quality[i] if is16 else r
            paired = truth(q["east_valid"]) and truth(q["west_valid"])
            if is16:
                if truth(r["valid"]) != paired or stamp(r["end_utc"]) != times[i] + config["cadence_s"]:
                    raise ValueError("G16 validity/duration mismatch")
                warned.append(truth(r["warning_E"]) or truth(r["warning_W"]))
                retro.append(truth(r["retrospective_bridge_E"]) or truth(r["retrospective_bridge_W"]))
                incomplete.append(int(q["min_differential_samples"]) < 300 or
                                  int(q["min_integral_samples"]) < 300 or not truth(q["lut_match"]))
            else:
                warned.append(truth(r["east_quality_flag"]) or truth(r["west_quality_flag"]))
                retro.append(r["timestamp_utc"] in fallback)
                incomplete.append(False)  # sample counts absent from this derived CSV
            valid.append(paired)
        screened = [ok and not w and not r and not inc for ok, w, r, inc in zip(valid, warned, retro, incomplete)]
        if is16:
            # Verify historical normalization without treating nu_array as event rate.
            for r, ok in zip(rows, valid):
                if ok and not math.isclose(float(r["nu_array_s_1"]), float(r["lambda_bit_central_s_1"]) * config["historical_array_bits"], rel_tol=1e-12):
                    raise ValueError("G16 array normalization changed")
        summary = {"start_utc": iso(times[0]), "end_exclusive_utc": iso(times[-1] + config["cadence_s"]),
                   "rows": len(rows), "versions_rows": dict(Counter(versions)),
                   "missing_grid_bins": (times[-1] - times[0]) // config["cadence_s"] + 1 - len(rows),
                   "paired_invalid_rows": len(rows) - sum(valid), "warning_rows": sum(warned),
                   "retrospective_fallback_rows": sum(retro), "screened_rows": sum(screened),
                   "invalid_timestamps_utc": [iso(t) for t, ok in zip(times, valid) if not ok],
                   "g16_incomplete_samples_or_lut_rows": sum(incomplete) if is16 else None,
                   "diagnostics": {}}
        for direction in ("E", "W", "central"):
            column = f"lambda_bit_{direction}_s_1" if is16 else f"d1_lambda_{direction}_s-1"
            factor = 1 if is16 else 1 / config["historical_array_bits"]
            values = [numeric(r[column]) * factor for r in rows]
            by_policy = {}
            for policy, mask in [("published_valid", valid), ("screened", screened)]:
                rs = frame(times, versions, values, mask, config["cadence_s"])
                by_policy[policy] = {
                    "native": describe(rs, config["cadence_s"]),
                    "hourly": describe(aggregate(rs, config["cadence_s"], config["aggregate_s"]), config["aggregate_s"])}
            summary["diagnostics"][direction] = {"source_column": column, "factor_to_per_bit_s": factor, **by_policy}
        result["series"][name] = summary
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenerate task summary after tests")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_recipe.py")
    tests = unittest.TextTestRunner(verbosity=1).run(suite)
    if not tests.wasSuccessful():
        raise SystemExit(1)
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    result = audit(config)
    payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    target = HERE / "summary.json"
    if args.write:
        target.write_text(payload, encoding="utf-8", newline="\n")
    elif json.loads(target.read_text(encoding="utf-8")) != result:
        raise SystemExit("Stored summary differs; investigate inputs/code, do not replace accepted data")
    print(f"T37: {tests.testsRun} tests; four source hashes; two descriptive series verified.")


if __name__ == "__main__":
    main()

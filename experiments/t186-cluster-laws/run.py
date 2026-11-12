"""Reproduce the preregistered paired comparison. Requires Python, NumPy, Numba, SciPy."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter

import numba
import numpy as np
import scipy
from scipy.stats import beta

import engine as e
from inputs import CFG, HERE, NS, Profile, generate
from verify import geometry


def clopper_pearson(hits, n, alpha):
    lower = 0.0 if hits == 0 else float(beta.ppf(alpha / 2, hits, n - hits + 1))
    upper = 1.0 if hits == n else float(beta.isf(alpha / 2, hits + 1, n - hits))
    return [lower, upper]


def exact_sum(column):
    # Per-row nanoseconds fit int64. Totals over a decade of replicas do not.
    return int(np.sum(column // NS)) * NS + int(np.sum(column % NS))


def one_case(profile, pi, li, batches, family):
    size = CFG["batch_size"]
    strides = np.asarray([0] + [2**x for x in profile.spec["fixed_log2_L"]], dtype=np.int64)
    totals = [[0] * len(e.FIELDS) for _ in strides]
    discord = [[0, 0] for _ in strides]
    digest = hashlib.sha256()
    multiplicities = np.zeros(6, dtype="int64")
    for batch in range(batches):
        times, words, bits, edges, parents, multi = generate(profile, pi, li, batch, size)
        assert len(bits) == len(times) == len(words) == edges[-1]
        assert len(multi) == parents.sum() and multi.sum() == len(bits)
        multiplicities += np.bincount(multi, minlength=6)
        for arr in (parents, multi, times, words, bits):
            digest.update(np.asarray([len(arr)], dtype="<i8").tobytes())
            digest.update(np.asarray(arr, dtype="<i8").tobytes())
        stats = e.block(times, words, bits, edges, profile.horizon, strides)
        fails = stats[:, :, e.FIRST] >= 0
        for j in range(len(strides)):
            totals[j][e.FIRST] += int(fails[j].sum())
            for k in range(1, len(e.FIELDS)):
                totals[j][k] += exact_sum(stats[j, :, k])
            discord[j][0] += int(np.count_nonzero(fails[j] & ~fails[0]))
            discord[j][1] += int(np.count_nonzero(fails[0] & ~fails[j]))
    n = size * batches
    rows = []
    for j, total in enumerate(totals):
        k = total[e.FIRST]
        assert k - totals[0][e.FIRST] == discord[j][0] - discord[j][1]
        upper = clopper_pearson(k, n, CFG["alpha"] / family)
        port = (total[e.READ_NS] + total[e.WRITE_NS]) / n / NS
        label = "below" if upper[1] < CFG["comparison_probability"] else (
            "above" if upper[0] > CFG["comparison_probability"] else "unresolved")
        row = {
            "mode": "ladder" if not j else f"fixed_{strides[j]}L",
            "period_ns": int(strides[j]) * e.L if j else None,
            "first_exceedances": k, "Q_estimate": k / n,
            "CP95": clopper_pearson(k, n, CFG["alpha"]), "CP95_family": upper,
            "against_0p001_family": label,
            "port_s_mean": port, "port_pct_mean": 100 * port / profile.spec["T_s"],
            "resets_mean": total[e.RESETS] / n, "reset_cells_mean": total[e.CELLS] / n,
            "positive_reports_mean": total[e.REPORTS] / n,
            "downshifts_mean": total[e.DOWNS] / n, "switches_mean": total[e.SWITCHES] / n,
            "fast_s_mean": total[e.FAST_NS] / n / NS,
            "failed_only_here_vs_ladder": discord[j][0], "failed_only_ladder_vs_here": discord[j][1],
            "totals": dict(zip(e.FIELDS[1:], total[1:])),
        }
        rows.append(row)
    fixed = rows[1:]
    return {"law": CFG["laws"][li]["id"], "n": n, "parents_by_size_0_to_5": multiplicities.tolist(),
            "shared_input_sha256": digest.hexdigest(), "rows": rows,
            "largest_tested_below_ns": max((r["period_ns"] for r in fixed if r["against_0p001_family"] == "below"), default=None),
            "smallest_tested_above_ns": min((r["period_ns"] for r in fixed if r["against_0p001_family"] == "above"), default=None),
            "unresolved_fixed_ns": [r["period_ns"] for r in fixed if r["against_0p001_family"] == "unresolved"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True, help="directory containing T141 bands.npy")
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    parser.add_argument("--pilot", action="store_true", help="time the first block per case; do not write results")
    parser.add_argument("--check", action="store_true", help="compare the full run to the stored numbers")
    args = parser.parse_args()
    family = len(CFG["laws"]) * sum(1 + len(p["fixed_log2_L"]) for p in CFG["profiles"])
    assert family == 136 and CFG["trials_per_law_profile"] % CFG["batch_size"] == 0
    batches = 1 if args.pilot else CFG["trials_per_law_profile"] // CFG["batch_size"]
    config_digest = hashlib.sha256((HERE / "inputs.json").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    result = {"basis_sha": CFG["base"], "protocol_commit": "c6a54e0d02233a21015d8429efd329ed7a4ce444",
              "inputs_sha256_lf": config_digest, "family_rows": family,
              "geometry_P_intersection": geometry(), "profiles": {}}
    print(f"Python {platform.python_version()}, numpy {np.__version__}, numba {numba.__version__}, scipy {scipy.__version__}", flush=True)
    start = perf_counter()
    for i, spec in enumerate(CFG["profiles"]):
        profile = Profile(spec, args.cache)
        cases = []
        for j, law in enumerate(CFG["laws"]):
            t0 = perf_counter()
            cases.append(one_case(profile, i, j, batches, family))
            print(f"{spec['id']} / {law['id']} {batches * CFG['batch_size']} paths, {perf_counter() - t0:.2f} s", flush=True)
        result["profiles"][spec["id"]] = {"input": profile.notes, "cases": cases}
    print(f"Total {perf_counter() - start:.2f} s", flush=True)
    if args.pilot:
        return
    if args.check:
        assert json.loads(args.output.read_bytes()) == result, "replay differs from saved results"
        print("Full replay matches the stored result")
    else:
        with args.output.open("w", encoding="utf-8", newline="\n") as out:
            json.dump(result, out, ensure_ascii=False, indent=2, allow_nan=False)
            out.write("\n")


if __name__ == "__main__":
    main()

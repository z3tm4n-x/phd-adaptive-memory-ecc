"""A2 order-of-magnitude check; no adaptive certificate or physical validation.

Run from any directory. Inputs are pinned accepted repository blobs. Rational
arithmetic is used until display; floating log values are illustrative only.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import sys

PINS = {
    "theory/t57-t58-diagnostic-inputs.json": "fceae13705f7c12fd9fd4886c31a4f51af4d011d",
    "theory/t57_uniform_budget.py": "2d16b0a94255ecb1873579929cae369e39382904",
    "experiments/t126-regime-map/outputs/map.json": "420185e63f2eb7b6eb05057532738d2d4d49c8e4",
}


def number(x):
    return {"exact": str(x), "decimal": float(x)}


def analyze(root):
    for name, expected in PINS.items():
        data = (root / name).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if actual != expected:
            raise ValueError(f"Input changed: {name}: {actual} != {expected}")
    sys.path.insert(0, str(root / "theory"))
    import t57_uniform_budget as t57
    h = t57.snapshot()["history"]
    T, B, b, FS, fluence, s2 = [F(h[k]) for k in (
        "T_s", "B_per_bit_s_inverse", "bbar_per_bit_s_inverse", "FS_per_bit",
        "F_per_bit", "S2_per_bit_s_inverse")]
    assert fluence == b * T + FS
    assert s2 == b * b * T + (B + b) * FS
    eps, n = F(".01"), 39
    ideal_gain = T * s2 / fluence**2
    points = []
    for W in (262144, 1935832):
        peak, quiet = n * W * B, n * W * b
        coefficient = W * (n * (n - 1) // 2) * s2
        period = eps / coefficient
        for rate in (64000000, 256000000):
            full_pass = F(W * n, rate)
            price = full_pass / period
            points.append(dict(
                W=W, R_eff_bit_s=rate,
                peak_parent_rate_s_inverse=number(peak),
                quiet_parent_rate_s_inverse=number(quiet),
                ideal_peak_mean_wait_s=number(1 / peak),
                ideal_quiet_mean_wait_s=number(1 / quiet),
                ideal_peak_one_event_95pct_s=-math.log(.05) / float(peak),
                expected_parents=number(n * W * fluence),
                full_busy_pass_s=number(full_pass),
                pair_approx_constant_period_s=number(period),
                pair_approx_constant_bus_fraction=number(price),
                clairvoyant_pair_relaxation_bus_fraction=number(price / ideal_gain)))
    rows = json.loads((root / "experiments/t126-regime-map/outputs/map.json").read_text())["rows"]
    accepted = []
    for row in rows:
        if (row["family"] == "R0B_grid" and row["W"] == 1935832
                and F(row["epsilon"]) == eps and F(row["quiet_budget"]) == F(".01")):
            accepted.append({"id": row["id"], "R_eff_bit_s": row["R_eff_bit_s"],
                             **{k: number(F(row[k])) for k in (
                                 "P_min", "risk_at_resource_boundary", "Q_lower_at_budget")},
                             "constant_excluded_at_quiet_1pct": row["constant_excluded_T58"],
                             "adaptive_mission_upper": row["adaptive_mission_upper"],
                             "quiet_gain_lower": row["quiet_gain_lower"]})
    p = t57.model(1935832, 256000000)
    resource = {peak: number(t57.first_resource_tick(p, F(peak)) * p.tick)
                for peak in (".05", ".25", ".5")}
    return dict(
        kind="preflight_not_certificate", accepted_base="e63964c2b9ddf6a53fe9c76bd5942f458f167f8e",
        source_blobs=PINS, n=n, epsilon=str(eps), T_s=str(T),
        W_ratio=number(F(1935832, 262144)),
        B_to_b_ratio=number(B / b),
        clairvoyant_pair_relaxation_gain=number(ideal_gain),
        eta_background_reference_not_gain=number(s2 / (b*b*T)),
        points=points, accepted_T126_rows=accepted,
        T57_layer_launch_ceiling_s=number(t57.launch_ceiling(p)),
        T57_resource_period_s_by_peak=resource,
        limitations=["Dstar=0 only in independent uniform singleton diagnostic full39 class",
                     "ideal gain assumes known future and pair-cost approximation; not a causal guarantee or universal upper bound",
                     "parent event rates are not observed ERR rates; actual observation and decision delays unpaid in idealization",
                     "T57 launch ceiling excludes its affine-price layer only; T126 P_min belongs to a different resource family",
                     "25pct peak is a different point of the original grid, not validation under the 5pct contract"],
        proposed_large_gain=dict(threshold=5, author_approved=False,
            metric="lower cost of the whole declared constant class / upper adaptive cost; lifetime mean protection and control interface occupancy; equal nonzero useful workload",
            separate_costs="total bus, calm interval, CPU, LUT/FF/BRAM, latency, observations and recovery"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(analyze(args.repo_root.resolve()), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")

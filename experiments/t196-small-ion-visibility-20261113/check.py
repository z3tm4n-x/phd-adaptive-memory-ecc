"""Directed substitutions for the small-parent visibility test on the #473 map."""
import argparse
import hashlib
import json
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
from runpy import run_path


HERE = Path(__file__).resolve().parent
MAIN_CASE = HERE.parent / "t196-cluster-main-20261112"
model = run_path(str(MAIN_CASE / "calculate.py"))
reviewed = json.loads((MAIN_CASE / "result.json").read_bytes())
W, C, T, EPS, DELTA = (model[k] for k in ("W", "C", "T", "EPS", "DELTA"))
up, down = model["up"], model["down"]
scan = model["SCAN"]
assert W == 32768 and W*C == F(1, 16)


def verify_mark_inequality():
    # Four words, two bits per word. Include direct marks in both size classes
    # and allow either one closed word or no active aperture.
    checked = 0
    for size in range(1, 5):
        for positions in combinations(range(8), size):
            words = {bit//2 for bit in positions}
            direct = len(words) < size
            large = size >= 3
            for closed in (None, 0, 1, 2, 3):
                visible = not large and not direct and bool(words - {closed})
                hidden_touch = not direct and closed in words
                assert size <= (size*large + 2*(direct and not large)
                                + 2*int(visible) + int(hidden_touch))
                checked += 1
    return checked


def result():
    anchor, counts = model["COMMON"], model["COUNTS"]
    minimum = model["HISTORY"]
    assert minimum == [model["XI_LO"]*(n*anchor-scan.drain)-2*model["J"] for n in counts]
    assert len(counts) == 8 and all(0 < first < second for first, second in zip(minimum, minimum[1:]))
    first_nominal = counts[0]*anchor - scan.drain - 2*model["J"]
    max_pair_gap = model["XI_HI"]*anchor+2*model["J"]+model["DE"]

    profiles = model["profiles"]()
    domains = {}
    for key, profile in zip(("geo", "reconstructions"), profiles):
        threshold = reviewed["thresholds"][key]
        eta, low = F(threshold["eta_sufficient"]), F(threshold["eta_fail"])
        q_pass = sum(model["risk"](eta, profile))
        assert up(q_pass, 12) == threshold["certificate_at_pass_upper"]
        assert q_pass <= EPS < sum(model["risk"](low, profile))
        m_small = 2
        needed = m_small*eta
        cap = 1-needed
        geom_cap = cap-F(1, W)
        assert geom_cap > 0
        # A distribution may put all inversions into distinct-word triples on I,
        # and singleton parents outside. The total profile and its word marginals
        # are unchanged. This is an upper on its whole-term large-inversion share,
        # valid even without assuming constant total rate.
        lifetime_share = profile.peak*first_nominal/(model["B0"]*T)
        assert lifetime_share < geom_cap < cap
        # Every pair of distinct residual parents responsible for an accumulation
        # stop lies in the same word with time separation at most max_pair_gap.
        blind_q = DELTA + W*C**2*max_pair_gap*profile.second
        assert EPS < blind_q < 1
        domains[key] = {
            "required_visible_parents_per_inversion": str(eta),
            "required_product_v_times_one_minus_f": str(needed),
            "max_large_inversion_share_at_v1": str(cap),
            "required_visible_share_if_no_large_percent_up": up(100*needed, 9),
            "max_large_inversion_share_at_v1_percent_down": down(100*cap, 9),
            "geometric_max_large_plus_small_direct_inversion_share": str(geom_cap),
            "geometric_max_large_plus_small_direct_percent_down": down(100*geom_cap, 9),
            "visible_floor_from_engineering_data": "0",
            "Q_upper_if_window_test_met": up(q_pass, 12),
            "max_gap_only_Q_upper": up(blind_q, 12),
            "local_all_triples_terminal_large_share_upper": up(lifetime_share, 12),
        }
    return {"T_s": int(T), "W": W, "epsilon_acc": str(EPS), "execution_quota": str(DELTA),
            "toy_mark_cases_checked": verify_mark_inequality(),
            "required_complete_cells": counts,
            "minimum_history_s_lower": [down(t, 9) for t in minimum],
            "first_nominal_history_s": str(first_nominal),
            "fixed_gap_upper_s": up(max_pair_gap, 12),
            "domains": domains}


def check_handoff(path, report):
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest() == "44f0657d562a0cd520f11e211d66066e2fa92b0a"
    handoff = json.loads(raw)
    for key, row in report["domains"].items():
        source = handoff["visibility"][key]
        assert row["required_visible_parents_per_inversion"] == source["eta"]
        assert row["required_product_v_times_one_minus_f"] == source["min_visible_fraction_of_small_parents_if_no_large_and_m2"]
        assert row["max_large_inversion_share_at_v1"] == source["max_large_inversion_fraction_if_all_small_visible_and_m2"]
    for key, numerator, denominator in (("low", 4042, 8461), ("pin", 885, 8640)):
        counts = handoff["total"][key]
        assert (counts["cells_in_large"], counts["unique_cells"]) == (numerator, denominator)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--handoff", type=Path, help="result.json from the engineering #477 SHA")
    args = parser.parse_args()
    report = result()
    if args.handoff is not None:
        check_handoff(args.handoff, report)
    if args.check:
        assert report == json.loads((HERE/"result.json").read_bytes())
        print("Two domains, eight history lengths and directed bounds match.")
    else:
        print(json.dumps(report, indent=2))

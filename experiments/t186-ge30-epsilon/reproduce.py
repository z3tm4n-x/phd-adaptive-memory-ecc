"""Four lifetime tolerances on the frozen, exactly two-word GE30-45 contract (#448)."""

import argparse
import json
import sys
from fractions import Fraction as F
from math import ceil, comb, floor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCEPTED = HERE.parent / "t186-advisor-ge30-20261110"
sys.path.insert(0, str(ACCEPTED))
import bounds as ge


def directed(value, places, *, up):
    scale = 10**places
    units = (ceil if up else floor)(value * scale)
    whole, decimal = divmod(abs(units), scale)
    sign = "-" if units < 0 else ""
    return f"{sign}{whole}.{decimal:0{places}d}"


def upper(value, places=3):
    return directed(value, places, up=True)


def lower(value, places=3):
    return directed(value, places, up=False)


def price(value, *, up):
    # The common initial scan is only milliseconds over a ten-year horizon.
    emit = upper if up else lower
    return {
        "seconds": emit(value, 12 if value < 1 else 3),
        "percent_of_T": emit(100 * value / ge.T, 16 if value < 1 else 6),
    }


def witness_limit():
    """P -> infinity in #448 lower(P, True): ell/P+2 becomes exactly 2."""
    plateau = F(ge.C1["lower_witness_plateau_used_s"])
    blocks = ceil(plateau / 10)
    span = plateau / blocks
    rate = ge.c * ge.B
    m = rate * span
    shared = m / (ge.W - 1)
    overlap = m**4 / 4 + shared * m**2 + shared**2 / 2
    free = max(0, span - 2 * ge.d)
    one = F(38, 78) * (1 - m) * rate**2 * free**2 / 3
    mass = blocks * max(0, ge.W * one - comb(ge.W, 2) * overlap)
    return max(0, mass / (1 + mass) - ge.delta)


def cutoff(epsilon, limit):
    """Return strict excluded right endpoint and nonexcluded left endpoint."""
    if limit <= epsilon:
        return None
    left, right = F(0), F(1)
    while ge.lower(right, True) <= epsilon:
        right *= 2
    while right - left > F(1, 10**12):
        middle = (left + right) / 2
        if ge.lower(middle, True) > epsilon:
            right = middle
        else:
            left = middle
    assert ge.lower(left, True) <= epsilon < ge.lower(right, True)
    return left, right


def candidate(epsilon):
    first = ge.fixed(1)["Q_upper"]
    if first > epsilon:
        return None
    slope = ge.fixed(2)["Q_upper"] - first
    k = 1 + floor((epsilon - first) / slope)
    ledger = ge.fixed(k)
    assert ledger["Q_upper"] <= epsilon < ge.fixed(k + 1)["Q_upper"]
    return k, ledger


def calculate():
    accepted = json.loads((ACCEPTED / "bounds.json").read_text(encoding="utf-8"))
    adaptive = accepted["binary_split"]["32"]
    stop = F(adaptive["Qstop_upper"]["exact"])
    base_upper = F(adaptive["budget_d0"]["known_bus_s"]["exact"])
    per_invalid = F(adaptive["bus_s_per_recognized_invalid"]["exact"])
    assert adaptive["quiet_cells"] == 205 and stop == F("0.000880198")
    min_period = ge.L * ge.xm - 2 * ge.J
    slow_gap = 32 * ge.L * ge.xp + 2 * ge.J
    # No post-stop service assumption is needed for this lower bound.
    adaptive_lower = (1 - stop) * ge.W * (ge.T / slow_gap - 2) * ge.read_lo
    limit = witness_limit()
    assert ge.lower(ge.T, True) < limit

    result = {
        "source_pr448": "873465fcc24e151cccd5c735863250c4bbd70cda",
        "T_seconds": int(ge.T),
        "min_physical_period_lower_s": lower(min_period, 12),
        "witness_Q_lower_at_min_physical_period": lower(ge.lower(min_period, True), 12),
        "witness_Q_lower_at_nominal_L_on_witness_clock": lower(ge.lower(ge.L * ge.xp, True), 12),
        "witness_Q_limit_at_infinity_upper": upper(limit, 12),
        "adaptive": {
            "history_cells": adaptive["quiet_cells"],
            "Q_upper": upper(stop, 9),
            "mandatory_read_price_lower": price(adaptive_lower, up=False),
            "known_price_upper_at_I0": price(base_upper, up=True),
            "seconds_per_invalid_upper": upper(per_invalid, 6),
        },
        "rows": {},
    }

    for label in ("0.1", "0.01", "0.001", "0.0001"):
        epsilon = F(label)
        bracket = cutoff(epsilon, limit)
        test = candidate(epsilon)
        row = {
            "fixed_candidate": None,
            "class_price_lower": None,
            "cutoff_bracket_s": [lower(bracket[0], 12), upper(bracket[1], 12)] if bracket else None,
            "adaptive_risk_certified": stop <= epsilon,
        }
        result["rows"][label] = row
        if test is None:
            # Failed sufficient risk test alone would leave admissibility open.
            assert bracket and bracket[1] < min_period
            assert ge.lower(min_period, True) > epsilon
            row["comparison"] = "fixed_class_empty"
            continue

        k, ledger = test
        candidate_cost = ledger["bus_upper_s"]
        row["fixed_candidate"] = {
            "k": k,
            "period_s": upper(ledger["P_nominal"], 9),
            "Q_upper": upper(ledger["Q_upper"], 9),
            "known_price_upper": price(candidate_cost, up=True),
        }
        if bracket:
            # Same arbitrary-phase and two-edge allowance as #448 floor_price().
            necessary_reads = (1 - ge.delta) * ge.W * (ge.T / (bracket[1] + 2 * ge.J) - 2)
            row["first_excluded_grid_k"] = ceil(bracket[1] / (ge.L * ge.xp))
        else:
            necessary_reads = (1 - ge.delta) * ge.W  # mandatory initial pass
        class_floor = necessary_reads * ge.read_lo
        row["class_price_lower"] = price(class_floor, up=False)
        margin = class_floor / 2 - base_upper
        row["sufficient_X_plus_cI_budget_s_floor"] = lower(margin)
        row["half_candidate_known_price_upper_s"] = upper(candidate_cost / 2)
        assert row["adaptive_risk_certified"] and class_floor <= candidate_cost
        if margin >= 0:
            row["comparison"] = "sufficient_with_overhead_budget"
        elif 2 * adaptive_lower > candidate_cost:
            row["comparison"] = "excluded_for_known_work"
            row["fixed_extra_price_strictly_below_s_excludes_full_2x"] = lower(
                2 * adaptive_lower - candidate_cost
            )
        else:
            row["comparison"] = "open_from_current_bounds"

        if epsilon == F(1, 1000):
            assert class_floor == F(accepted["exact_two_word_class"]["fixed_class_bus_lower_s"]["exact"])
            assert margin == F(adaptive["budget_d0"]["paired_extra_s"]["exact"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check the published four rows")
    args = parser.parse_args()
    text = json.dumps(calculate(), indent=2) + "\n"
    output = HERE / "result.json"
    if args.check:
        if text != output.read_text(encoding="utf-8"):
            parser.exit(1, "Published results differ from the recomputed slice\n")
        print("OK: four tolerances, two-word tail, published #448 anchor and cost signs")
    else:
        output.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

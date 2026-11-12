"""Task 1.2. Parent visibility and necessary bus seconds on each eligible map."""
import argparse
import json
from fractions import Fraction as F
from math import ceil, floor
from pathlib import Path
from runpy import run_path


HERE = Path(__file__).resolve().parent
ARCHIVE = run_path(str(HERE.parent / "t196-archive-same-map-20261110/calculate.py"))
BASE = ARCHIVE["base"]
A, L, C, T = (ARCHIVE[key] for key in ("A", "L", "C", "T"))
LO, HI = ARCHIVE["W_LO"], ARCHIVE["W_HI"]
XI_LO, XI_HI, J, APERTURE = (ARCHIVE[key] for key in ("XI_LO", "XI_HI", "J", "D_E"))
READ, EPS, DELTA = BASE["READ"], BASE["EPS"], BASE["DELTA"]
DEAD = XI_HI * L + APERTURE
BITS = 38
DISTINCT = F(BITS - 1, BITS)
LAWS = {
    "single": (F(1), 1, F(1)),
    "two_uniform": (F(2), 2, F(0)),
    "compact_1p2": (F(6, 5), 2, F(4, 5)),
    "compact_5": (F(5), 5, F(0)),
}


def down(value, digits):
    return BASE["emit"](value, digits, upward=False)


def both_word_ratio(law, words, distance):
    """Shared parent mean / word mean for distinct words at ring distance d."""
    assert 1 <= distance <= words // 2
    if law == "single":
        return F(0)
    if law == "two_uniform":
        return F(1, words - 1)
    if law == "compact_1p2":
        return F(int(distance == 1), 6)
    if law == "compact_5":
        return F(max(0, 5 - distance), 5)
    raise ValueError(law)


def overlap_success(law, words):
    """W times P(two independent parents exceed in at least one shared word | clean)."""
    p = DISTINCT
    if law == "single":
        return p
    if law == "two_uniform":
        return 4 * p - 2 * p**2 / (words - 1)
    if law == "compact_1p2":
        return F(36, 25) * p - p**2 / 25
    if law == "compact_5":
        return 1 - F(1, BITS**5) + 2 * sum(1 - F(1, BITS**i) for i in range(1, 5))
    raise ValueError(law)


def plateau():
    b, peak = BASE["B0"], BASE["B"]
    duration = F(BASE["C1"]["plateau_s"])
    first = duration * peak + (T - duration) * b
    second = duration * peak**2 + (T - duration) * b**2
    assert 1 < duration < T and first == BASE["S1"] and second <= BASE["S2"]
    assert 0 < peak - b <= BASE["U"]
    return peak, peak - b, floor(second)


def exclusion(law, witness, cap):
    """Lower Q for every physical P >= cap/W, on a fixed witness."""
    b, variation, s2_lower = witness
    mean, _, _ = LAWS[law]
    p_star = F(cap, LO)
    max_parents = 2 * cap * C * b / mean
    relative_dead = DEAD * HI / cap
    loss = DEAD * (b**2 + 4 * b * variation) + (1 + 4 * p_star) * b**2 + p_star * b * variation
    profile = (1 - relative_dead)**2 * s2_lower - loss
    if relative_dead >= 1 or max_parents >= 1 or profile <= 0:
        return F(0)
    coefficient = overlap_success(law, LO) / mean**2
    z = (1 - max_parents) * C**2 * cap / 2 * coefficient * profile
    return max(F(0), z / (1 + z) - DELTA)


def certified_cap(law, witness):
    low = ceil(2 * HI * DEAD)
    if exclusion(law, witness, low) > EPS:
        return low
    high = low
    while exclusion(law, witness, high) <= EPS:
        low, high = high, 2 * high
        if 2 * high * C * witness[0] >= LAWS[law][0]:
            raise ValueError("No certified crossing in the registered doubling procedure")
    while high - low > 1:
        mid = (low + high) // 2
        if exclusion(law, witness, mid) > EPS:
            high = mid
        else:
            low = mid
    assert exclusion(law, witness, low) <= EPS < exclusion(law, witness, high)
    return high


def fixed_floor(words, cap):
    n = T * words / (cap + 2 * J * HI) - 2
    return (1 - DELTA) * A * (XI_LO * READ - 2 * J) * n


def price_at(cap, risk_lower):
    ends = []
    for words in (LO, HI):
        seconds = fixed_floor(words, cap)
        ends.append({"W": words, "P0_s_upper": BASE["emit"](F(cap, words), 9),
                     "bus_s_lower": down(seconds, 3), "bus_percent_lower": down(100 * seconds / T, 6)})
    return {"K_word_s": int(cap), "Q_lower": down(risk_lower, 12), "endpoints": ends}


def price(law, witness):
    cap = certified_cap(law, witness)
    return price_at(cap, exclusion(law, witness, cap))


def result():
    archive = ARCHIVE["histories"]()
    archive_witness = (F(archive["B_witness_upper"]), F(archive["U_witness_upper"]),
                       archive["S2_witness_lower_used"])
    geo_witness = plateau()
    assert archive["start_bin"] == 2362840 and archive["number_bins"] == 1051920
    fixed_q = BASE["physical_q"](ARCHIVE["scan"], HI, F("0.0934444") / L)
    assert fixed_q < EPS
    previous_cap = ARCHIVE["CAP"]
    previous_lower = F(ARCHIVE["witness_test"](archive)["physical_Q_lower"])
    scan = ARCHIVE["scan"]
    thresholds = BASE["thresholds"](scan, 8)
    histories = [XI_LO * (n * 256 * L - scan.drain) - 2 * J for n in thresholds]
    out = {}
    for law, (mean, maximum, single) in LAWS.items():
        visible = (LO - single) * C / mean
        coarse = (LO - 1) * C / maximum
        multiplicity = overlap_success(law, LO)
        out[law] = {
            "mean": str(mean), "maximum": maximum,
            "one_excluded_Wmin": {
                "rate_over_reference_rate": str(visible),
                "cap_rate_over_reference_rate": str(coarse),
                "visible_parents_per_s_at_b_lower": down(visible * BASE["B0"], 12),
                "visible_parents_per_s_at_B_lower": down(visible * BASE["B"], 12),
                "live_admission_first_level_at_B_upper": BASE["emit"](
                    BASE["exp_upper"](visible * BASE["B"] * histories[0]), 6),
                "live_admission_top_level_at_b_upper": BASE["emit"](
                    BASE["exp_upper"](visible * BASE["B0"] * histories[-1]), 6),
            },
            "W_times_two_parent_success_at_Wmin": str(multiplicity),
            "W_times_overlap_correction_at_Wmin": str(DISTINCT * mean**2 - multiplicity),
            "shared_rate_over_word_rate_d1_to_5": [str(both_word_ratio(law, LO, d)) for d in range(1, 6)],
            "geo": price(law, geo_witness), "archives": price(law, archive_witness),
        }
        if law in ("single", "two_uniform"):
            # Every pair has rho <= mu/(W-1) at any W in these laws. The word
            # terms in the accepted per-word free-interval test are unchanged.
            out[law]["archives_word_phase_bound_462"] = price_at(previous_cap, previous_lower)
    return {"W_min": LO, "W_max": HI, "T_s": int(T),
            "reference_words": int(1 / C), "seconds_dead_upper": str(DEAD),
            "guaranteed_history_s_lower": [down(h, 9) for h in histories],
            "geo_witness_S2_lower_per_s": geo_witness[2],
            "archive_witness": archive["start"], "archive_S2_lower_per_s": archive_witness[2],
            "fixed_0p0934444s_Q_upper": BASE["emit"](fixed_q, 12), "laws": out}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = result()
    if args.check:
        assert data == json.loads((HERE / "bounds.json").read_bytes())
        print("Exact bounds, directed prices and four laws match bounds.json.")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))

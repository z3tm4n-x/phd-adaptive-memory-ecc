"""One registered 256 KiB GEO row. Exact rational bounds and outward rounding."""
import argparse
import json
from fractions import Fraction as F
from math import floor
from pathlib import Path
from runpy import run_path


HERE = Path(__file__).resolve().parent
EXP = HERE.parent
ref = run_path(str(EXP / "t186-native-cost-map/calculate.py"))
old = json.loads((EXP / "t504-large-bank/result.json").read_bytes())
row = next(r for r in old["rows"] if r["MiB"] == "1/4")
up, down = ref["up"], ref["down"]


def two_phase_risk(ladder, profile):
    period, aperture = ladder.scan.L, ref["DE"]
    clock, weight = ref["XP"], ref["weight"]
    half = clock * period / 2
    fast = half + aperture
    levels = [period, *ladder.levels[1:]]
    amplitudes = [half, *ladder.amplitude]
    history = [ladder.history[0], *ladder.history]
    rate = ladder.words * ref["C"] * ladder.eta

    def coefficient(x):
        return fast + sum(a * weight(rate * h * x) for a, h in zip(amplitudes, history))

    b, T = ref["B0"], ref["T"]
    slope = max(hi_b * coefficient(lo) for lo, hi_b in ref["REVIEW"]["strips"](profile.peak))
    integrated = T * b**2 * coefficient(b) + (profile.exposure - b*T) * slope
    overlap = fast * ref["aperture"](profile, period/2)
    overlap += sum(a * ref["aperture"](profile, p) for a, p in zip(amplitudes, levels))
    mass = profile.peak * clock * ladder.levels[-1]
    kernel = mass / (1-weight(rate * mass)) + profile.peak * clock * ladder.scan.phase_max
    rises = (1 + 1/F("2.71828")**2) * profile.rise * sum(amplitudes) * kernel
    pair = ladder.words * ref["C"]**2 / 2
    return ref["DELTA"], pair * integrated, pair * overlap, pair * rises


def calculate():
    ladder = ref["Ladder"](row["words"])
    env, c, T = ref["GEO"], ref["C"], ref["T"]
    cr, cw, hard = ref["READ"], ref["WRITE"], ref["HARD"]
    xp, xm, jitter = ref["XP"], ref["XM"], ref["J"]
    assert row["words"] == 65536 and row["addresses_x16"] == 2*ladder.words
    assert row["zero_cell_counts"] == ladder.counts == [10, 19, 38, 75, 149, 298, 596]
    assert row["eta"] == str(ladder.eta) and F(row["L_local_s"]) == ladder.scan.L
    prior = ladder.risk(ladder.eta, env)
    assert [up(t, 15) for t in prior] == row["ladder"]["q_terms_upper"]
    terms = two_phase_risk(ladder, env)
    stop = sum(terms)
    eps = F(old["epsilon_accumulation"])

    # Only the stop probability changes in the after-stop tariff.
    hits = (ladder.words+1) * c * env.exposure
    anchor = ladder.levels[-1]
    mask = min(env.exposure, (ladder.fast+2*jitter) * (
        env.exposure/(xm*anchor) + 2*(env.peak+env.rise)))
    cells = min(hits, ladder.words*c*(env.exposure+mask)/ref["MEAN"])
    start, reset = ladder.fees
    before_read, before_write = start + reset*(1+cells), cw*hits
    tail = stop * (cr+cw) * hard
    price = before_read + before_write + tail
    old_price = before_read + before_write + sum(prior)*(cr+cw)*hard
    assert up(old_price, 3) == row["ladder"]["s_upper"]

    top_real = xp*anchor + 2*jitter
    fast_per_reset = (ladder.counts[0]+1)*top_real
    fast_time = min(T, xp*ladder.scan.L + jitter + fast_per_reset*(1+cells) + stop*T)
    price_floor = (1-stop)*ladder.scan.addresses*ref["READ_LO"]*(T/top_real-2)
    # State sufficient extra-cost budgets using the printed, conservative prices.
    fixed = F(row["fixed"]["s_lower"])
    quoted = F(up(price, 3))
    reset_upper = F(up(reset, 6))
    return {
        "base": "b2b9871e4e810411d9f078881248d1322f79f388",
        "registered": "e41909cb667584149217b2a80945f7e3fba552ec",
        "word_count": ladder.words, "local_scan_s": str(ladder.scan.L),
        "zero_cell_counts": ladder.counts, "visibility_parents_per_inversion": str(ladder.eta),
        "old_stop_upper": up(sum(prior), 12),
        "old_terms_upper": [up(t, 15) for t in prior],
        "new_terms_upper": [up(t, 15) for t in terms],
        "physical_Q_lower_from_plateau": row["ladder"]["Q_lower"],
        "stop_upper_also_bounds_physical_Q": up(stop, 12),
        "certified": stop <= eps, "epsilon_minus_stop_lower": down(eps-stop, 12),
        "reduction_of_certificate_lower": down(sum(prior)-stop, 12),
        "pre_stop_read_s_upper": up(before_read, 6), "pre_stop_write_s_upper": up(before_write, 6),
        "post_stop_bus_s_upper": up(tail, 6), "price_s_lower": down(price_floor, 3),
        "price_s_upper": up(price, 3), "price_percent_upper": up(100*price/T, 6),
        "reset_bus_s_upper": up(reset, 6), "true_cells_upper": up(cells, 6),
        "fast_s_upper": up(fast_time, 3), "fast_percent_upper": up(100*fast_time/T, 6),
        "extra_fast_s_per_reset_upper": up(fast_per_reset, 6),
        "peak_sliding_1400ns_percent_upper": old["port"]["sliding_1400ns_peak_pct_upper"],
        "best_fixed_s_lower": row["fixed"]["s_lower"],
        "sufficient_fixed_candidate_s_upper": row["fixed"]["quote"]["s_upper"],
        "saved_s_lower": down(fixed-quoted, 3), "fixed_over_ladder_lower": down(fixed/quoted, 6),
        "twofold_extra_s_lower": down(fixed/2-quoted, 3),
        "twofold_whole_resets_X0": floor((fixed/2-quoted)/reset_upper),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    path = HERE / "result.json"
    result = calculate()
    if parser.parse_args().check:
        assert result == json.loads(path.read_bytes())
        print("Registered GEO risk, after-stop cost and budgets match.")
    else:
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

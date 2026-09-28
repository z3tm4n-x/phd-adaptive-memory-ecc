"""Bounded T44 calculations. No simulation, transport, controller or optimizer."""
from collections import Counter
from decimal import Decimal, localcontext, ROUND_FLOOR
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def blob(sha, path):
    return subprocess.check_output(["git", "show", f"{sha}:{path}"], cwd=ROOT)


def decimal_fraction(x):
    return Decimal(x.numerator) / Decimal(x.denominator)


def sum_integers(k):
    return k * (k + 1) // 2 if k >= 0 else 0


def sum_squares(k):
    return k * (k + 1) * (2 * k + 1) // 6 if k >= 0 else 0


def affine_squares(c, step, first, last):
    """Exact sum of positive (c-j*step)^2 over the indicated integer range."""
    last = min(last, c // step)
    if last < first:
        return Fraction(0)
    count = last - first + 1
    s1 = sum_integers(last) - sum_integers(first - 1)
    s2 = sum_squares(last) - sum_squares(first - 1)
    return count * c * c - 2 * c * step * s1 + step * step * s2


def fixed_cells(words, period, horizon, gap):
    """Cyclic reads at j*P/W+k*P; latest writes gap seconds after each read.

    Discard all read/write windows, including unfinished last ones. All other
    intervals are deterministic, disjoint per word and have length <= P.
    Algebraic compression avoids enumerating ~5e14 cells.
    """
    period, horizon, gap = map(Fraction, (period, horizon, gap))
    if words <= 0 or period <= 0:
        raise ValueError("Require positive word count and period")
    step = period / words
    if not (horizon >= period and 0 <= gap <= step):
        raise ValueError("Require T >= P and 0 <= gap <= one slot")
    cycles, rest = divmod(horizon, period)
    split = min(words - 1, rest // step)
    complete = (split + 1) * cycles + (words - split - 1) * (cycles - 1)
    head_sq = step * step * sum_squares(words - 1)
    tail_sq = affine_squares(rest - gap, step, 0, split)
    tail_sq += affine_squares(rest + period - gap, step, split + 1, words - 1)
    length = period - gap
    return {"cycles": cycles, "rest": rest, "full_count": complete,
            "full_length": length, "head_sum_h2": head_sq,
            "tail_sum_h2": tail_sq,
            "sum_h2": complete * length * length + head_sq + tail_sq}


def probability_lower_from_rational_s(s):
    """Conservative decimal report of 1-exp(-S), using a rational S >= 0.

    Floor S exactly to 12 decimals. Decimal.exp is correctly rounded; take its
    next larger representable value and move the final subtraction downward.
    Return both report and floor, so the arithmetic is independently auditable.
    """
    if s < 0:
        raise ValueError("Negative exponent")
    scale = 10 ** 12
    floor_s = Decimal((s.numerator * scale) // s.denominator) / Decimal(scale)
    with localcontext() as ctx:
        ctx.prec = 60
        upper_survival = (-floor_s).exp().next_plus()
        lower = (Decimal(1) - upper_survival).next_minus()
        reported = max(Decimal(0), lower.quantize(Decimal("1e-12"), rounding=ROUND_FLOOR))
    return str(reported), str(floor_s)


def peak_risk(memory, r):
    words, n = memory["words"], memory["bits_per_word"]
    period = Fraction(memory["scan_period_s"])
    horizon = Fraction(memory["years"]) * Fraction(memory["days_per_year"]) * memory["seconds_per_day"]
    rate = Fraction(str(r))
    coefficient = math.comb(n, 2) * rate * rate
    # e^(-nrh) >= 1-nrP for every retained cell h <= P.
    factor = 1 - n * rate * period
    if factor <= 0:
        raise ValueError("This linear lower witness requires nrP < 1")
    records = []
    for gap_s in memory["read_write_gap_s"]:
        cells = fixed_cells(words, period, horizon, gap_s)
        lower_s = coefficient * factor * cells["sum_h2"]
        prob, floor_s = probability_lower_from_rational_s(lower_s)
        with localcontext() as ctx:
            ctx.prec = 60
            h, rd = decimal_fraction(cells["full_length"]), decimal_fraction(rate)
            p_d4 = Decimal(math.comb(n, 2)) * (rd * h) ** 2 * (-n * rd * h).exp()
            # Product using complete cells only is also a valid lower bound.
            product_lower = 1 - (cells["full_count"] * (1 - p_d4).ln()).exp()
        records.append({
            "gap_s": gap_s, "full_cells": cells["full_count"],
            "full_cell_length_s": float(cells["full_length"]),
            "p_D4_full_cell_numerical": str(p_d4),
            "p_safe_full_cell": str(decimal_fraction(coefficient * factor * cells["full_length"] ** 2)),
            "S_safe_rational_numerator": str(lower_s.numerator),
            "S_safe_rational_denominator": str(lower_s.denominator),
            "S_safe_floor_12dp": floor_s,
            "probability_lower_reported_down": prob,
            "complete_cells_product_lower_numerical": str(product_lower),
            "sum_head_h2_s2": float(cells["head_sum_h2"]),
            "sum_tail_h2_s2": float(cells["tail_sum_h2"]),
            "S_boundary_safe": float(coefficient * factor * (cells["head_sum_h2"] + cells["tail_sum_h2"])),
            "S_full_D4_numerical": str(cells["full_count"] * p_d4)
        })
    approximate_s = words * coefficient * period * horizon
    eps = float(memory["epsilon"])
    a_coeff = words * math.comb(n, 2) * float(period * horizon)
    beta = words * n * rate
    return {"r_bit_per_s": str(r), "beta_singleton_parent_per_s": float(beta),
            "horizon_s": int(horizon), "cycles": int(horizon // period),
            "last_cycle_remainder_s": float(horizon % period),
            "S_author_pair_approximation": float(approximate_s),
            "r_threshold_pair_S_equals_epsilon_per_bit_s": math.sqrt(eps / a_coeff),
            "r_threshold_pair_S_equals_minus_log1m_epsilon_per_bit_s": math.sqrt(-math.log1p(-eps) / a_coeff),
            "T36_test11_pair_term_lower_even_d_and_K_zero": float(beta * beta * period * horizon / (2 * words)),
            "meaning": "model lower probability, fixed schedule only; pair approximation is not inserted as a certificate",
            "cells": records}


def mu(v, a, period, g):
    if a < period or min(v, g, period) < 0:
        raise ValueError("Invalid input")
    if a == period:
        return 0.0
    if g == 0:
        return v * (a - period)
    if v <= g * period:
        return 0.0
    if v < g * a:
        return (v - g * period) ** 2 / (2 * g)
    return (a - period) * (v - g * (a + period) / 2)


def poisson_chernoff_root(c, H):
    if c < 0 or H <= 0:
        raise ValueError("Require c >= 0 and H > 0")
    if c == 0:
        return H
    lo, hi = float(c), c + H + 1.0
    def j(m):
        return m - c - c * math.log(m / c)
    while j(hi) < H:
        hi *= 2
    for _ in range(90):
        mid = (lo + hi) / 2
        if j(mid) < H:
            lo = mid
        else:
            hi = mid
    return hi


def t36_upper(c, H, a, period, g, B):
    if a < period or min(g, B) < 0:
        raise ValueError("Invalid input")
    if a == period:
        return B
    M = poisson_chernoff_root(c, H)
    span = a - period
    if g == 0:
        v = M / span
    elif M <= g * span * span / 2:
        v = g * period + math.sqrt(2 * g * M)
    else:
        v = M / span + g * (a + period) / 2
    return min(B, v)


def counter_tables(config, t37):
    memory, cfg = config["diagnostic_memory"], config["counter_diagnostics"]
    total_s = memory["years"] * Fraction(memory["days_per_year"]) * memory["seconds_per_day"]
    N = max(1, total_s // Fraction(cfg["a_min_s"]))
    period = float(memory["scan_period_s"])
    bits = memory["words"] * memory["bits_per_word"]
    eps = float(memory["epsilon"])
    rows = []
    for spec in cfg["growth_inputs"]:
        series, direction, policy, resolution = spec.split("/")
        src = t37["series"][series]["diagnostics"][direction][policy][resolution]
        B = src["max"] * bits
        g = src["max_positive_increment"]["increment_divided_by_step_s"] * bits
        setups = [("H=28 illustration", cfg["illustrative_H"], None)]
        setups += [(f"fraction={f}", math.log(N / (eps * float(f))), eps * float(f)) for f in cfg["epsilon_fractions"]]
        for label, H, alpha in setups:
            inf_u = min(B, g * period + math.sqrt(2 * g * H))
            info = min(B, math.sqrt(2 * g * math.log(1 / alpha))) if alpha else None
            row = {"source": spec, "scenario": label, "B_sample_singleton_s_1": B,
                   "g_sample_singleton_s_2": g, "N": N, "H": H,
                   "alpha_star_aux": alpha, "alpha_info_channel_separately_assumed": alpha,
                   "T36_zero_min_upper_s_1": inf_u,
                   "T36_zero_min_upper_percent_of_own_peak": 100 * inf_u / B,
                   "T36_saturation_a_s": period + math.sqrt(2 * H / g),
                   "info_zero_candidate_s_1": info,
                   "info_candidate_percent_of_own_peak": 100 * info / B if info is not None else None,
                   "info_ramp_history_needed_s": math.sqrt(2 * math.log(1 / alpha) / g) if alpha else None,
                   "T36_zero_point_latency_threshold_s": inf_u / g,
                   "info_zero_point_latency_threshold_s": info / g if info is not None else None,
                   "finite_actions": [], "latencies": [],
                   "type": "hypothetical-input evaluation; info is candidate necessary channel bound pending #45; T36 is its estimator-specific floor"}
            for a in map(float, cfg["finite_a_s"]):
                row["finite_actions"].append({"a_s": a, "upper_s_1_by_count": {
                    str(c): t36_upper(c, H, a, period, g, B) for c in cfg["counts"]}})
            row["minimum_over_declared_finite_actions_s_1"] = min(x["upper_s_1_by_count"]["0"] for x in row["finite_actions"])
            for L in config["external_channel"]["latency_s"]:
                ext = {"L_s": L, "gL_s_1": g * L, "gL_percent_of_own_peak": 100 * g * L / B,
                       "zero_ideal_point_upper_s_1": min(B, g * L),
                       "tighter_than_T36_floor": min(B, g * L) < inf_u,
                       "tighter_than_info_candidate": min(B, g * L) < info if info is not None else None,
                       "mean_zero_error_zero_upper_by_h_s_1": {}}
                for h in config["external_channel"]["mean_window_s"]:
                    ext["mean_zero_error_zero_upper_by_h_s_1"][str(h)] = min(B, g * (h / 2 + L))
                row["latencies"].append(ext)
            rows.append(row)
    return rows


def load_t37(config):
    files = {}
    for path, expected in config["pinned_files"].items():
        data = blob(config["base_sha"], path)
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"Pinned file drift: {path}")
        files[path] = data
    prefix = "experiments/t37-lambda-recipe/"
    module = types.ModuleType("t44_frozen_t37")
    module.__file__ = str(ROOT / prefix / "reproduce.py")
    # Execute the pinned accepted code, never a possibly edited working copy.
    exec(compile(files[prefix + "reproduce.py"], module.__file__, "exec"), module.__dict__)
    t37_config = json.loads(files[prefix + "config.json"])
    accepted = json.loads(files[prefix + "summary.json"])
    captured, original = {}, module.describe
    def capture(rows, step):
        answer = original(rows, step)
        captured[id(answer)] = rows
        return answer
    module.describe = capture
    try:
        regenerated = module.audit(t37_config)
    finally:
        module.describe = original
    if regenerated != accepted:
        raise ValueError("T37 summary does not reproduce exactly")
    frames = {}
    for name, series in regenerated["series"].items():
        for direction, values in series["diagnostics"].items():
            for policy in t37_config["policies"]:
                diag = values[policy]["native"]
                frames[(name, direction, policy)] = (captured[id(diag)], diag)
    return module, t37_config, regenerated, frames


def witness(pair, iso, step):
    a, b = pair
    return {"from_utc": iso(a[0]), "to_utc": iso(b[0]), "from_per_bit_s": a[2],
            "to_per_bit_s": b[2], "algorithm_version": a[1],
            "log_growth_s_1": max(0.0, math.log(b[2] / a[2])) / step}


def relative_growth(rows, sample_max, fractions, iso, step=300):
    counts = Counter(total_pairs=max(0, len(rows) - 1))
    valid = []
    for a, b in zip(rows, rows[1:]):
        if b[0] - a[0] != step:
            counts["excluded_gap"] += 1
        elif a[1] != b[1]:
            counts["excluded_version"] += 1
        elif not (a[3] and b[3]):
            counts["excluded_mask"] += 1
        elif not (a[2] > 0 and b[2] > 0):
            counts["excluded_nonpositive"] += 1
        else:
            valid.append((a, b))
    for key in ("excluded_gap", "excluded_version", "excluded_mask", "excluded_nonpositive"):
        counts.setdefault(key, 0)
    counts["valid_positive_same_version_pairs"] = len(valid)
    diagnostics = []
    for f in fractions:
        threshold = f * sample_max
        buckets = {k: [] for k in ("both_above", "both_below", "up_crossing", "down_crossing")}
        for pair in valid:
            x, y = pair[0][2], pair[1][2]
            key = ("both_above" if y >= threshold else "down_crossing") if x >= threshold else ("up_crossing" if y >= threshold else "both_below")
            buckets[key].append(pair)
        candidates = buckets["both_above"]
        maximum = max(candidates, key=lambda p: max(0, math.log(p[1][2] / p[0][2]))) if candidates else None
        excluded_positive = [p for k, ps in buckets.items() if k != "both_above" for p in ps]
        diagnostics.append({"threshold_fraction": f, "threshold_per_bit_s": threshold,
                            "counts": {k: len(v) for k, v in buckets.items()},
                            "maximum": witness(maximum, iso, step) if maximum else None,
                            "excluded_threshold_maximum": witness(max(excluded_positive, key=lambda p: math.log(p[1][2] / p[0][2])), iso, step) if excluded_positive else None,
                            "crossings": [{"kind": k, **witness(p, iso, step)} for k in ("up_crossing", "down_crossing") for p in buckets[k]]})
    return {"pair_audit": dict(counts), "B_sample_per_bit_s": sample_max,
            "thresholds": diagnostics, "unit_growth": "s^-1, discrete log ratio / 300 s",
            "type": "empirical diagnostic, not a continuous-time or future bound"}


def shielding_check(module, t37_config, frames):
    source = module.source_tables(t37_config)["proton_rate_5min.csv"]
    output = []
    for direction in ("E", "W", "central"):
        for policy in t37_config["policies"]:
            frame, _ = frames[("GOES19_1mm", direction, policy)]
            if len(source) != len(frame):
                raise ValueError("Shielding source/mask length mismatch")
            pairs = []
            for row, (t, _, _, ok) in zip(source, frame):
                if module.stamp(row["timestamp_utc"]) != t:
                    raise ValueError("Shielding source/mask timestamp mismatch")
                if ok:
                    pairs.append((row["timestamp_utc"], Fraction(row[f"d1_lambda_{direction}_s-1"]), Fraction(row[f"d3_lambda_{direction}_s-1"])))
            positive_denominator = [p for p in pairs if p[2] > 0]
            worst = min(positive_denominator, key=lambda z: z[1] / z[2])
            peak = max(pairs, key=lambda z: z[1])
            output.append({"direction": direction, "mask": policy, "valid_rows": len(pairs),
                           "violations_r1_lt_r3": sum(x < y for _, x, y in pairs),
                           "zero_3mm_rows_ratio_undefined": sum(y == 0 for _, _, y in pairs),
                           "minimum_ratio_1mm_to_3mm": float(worst[1] / worst[2]),
                           "minimum_ratio_utc": worst[0], "at_1mm_peak": {
                               "utc": peak[0], "rate_1mm_old_array_s_1": float(peak[1]),
                               "rate_3mm_old_array_s_1": float(peak[2]), "ratio": float(peak[1] / peak[2])},
                           "type": "same-timestamp same-spectrum same-response existing model outputs; no new transport"})
    return output


def poisson_sf(k, mean):
    """P(Pois(mean)>k), evaluated directly in Decimal (no 1-CDF cancellation)."""
    if mean < 0 or k < -1:
        raise ValueError("Invalid Poisson parameters")
    if k == -1:
        return Decimal(1)
    if mean == 0:
        return Decimal(0)
    with localcontext() as ctx:
        ctx.prec = 65
        m = Decimal(str(mean))
        term = (-m).exp()
        for j in range(1, k + 2):
            term *= m / j
        total, j = term, k + 1
        while True:
            j += 1
            term *= m / j
            old = total
            total += term
            if total == old and j > m:
                return +total


def poisson_k(mean, delta):
    if not 0 < Decimal(str(delta)) < 1 or mean < 0:
        raise ValueError("Invalid quantile inputs")
    k = max(0, int(mean))
    target = Decimal(str(delta))
    while poisson_sf(k, mean) > target:
        k += 1
    while k > 0 and poisson_sf(k - 1, mean) <= target:
        k -= 1
    return {"mean_events": mean, "delta_K": delta, "K": k,
            "tail_at_K": str(poisson_sf(k, mean)),
            "tail_at_K_minus_1": str(poisson_sf(k - 1, mean)),
            "type": "conditional Poisson arithmetic example, not an adopted mission input"}


def compute(config):
    if Fraction(config["diagnostic_memory"]["slot_s"]) * config["diagnostic_memory"]["words"] != Fraction(config["diagnostic_memory"]["scan_period_s"]):
        raise ValueError("Slot/scan contract mismatch")
    ext = config["external_channel"]
    if any(ext[k] != 0 for k in ("point_value_s_1", "illustrative_mean_value_s_1", "illustrative_error_s_1")):
        raise ValueError("This diagnostic implements only the explicitly ideal zero examples")
    module, old_config, t37, frames = load_t37(config)
    expected = {(s, d, m) for s in config["relative_growth"]["series"] for d in config["relative_growth"]["directions"] for m in config["relative_growth"]["masks"]}
    if set(frames) != expected or config["relative_growth"]["cadence_s"] != old_config["cadence_s"]:
        raise ValueError("Frozen T37 series/mask/cadence mismatch")
    peak = t37["series"]["GOES16_3mm"]["diagnostics"]["central"]["published_valid"]["native"]["max"]
    relative = []
    for key, (rows, diag) in frames.items():
        series, direction, policy = key
        relative.append({"series": series, "direction": direction, "mask": policy,
                         **relative_growth(rows, diag["max"], config["relative_growth"]["threshold_fraction_of_t37_sample_max"], module.iso)})
    return {"base_sha": config["base_sha"], "numeric_contract": "Analytic bounds plus deterministic diagnostic evaluation; no Monte Carlo; see conditions.md",
            "config_sha256": hashlib.sha256((HERE / "config.json").read_bytes()).hexdigest(),
            "t37_reproduced": True, "source_sha256": old_config["source_hashes"],
            "peak_risk": [peak_risk(config["diagnostic_memory"], r) for r in (config["diagnostic_memory"]["rounded_r_per_bit_s"], str(peak))],
            "counter_and_external": counter_tables(config, t37),
            "relative_growth": relative,
            "shielding": shielding_check(module, old_config, frames),
            "poisson_arithmetic_examples": ([poisson_k(m, d) for m in config["rarity"]["conditional_poisson_demo_means"] for d in config["rarity"]["conditional_poisson_demo_delta_K"]]
                                            if config["rarity"]["count_law_primary_status"] == "confirmed" else []),
            "physical_rarity_parameters": {k: v for k, v in config["rarity"].items() if not k.startswith("conditional_") and k != "demo_status"}}

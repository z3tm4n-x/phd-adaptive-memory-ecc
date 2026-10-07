"""Derived event statistics for explicitly piecewise-constant SEPEM profiles.

No raw measurements are emitted.  Every result is conditional on the upstream
spectral response and on the event extraction rules, not a future-event bound.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np
from scipy.ndimage import maximum_filter1d
from scipy.stats import binom, spearmanr


def validate_series(times, values, dt=300):
    times = np.asarray(times, dtype="datetime64[s]")
    values = np.asarray(values, dtype=float)
    if times.ndim != 1 or values.shape[0] != len(times) or len(times) == 0:
        raise ValueError("nonempty aligned time/value arrays required")
    if np.any(np.isnat(times)) or np.any(np.diff(times).astype(int) != dt):
        raise ValueError("complete regular time grid required; gaps cannot be zero-filled")
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("finite nonnegative values required")
    return times, values


def detect_events(values, baseline=None, multiplier=10.0, merge_hours=24.0,
                  minimum_above_hours=1.0, dt=300):
    """Return half-open index ranges, merging BEFORE minimum-above filtering.

    The baseline is the global 10th percentile unless supplied. Strictly greater
    than the threshold is active. Internal below-threshold gaps are retained;
    outside tails are excluded. Missing values must be handled upstream.
    """
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("finite nonnegative nonempty vector required")
    if multiplier <= 0 or merge_hours < 0 or minimum_above_hours < 0 or dt <= 0:
        raise ValueError("invalid extraction parameters")
    baseline = float(np.quantile(values, .1)) if baseline is None else float(baseline)
    if not np.isfinite(baseline) or baseline < 0:
        raise ValueError("invalid baseline")
    active = values > multiplier * baseline
    edges = np.diff(np.r_[False, active, False].astype(np.int8))
    starts, stops = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    merged = []
    for a, b in zip(starts, stops):
        if merged and (a - merged[-1][1]) * dt <= merge_hours * 3600:
            merged[-1] = (merged[-1][0], int(b))
        else:
            merged.append((int(a), int(b)))
    return [(a, b) for a, b in merged
            if np.count_nonzero(active[a:b]) * dt >= minimum_above_hours * 3600]


def moments(values, dt=300):
    values = np.asarray(values, dtype=float)
    if not len(values) or not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("finite nonnegative nonempty vector required")
    peak = float(np.max(values))
    total = float(np.sum(values, dtype=np.float64) * dt)
    square = float(np.dot(values, values) * dt)
    shape = square / (peak * total) if peak * total > 0 else None
    return peak, total, square, shape


def _iso(t):
    return str(np.datetime_as_string(t, unit="s")) + "Z"


def event_metrics(times, rates, intervals, flux_integrals=None, dt=300):
    rows = []
    for index, (a, b) in enumerate(intervals, 1):
        y = np.asarray(rates[a:b], dtype=float)
        peak, total, square, shape = moments(y, dt)
        k = int(np.argmax(y))
        # Earliest upward threshold crossings, both before the FIRST peak.
        # A series already above 0.1 peak at its extracted start is left-censored.
        low = .1 * peak
        early = y[:k + 1]
        rising_low = np.flatnonzero((early[1:] >= low) & (early[:-1] < low)) + 1
        efold = None
        if early[0] < low and len(rising_low):
            first = int(rising_low[0])
            high_cross = np.flatnonzero(early[first:] >= np.e * low)
            if len(high_cross):
                efold = int(high_cross[0]) * dt
        row = {
            "event_id": f"E{index:04d}", "start_utc": _iso(times[a]),
            "peak_utc": _iso(times[a+k]),
            "end_exclusive_utc": _iso(times[b-1] + np.timedelta64(dt, "s")),
            "start_index": a, "stop_index_exclusive": b,
            "duration_s": (b-a)*dt, "peak_lambda_s-1": peak,
            "N_expected_upsets": total, "S2_s-1": square, "shape_r": shape,
            "above_half_peak_s": int(np.count_nonzero(y > .5*peak))*dt,
            "above_tenth_peak_s": int(np.count_nonzero(y > .1*peak))*dt,
            "early_efold_s": efold,
            "early_efold_status": "calculated_bin_crossing" if efold is not None else "not_identifiable_within_extracted_rise",
            "edge_truncated": a == 0 or b == len(times),
            "value_type": "calculated", "background_subtracted": False,
        }
        if flux_integrals is not None:
            flux = np.asarray(flux_integrals[a:b])
            for j, energy in enumerate((10, 30, 60, 100)):
                row[f"fluence_gt{energy}_omni_cm-2"] = float(np.sum(flux[:, j])*dt*4*np.pi)
                row[f"peak_flux_gt{energy}_cm-2_s-1_sr-1"] = float(np.max(flux[:, j]))
        rows.append(row)
    return rows


def quantile_order_interval(samples, probability=.9, coverage=.95):
    """Equal-tail binomial order-statistic interval; MC uncertainty ONLY.

    For a continuous population, ranks L and U cover its q quantile when
    L <= Binomial(n,q) <= U-1. Ties make the quantile interval conservative.
    """
    x = np.sort(np.asarray(samples, dtype=float))
    if not len(x) or not np.isfinite(x).all() or not 0 < probability < 1 or not 0 < coverage < 1:
        raise ValueError("invalid quantile inputs")
    n = len(x)
    alpha = 1-coverage
    lower_rank = int(binom.ppf(alpha/2, n, probability))
    upper_rank = int(binom.ppf(1-alpha/2, n, probability))+1
    return {
        "estimate": float(np.quantile(x, probability, method="inverted_cdf")),
        "lower": float(x[lower_rank-1]) if lower_rank > 0 else None,
        "upper": float(x[upper_rank-1]) if upper_rank <= n else None,
        "lower_order_rank_1_based": lower_rank,
        "upper_order_rank_1_based": upper_rank,
        "coverage": coverage,
        "uncertainty_scope": "Monte Carlo conditional on fixed empirical population and mean count; not archive or physical uncertainty",
    }


def compound_poisson(event_values, mean_count, missions=200000, seed=2026100701, batch=4096):
    """Uniform event resampling with replacement, same draws across columns.

    Draw all counts first, then one contiguous random-index stream. Changing the
    calculation batch leaves the sample invariant. No event chronology or
    overlap cross-terms are simulated: the output is a sum of event integrals.
    """
    values = np.asarray(event_values, dtype=float)
    if values.ndim == 1:
        values = values[:, None]
    if not len(values) or not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("nonempty finite nonnegative event population required")
    if mean_count < 0 or not np.isfinite(mean_count) or missions <= 0 or batch <= 0:
        raise ValueError("invalid simulation parameters")
    rng = np.random.Generator(np.random.PCG64(seed))
    counts = rng.poisson(mean_count, size=missions)
    output = np.zeros((missions, values.shape[1]), dtype=float)
    for start in range(0, missions, batch):
        stop = min(start+batch, missions)
        size = counts[start:stop]
        number = int(np.sum(size))
        if not number:
            continue
        sampled = rng.integers(0, len(values), number, dtype=np.int64)
        destinations = np.repeat(np.arange(stop-start), size)
        for column in range(values.shape[1]):
            output[start:stop, column] = np.bincount(
                destinations, weights=values[sampled, column], minlength=stop-start)
    return output, counts


def _calendar_plus_ten_years(days):
    result = []
    for day in days:
        d = date.fromisoformat(str(day))
        try:
            target = d.replace(year=d.year+10)
        except ValueError:
            target = d.replace(year=d.year+10, day=28)
        result.append(target.isoformat())
    return np.asarray(result, dtype="datetime64[D]")


def rolling_ten_year_windows(times, values, intervals, dt=300):
    """All available 5-minute starts, exact calendar +10 years.

    Event portions crossing boundaries are clipped to each window. The compact
    CSV selects daily starts; the JSON extrema/quantiles use EVERY grid start.
    Outside extracted event windows lambda is zero for this event-only statistic.
    """
    times, values = validate_series(times, values, dt)
    day = times.astype("datetime64[D]")
    unique_days, day_index = np.unique(day, return_inverse=True)
    end_days = _calendar_plus_ten_years(unique_days)[day_index]
    target = end_days.astype("datetime64[s]") + (times-day.astype("datetime64[s]"))
    ends = ((target-times[0]).astype("timedelta64[s]").astype(np.int64) // dt)
    starts = np.flatnonzero(ends <= len(times))
    if not len(starts):
        return [], {"status": "less_than_ten_years", "all_grid_window_count": 0}
    ends = ends[starts]
    masked = np.zeros(len(values), dtype=float)
    for a, b in intervals:
        masked[a:b] = values[a:b]
    total = np.r_[0., np.cumsum(masked, dtype=np.float64)] * dt
    squares = np.r_[0., np.cumsum(masked*masked, dtype=np.float64)] * dt
    n = total[ends]-total[starts]
    s2 = squares[ends]-squares[starts]
    peaks = np.zeros(len(starts))
    lengths = ends-starts
    for length in np.unique(lengths):
        # origin=-floor(length/2) gives the forward window [i,i+length).
        maximum = maximum_filter1d(masked, size=int(length), origin=-(int(length)//2), mode="constant", cval=0)
        select = lengths == length
        peaks[select] = maximum[starts[select]]
    denominator = peaks*n
    ratios = np.divide(s2, denominator, out=np.full_like(s2, np.nan), where=denominator > 0)
    valid = np.isfinite(ratios)
    if np.any(ratios[valid] > 1+1e-10) or np.any(ratios[valid] < -1e-10):
        raise AssertionError("window shape ratio outside [0,1]")
    def row(k):
        return {"start_utc": _iso(times[starts[k]]), "end_exclusive_utc": _iso(target[starts[k]]),
                "N_expected_upsets": float(n[k]), "S2_s-1": float(s2[k]),
                "peak_lambda_s-1": float(peaks[k]),
                "multi_event_ratio": float(ratios[k]) if valid[k] else None,
                "value_type": "calculated", "support": "event portions within window"}
    daily = np.flatnonzero((times[starts]-day[starts].astype("datetime64[s]")).astype(int) == 0)
    summary = {
        "all_grid_window_count": len(starts), "grid_seconds": dt,
        "calendar_rule": "+10 calendar years; 29 February maps to 28 February; [start,end)",
        "csv_scope": "daily starts only; JSON extrema and quantiles use all grid starts",
        "empty_exposure_window_count": int(np.count_nonzero(~valid)),
        "ratio_quantiles": dict(zip(("min", "q10", "median", "q90", "max"), map(float, np.quantile(ratios[valid], [0,.1,.5,.9,1])))) if valid.any() else {},
        "maximum_ratio_window": row(int(np.nanargmax(ratios))) if valid.any() else None,
        "maximum_S2_window": row(int(np.argmax(s2))),
    }
    return [row(int(k)) for k in daily], summary


def write_csv(path, rows, fieldnames=None):
    path = Path(path)
    if not rows and not fieldnames:
        fieldnames = ["status"]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames or list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _shape_summary(rows):
    if not rows:
        return {"event_count": 0}
    r = np.asarray([x["shape_r"] for x in rows])
    n = np.asarray([x["N_expected_upsets"] for x in rows])
    peak = np.asarray([x["peak_lambda_s-1"] for x in rows])
    corr = {}
    if len(rows) >= 3 and np.ptp(r) > 0:
        for name, variable in (("N", n), ("peak", peak)):
            if np.ptp(variable) > 0:
                result = spearmanr(variable, r)
                corr[name] = {"rho": float(result.statistic), "p_nominal_exploratory": float(result.pvalue)}
    return {"event_count": len(rows), "shape_quantiles": dict(zip(
        ("min", "q10", "q25", "median", "q75", "q90", "max"), map(float, np.quantile(r, [0,.1,.25,.5,.75,.9,1])))),
        "maximum_shape_event": rows[int(np.argmax(r))], "spearman_descriptive": corr,
        "S2_sum_s-1": float(sum(x["S2_s-1"] for x in rows)),
        "N_sum_expected_upsets": float(np.sum(n)), "peak_lambda_s-1": float(np.max(peak))}


def _figures(times, nominal, rows, samples, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "svg.hashsalt": "sepem-profiles-fixed"})
    def save(fig, name):
        fig.tight_layout()
        fig.savefig(out / f"{name}.png", dpi=160)
        fig.savefig(out / f"{name}.svg", metadata={"Date": None})
        plt.close(fig)
    if rows:
        largest = sorted(rows, key=lambda r: r["N_expected_upsets"], reverse=True)[:8]
        fig, axes = plt.subplots(4, 2, figsize=(11, 10), squeeze=False)
        fig.suptitle("Расчёт: протоны SEPEM, CSDA 3 г/см² Al, PDI, 38·2¹⁹ бит", fontsize=11)
        for ax, event in zip(axes.flat, largest):
            a, b = event["start_index"], event["stop_index_exclusive"]
            ax.plot((times[a:b]-times[a]).astype(int)/86400, nominal[a:b], lw=1)
            ax.set_title(event["start_utc"][:10] + f"; r={event['shape_r']:.3f}")
            ax.set_xlabel("Сутки от начала события")
            ax.set_ylabel("λ, с⁻¹")
            ax.grid(alpha=.2)
        for ax in list(axes.flat)[len(largest):]:
            ax.axis("off")
        save(fig, "largest-event-profiles")
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        fig.suptitle("Пятиминутная протонная модель; исторические коэффициенты формы", fontsize=11)
        for ax, key, label in zip(axes, ("N_expected_upsets", "peak_lambda_s-1"), ("N, ожидаемые сбои", "Пиковая λ, с⁻¹")):
            ax.scatter([r[key] for r in rows], [r["shape_r"] for r in rows], s=12, alpha=.6)
            ax.set_xscale("log")
            ax.set_xlabel(label)
            ax.set_ylabel("Коэффициент формы r")
            ax.set_ylim(0, 1.03)
            ax.grid(alpha=.2)
        save(fig, "shape-by-size")
    if samples is not None:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.set_title("Условная эмпирическая модель Б — не полный конверт R0-A", fontsize=10)
        q = float(np.quantile(samples, .9, method="inverted_cdf"))
        ax.hist(samples, bins=80, density=True, color="#587caa", alpha=.75)
        ax.axvline(q, color="#a53030", label=f"Π = 0,1: {q:.4g} с⁻¹")
        ax.set_xlabel("Сумма S₂ за модельные 10 лет, с⁻¹")
        ax.set_ylabel("Плотность модельных реализаций")
        ax.legend()
        save(fig, "mission-S2-distribution")


def analyze(time_start, rates, flux_integrals, out, config):
    """Create compact derived tables and figures; return JSON summary.

    Optional config['gost'][variant] supplies peak_lambda_s-1,
    N_expected_upsets, and fluence_gt30_omni_cm-2 from an upstream matched
    convolution. No default silently uses the historical 6940 envelope.
    """
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    dt = int(config.get("bin_seconds", 300))
    nominal_key = config.get("nominal_rate_key", config.get("nominal_rate", "csda_3_pdi"))
    times, nominal = validate_series(time_start, rates[nominal_key], dt)
    flux = np.asarray(flux_integrals, dtype=float)
    if flux.shape != (len(times), 4) or not np.isfinite(flux).all() or np.any(flux < 0):
        raise ValueError("four valid integral flux channels required")
    for values in rates.values():
        validate_series(times, values, dt)
    baseline_quantile = float(config.get("event_baseline_quantile", .1))
    if baseline_quantile != .1 or float(config.get("design_exceedance_probability", .1)) != .1:
        raise ValueError("This fixed study supports baseline q10 and exceedance 0.1 only")
    baseline = float(np.quantile(nominal, baseline_quantile))
    factor = float(config.get("event_threshold_factor", 10))
    merge_hours = float(config.get("event_merge_gap_hours", 24))
    min_hours = float(config.get("event_min_above_hours", 1))
    fluence_cut = float(config.get("gost_population_fluence_30_cm2", 1e5))
    rules = [(factor,merge_hours), (factor/2,merge_hours), (factor*2,merge_hours),
             (factor,merge_hours/2), (factor,merge_hours*2)]
    nominal_rule = f"threshold_{factor:g}_merge_{merge_hours:g}h"
    summaries, sensitivity, rows_by_rule = {}, [], {}
    for multiplier, merge in rules:
        key = f"threshold_{multiplier:g}_merge_{merge:g}h"
        intervals = detect_events(nominal, baseline, multiplier, merge, min_hours, dt=dt)
        rows = event_metrics(times, nominal, intervals, flux, dt)
        rows_by_rule[key] = rows
        summaries[key] = _shape_summary(rows)
    rows = rows_by_rule[nominal_rule]
    write_csv(out/"events.csv", rows)
    for key, selected in rows_by_rule.items():
        for criterion in ("N_expected_upsets", "peak_lambda_s-1"):
            top = sorted(selected, key=lambda r: (-r[criterion], r["start_utc"]))[:20]
            summaries[key]["top20_by_"+criterion] = _shape_summary(top)
        sensitivity.append({"kind": "event_extraction", "variant": key, "event_count": len(selected),
                            "S2_sum_s-1": sum(r["S2_s-1"] for r in selected),
                            "maximum_r": max((r["shape_r"] for r in selected), default=None),
                            "mission_S2_q90_s-1": None, "value_type": "calculated"})
    top_rows = []
    for criterion in ("N_expected_upsets", "peak_lambda_s-1"):
        top_rows.extend({"ranking": criterion, "rank": i, **r} for i, r in enumerate(
            sorted(rows, key=lambda r: (-r[criterion], r["start_utc"]))[:20], 1))
    write_csv(out/"largest-events.csv", top_rows)
    special = [r for r in rows if int(r["peak_utc"][:4]) in (1989, 2000, 2001, 2003, 2005)]
    write_csv(out/"requested-years-events.csv", special)
    intervals = [(r["start_index"], r["stop_index_exclusive"]) for r in rows]
    daily, rolling = rolling_ten_year_windows(times, nominal, intervals, dt)
    write_csv(out/"ten-year-windows-daily.csv", daily)
    variants = {}
    for name, values in rates.items():
        variants[name] = event_metrics(times, values, intervals, flux, dt)
    # Missing or edge-truncated events are not a defensible complete bootstrap draw.
    eligible = [i for i, r in enumerate(rows) if r["fluence_gt30_omni_cm-2"] >= fluence_cut and not r["edge_truncated"]]
    mean_count = config.get("mission_mean_events")
    missions = int(config.get("bootstrap_missions", config.get("monte_carlo_missions", 200000)))
    seed = int(config.get("bootstrap_seed", config.get("mission_seed", 2026100701)))
    mission_rows, nominal_samples, mc = [], None, {"status": "not_computed", "eligible_events": len(eligible)}
    if eligible and mean_count is not None:
        names = list(variants)
        matrix = np.array([[variants[name][i]["S2_s-1"] for name in names] +
                           [rows[i]["fluence_gt30_omni_cm-2"]] for i in eligible])
        samples, counts = compound_poisson(matrix, float(mean_count), missions, seed)
        nominal_samples = samples[:, names.index(nominal_key)]
        for k, name in enumerate(names + ["fluence_gt30_omni_cm-2"]):
            result = quantile_order_interval(samples[:, k])
            mission_rows.append({"variant": name, "method": "B_compound_Poisson_empirical_events",
                "q90": result["estimate"], "q90_MC95_lower": result["lower"],
                "q90_MC95_upper": result["upper"], "missions": missions,
                "value_type": "estimate", "units": "cm-2" if k == len(names) else "s-1"})
        mc = {"status": "conditional_empirical_model", "eligible_events": len(eligible),
              "population_filter": f"omnidirectional >30 MeV fluence >={fluence_cut:g} cm-2 and not edge truncated",
              "population_identity_to_GOST": "not established by threshold alone",
              "mean_count": float(mean_count), "missions": missions, "seed": seed,
              "sample_count_mean": float(np.mean(counts)), "sample_count_variance": float(np.var(counts, ddof=1)),
              "count_histogram": {str(k): v for k, v in sorted(Counter(counts.tolist()).items())},
              "assumptions": "independent identically distributed empirical event draws; additive non-overlapping event S2; no archive uncertainty or unseen-tail guarantee",
              "order_statistic_interval": quantile_order_interval(nominal_samples)}
        supplied_gost = config.get("gost", {}).get(nominal_key, {})
        gost_f30 = supplied_gost.get("fluence_gt30_omni_cm-2")
        empirical_f30 = mission_rows[-1]["q90"]
        if gost_f30 is not None and empirical_f30 > 0:
            scale = float(gost_f30) / empirical_f30
            mc["fluence_gt30_comparison"] = {
                "empirical_mission_q90_cm-2": empirical_f30,
                "GOST_marginal_q90_cm-2": float(gost_f30),
                "empirical_over_GOST": empirical_f30 / float(gost_f30),
                "proposed_uniform_flux_scale": scale,
                "diagnostic_scaled_S2_q90_s-1": mc["order_statistic_interval"]["estimate"]*scale**2,
                "status": "diagnostic only; fixed event membership/count; matching one fluence quantile does not validate an S2 tail",
            }
        write_csv(out/"mission-S2-cdf.csv", [{"probability": float(p), "S2_s-1": float(q), "value_type": "estimate"}
                    for p, q in zip(np.linspace(0, 1, 1001), np.quantile(nominal_samples, np.linspace(0, 1, 1001), method="inverted_cdf"))])
        # Event-definition sensitivity uses the same seed and count law, but a
        # changed empirical population. It is not a simultaneous interval.
        for item in sensitivity:
            selected = rows_by_rule[item["variant"]]
            keep = [r for r in selected if r["fluence_gt30_omni_cm-2"] >= fluence_cut and not r["edge_truncated"]]
            if keep:
                if item["variant"] == nominal_rule:
                    q = mc["order_statistic_interval"]["estimate"]
                else:
                    trial, _ = compound_poisson([r["S2_s-1"] for r in keep], float(mean_count), missions, seed)
                    q = quantile_order_interval(trial[:, 0])["estimate"]
                item["mission_S2_q90_s-1"] = q
                item["value_type"] = "calculated_and_model_estimate"
    write_csv(out/"mission-model-B.csv", mission_rows)
    a_rows = []
    for name, selected in variants.items():
        if not selected:
            continue
        rmax = max(r["shape_r"] for r in selected if r["shape_r"] is not None)
        b = next((r["q90"] for r in mission_rows if r["variant"] == name), None)
        sensitivity.append({"kind": "response_at_nominal_event_boundaries", "variant": name,
                            "event_count": len(selected), "S2_sum_s-1": sum(r["S2_s-1"] for r in selected),
                            "maximum_r": rmax, "mission_S2_q90_s-1": b, "value_type": "calculated_and_model_estimate"})
        reference = config.get("gost", {}).get(name)
        for rule, shape_factor, status in (("empirical_max", rmax, "estimate_no_future_bound"),
                ("empirical_max_plus_10_percent", min(1.,1.1*rmax), "heuristic_margin_not_quantile"),
                ("universal_shape_1", 1., "shape_inequality_only_not_joint_marginal_quantile")):
            a_rows.append({"variant": name, "shape_rule": rule, "r": shape_factor,
                "peak_lambda_s-1": reference.get("peak_lambda_s-1") if reference else None,
                "N_expected_upsets": reference.get("N_expected_upsets") if reference else None,
                "S2_s-1": shape_factor*reference["peak_lambda_s-1"]*reference["N_expected_upsets"] if reference else None,
                "status": status if reference else "matched_GOST_convolution_not_supplied", "value_type": "estimate"})
    write_csv(out/"design-model-A.csv", a_rows)
    write_csv(out/"sensitivity.csv", sensitivity)
    summary = {"value_type": "calculated_and_conditional_model_estimates", "nominal_rate": nominal_key,
        "baseline_global_q10_s-1": baseline, "threshold_nominal_s-1": factor*baseline,
        "event_definition": f"strict threshold; merge gaps <={merge_hours:g} h before >={min_hours:g} h active-bin filter; internal gaps and background included; no outer tails",
        "event_population_summaries": summaries, "ten_year_windows": rolling, "mission_model_B": mc,
        "bootstrap_eligible_event_ids": [rows[i]["event_id"] for i in eligible],
        "limitations": ["all lambda profiles constant within 300 s bins", "bin averages do not bound unobserved sub-bin squared intensity",
                        "historical maximum r with a margin is not a probabilistic future bound", "marginal GOST peak/fluence quantiles do not supply a joint S2 quantile",
                        "empirical bootstrap excludes unobserved event sizes and unresolved original-data quality"]}
    (out/"analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    _figures(times, nominal, rows, nominal_samples, out)
    return summary

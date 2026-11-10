"""Single registered NYC/ULA calculation. Python 3.10+, standard library."""

import argparse
import hashlib
import json
from decimal import Decimal, localcontext
from fractions import Fraction as F
from math import ceil, floor
from pathlib import Path

HERE = Path(__file__).resolve().parent
NS = F(1, 10**9)
FIT_HOURS = 10**9


def fixed_decimal(value, places, *, up):
    """Issue a decimal bound from an exact rational; avoid binary floats."""
    assert value >= 0
    scale = 10**places
    units = ceil(value * scale) if up else floor(value * scale)
    return f"{units // scale}.{units % scale:0{places}d}"


def upper(value, places=12):
    return fixed_decimal(value, places, up=True)


def lower(value, places=12):
    return fixed_decimal(value, places, up=False)


def collision_reference(mean, words):
    """Exact event in the marked Poisson model, evaluated to high precision."""
    with localcontext() as ctx:
        ctx.prec = 75
        per_word = Decimal(mean.numerator) / Decimal(mean.denominator) / words
        # P(all physical words get <=1 hit) = [exp(-m) (1+m)]**words.
        log_no_repeat = words * ((1 + per_word).ln() - per_word)
        return 1 - log_no_repeat.exp()


def frozen_calendar(service):
    raw = (HERE / service["calendar"]).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != service["calendar_sha256_lf"]:
        raise ValueError("Calendar differs from the preregistered revision")
    return json.loads(raw)


def calculate(inputs):
    src, model, service = inputs["source"], inputs["model"], inputs["service"]
    cal = frozen_calendar(service)
    words, mission = cal["W"], F(cal["mission_s"])
    hours = mission / 3600
    density, data_bits = src["die_density_mbit"], src["inner_data_bits"]
    inner_words, remainder = divmod(density * 2**20, data_bits)
    assert remainder == 0 and words * 3 <= density * 2**20 // 16
    assert words * 4 == 2**18 and cal["n"] == 39
    die_fit = density * (src["neutron_nyc_fit_per_mbit"] + src["alpha_ula_fit_per_mbit"])
    assert die_fit == src["table1_errors_per_billion_device_hours"]
    hidden_ratio = F(model["hidden_cell_rate_over_data_cell_rate_upper"])
    cell_factor = 1 + hidden_ratio * src["inner_check_bits"] / data_bits
    full_die_mean = die_fit * cell_factor * hours / FIT_HOURS

    eps = F(model["epsilon"])
    execution = F(model["execution_exception_probability_upper"])
    direct = F(model["direct_inner_parent_mean_upper"])
    pair_bound = full_die_mean**2 / (2 * inner_words)
    excursion_upper = pair_bound + direct + execution
    direct_budget = eps - execution - pair_bound
    repeat = collision_reference(full_die_mean, inner_words)
    # The first-moment bound must cover the independent occupancy calculation.
    assert 0 < F(repeat) <= pair_bound and excursion_upper <= eps

    scale_lo, scale_hi = F(cal["xi_minus"]), F(cal["xi_plus"])
    edge = 2 * F(cal["J_ns"]) * NS
    read = cal["read_port_ns"] * NS
    write = cal["repair_extra_ns"] * NS
    read_lo, read_hi = read * scale_lo - edge, read * scale_hi + edge
    write_hi = write * scale_hi + edge
    scan = cal["L_ns"] * NS
    # Includes both horizon edges of the first pass and the last word operation.
    scan_hi = scan * scale_hi + edge + F(cal["aperture_upper_ns"]) * NS
    first_pair = pair_bound * (scan_hi / mission)**2
    # No assumption that execution exceptions or direct marks are spread over T.
    startup_bad = min(F(1), first_pair + execution + direct)
    startup_repairs_upper = words * startup_bad
    nominal_base = words * read
    expected_port_hi = words * read_hi + startup_repairs_upper * write_hi
    path_port_hi = words * (read_hi + write_hi)
    # Sensitivity only: a different recovery implementation may consume the
    # entire exclusive port on a bad path, including one operation at the edge.
    fallback_overhead = excursion_upper * (mission + read_hi + write_hi)

    # Longest distance between pass starts on successful execution of L/32L.
    longest_gap = service["longest_adaptive_period_in_passes"] * scan * scale_hi + edge
    full_passes = 1 + floor((mission - scan_hi) / longest_gap)
    # On the common good event all compound DQ words are clean. The mandatory
    # start is coupled across policies; only complete subsequent passes enter.
    extra_lower = (1 - excursion_upper) * (full_passes - 1) * words * read_lo
    assert (full_passes - 1) * longest_gap + scan_hi <= mission
    assert full_passes * longest_gap + scan_hi > mission

    # An arbitrary phase in [0, period) can change the arrival count by one.
    # In-flight final request costs at most one additional read at the edge.
    app_period = service["app_interarrival_si_ns"] * NS
    app_low, app_high = floor(mission / app_period) - 1, ceil(mission / app_period)
    grant_start, grant_end = cal["app_grant_ns"]
    response_ns = 20 + cal["frame_ns"] + grant_end - grant_start
    app_response_hi = response_ns * NS * scale_hi + edge
    assert app_response_hi < app_period
    peak_window = F(1, 1000)
    frame = cal["frame_ns"] * NS
    aperture = F(cal["aperture_upper_ns"]) * NS
    frames = 2 + ceil((peak_window + aperture + edge) / (frame * scale_lo))
    peak = frames * len(cal["word_slots_ns"]) * (read_hi + write_hi) / peak_window

    return {
        "probability": {
            "mission_hours": int(hours),
            "full_die_internal_words": inner_words,
            "table1_die_fit_data": die_fit,
            "model_fit_including_checks_upper": upper(die_fit * cell_factor, 3),
            "mean_single_hits_whole_die_upper": upper(full_die_mean, 12),
            "two_parents_same_inner_word_upper": upper(pair_bound, 15),
            "two_hits_one_inner_word_model_probability_check_approx": format(repeat, ".18f"),
            "first_external_weight_above_one_upper": upper(excursion_upper, 15),
            "direct_parent_budget_sufficient_floor_per_die_per_T": lower(direct_budget, 15),
            "direct_parent_budget_sufficient_floor_fit_per_die": lower(direct_budget * FIT_HOURS / hours, 9),
        },
        "off_after_common_start": {
            "protective_reads": words,
            "additional_passes_after_start": 0,
            "nominal_start_calendar_s": upper(scan),
            "physical_start_duration_upper_s": upper(scan_hi),
            "expected_repairs_upper": upper(startup_repairs_upper),
            "maximum_repairs": words,
            "nominal_known_port_lower_s": lower(nominal_base),
            "nominal_expected_known_port_upper_s": upper(nominal_base + startup_repairs_upper * write),
            "physical_known_port_lower_s": lower(words * read_lo),
            "physical_expected_known_port_upper_s": upper(expected_port_hi),
            "physical_expected_known_port_upper_pct_of_T": upper(100 * expected_port_hi / mission, 16),
            "physical_known_port_any_path_upper_s": upper(path_port_hi),
            "startup_peak_any_1ms_known_protection_upper_pct": upper(100 * peak, 6),
            "extra_expected_port_if_bad_path_saturates_port_to_T_upper_s": upper(fallback_overhead, 6),
        },
        "adaptive_read_comparison": {
            "window_nominal_s": upper(service["longest_adaptive_period_in_passes"] * scan),
            "complete_passes_at_least_on_good_event": full_passes,
            "expected_additional_known_read_port_lower_s": lower(extra_lower, 6),
            "expected_additional_known_read_port_lower_pct_of_T": lower(100 * extra_lower / mission, 8),
        },
        "common_application": {
            "reads_started_lower_under_service": app_low,
            "reads_started_upper_under_service": app_high,
            "nominal_useful_port_lower_s": lower(app_low * read, 9),
            "nominal_useful_port_upper_s": upper(app_high * read, 9),
            "physical_useful_port_upper_s": upper(app_high * read_hi, 6),
            "response_under_service_upper_us": upper(app_response_hi * 10**6, 6),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the published result")
    parser.add_argument("--source-pdf", type=Path, help="also verify the local AN88889 Rev. *C copy")
    args = parser.parse_args()
    inputs = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
    if args.source_pdf:
        if hashlib.sha256(args.source_pdf.read_bytes()).hexdigest() != inputs["source"]["sha256"]:
            parser.error("Source PDF differs from AN88889 Rev. *C in inputs.json")
    result = calculate(inputs)
    contents = json.dumps(result, indent=2) + "\n"
    dest = HERE / "result.json"
    if args.check:
        if dest.read_text(encoding="utf-8") != contents:
            parser.exit(1, "Published result differs from the calculation\n")
        print("OK: source parameters, calendar, collision check, horizon edges and result")
    else:
        dest.write_text(contents, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

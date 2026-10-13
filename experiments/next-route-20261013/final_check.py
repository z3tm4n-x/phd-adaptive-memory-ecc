"""T146 addressed closure: exact outward bounds and corrected ARM composition.

No new controller search, hardware timing, or E-transfer certificate.
Default is read-only; --write generates this T146 final-report.json only.
"""
import argparse
import hashlib
import json
import math
import subprocess
from fractions import Fraction as F
from pathlib import Path

from route_check import decimal, enc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ENGINEER = "976409126c21bde4773f9583847e6ce9cde2a2fc"
OLD_ENGINEER = "e8b1225fe71ceb34bb3684a6b8890c8f1f3adb67"
SCIENCE = "e8d2df32b87c33a1a9ab1ad1de3112225f9d8bf7"
INSTRUCTIONS = "bc44a9adec1afee72dd65d5c6e36e1786078fa13"


def source(sha, path):
    return subprocess.check_output(["git", "show", f"{sha}:{path}"], cwd=ROOT)


def calculate():
    checks = []

    def check(name, value):
        assert value, name
        checks.append(name)

    pins = {}
    for name in ("route-report.json", "potential-report.json", "arm-report.json"):
        data = (HERE/name).read_bytes()
        check("unchanged_science_output:"+name,
              data == source(SCIENCE, "experiments/next-route-20261013/"+name))
        pins[name] = hashlib.sha256(data).hexdigest()
    r = json.loads((HERE/"route-report.json").read_text())
    a, s = r["recommended"], r["summaries"]
    # The report's exact fractions, not rounded output values, are authoritative.
    upper_fields = {
        "recommended_risk_upper": F(a["risk_upper"]),
        "recommended_paid_mission_percent": 100*F(a["mission_paid_upper"]),
        "recommended_paid_quiet_percent": 100*F(a["quiet_paid_upper"]),
        "fixed_witness_upper_percent": 100*F(r["fixed_witness_upper"]),
        "full_bus_percent": 100*F(a["full_bus_upper_with_app"]),
        "full_peak_percent": 100*F(a["full_peak_with_app_upper"]),
        "app_delay_us": 10**6*F(a["app_delay_with_margin_s"]),
    }
    lower_fields = {
        "fixed_lower_percent": 100*F(r["fixed_lower"]),
        "recommended_gain_lower": F(a["gain_lower"]),
        "risk_relative_margin_percent": 100*F(a["risk_slack"])/F(a["epsilon"]),
        "remaining_bus_percentage_points": 100*F(a["remaining_bus_price_for_5x"]),
    }
    for key, value in upper_fields.items():
        check("outward_upper:"+key, F(s[key]) >= value)
    for key, value in lower_fields.items():
        check("outward_lower:"+key, F(s[key]) <= value)
    # Even the independently rounded published endpoints suffice for 5.25.
    rounded_ratio = F(s["fixed_lower_percent"])/F(s["recommended_paid_mission_percent"])
    check("5_25_from_published_endpoints", rounded_ratio >= F("5.25"))
    check("5_251393145481_from_exact_fractions", F(a["gain_lower"]) >= F("5.251393145481"))
    check("risk_and_quiet", F(s["recommended_risk_upper"]) <= F(".001")
          and F(s["recommended_paid_quiet_percent"]) <= 1)
    check("post_window_is_one_second_not_margin_value",
          F(a["post_window_requirement_s"]) == 1
          and F(a["post_window_with_margin_s"]) == F("1.10002200111001"))
    check("rounded_delay_is_not_new_nominal_1_1",
          F(a["post_window_with_margin_s"]) > F("1.1") > F(a["post_window_requirement_s"]))
    check("no_whole_bus_5x_at_4percent",
          F(a["full_bus_gain_lower_if_equal_app_rate_at_cap"]) < 5)
    full_bus_finite = (F(a["full_bus_upper_with_app"])
                       +(F(a["app_sigma_s"])+2*F(a["app_atomic_s"]))/F(a["T_s"]))
    check("full_bus_display_also_pays_finite_app_edges",
          100*full_bus_finite <= F(s["full_bus_percent"]))
    # Scope diagnostic only: this does NOT transfer the U rule to E.
    epath = "experiments/t119-err-joint-bound/report.json"
    eraw = (ROOT/epath).read_bytes()
    check("unchanged_T119_source", eraw == source(SCIENCE, epath))
    ep = json.loads(eraw)["constant_E"]["3"]["class_lower"]
    elower = F(ep["read_price_lower"])
    ebudget = elower/F("5.25")
    check("E_lower_not_U_lower", 0 < elower < F(r["fixed_lower"]))
    check("same_U_price_not_5_25_via_E_lower", elower/F(a["mission_paid_upper"]) < F("5.25"))
    check("E_sufficient_price_threshold_rounds_down",
          F("5.869280870923") <= 100*ebudget)
    check("E_cannot_fit_U100_slot", F("1.1")*F("148.501480") > 100*F(".99999"))

    prefix = "experiments/t105-arm-rule/"
    epins = {}
    for name in ("ADVANCE_CONTRACT.md", "HANDOFF.md", "advance_budget.py",
                 "outputs/advance-budget.json", "config.json"):
        epins[name] = hashlib.sha256(source(ENGINEER, prefix+name)).hexdigest()
    production = ("batch.c", "history_batch.sv", "interval_link.sv",
                  "interval_guard.sv", "arm_executor.sv", "rule.c", "rule.h")
    check("production_unchanged", all(source(ENGINEER, prefix+n) ==
                                     source(OLD_ENGINEER, prefix+n) for n in production))
    cfg = json.loads(source(ENGINEER, prefix+"config.json"))
    engineering = json.loads(source(ENGINEER, prefix+"outputs/advance-budget.json"))
    lo, hi, jitter = F(".99999"), F("1.00001"), F(".5")
    upper = lambda ticks: ticks*hi+jitter
    history = F("531869457677237/102498975000")
    external, second, edge = upper(80), upper(36), upper(20)
    certificate, calendar = upper(600), upper(748)
    shortest = min((cfg[k]-1)*20*lo-jitter for k in ("NW", "NH", "NR"))
    prepare_fixed = external+second+history+edge+certificate
    prepare_limit = (shortest-prepare_fixed)/2
    pair_limit = cfg["PAIR_WINDOW"]*4*lo-jitter-history-2*edge
    count_limit = (2**32-3)*20*lo-jitter
    literal_fixed = external+second+history+certificate+calendar
    literal_limit = (10000-literal_fixed)/2
    expiry = edge+certificate+calendar
    tail = external+second+history+expiry
    allocation = F(10**6)
    margin = shortest-prepare_fixed-2*allocation
    values = {
        "old_literal_fresh_history_B_limit_ns": literal_limit,
        "loss_slow_to_fast_ns": second,
        "prepare_fixed_ns": prepare_fixed,
        "preparation_B_limit_ns": prepare_limit,
        "source_span_B_limit_ns": pair_limit,
        "count32_B_limit_ns": count_limit,
        "joint_B_limit_ns": min(prepare_limit, pair_limit, count_limit),
        "expiry_to_first_usable_operation_ns": expiry,
        "non_hold_tail_including_history_ns": tail,
        "selected_preparation_margin_ns": margin,
        "selected_source_span_upper_ns": allocation+history+2*edge,
        "selected_first_event_reply_upper_ns": external+second+history+2*allocation+edge,
    }
    for key, value in values.items():
        check("engineer_fraction:"+key, value == F(engineering[key]["rational"]))
    check("second_CDC_not_double_or_zero", second == F("36.500360")
          and F(engineering["historical_published_B_limit_ns"]["rational"])-literal_limit == second/2)
    check("literal_boundary_and_next_ns", literal_fixed+2*literal_limit == 10000
          and literal_fixed+2*(literal_limit+1) > 10000)
    # Review #151: the historical omission accepts B=1680 ns incorrectly.
    counterexample_B = F(1680)
    counterexample_old = literal_fixed-second+2*counterexample_B
    counterexample_corrected = literal_fixed+2*counterexample_B
    check("review_151_B1680_old_passes_corrected_fails",
          counterexample_old <= 10000 < counterexample_corrected)
    check("preparation_boundary_and_next_ns", prepare_fixed+2*prepare_limit == shortest
          and prepare_fixed+2*(prepare_limit+1) > shortest)
    check("1ms_passes_new_not_literal", margin > 0 and literal_fixed+2*allocation > 10000)
    check("all_summary_limits", allocation < prepare_limit < min(pair_limit, count_limit))
    check("49999_ticks_pass_50000_fail", upper(49999*20) <= allocation < upper(50000*20))
    count = math.ceil((allocation+jitter)/(20*lo))+2
    check("count32_not_ERR_rate_assumption", count == 50003 < 2**32-1)
    edges = math.ceil((F(315576000)*10**9+jitter)/(4*lo))+1
    check("G64_no_runtime_reset", edges == 78894788947889481 < 2**57 < 2**64-1)
    mission_slow = math.ceil((F(315576000)*10**9+jitter)/(20*lo))+1
    start_max = 2**64-1-mission_slow-cfg["NR"]
    check("qualified_start_no_tick_wrap", start_max+mission_slow+cfg["NR"] < 2**64
          and start_max+1+mission_slow+cfg["NR"] == 2**64)
    check("deadline_link_and_total_tail", 2*upper(112)+upper(320)+edge < certificate
          and tail < 10000 and F("1.1")*certificate < 1000)
    check("UNKNOWN_service_preserved", engineering["platform_service_established"] is False
          and engineering["new_physical_ARM_upper_ns"] is None)

    return enc({
        "task": 146, "scope": "final conditional U theorem and addressed ARM arithmetic; NOT E transfer or platform WCET",
        "science_input_sha": SCIENCE, "instructions_sha": INSTRUCTIONS,
        "engineer_sha": ENGINEER, "unchanged_report_sha256": pins,
        "engineer_source_sha256": epins,
        "theorem_outward_summaries": s,
        "gain_from_rounded_published_endpoints_lower": decimal(rounded_ratio, False),
        "full_bus_with_finite_app_edges_upper": full_bus_finite,
        "proved_N": "5.25", "E_transfer_proved": False,
        "T119_report_sha256": hashlib.sha256(eraw).hexdigest(),
        "E_only_scope_diagnostic": {
            "fixed_E_read_lower": elower,
            "sufficient_price_for_5_25_if_other_premises_proved": ebudget,
            "price_percent_safe_floor": decimal(100*ebudget, False),
            "NOT_a_new_E_certificate_or_impossibility": True,
        },
        "E_remaining": ["E-cross and residuals in combined LOW rule", "actual E price and observed application writes", "same-service fixed E comparator and resource/calendar"],
        "ARM_ns_exact": values,
        "ARM_review_151_counterexample_ns": {
            "B": counterexample_B,
            "historical_total_missing_second_CDC": counterexample_old,
            "corrected_total": counterexample_corrected,
            "deadline": F(10000),
        },
        "ARM_safe_displays": {
            "literal_B_upper_ns_floor": decimal(literal_limit, False, 9),
            "preparation_B_upper_s_floor": decimal(prepare_limit/10**9, False, 12),
            "non_hold_tail_upper_ns": decimal(tail, True, 9),
            "expiry_tail_upper_ns": decimal(expiry, True, 6),
            "preparation_margin_s_lower": decimal(margin/10**9, False, 12),
        },
        "ARM_selected_allocation_ns": allocation, "ARM_platform_WCET_ns": None,
        "ARM_qualified_start_tick_upper": start_max,
        "literal_processed_history_10us_satisfied": False,
        "new_internal_contract_authorized": True,
        "r4_delta_Q_and_bus_price_if_all_premises": [0, 0],
        "CPU_reserved_cores_not_bus_gain": 1,
        "device_classes": {
            "specialized_monitor": {"qualified_a": None, "qualified_latency": None},
            "star_tracker_full_frames": {"qualified_a": None, "qualified_latency": None},
            "science_CCD_available_frames": {"qualified_a": None, "qualified_latency": None},
        },
        "checks": checks, "check_count": len(checks),
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = calculate()
    text = json.dumps(data, ensure_ascii=False, indent=2)+"\n"
    out = HERE/"final-report.json"
    if args.write:
        out.write_text(text)
    else:
        assert out.read_text() == text, "T146 final-report.json mismatch"
    print(json.dumps({"checks": data["check_count"], "byte_match": not args.write,
                      "N": data["proved_N"], "ARM": data["ARM_safe_displays"]}, indent=2))


if __name__ == "__main__":
    main()

"""T146-B: 15 predeclared substitutions, no campaign or hardware qualification."""
import argparse
import copy
import hashlib
import json
import subprocess
import sys
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "519ac5e0c858ce5f71ba71c0f344d2a79edf60f2"
T141 = "ea789fc4b4d69699696d66a41b2738099d4154bb"
sys.path.insert(0, str(ROOT / "experiments/t88-dstar-sensitivity"))
import engine as accepted


def git_bytes(sha, path):
    return subprocess.check_output(["git", "show", f"{sha}:{path}"], cwd=ROOT)


def enc(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: enc(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [enc(v) for v in value]
    return value


def decimal(value, up=True, places=12):
    value = F(value)
    q = 10**places
    n = -((-value*q).numerator // (-value*q).denominator) if up else (value*q).numerator//(value*q).denominator
    sign = "-" if n < 0 else ""
    n = abs(n)
    return f"{sign}{n//q}.{n%q:0{places}d}"


def mission_price(p, quiet_return):
    """Q fraction >=.9, KQ<=1000; pay complement edges separately."""
    fast = p["cp"]/p["gm"] + p["CX"]
    assert quiet_return <= fast + F(1, 10**9)
    edge = (2*p["cp"]+p["sigmaX"])*1001/p["T"]
    return F(".9")*quiet_return + F(".1")*fast + edge


def calculate():
    checks = []

    def check(name, predicate):
        assert predicate, name
        checks.append(name)

    files = [
        "experiments/t95-method-regime-map/report.json",
        "experiments/t95-method-regime-map/verify.py",
        "experiments/t88-dstar-sensitivity/engine.py",
        "experiments/t88-dstar-sensitivity/outputs/selected.json",
        "experiments/t82-realistic-timing/t80_joint.py",
        "experiments/t82-realistic-timing/t80_engine.py",
        "experiments/t82-realistic-timing/t80_err.py",
        "experiments/t82-realistic-timing/timing.py",
        "experiments/t90-monitor-physical/outputs/handoff.json",
        "experiments/t90-monitor-physical/outputs/pinned_inputs.json",
        "experiments/t126-regime-map/SOURCES.md",
    ]
    pins = {}
    for path in files:
        raw = (ROOT/path).read_bytes()
        check("unchanged:"+path, raw == git_bytes(BASE, path))
        pins[path] = hashlib.sha256(raw).hexdigest()
    t95 = json.loads((ROOT/files[0]).read_text())
    fixed = t95["rows"][0]
    LB = F(t95["lower_bound"]["fixed_class_cost_lower"])
    UB = F(fixed["fixed_cost_upper"])
    check("nonempty_constant_bracket", 0 < LB < UB < F(".8"))
    p0 = accepted.context("3", "combined")
    rows = []
    full = {}
    for g, ka in ((140, 367), (176, 101), (196, 51)):
        p = accepted.calendar(p0, g)
        p["Dstar"] = F(".0002802445")
        vc = accepted.j.flat_v(p, ka)
        check(f"resource_{g}", p["resource_pass"])
        for a in (1000, 10000, 20000, 100000, 1000000):
            m = accepted.j.window(p, F(a), F(1), F(1), F(2), "total_load", 2)
            r = accepted.j.evaluate(p, m, ka, vc, "direct-fast", F(0), vc_kind="flat")
            key = f"g{g}_ka{ka}_a{a}"
            item = {
                "id": key, "g_ticks": g, "ka": ka, "aM_requirement": a,
                "vc_per_s": vc, "status": r["status"],
                "risk_upper": r["risk_upper"], "k_safe": r["k"],
                "resource_pass": p["resource_pass"],
                "quiet_returns_upper": None, "mission_upper": None,
                "certified_gain_lower": None, "physical_channel_qualified": False,
                "safe_no_information_cap": p["cp"]/p["gm"]+p["CX"]+(2*p["cp"]+p["sigmaX"])*1001/(F(".9")*p["T"]),
            }
            if r["status"] == "certified_conditional":
                cost = mission_price(p, r["returns_upper"])
                item.update(
                    quiet_returns_upper=r["returns_upper"], mission_upper=cost,
                    certified_gain_lower=LB/cost, pM_upper=r["pM_upper"],
                    ideal_information_family_gain_upper=UB/(p["cm"]/p["gp"]/ka-2*p["cp"]/p["T"]),
                )
                full[key] = (p, m, r)
            rows.append(item)
    check("exactly_predeclared_15_rows", len(rows) == 15)
    old = full["g140_ka367_a1000000"][2]
    check("T95_anchor_risk_byte_value", old["risk_upper"] == F(fixed["risk_upper"]))
    check("T95_anchor_quiet_value", old["returns_upper"] == F(fixed["normal_price_upper"]))
    old_mission = next(x["mission_upper"] for x in rows if x["id"] == "g140_ka367_a1000000")
    check("quiet_117x_is_not_mission_5x", LB/old_mission < 5)
    p, m, r = full["g176_ka101_a100000"]
    fixed_check = accepted.fixed(p, p["Dstar"])
    check("fixed_witness_recomputed_same_M", fixed_check["M"] == fixed["fixed_M"] and fixed_check["resource_pass"])
    core = mission_price(p, r["returns_upper"])
    Cf = p["cp"]/p["gm"]
    outage_requirement = F(".001")
    extra_X_requirement = F(".001")
    paid = core + Cf*outage_requirement + extra_X_requirement
    quiet_paid = r["returns_upper"] + Cf*outage_requirement/F(".9") + extra_X_requirement
    cfg = copy.deepcopy(p["cfg"])
    cfg["resources"]["extra_monitor_control_rate"] = str(p["CX"]+extra_X_requirement)
    rv = accepted.resources(cfg)
    delay = (1+p["margin"])*rv["delay"]
    h = F(".001")
    app_rate = F(cfg["resources"]["application_rate"])
    sigma_app = F(cfg["resources"]["application_sigma_s"])
    atomic_app = F(cfg["resources"]["application_max_request_s"])
    # All busy fragments in an arbitrary window, including arrivals outside it.
    full_peak = rv["peak"] + (sigma_app+app_rate*(h+2*delay)+2*atomic_app)/h
    check("paid_mission_5x", LB/paid >= 5)
    check("paid_quiet_1pct", quiet_paid <= F(".01"))
    check("risk_margin_5pct", r["risk_upper"] <= F(".00095"))
    check("full_peak_80pct_including_app", full_peak <= F(".8"))
    check("app_delay_3us_with_10pct", delay <= F(".000003"))
    check("resource_with_extra_X", rv["ok"])
    statistical_upper = m["J"]*F((accepted.j.I(0)-accepted.j.I(m["H"])).exp().hi)
    check("statistical_quota_whole_mission", statistical_upper <= F(p["q"]["alpha_M"]))
    check("repeated_outages_no_new_quota", r["quota_upper"] == F(6, 10**6) if "quota_upper" in r else accepted.old.errors(p["q"], p["mode"]) == F(6,10**6))
    check("failed_information_prices_not_zero", all(x["mission_upper"] is None for x in rows if x["status"] != "certified_conditional"))
    cheap = min((x for x in rows if x["mission_upper"] is not None), key=lambda x:x["mission_upper"])
    check("best_declared_family_not_recommendation", cheap["g_ticks"] == 196)
    # Addressed inverse requirement, not an additional controller search.
    phi_lower = accepted.old.phi(r["z"])[0]
    a_sufficient = (r["z"]*r["k"]+m["H"])/(phi_lower*r["mass_lower"])
    hidden_mass = accepted.j.fast_exposure(r["vc"],p["b"],m["wm"],m["hF_max"])[0]
    a_with_hidden_background = (r["z"]*r["k"]+m["H"])/(phi_lower*hidden_mass)
    TQ = F(".9")*p["T"]
    freqQ = 1/m["Delta_m"]+2*1000*m["wp"]/(m["Delta_m"]*TQ)+F(2000)/TQ
    price_slope_pM = Cf*r["DM"]*freqQ
    pM_cap = min(
        r["pM_upper"]+(F(".01")-quiet_paid)/price_slope_pM,
        r["pM_upper"]+(LB/5-paid)/(F(".9")*price_slope_pM),
    )
    quantum = F(1,10**6)
    lo_mu, hi_mu = 0, 92*10**6
    while hi_mu-lo_mu>1:
        md=(hi_mu+lo_mu)//2
        if accepted.j.poisson_chernoff(md*quantum,r["k"]) <= pM_cap:
            lo_mu=md
        else:
            hi_mu=md
    mu_cap = lo_mu*quantum
    check("derived_channel_lower_sufficient", a_sufficient <= 100000)
    check("derived_quiet_mean_cap", m["mu"] < mu_cap and accepted.j.poisson_chernoff(mu_cap,r["k"]) <= pM_cap < accepted.j.poisson_chernoff(mu_cap+quantum,r["k"]))

    # Separate T141 sensitivity: NOT an inferred grouped-parent model.
    chain_path = "experiments/t141-radiation-chain/outputs/contract.json"
    raw_chain = git_bytes(T141, chain_path)
    chain = json.loads(raw_chain)
    ch = next(x for x in chain["scenarios"] if x["shield_g_cm2"] == 3)
    B, b, FS = (F(str(ch[x])) for x in ("peak_upper_s_inv", "background_s_inv", "N_solar_upper"))
    # One-second inward margin also avoids treating printed T141 decimals
    # as exact unrounded equalities of peak*fluence and its printed S2.
    L = F(115775)
    S2_chain = F(str(ch["S2_upper_s_inv"]))
    check("T141_witness_inside_both_scalar_caps",
          (B-b)*L <= FS and b*b*p["T"]+(B*B-b*b)*L <= S2_chain)
    W, n = p["W"], 38
    beta = F(n-1, 2*n*W)
    Pmin = W*p["cm"]  # even 100% bus, stronger than any 80%-peak limit
    P1 = F(2)
    z = beta*B*B*(L-2*P1)*Pmin*(1-p["cp"]/Pmin)**2*(1-B*P1/W)
    risk_lb = z/(1+z)-F("1e-6")
    J = int(L//P1)+2
    cell = (L-J*p["cp"])/(4*J)
    x = B*cell/W
    zz = 2*W*J*F(n-1,2*n)*x*x*(1-x)
    tail_lb = zz/(1+zz)-F("1e-6")
    check("T141_unit_singleton_extension_constant_exclusion", min(risk_lb, tail_lb) > F(".001"))
    check("T141_unknown_fields_remain_null", chain["physical_unresolved"]["full38_Dstar"] is None and chain["physical_unresolved"]["ERR_lower_informativeness"] is None)
    rec = {
        "id": "g176_ka101_a100000",
        "status": "PAID_CONDITIONAL_METHOD; actual star-tracker contract NOT established",
        "W": p["W"], "n": 38, "T_s": p["T"], "epsilon": p["eps"],
        "Dstar": p["Dstar"], "b_per_s": p["b"], "B_per_s": p["B"],
        "FS": p["FS"], "rho_all_rises_per_s": F(".048"), "l_per_s": F(".001"),
        "service": "full-U100, NOT E/r4 physical implementation",
        "g_ticks": 176, "ka": 101, "c_ticks": 100,
        "Ps_upper_s": p["Ps"], "Pl_upper_s": 101*p["Ps"],
        "vc_per_s": r["vc"], "window_lower_s": m["wm"], "window_upper_s": m["wp"],
        "stride_lower_s": m["Delta_m"], "stride_upper_s": m["Delta_p"],
        "post_window_requirement_s": F(1), "post_window_with_margin_s": m["dp"],
        "hF_ticks": m["hF_ticks"], "hF_min_s": m["hF_min"], "hF_max_s": m["hF_max"],
        "k_safe": r["k"], "z": r["z"], "H": m["H"], "J": m["J"],
        "actual_statistics_union_upper": statistical_upper,
        "LOW_slack_lower": r["LOW_slack"], "lease_slack_s": r["lease_slack_s"],
        "aM_requirement": F(100000), "quiet_A_M_requirement": F(100000),
        "eta_requirement_per_s": F(".001"),
        "mF_lower": r["mass_lower"], "quiet_mu_upper": m["mu"],
        "sufficient_a_for_fixed_threshold": a_sufficient,
        "sufficient_a_if_hidden_component_le_b": a_with_hidden_background,
        "pM_cap_for_5x_and_quiet_1pct": pM_cap,
        "quiet_mu_sufficient_cap_for_fixed_threshold": mu_cap,
        "quiet_mu_cap_NOT_selected_point": True,
        "peak_ideal_lower_rate_per_s_NOT_detector_capacity": 100000*p["B"],
        "pM_upper": r["pM_upper"], "per_window_invalid_probability_requirement": F("1e-9"),
        "risk_upper": r["risk_upper"], "risk_slack": p["eps"]-r["risk_upper"],
        "DE_s": r["DE"], "DM_s": r["DM"],
        "quiet_before_extra": r["returns_upper"], "mission_before_extra": core,
        "outage_dilated_fraction_requirement": outage_requirement,
        "extra_X_rate_requirement": extra_X_requirement,
        "whole_X_rate_requirement": p["CX"]+extra_X_requirement,
        "whole_X_burst_s_requirement": p["sigmaX"],
        "whole_X_max_atomic_s_requirement": F("45e-9"),
        "outage_price_upper": Cf*outage_requirement,
        "mission_paid_upper": paid, "quiet_paid_upper": quiet_paid,
        "gain_lower": LB/paid, "remaining_bus_price_for_5x": LB/5-paid,
        "app_rate_envelope": app_rate, "app_sigma_s": sigma_app,
        "app_atomic_s": atomic_app, "full_bus_upper_with_app": paid+app_rate,
        "protection_plus_X_peak_upper": rv["peak"],
        "full_peak_with_app_upper": full_peak, "app_delay_with_margin_s": delay,
        "full_bus_gain_lower_if_equal_app_rate_at_cap": (LB+app_rate)/(paid+app_rate),
        "app_mean_cap_for_full_bus_5x": (LB-5*paid)/4,
        "CPU_utilization_actual": None,
        "CPU_requirement": "bounded per-message/recovery work and total post-window path <=1s; incremental core occupancy reported separately, all shared traffic inside X",
        "measured_or_hardware_qualified": False,
    }
    summaries = {
        "fixed_lower_percent": decimal(100*LB, False),
        "fixed_witness_upper_percent": decimal(100*UB),
        "recommended_risk_upper": decimal(r["risk_upper"], True, 15),
        "risk_relative_margin_percent": decimal(100*(p["eps"]-r["risk_upper"])/p["eps"], False),
        "recommended_paid_mission_percent": decimal(100*paid),
        "recommended_paid_quiet_percent": decimal(100*quiet_paid),
        "recommended_gain_lower": decimal(LB/paid, False),
        "remaining_bus_percentage_points": decimal(100*(LB/5-paid), False),
        "full_bus_percent": decimal(100*(paid+app_rate)),
        "full_peak_percent": decimal(100*full_peak),
        "app_delay_us": decimal(delay*10**6),
    }
    return enc({
        "task": 146, "part": "B", "base_sha": BASE,
        "accepted_sources_unchanged_sha256": pins,
        "method": "accepted direct-fast T80(6a), T95 fixed lower and erasure theorem; new finite-horizon price composition",
        "fixed_lower": LB, "fixed_witness_upper": UB,
        "fixed_M_ticks": fixed["fixed_M"], "fixed_witness_risk_at_next_tick": fixed["fixed_next_risk"],
        "fixed_witness_recomputed": fixed_check,
        "rows": rows, "recommended": rec,
        "best_only_in_declared_family": cheap["id"],
        "summaries": summaries,
        "LEO": {
            "status": "NUMERIC_ADMISSION_UNKNOWN; not declared physically impossible",
            "part_word_code": None, "response_and_direct": None,
            "position_error_and_delivery": None, "safe_region_upper_including_solar": None,
            "high_duty_fraction": None, "constant_witness": None,
            "L_fixed": None, "U_adaptive": None, "gain": None,
            "diagnostic_class": "two calendars, short=admissible constant witness; cost-free perfect position lower-price relaxation only",
            "leading_term_diagnostic_ignoring_finite_edges_by_high_fraction": {
                ".05": "20", ".1": "10", ".2": "5", ".3": "10/3"
            },
            "necessary_for_same_short_witness_family_5x": "f_H <= .2 + (e_F/5+e_H)/C_f; full finite-edge values unknown",
            "source": "experiments/t126-regime-map/SOURCES.md A5 including 08.10 correction",
        },
        "T141_separate": {
            "sha": T141, "source_sha256": hashlib.sha256(raw_chain).hexdigest(),
            "S2_covered_s_inv": str(ch["S2_upper_s_inv"]),
            "physical_Dstar": None, "physical_ERR_lower": None,
            "transfer_to_nu_Theta": None, "conditional_singleton_unit_map": True,
            "extra_hypotheses": "ONLY if T141 scalar lambda is also the singleton NHPP load and the initial plateau is a member; not established T141 full-word law",
            "plateau_length_s": L, "minimum_serial_U_period_s_even_100pct": Pmin,
            "moderate_constant_risk_lower": risk_lb, "tail_constant_risk_lower": tail_lb,
            "conclusion_in_extra_hypotheses": "constant full-U class empty; no gain ratio may be claimed; accepted R0-A unchanged",
        },
        "checks": checks, "check_count": len(checks),
        "real_channel_contract": {
            "star_tracker_identity": None, "full_spectral_lower": None,
            "quiet_count_upper": None, "frame_cadence_latency": None,
            "misleading_count_lifetime_probability": None,
            "expanded_outage_fraction": None, "bus_and_CPU_cost": None,
            "no_area_to_sensitivity_conversion": True,
        },
    })


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    obj = calculate()
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    out = HERE/"route-report.json"
    if args.write:
        out.write_text(text)
    else:
        assert out.read_text() == text, "route-report differs"
    print(json.dumps({"checks": obj["check_count"], "rows": len(obj["rows"]),
                      "byte_match": not args.write, **obj["summaries"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

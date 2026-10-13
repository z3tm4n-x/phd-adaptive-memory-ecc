"""T146 updated issue: two distinct potentials and a JOINT channel region.

Addressed algebra/inversion only; no new environment or controller campaign.
Default is read-only, --write changes this task's own report only.
"""
import argparse
import copy
import hashlib
import json
from fractions import Fraction as F

from route_check import HERE, ROOT, BASE, accepted, decimal, enc, git_bytes, mission_price


def calculate():
    checks = []

    def check(name, value):
        assert value, name
        checks.append(name)

    pins = {}
    for name in (
        "experiments/t58-fixed-baseline-r0b/summary.json",
        "experiments/t58-fixed-baseline-r0b/conditions.md",
        "experiments/a2-preflight-20261009/results.json",
        "experiments/a2-preflight-20261009/analyze.py",
        "experiments/t119-err-joint-bound/HANDOFF.md",
        "experiments/t119-err-joint-bound/config.json",
        "experiments/t119-err-joint-bound/report.json",
    ):
        raw = (ROOT/name).read_bytes()
        check("unchanged:"+name, raw == git_bytes(BASE, name))
        pins[name] = hashlib.sha256(raw).hexdigest()
    hist = json.loads((ROOT/"experiments/t58-fixed-baseline-r0b/summary.json").read_text())["history"]
    pre = json.loads((ROOT/"experiments/a2-preflight-20261009/results.json").read_text())
    Th, Fh, Sh = (F(hist[k]) for k in ("T_s", "I1_nu", "I2_nu_s_inverse"))
    Jh = Th*Sh/Fh**2
    check("historical_7p24_exact_provenance", Jh == F(hist["J"]))
    Fd, Sd = (F(hist[k]) for k in ("F_diagnostic_nu", "S2_diagnostic_nu_s_inverse"))
    Jd = Th*Sd/Fd**2
    check("A2_5p87_exact_provenance", Jd == F(pre["clairvoyant_pair_relaxation_gain"]["exact"]))
    check("different_profiles_not_same_potential", Jh != Jd)

    old = json.loads((HERE/"route-report.json").read_text())
    rec = old["recommended"]
    p = accepted.calendar(accepted.context("3", "combined"), 176)
    p["Dstar"] = F(rec["Dstar"])
    T, B, b, FS = (p[k] for k in ("T", "B", "b", "FS"))
    L = FS/(B-b)
    Fw = b*T+FS
    S2w = b*b*T+(B+b)*FS
    Jw = T*S2w/Fw**2
    check("R0A_witness_moments_are_attainable", L == 115776 and 0 < L < T and
          Fw == B*L+b*(T-L) and S2w == B*B*L+b*b*(T-L))
    check("Cauchy_unit_check", Jw >= 1 and T*(b*b*T)/(b*T)**2 == 1)
    # A concrete oracle nested-calendar policy: execute all until L+2Ps;
    # afterwards execute only mandatory slots. No actual channel is credited.
    ka, Ps = 101, p["Ps"]
    cf_lo, cf_hi = p["cm"]/p["gp"], p["cp"]/p["gm"]
    cs_lo, cs_hi = cf_lo/ka, cf_hi/ka
    Hplus = L+2*Ps
    # Two joined components, with <=2 full-U edge blocks each.
    edge = 4*p["cp"]/T
    oracle_lo = cf_lo*L/T+cs_lo*(1-L/T)-edge
    oracle_hi = cf_hi*Hplus/T+cs_hi*(1-Hplus/T)+edge
    fixed = old["fixed_witness_recomputed"]
    f_lo, f_hi = F(fixed["cost_lower"]), F(fixed["cost_upper"])
    oracle_gain_lo, oracle_gain_hi = f_lo/oracle_hi, f_hi/oracle_lo
    check("oracle_interval_order", 0 < oracle_lo < oracle_hi < f_lo < f_hi)
    check("oracle_risk_and_resources_keep_same_mask",
          F(rec["risk_upper"]) <= p["eps"] and p["resource_pass"])
    check("oracle_is_mission_not_quiet", oracle_lo > cs_lo)
    check("different_potential_types", not (oracle_gain_lo <= Jw <= oracle_gain_hi))

    LB, vc, risk = F(old["fixed_lower"]), F(rec["vc_per_s"]), F(rec["risk_upper"])
    a, mu, k, z = F(100000), F(rec["quiet_mu_upper"]), 91, F(1)
    phi, phi_upper = accepted.old.phi(z)
    extra, omega = F(".001"), F(".001")

    def joint(d, extra_rate=extra, expanded_outage=omega, quiet_mu=mu):
        m = accepted.j.window(p, a, F(1), d, F(2), "total_load", 2)
        mass, mass_upper = accepted.j.fast_exposure(vc, F(0), m["wm"], m["hF_max"])
        DE, DM = accepted.j.strips(p, m, F(0), "direct-fast")
        tail = accepted.j.poisson_chernoff(quiet_mu, k)
        pr = accepted.j.price(p, m, ka, risk, DE, DM, tail)
        core = mission_price(p, pr["returns_upper"])
        paid = core+cf_hi*expanded_outage+extra_rate
        quiet_paid = pr["returns_upper"]+cf_hi*expanded_outage/F(".9")+extra_rate
        a_suff = (z*k+m["H"])/(phi*mass) if mass else None
        omega_cap = min((LB/5-core-extra_rate)/cf_hi,
                        F(".9")*(F(".01")-pr["returns_upper"]-extra_rate)/cf_hi)
        cfg = copy.deepcopy(p["cfg"])
        cfg["resources"]["extra_monitor_control_rate"] = str(p["CX"]+extra_rate)
        rv = accepted.resources(cfg)
        delay = (1+p["margin"])*rv["delay"]
        full_peak = rv["peak"]+(F("45e-9")+F(".04")*(F(".001")+2*delay)+F("90e-9"))/F(".001")
        # Both exposure and price at the SAME rounded lease and strip widths.
        allowed = (mass > 0 and a_suff <= a and m["hF_slack"] >= 0 and
                   expanded_outage <= omega_cap and paid <= LB/5 and quiet_paid <= F(".01") and
                   rv["ok"] and delay <= F("3e-6") and full_peak <= F(".8"))
        return dict(d_requested_s=d, post_window_rounded_s=m["dp"],
                    hF_ticks=m["hF_ticks"], hF_lower_s=m["hF_min"],
                    hF_upper_s=m["hF_max"], lease_slack_s=m["hF_slack"],
                    mass_lower=mass, mass_upper=mass_upper, a_sufficient=a_suff,
                    LOW_slack=a*phi*mass-z*k-m["H"],
                    LOW_slack_upper=a*phi_upper*mass_upper-z*k-m["H"],
                    DM_s=DM, DE_s=DE, pM_upper=tail, omega_cap=omega_cap,
                    expanded_outage_requirement=expanded_outage,
                    extra_X_rate=extra_rate, quiet_mu_upper=quiet_mu,
                    mission_paid_upper=paid, quiet_paid_upper=quiet_paid,
                    gain_lower=LB/paid, full_peak_upper=full_peak,
                    app_delay_upper_s=delay, all_joint_conditions_pass=allowed)

    anchor = joint(F(1))
    check("anchor_unchanged", anchor["mission_paid_upper"] == F(rec["mission_paid_upper"]) and
          anchor["quiet_paid_upper"] == F(rec["quiet_paid_upper"]) and anchor["all_joint_conditions_pass"])
    # All relevant quantities are monotone in d under a fixed threshold:
    # lease/dilation grow, exposure decreases, price cannot decrease.
    scale = 10**6
    lo, hi = 0, 60*scale
    check("delay_bracket", joint(F(lo, scale))["all_joint_conditions_pass"] and
          not joint(F(hi, scale))["all_joint_conditions_pass"])
    steps = 0
    while hi-lo > 1:
        md = (lo+hi)//2
        if joint(F(md, scale))["all_joint_conditions_pass"]:
            lo = md
        else:
            hi = md
        steps += 1
    good, bad = joint(F(lo, scale)), joint(F(hi, scale))
    check("finite_delay_certificate", good["all_joint_conditions_pass"] and
          not bad["all_joint_conditions_pass"] and steps <= 26)
    check("delay_blocked_by_LOW_not_changed_risk", bad["LOW_slack_upper"] < 0 and
          bad["mission_paid_upper"] < LB/5 and bad["quiet_paid_upper"] < F(".01"))
    check("joint_outage_cap_not_independent_axis", anchor["omega_cap"] >= omega and
          not joint(F(1), expanded_outage=anchor["omega_cap"]+F(1,10**12))["all_joint_conditions_pass"])
    check("extra_information_price_charged", not joint(F(1),extra_rate=F(".01"))["all_joint_conditions_pass"])
    check("counter_silence_not_free", not joint(F(1),quiet_mu=F(92))["all_joint_conditions_pass"])
    check("same_no_restart_quota", accepted.old.errors(p["q"],p["mode"]) == F("0.000006"))
    # Several outages may be much more expensive than one interval of equal
    # total length. No independence from peaks is used.
    coarse_outages = F(".0009")+2*good["DM_s"]*1000/T
    fragmented_outages = F(".0009")+2*good["DM_s"]*1000000/T
    check("number_and_length_of_outages_both_count", coarse_outages < omega < fragmented_outages)
    # Mechanism checks for LEO algebra; these are NOT LEO data.
    sectors = [(F(1), F(2), F(0)), (F(1), F(0), F(3)),
               (F(1), F(2), F(3)), (F(1), F(0), F(0))]
    actual_square = sum((bg+sa+sp)**2 for bg,sa,sp in sectors)
    separate_square = sum(bg*bg+sa*sa+sp*sp for bg,sa,sp in sectors)
    cross = sum(2*(bg*sa+bg*sp+sa*sp) for bg,sa,sp in sectors)
    check("LEO_cross_moments_are_not_deleted", actual_square == separate_square+cross and cross > 0)
    zone = {0,2}; polar = {1,2}
    check("LEO_union_price_pays_overlap_once", len(zone | polar) == len(zone)+len(polar)-len(zone & polar))
    check("position_alone_cannot_exclude_outside_solar_peak", b < vc < B)

    return enc({
        "task": 146, "supplement": "author update: two potentials and JOINT channel conditions",
        "plan_sha": "184cabf8f03107544e60381e608817637a50a14d",
        "source_base": BASE, "source_hashes_sha256": pins,
        "historical_7p24": {
            "T_s": Th, "F_model": Fh, "S2_model": Sh, "G_ideal": Jh,
            "source": "T58 summary.history, master cf7ab706224f7872fdafcf34febda70e3f6c8dd1",
            "raw_stream_response": "upsets.xlsx -> filled hourly gp/sp -> nu=11.7gp+4sp; NOT raw GOES flux equals memory lambda",
            "CSV_sha256": "5b1f77b83c2c1a708c99663b7da13437414527e1a1ecebeee091bc71356eea22",
            "physical_forward_response_qualified": False,
        },
        "A2_5p87": {"T_s": Th, "F_diagnostic": Fd, "S2_diagnostic": Sd, "G_ideal": Jd,
                     "kind": "attainable two-level rarity witness, NOT same historical profile or achieved gain"},
        "R0A_potentials": {
            "profile": "nu=B on [0,L], then b; conditional T95 witness; not actual satellite trace",
            "L_s": L, "T_s": T, "F": Fw, "S2": S2w, "G_ideal_quadratic": Jw,
            "quadratic_model": "Qpair=beta*integral(nu^2 P), price=Wc/T*integral(1/P); known future, no bus/clock/phase/info cost",
            "quadratic_value_is_not_class_wide_guarantee_or_ceiling": True,
            "declared_fixed_M_ticks": fixed["M"],
            "declared_fixed_cost_lower": f_lo, "declared_fixed_cost_upper": f_hi,
            "oracle_family": "same nested calendar g176/ka101; all short through L+2Ps, then mandatory; cost-free true environment, not future errors",
            "oracle_mission_cost_lower": oracle_lo, "oracle_mission_cost_upper": oracle_hi,
            "G_declared_fixed_oracle_lower": oracle_gain_lo,
            "G_declared_fixed_oracle_upper": oracle_gain_hi,
            "oracle_global_optimum_claimed": False,
            "actual_R0A_trace_Gideal": None,
            "paid_causal_Gcert_lower": F(rec["gain_lower"]),
        },
        "joint_channel": {
            "units_a": "ideal counted traces per unit memory word-load nu; NOT observed ERR ratio",
            "a_selected": a, "quiet_mu_selected": mu, "k": k, "z": z, "H": 35,
            "anchor": anchor, "delay_sufficient_grid_endpoint": good,
            "next_grid_point_fails_this_test": bad, "inversion_steps": steps,
            "endpoint_kind": "greatest passing 1us grid point for THIS fixed-threshold sufficient test, NOT L*",
            "coarse_outages_example_dilated_fraction": coarse_outages,
            "fragmented_outages_example_dilated_fraction": fragmented_outages,
            "outage_example_values_are_requirements_not_measurements": True,
        },
        "LEO_potentials": {
            "G_ideal": None, "G_declared_fixed_oracle": None, "G_cert": None,
            "predictable_zone_fraction": None, "unpredictable_polar_fraction": None,
            "overlap_fraction": None, "predictable_savings_fraction": None,
            "missing": "response trace and matched memory/service/position/solar contract; no R0A/A2 transplant",
        },
        "ERR_comparison": {
            "accepted_point": "T119 one_presented: ka=5, h=120s, g196, ERR-write E",
            "accepted_gain_lower": "2.80545",
            "not_point": "r4/T135 ka=3",
            "same_hardware_comparison_to_U100_available": False,
            "required_before_hardware_information_gain_claim": "recompute both with SAME E or SAME U, workload, time and quotas",
        },
        "summaries": {
            "historical_Gideal": decimal(Jh, False),
            "A2_diagnostic_Gideal": decimal(Jd, False),
            "R0A_witness_Gideal": decimal(Jw, False),
            "R0A_oracle_mission_percent_lower": decimal(100*oracle_lo, False),
            "R0A_oracle_mission_percent_upper": decimal(100*oracle_hi),
            "R0A_declared_fixed_oracle_gain_lower": decimal(oracle_gain_lo, False),
            "R0A_declared_fixed_oracle_gain_upper": decimal(oracle_gain_hi),
            "post_window_sufficient_s": decimal(good["d_requested_s"], False, 6),
            "post_window_next_test_failure_s": decimal(bad["d_requested_s"], True, 6),
            "joint_at_delay_endpoint_mission_percent": decimal(100*good["mission_paid_upper"]),
            "joint_at_delay_endpoint_quiet_percent": decimal(100*good["quiet_paid_upper"]),
            "joint_at_delay_endpoint_gain_lower": decimal(good["gain_lower"], False),
            "anchor_dilated_outage_cap": decimal(anchor["omega_cap"], False),
        },
        "checks": checks, "check_count": len(checks),
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    obj = calculate()
    text = json.dumps(obj, ensure_ascii=False, indent=2)+"\n"
    output = HERE/"potential-report.json"
    if args.write:
        output.write_text(text)
    else:
        assert output.read_text() == text, "potential-report differs"
    print(json.dumps({"checks": obj["check_count"], "byte_match": not args.write,
                      **obj["summaries"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

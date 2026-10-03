"""Bounded T81 audit. Reuse accepted T68 inputs; never rerun raw-data campaigns.

Units: fluence cm^-2, cross section cm^2 per tested array, D expected
number of parents with >=2 distinct positions in at least one codeword.
All numerical exposure forecasts are CONDITIONAL, not test orders.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import zipfile

import numpy as np
import scipy
from scipy.stats import chi2

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
T68 = REPO / "experiments/t68-v21-inputs"
CFG = json.loads((HERE / "config.json").read_text())
OUT = HERE / "outputs"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


# Importing T68 does not run main, extract archives, or write accepted outputs.
t68 = module("t68_readonly", T68 / "run.py")

def accepted_gf2_solver():
    path = REPO / "experiments/RE-CY62167-ADDRESS-MAPPING-01/address_mapping_gf2.py"
    tree = ast.parse(path.read_text())
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "solve_gf2_unique"]
    ns = {}
    exec(compile(tree, str(path)+":solver_only", "exec"), ns)
    return ns["solve_gf2_unique"]


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(name, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def save_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                      allow_nan=False) + "\n", encoding="utf-8")


def mu_upper(n, alpha):
    """One-sided Poisson mean upper, conditional on fixed complete exposure."""
    if isinstance(n, bool) or int(n) != n or n < 0 or not 0 < alpha < 1:
        raise ValueError("Invalid Poisson count/alpha")
    return -math.log(alpha) if n == 0 else float(chi2.isf(alpha, 2*(n+1))/2)


def sigma_upper(n, nominal_fluence, alpha, theta=0., efficiency=1., geometry=1.):
    if (not all(math.isfinite(v) for v in (nominal_fluence, theta, efficiency, geometry))
        or nominal_fluence <= 0 or not 0 <= theta < 1 or not 0 < efficiency <= 1 or geometry <= 0):
        raise ValueError("Positive qualified exposure/efficiency/geometry required")
    return mu_upper(n, alpha) / ((1-theta)*nominal_fluence*efficiency*geometry)


def allocation_fluence(weight, budget, alpha, old_effective=0., theta=0., efficiency=1., geometry=1.):
    """Nominal NEW zero-count fluence for C_j sigma_j <= b_j.

    C_j is mission fluence in the SAME angular/area normalization as sigma_j.
    Old exposure may be credited only for the same predeclared full event law.
    """
    if not all(math.isfinite(v) for v in (weight, budget, old_effective)) or weight < 0 or budget <= 0 or old_effective < 0:
        raise ValueError("Invalid weight/budget/existing exposure")
    scale = sigma_upper(0, 1., alpha, theta, efficiency, geometry)/mu_upper(0, alpha)
    return max(0., mu_upper(0, alpha)*weight/budget-old_effective)*scale


def angular_requirements():
    """Coefficients, NOT fabricated mission angular weights or test qualification.

    Equal budget b_j=(Dtarget-R)/J is an explicit algebraic sensitivity.
    C_j, R, q_j and g_j remain unknown. R=0 is only the optimistic limit
    used to print a coefficient; never exported as a physical input.
    """
    a = CFG["angular_sensitivity"]
    j = len(a["polar_strata_deg"])
    alpha = a["alpha_family"]/(j*a["architectures_in_joint_family"])
    rows = []
    for arch in ("internal38", "external39_assembly"):
        for rho in CFG["scenario"]["shields_g_cm2"]:
            for target in CFG["scenario"]["direct_mean_targets"]:
                for lo, hi in a["polar_strata_deg"]:
                    rows.append({"architecture": arch, "shield_g_cm2": rho, "target_D": target,
                        "theta_polar_low_deg": lo, "theta_polar_high_deg": hi,
                        "azimuth_deg": "all [0,360)", "test_LET_min_MeV_cm2_mg": 57,
                        "joint_comparisons": j*a["architectures_in_joint_family"], "alpha_per_stratum": alpha,
                        "unknown_mission_weight_C_cm2_inv": None, "unknown_remainder_R": None,
                        "unknown_efficiency_lower": None, "unknown_geometry_factor": None,
                        "budget_formula": "(Dtarget-R)/3",
                        "Fnew_per_C_optimistic_R0_q1_g1_theta03": allocation_fluence(1, target/j, alpha, theta=.3),
                        "required_actual_Fnew_cm2_inv": None,
                        "continuum_requirement": "upper for entire polar/azimuth stratum; points alone insufficient"})
    save_csv("angular_requirements.csv", rows)


def original_spectral_functions():
    # T68's AST-only reuse pattern: not executing original top-level pickle I/O.
    with zipfile.ZipFile(T68 / "inputs/calc_v18.zip") as z:
        tree = ast.parse(z.read("spectra_lib.py").decode("utf-8"))
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    ns = {"np": np}
    exec(compile(tree, "calc_v18.zip/spectra_lib.py:functions_only", "exec"), ns)
    return ns


def segment_integral(x0, x1, y0, y1, lo, hi):
    """Analytic integral of T68's log/log or zero-node log-linear interpolant."""
    if not (0 < x0 <= lo < hi <= x1) or min(y0, y1) < 0:
        raise ValueError("Invalid segment")
    dlog = math.log(x1/x0)
    if y0 > 0 and y1 > 0:
        power = math.log(y1/y0)/dlog
        at_lo = y0*math.exp(power*math.log(lo/x0))
        q = power+1
        return at_lo*lo*(math.log(hi/lo) if abs(q) < 1e-12 else math.expm1(q*math.log(hi/lo))/q)
    slope = (y1-y0)/dlog
    primitive = lambda x: y0*x+slope*(x*math.log(x/x0)-x)
    return primitive(hi)-primitive(lo)


def integrate_spectrum(table, col, lo, hi):
    # Native export: LET MeV/(g/cm2); L=X/1000, phi_L=1000*phi_X.
    xs, ys = table[:, 0]/1000., table[:, col]*1000.
    if not xs[0] <= lo <= hi <= xs[-1]:
        raise ValueError("No extrapolation outside printed spectrum")
    return math.fsum(segment_integral(a, b, c, d, max(a, lo), min(b, hi))
                     for a, b, c, d in zip(xs[:-1], xs[1:], ys[:-1], ys[1:])
                     if min(b, hi) > max(a, lo))


def envelope(values, x):
    levels = CFG["historical_envelope"]["let_nodes_MeV_cm2_mg"]
    idx = np.minimum(np.searchsorted(levels, x, side="left"), len(levels)-1)
    return np.where(np.asarray(x) < 27, 0., np.asarray(values)[idx])


def additional_fluence(weights, pools, target, alpha, theta, update="all"):
    """Bracket (not point-only root) for the conditional pooled zero-count model."""
    weights, pools = np.asarray(weights), np.asarray(pools)
    if (weights.ndim != 1 or weights.shape != pools.shape or not len(weights)
        or not np.all(np.isfinite(weights)) or not np.all(np.isfinite(pools))
        or not math.isfinite(target) or not 0 <= theta < 1
        or np.any(weights < 0) or np.any(pools <= 0) or target <= 0 or update not in ("all", "last")):
        raise ValueError("Invalid exposure forecast")
    mu = mu_upper(0, alpha)
    mask = np.ones(len(pools)) if update == "all" else np.eye(1, len(pools), len(pools)-1)[0]
    floor = float(np.sum(weights[mask == 0]*mu/((1-theta)*pools[mask == 0])))
    value = lambda f: float(np.sum(weights*mu/((1-theta)*(pools+f*mask))))
    if value(0) <= target:
        return {"lower_cm2_inv": 0., "upper_cm2_inv": 0., "D_at_upper": value(0), "limit_D": floor}
    if floor >= target:
        return {"lower_cm2_inv": None, "upper_cm2_inv": None, "D_at_upper": None, "limit_D": floor}
    lo, hi = 0., 1.
    while value(hi) > target:
        hi *= 2
        if not math.isfinite(hi):
            raise ArithmeticError("No finite bracket")
    for _ in range(100):
        mid = (lo+hi)/2
        if mid in (lo, hi):
            break
        if value(mid) > target:
            lo = mid
        else:
            hi = mid
    assert value(hi) <= target < value(lo)
    return {"lower_cm2_inv": lo, "upper_cm2_inv": hi, "D_at_upper": value(hi), "limit_D": floor}


def verify_sources():
    hashes = {}
    for name, expected in CFG["source_sha256"].items():
        actual = hashlib.sha256((REPO / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Changed accepted input: {name}")
        hashes[name] = actual
    return hashes


def grouping_audit():
    m = json.loads((REPO / "experiments/RE-CY62167-ADDRESS-MAPPING-01/address_mapping_coefficients.json").read_text())
    # Solve each y-bit as a combination of address bits in the already accepted map.
    # No fitting and no new raw-data pass. Constants do not affect XOR differences.
    coeff = m["coefficient_masks_lsb_feature_order"]
    rows = [sum(((c >> (i+1)) & 1) << j for j, c in enumerate(coeff)) for i in range(24)]
    solve = accepted_gf2_solver()
    ymasks = [solve(rows, [int(i == k+12) for i in range(24)], 21) for k in range(12)]
    ysupport = 0
    for mask in ymasks:
        ysupport |= mask
    out = []
    for row in read_csv(T68 / "outputs/groupings.csv"):
        pair = list(map(int, row["address_bits"].split(",")))
        varying = sum(1 << b for b in pair)
        out.append({"address_bits": row["address_bits"], "merged_data32_SMU": int(row["SMU_merged_HI"]),
                    "same_transformed_y": not bool(varying & ysupport),
                    "H_low_contains_x16_pair": 0 in pair,
                    "H_pin_contains_x16_pair": 20 in pair,
                    "actual_internal38_grouping_confirmed": False})
    return out


def audits():
    levels = CFG["historical_envelope"]["let_nodes_MeV_cm2_mg"]
    clusters = read_csv(T68 / "outputs/clusters.csv")
    old = json.loads((T68 / "outputs/v21_reconstructed.json").read_text())
    numerics = {float(r["rho"]): r for r in read_csv(T68 / "outputs/numerics.csv")}
    exposures = {int(float(r["LET"])): r for r in clusters if float(r["LET"]) in levels}
    f = [float(exposures[l]["fluence_inferred_cm2"]) for l in levels]
    pools = [sum(f[i:]) for i in range(len(f))]
    counts = [sum(int(exposures[l]["SMU_objects_A0_A1"]) for l in levels[i:]) for i in range(len(levels))]
    assert all(math.isclose(f[i], old["F"][str(l)], rel_tol=1e-14) for i, l in enumerate(levels))
    normalization = []
    for row in clusters:
        l = float(row["LET"])
        sbit = 2.6e-7*(-math.expm1(-((l-.15)/70)**1.2))
        calculated = int(row["registered_cell_occurrences"])/(2**24*sbit)
        archived = float(row["fluence_inferred_cm2"])
        normalization.append({"run": row["run"], "LET_MeV_cm2_mg": l,
            "cell_occurrences": int(row["registered_cell_occurrences"]), "modeled_sigma_bit_cm2": sbit,
            "active_data_bits": 2**24, "F_reconstructed_cm2_inv": calculated,
            "F_T68_cm2_inv": archived, "relative_difference": calculated/archived-1,
            "F_independently_measured": False, "full_parent_registration_confirmed": False})
    bounds = []
    for theta in CFG["historical_envelope"]["fluence_relative_error_sensitivities"]:
        for cov in CFG["coverage"]:
            alpha = cov["alpha_family"]/cov["comparisons"]
            for i, l in enumerate(levels):
                bounds.append({"coverage": cov["id"], "alpha_family": cov["alpha_family"],
                    "comparisons": cov["comparisons"], "alpha_point": alpha, "theta": theta,
                    "LET_node_MeV_cm2_mg": l, "nominal_tail_F_cm2_inv": pools[i],
                    "effective_tail_F_cm2_inv": (1-theta)*pools[i], "row_observed": 0,
                    "sigma_row_upper_cm2_array": sigma_upper(0, pools[i], alpha, theta),
                    "A0_observed_merged_objects": counts[i],
                    "sigma_A0_upper_cm2_array": sigma_upper(counts[i], pools[i], alpha, theta)})
    spec = original_spectral_functions()
    gl = t68.read_table(T68 / "inputs/cosrad_main/gl_x.txt", 10)
    sl = t68.read_table(T68 / "inputs/cosrad_main/sl_x.txt", 10)
    rows, bins, forecasts, allocated, fullword, floors = [], [], [], [], [], []
    ceiling = min(float(gl[-1, 0])/1000., CFG["historical_envelope"]["gcr_integration_ceiling_MeV_cm2_mg"])
    points = [27, 29, 33, 42, 44, 57, ceiling]
    t, ts = CFG["scenario"]["mission_seconds"], CFG["scenario"]["effective_sep_seconds"]
    for rho in CFG["scenario"]["shields_g_cm2"]:
        col = [1.5, 1.75, 2., 2.25, 2.5, 2.75, 3., 3.5, 4.].index(rho)+1
        gx, gp = spec["make_phi"](col, gl)
        sx, sp = spec["make_phi"](col, sl)
        sp = np.where(sx <= 32.6, sp, 0.)
        integral_old = lambda vals: t*spec["rate_naive"](gx, gp, lambda x: envelope(vals, x))+ts*spec["rate_naive"](sx, sp, lambda x: envelope(vals, x))
        weights = np.zeros(6)
        detail = []
        for lo, hi in zip(points[:-1], points[1:]):
            # Sigma at the right measured endpoint dominates this interval;
            # [57,table end] additionally needs a plateau, not mere monotonicity.
            node = min(hi, 57)
            i = levels.index(node)
            cg = t*integrate_spectrum(gl, col, lo, hi)
            cs = ts*integrate_spectrum(sl, col, lo, min(hi, 32.6)) if lo < 32.6 else 0.
            weights[i] += cg+cs
            detail.append((lo, hi, node, cg+cs))
            bins.append({"shield_g_cm2": rho, "LET_low": lo, "LET_high": hi,
                         "upper_node": node, "C_GCR_cm2_inv": cg, "C_SEP_cm2_inv": cs,
                         "C_total_cm2_inv": cg+cs, "angular_status": "T68_normal_as_isotropic_comparator"})
        legacy_row = integral_old([old["bRow"][str(l)] for l in levels])
        legacy_a0 = integral_old([old["bA0"][str(l)] for l in levels])
        analytic3 = float(weights @ (3/(.7*np.asarray(pools))))
        quad3 = t*t68.quadrature_integral(gl, col, lambda x: envelope([old["bRow"][str(l)] for l in levels], x))
        quad3 += ts*t68.quadrature_integral(sl, col, lambda x: envelope([old["bRow"][str(l)] for l in levels], x), 32.6)
        rows.append({"shield_g_cm2": rho, "T68_UR": float(numerics[rho]["UR"]),
            "reproduced_UR": legacy_row, "T68_UA0": float(numerics[rho]["UA0"]),
            "reproduced_UA0": legacy_a0, "theta0_UR": .7*legacy_row,
            "analytic_UR_numerator3": analytic3, "independent_quad_UR_numerator3": quad3,
            "analytic_vs_grid_relative": analytic3/legacy_row-1,
            "T68_Fadd_for_D_5e_minus4_NOT_current_target": float(numerics[rho]["Fadd"]),
            "fullword_physical_upper": None})
        for cov in CFG["coverage"]:
            alpha = cov["alpha_family"]/cov["comparisons"]
            for theta in CFG["historical_envelope"]["fluence_relative_error_sensitivities"]:
                d = float(weights @ np.asarray([sigma_upper(0, p, alpha, theta) for p in pools]))
                da0 = float(weights @ np.asarray([sigma_upper(n, p, alpha, theta) for n, p in zip(counts, pools)]))
                floors.append({"shield_g_cm2": rho, "coverage": cov["id"], "theta": theta,
                    "data32_row_D_upper": d, "data32_A0_D_upper": da0,
                    "P_at_least_one_upper_if_Poisson": -math.expm1(-d),
                    "P_at_least_one_upper_Markov": min(1., d),
                    "physical_first_passage_lower": None, "full38_D_upper": None, "full39_D_upper": None})
                for target in CFG["scenario"]["direct_mean_targets"]:
                    common = {"shield_g_cm2": rho, "coverage": cov["id"], "theta": theta, "target_D": target}
                    for update in ["all", "last"]:
                        r = additional_fluence(weights, pools, target, alpha, theta, update)
                        forecasts.append({**common, "reuse": "monotone_pool_all_nodes" if update == "all" else "update_57_bound_only", **r,
                                          "physical_fullword_qualification": False})
                    # Prospective whole-array measurement: no data32 credit for full38/39.
                    # One uniform cap on L>=27 under the SAME explicit comparator.
                    # In a predeclared independent test no retrospective 55-way penalty.
                    if cov["id"] in ("point95", "fixed_group_nodes_1e-6"):
                        for arch in ["internal38", "external39_assembly"]:
                            fullword.append({**common, "architecture": arch,
                                "alpha_for_uniform_cap": alpha,
                                "existing_qualified_fullword_F": 0,
                                "required_new_zero_F_cm2_inv": allocation_fluence(float(sum(weights)), target, alpha, theta=theta),
                                "status": "conditional_uniform_cap_exposure_not_physical_requirement"})
        for target in CFG["scenario"]["direct_mean_targets"]:
            for lo, hi, node, weight in detail:
                allocated.append({"shield_g_cm2": rho, "target_D": target, "LET_low": lo, "LET_high": hi,
                    "upper_node": node, "C_cm2_inv": weight,
                    "uniform_cap_budget_bj": target*weight/sum(weights),
                    "sigma_uniform_cap_cm2_array": target/sum(weights),
                    "scope": "conditional_T68_domain_only_uncovered_not_paid"})
    save_csv("fluence_normalization.csv", normalization)
    save_csv("cross_section_bounds.csv", bounds)
    save_csv("T68_reproduction.csv", rows)
    save_csv("mission_weights.csv", bins)
    save_csv("direct_bounds.csv", floors)
    save_csv("additional_exposure.csv", forecasts)
    save_csv("prospective_fullword_exposure.csv", fullword)
    save_csv("LET_budget.csv", allocated)
    save_csv("grouping_audit.csv", grouping_audit())
    return rows, floors, forecasts, fullword


def handoff():
    direct = read_csv(OUT / "direct_bounds.csv")
    history = {float(x["shield_g_cm2"]): x for x in read_csv(OUT / "T68_reproduction.csv")}
    sigma57 = next(x for x in read_csv(OUT / "cross_section_bounds.csv")
                   if x["coverage"] == "point95" and float(x["theta"]) == .3 and float(x["LET_node_MeV_cm2_mg"]) == 57)
    architecture_rows = []
    for arch, n in [("internal38", 38), ("external39", 39)]:
        for rho in CFG["scenario"]["shields_g_cm2"]:
            ref = next(x for x in direct if float(x["shield_g_cm2"]) == rho and x["coverage"] == "selected55_nodes95" and float(x["theta"]) == .3)
            architecture_rows.append({"architecture": arch, "shield_g_cm2": rho, "W": 524288, "n": n,
                "physical_word": "32 data + 6 hidden check" if n == 38 else "M0:16 data;M1:16 data;M2:7 check+9 padding",
                "observed_domain": "ECC-off data cells;normal-incidence scenario;38/39 law unobserved",
                "data32_reference_zero_groups_of_55": 45,
                "data32_reference_F_at_57_cm2_inv": 8974.600857765849,
                "data32_reference_sigma57_point95_theta03": float(sigma57["sigma_row_upper_cm2_array"]),
                "data32_reference_UR_T68_theta03": float(history[rho]["T68_UR"]),
                "data32_reference_D_family95_theta03": float(ref["data32_row_D_upper"]),
                "data32_reference_applies_to_full_architecture": False,
                "existing_qualified_fullword_F_cm2_inv": None, "fullword_observed_direct_count": None,
                "fullword_sigma_upper_cm2": None, "fullword_D_upper": None, "joint_coverage": None,
                "direct_targets": "5e-5;1e-4", "status": "insufficient_fullword_evidence",
                "required_data": "internal_W_and_6check_joint_marks_angles_registration" if n == 38 else "raw_to_pins_lane_ECC_on_DQ47:0_ERR2:0_joint_marks_crosschip_angles"})
    save_csv("architectures.csv", architecture_rows)
    save_json("handoff.json", {"issue": 81, "source_base": CFG["base_commit"],
        "mission_seconds": CFG["scenario"]["mission_seconds"], "direct_quantity": "mean parents with >=2 distinct positions in any full word",
        "architectures": architecture_rows,
        "conditional_target_D_ranges": {"main": [0, 5e-5], "alternative": [0, 1e-4]},
        "ranges_status": "requested_model_budgets_not_measured_or_qualified_bounds",
        "ERR": {"pin_exists": True, "internal38_parity_only_completeness": None,
                "external39_count_dominance": None, "repeated_read_is_new_parent": False},
        "U": {"required": "known word/aliases;full clean fence including hidden ECC;pending and latch-write hits charged",
              "qualified_fullword_implementation": None, "timing_owner": 82},
        "direct_not_reduced_by_shorter_service_period": True,
        "impossibility_of_any_policy_established": False,
        "additional_zero_data_are_hypothetical": True})


def main():
    hashes = verify_sources()
    OUT.mkdir(exist_ok=True)
    audits()
    angular_requirements()
    handoff()
    test = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_*.py", "-v"],
                          capture_output=True, text=True)
    (OUT / "tests.txt").write_text(test.stdout+test.stderr, encoding="utf-8")
    print(test.stderr)
    if test.returncode:
        raise RuntimeError("T81 verification failed")
    save_json("protocol.json", {"source_base": CFG["base_commit"], "source_sha256": hashes,
        "python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__,
        "tests_returncode": test.returncode, "network_used_in_reproduction": False,
        "accepted_inputs_unchanged": hashes == verify_sources(),
        "formula_scope": "conditional confidence bounds, not physical fullword qualification"})
    print("T81 complete: experiments/t81-direct-architecture/outputs")


if __name__ == "__main__":
    main()

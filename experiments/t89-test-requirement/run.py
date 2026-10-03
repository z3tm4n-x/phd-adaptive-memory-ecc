"""One offline command for T89, writing only inside this task directory."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import unittest
from fractions import Fraction as Q

from fluence import (HERE, REPO, allocation_budget, decimal_text, rational, zero_fluence)
from t88_handoff import accepted_targets


def verify_sources(cfg):
    checked = {}
    for path, expected in cfg["source_sha256"].items():
        actual = hashlib.sha256((REPO/path).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("Pinned T81/T88 source changed: " + path)
        checked[path] = actual
    return checked


def mission_weights():
    p = REPO/"experiments/t81-direct-architecture/outputs/mission_weights.csv"
    with p.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    weights = {s: sum(rational(r["C_total_cm2_inv"]) for r in rows
                      if rational(r["shield_g_cm2"]) == s) for s in (Q(3), Q("2.5"))}
    return weights, rows


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def baseline_rows(cfg, target, weights, kind="baseline", variant="all"):
    rows = []
    s = cfg["conditional_scale"]
    for rho in cfg["scenario"]["shields_g_cm2"]:
        C = weights[rational(rho)]
        for cov in s["coverage_profiles"]:
            alpha = rational(cov["alpha_family"])/cov["comparisons"]
            R = None if s["R"] is None else rational(s["R"])
            if R is not None and R < 0:
                raise ValueError("Nonnegative remainder required")
            if R is None:
                result = {"status": "undefined", "missing": "R", "F_required": None}
            elif R >= target:
                result = {"status": "no_positive_covered_budget", "F_required": None}
            else:
                result = zero_fluence(C, target-R, alpha,
                                     cfg["calculation"]["old_exposure_credit_cm2_inv"],
                                     s["theta_F"], s["q_lower"], s["g_lower"],
                                     cfg["calculation"]["fluence_rounding_cm2_inv"],
                                     cfg["calculation"]["hypothetical_new_count"])
            rows.append({"target_kind": kind, "variant": variant, "D0": decimal_text(target, 18),
                         "shield_g_cm2": rho, "C_cm2_inv": decimal_text(C, 20),
                         "coverage": cov["id"], "alpha_cap_exact": str(alpha),
                         "E_old_credit_cm2_inv": cfg["calculation"]["old_exposure_credit_cm2_inv"], "theta_F": s["theta_F"],
                         "q_lower": s["q_lower"], "g_lower": s["g_lower"], "R": s["R"],
                         "domain": "T81 conditional normal-as-isotropic uniform-cap domain",
                         "physical_qualification": False, "physical_F_required": None, **result})
    return rows


def calculate(cfg, target):
    weights, weight_rows = mission_weights()
    rows = baseline_rows(cfg, target, weights)
    for rho in cfg["scenario"]["shields_g_cm2"]:
        rows.append({"target_kind": "baseline_physical", "variant": "all", "D0": decimal_text(target, 18),
                     "shield_g_cm2": rho, "coverage": "joint_Theta_unknown", "R": None,
                     "E_old_credit_cm2_inv": "0", "q_lower": None, "g_lower": None,
                     "theta_F": None, "C_cm2_inv": None, "F_required": None,
                     "status": "undefined_physical_contract", "physical_qualification": False,
                     "missing": "C_rho_j,R,q,g,theta_F,coverage,full38_registration,envelope"})
    for row in accepted_targets(cfg):
        d = row["D0_exact"]
        if d is None:
            rows.append(dict(row, D0=None))
        else:
            sub = baseline_rows(cfg, rational(d), weights, row["target_kind"], row["variant"])
            rows += [dict(r, **row)
                     for r in sub if rational(r["shield_g_cm2"]) == rational(row["shield_g_cm2"])]

    angular = []
    J = len(cfg["angular_coefficient_illustration"]["polar_strata_deg"])
    alpha = rational(cfg["angular_coefficient_illustration"]["alpha_family"])/J
    b = target/J
    allocation_budget(target, "0", [{"b": b, "alpha": alpha}]*J, "0.05")
    coeff = zero_fluence("1", b, alpha, "0", ".3", "1", "1")
    for rho in cfg["scenario"]["shields_g_cm2"]:
        for lo, hi in cfg["angular_coefficient_illustration"]["polar_strata_deg"]:
            angular.append({"shield_g_cm2": rho, "D0": decimal_text(target, 18),
                            "polar_low_deg": lo, "polar_high_deg": hi, "azimuth": "all [0,360)",
                            "alpha_j_exact": str(alpha), "b_j_formula": "(D0-R)/3",
                            "Fnew_per_C_optimistic_R0_q1_g1_theta03_upper": coeff["F_required"],
                            "C_rho_j_cm2_inv": None, "R_physical": None, "q_physical": None,
                            "g_physical": None, "physical_Fnew": None,
                            "status": "coefficient_not_qualified_point_grid"})

    sensitivity = []
    # Explicit algebraic scenarios, not silently filled physical inputs.
    for rho in cfg["scenario"]["shields_g_cm2"]:
        for label, frac_R, q, theta in [("illustrative_base", Q(0), Q(1), Q(".3")),
                                       ("illustrative_R20pct", Q(".2"), Q(1), Q(".3")),
                                       ("illustrative_q90pct", Q(0), Q(".9"), Q(".3")),
                                       ("illustrative_theta0", Q(0), Q(1), Q(0))]:
            result = zero_fluence(weights[rational(rho)], target*(1-frac_R), ".05", 0, theta, q, 1)
            sensitivity.append({"assumption_only": label, "shield_g_cm2": rho, "D0": decimal_text(target, 18),
                                "R_fraction_of_D0": str(frac_R), "q": str(q), "theta_F": str(theta),
                                "physical_qualification": False, **result})
    return rows, angular, sensitivity, weight_rows


def table_markdown(rows):
    text = ["# D₀ / защита / добавочный флюенс / область / покрытие / остаток", "",
            "Флюенс — достаточное условное требование при будущем нуле, см⁻²;",
            "округление вверх до 0,001. Это не измеренная граница D*.", "",
            "T88: наибольшие найденные сертифицированные точки объявленного конечного",
            "семейства, не точные глобальные пороги. SHA `"+cfg_sha(rows)+"`.",
            "Полные физические флюенсы остаются null. Цена/запас по риску — из T88,",
            "не результат испытания; их точные дроби и witness находятся в JSON/CSV."]
    groups = [("baseline", "Исходный D₀"), ("baseline_physical", "Физический контракт"),
              ("T88_largest_found_certified_1pct", "T88: граница с налогом ≤1%"),
              ("T88_certificate_only", "T88: сертификат без требования ≤1%"),
              ("T88_working_risk_reserve_proposal", "T88: предложенные рабочие точки с запасом риска ≥5e−5"),
              ("T88_interior_1pct_other_policy", "T88: тот же рабочий D₀, другая политика с налогом ≤1%")]
    for kind, title in groups:
        text += ["", "## "+title, "",
                 "| D₀ / вариант | Защита | F_new ≥, см⁻² | Покрытие счёта | Область / статус | R | Налог ≤, % | Запас риска ≥ |",
                 "|---|---:|---:|---|---|---|---:|---:|"]
        for r in rows:
            if r["target_kind"] != kind:
                continue
            d, f = r["D0"] or "не определён", r.get("F_required") or "не определён"
            scope = (f"условная T81; q={r['q_lower']}, g={r['g_lower']}, θ_F={r['theta_F']}"
                     if r.get("status") == "conditional_finite" else r["status"])
            rem = str(r["R"])+" (допущение)" if r.get("R") is not None else "неизвестен"
            text.append(f"| {d}; {r['variant']} | {r['shield_g_cm2']} | {f} | {r.get('coverage', '—')} | {scope} | {rem} | {r.get('T88_quiet_tax_upper_pct', '—')} | {r.get('T88_risk_slack_lower', '—')} |")
    text += ["", "Один новый заранее заданный cap не требует нового множителя 55. Две защиты",
             "используют одни сечения: для одновременного выполнения двух условий нужен максимум",
             "двух требований, не сумма флюенсов и не второй статистический штраф.",
             "`T81_fixed6_*` сохраняют α_cap=α_family/6 для сравнения с T81; это",
             "резерв на шесть границ, не автоматически совместное покрытие всей физической Θ.",
             "point95 — только статистическая граница одного cap; перенос на область условен.",
             "Ни 95%, ни 1−10⁻⁶ здесь не заменяют отдельные покрытия q/F/среды."]
    return "\n".join(text)+"\n"


def cfg_sha(rows):
    return next(r["T88_sha"] for r in rows if "T88_sha" in r)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--D0", help="positive illustrative target, not a T88 threshold")
    parser.add_argument("--config", type=Path, default=HERE/"config.json")
    parser.add_argument("--out", type=Path, default=HERE/"outputs")
    args = parser.parse_args()
    out = args.out.resolve()
    if not out.is_relative_to(HERE) or out == HERE:
        raise ValueError("Outputs must stay in a subdirectory of T89")
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    if cfg["calculation"]["old_exposure_credit_cm2_inv"] != "0":
        raise ValueError("T89 has no qualified old full38 exposure; positive credit needs a new reviewed input")
    target = rational(args.D0 or cfg["scenario"]["baseline_D0"])
    if target <= 0:
        raise ValueError("D0 must be positive; missing threshold is not zero")
    before = verify_sources(cfg)
    rows, angular, sensitivity, weight_rows = calculate(cfg, target)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out/"requirements.csv", rows)
    write_json(out/"requirements.json", rows)
    write_json(out/"t88_transfer.json", {"source_sha": cfg["T88_handoff"]["source_sha"],
               "transfer_checked": True, "search_or_independent_review_repeated": False,
               "physical_qualification": False, "targets": accepted_targets(cfg)})
    write_csv(out/"angular_coefficients.csv", angular)
    write_csv(out/"sensitivity.csv", sensitivity)
    write_csv(out/"mission_weights_reused.csv", weight_rows)
    (out/"table.md").write_text(table_markdown(rows), encoding="utf-8")
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_*.py")
    test = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (out/"tests.txt").write_text(stream.getvalue(), encoding="utf-8")
    print(stream.getvalue())
    if not test.wasSuccessful():
        raise RuntimeError("T89 tests failed")
    if before != verify_sources(cfg):
        raise ValueError("Accepted files changed during execution")
    write_json(out/"handoff.json", {"issue": 89, "T81_sha": cfg["T81_sha"],
                "D0": decimal_text(target, 18), "T88": cfg["T88_handoff"],
                "physical_contract": cfg["physical_contract"],
                "physical_qualification": False, "experiments_executed": False,
                "zero_counts_are_hypothetical": True,
                "ready": "formula, ECC-on protocol, baseline and four safe T88 1% endpoints delivered",
                "T88_cost_endpoints": 4, "T88_cost_empty_regions": 2,
                "T88_certificate_endpoints_separate": 5,
                "T88_working_points_separate": 5, "T88_interior_1pct_policies_separate": 4,
                "physical_blocker": "full38 registration/completeness, angular/LET envelope, residual and exposure bounds remain unknown"})
    write_json(out/"verification.json", {"python": platform.python_version(), "tests": test.testsRun,
                "tests_passed": True, "randomness": "none; seed not applicable", "network": False,
                "source_sha256": before, "accepted_files_unchanged": True,
                "arithmetic": "T81 double regression; Fraction + 70-digit directed ln; Decimal-100 tests",
                "source_hashes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(HERE.glob("*.py"))},
                "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest()})
    print("T89 ready:", out)


if __name__ == "__main__":
    main()

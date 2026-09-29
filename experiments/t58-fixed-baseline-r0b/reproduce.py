#!/usr/bin/env python3
"""Read-only bounded T58 reproduction. Python standard library + Git.

Use --master-repo PATH to a Git copy containing the pinned master's SHA.
Default checks committed results; --emit outputs freshly computed artifacts
as JSON (for a reviewable patch), without writing any files.
"""
import argparse
import csv
import hashlib
import io
import itertools
import json
from pathlib import Path
import sys
import types
import unittest
from dataclasses import replace
from fractions import Fraction as F
from certificate import Risk, Resource, rarity, fixed_period, resources, class_lower, ceil, floor, components
from inputs import load_sources

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def serialize(x):
    if isinstance(x, F):
        return str(x)
    if isinstance(x, dict):
        return {k: serialize(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [serialize(v) for v in x]
    return x


def number(x):
    """Display only. Admission/exclusion decisions never use float."""
    return "" if x is None else format(float(x), ".12g")


def bound_number(x, up=True, digits=12):
    """Outward significant-digit text; even reported bounds stay conservative."""
    if x is None:
        return ""
    if x == 0:
        return "0"
    if x < 0:
        raise ValueError("nonnegative bound required")
    x = F(x)
    exponent = len(str(x.numerator))-len(str(x.denominator))
    while x < F(10)**exponent:
        exponent -= 1
    while x >= F(10)**(exponent+1):
        exponent += 1
    power = exponent-digits+1
    mantissa = str(ceil(x/F(10)**power) if up else floor(x/F(10)**power))
    return mantissa[0]+"."+mantissa[1:]+"e"+str(power+len(mantissa)-1)


def parameters(cfg, h, W, R, tax):
    n, N = cfg["scenario"]["n"], W*cfg["scenario"]["n"]
    c = F(n, R)
    p = Risk(T=h["T_s"], B=h["B_per_bit_s_inverse"]*N,
             b=h["bbar_per_bit_s_inverse"]*N, FS=h["FS_per_bit"]*N,
             q=F(1, W), Q=F(1), chi=F(n-1, n*W), eta=F(n-1, n*W*W), D=c)
    app, grid = cfg["app_diagnostic"], cfg["reference_point_rule"]["table_resources"]
    r = Resource(W=W, c=c, H=h["T_s"], h=F(grid["h_s"]), tax=F(tax),
                 peak=F(grid["peak"]), delay=F(grid["delay_s"]),
                 sigma=F(app["sigma_s"]), u=F(app["u"]), g=F(app["g_s"]),
                 tick=F(cfg["actions"]["tick_s"]),
                 clock_error=F(cfg["actions"]["tick_relative_error"]))
    return p, r


def run_tests(t52_source):
    mod = types.ModuleType("pinned_t52_checks")
    exec(compile(t52_source, "T52@f7180c5:check_fixed_period_resource_contract.py", "exec"), mod.__dict__)
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(mod),
        unittest.defaultTestLoader.discover(str(HERE), pattern="test_*.py")])
    result = unittest.TextTestRunner(verbosity=1, stream=sys.stderr).run(suite)
    if not result.wasSuccessful():
        raise SystemExit("tests failed")
    return result.testsRun


def csv_text(rows):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def compute(cfg, h, limit=None):
    epsilon = F(cfg["scenario"]["epsilon"])
    Mmin, Mmax = int(cfg["actions"]["M_min"]), int(cfg["actions"]["M_max"])
    core, grid_rows = [], []
    keys = list(itertools.product(cfg["grid"]["W"], cfg["grid"]["R_eff_bit_s"], cfg["grid"]["tax"]))
    if limit:
        keys = keys[:limit]
    for W, R, tax in keys:
        p, r = parameters(cfg, h, W, R, tax)
        n = cfg["scenario"]["n"]
        critical = epsilon*F(tax)*R/(n*(n*(n-1)//2)*W*W)
        # Model witness is fixed for ALL periods of this W/R/tax class.
        low = class_lower(W, n, p.B, h["initial_peak_duration_s"], r.c, r.c,
                          r.H, r.tax, witness_admissible=True,
                          deterministic_window_contract=True)
        record = dict(W=W, R_eff_bit_s=R, tax=F(tax), c_s=r.c,
                      ideal_critical_I2_per_bit_s_inverse=critical,
                      lower_fixed_U=low,
                      critical_FS_per_bit=(critical-h["bbar_per_bit_s_inverse"]**2*h["T_s"])/
                       (h["B_per_bit_s_inverse"]+h["bbar_per_bit_s_inverse"]))
        for scenario in ["historical_moments", "rarity_diagnostic"]:
            current = replace(p, F_cap=h["I1_per_bit"]*W*n,
                              S2_cap=h["I2_per_bit_s_inverse"]*(W*n)**2) if scenario == "historical_moments" else p
            answer = fixed_period(current, r, epsilon, Mmin, Mmax)
            # For this unchanged grid, tax dominates the preregistered projection.
            # This assertion justifies reusing its largest candidate for all
            # looser peak/h/delay choices. A changed grid must not bypass search.
            tax_tick = max(Mmin, ceil(r.c*r.W/(r.tax-2*r.c/r.H)/r.tick),
                           r.W*ceil(r.c/r.tick))
            if r.clock_error or answer["first_resource_tick"] != tax_tick:
                raise ValueError("projection no longer tax-dominated; full search required")
            record[scenario] = answer
            # Even a rejected point gets an explicit upper decomposition at the
            # smallest resource-admitted action (not a claim of impossibility).
            M_evaluate = answer["selected_tick"] or answer["first_resource_tick"]
            if M_evaluate is not None:
                vv = resources(r, M_evaluate)
                record[scenario+"_evaluated"] = dict(tick=M_evaluate, resource=vv,
                    upper=components(current, vv["tau_lo"], vv["tau_hi"]),
                    purpose="certified_period" if answer["selected_tick"] else "resource_boundary_no_certificate")
            # Preserve the complete original resource grid. These computations
            # contain no adaptive trajectory/controller or mission Monte Carlo.
            for peak, window, delay in itertools.product(cfg["grid"]["peak"],
                                                        cfg["grid"]["h_s"], cfg["grid"]["delay_s"]):
                rr = replace(r, peak=F(peak), h=F(window), delay=F(delay))
                # Peak budgets are looser than the preregistered projection;
                # re-test a candidate, but do NOT infer impossibility from failure.
                M = answer["selected_tick"]
                v = resources(rr, M) if M is not None else None
                allowed = v is not None and all(v[k] for k in ["tax_ok", "peak_ok", "delay_ok", "schedule_ok"])
                if scenario == "rarity_diagnostic" and low["lower"] > epsilon:
                    status = "fixed_U_class_excluded_conditional"
                elif allowed:
                    status = "presented_constant_sufficient_conditional"
                elif rr.delay < rr.c and rr.g > 0:
                    status = "mandatory_U_block_exclusion_conditional"
                else:
                    status = "unresolved_no_certificate"
                grid_rows.append(dict(scenario=scenario, W=W, R_eff_bit_s=R, tax_budget=tax,
                    peak_budget=peak, h_s=window, delay_budget_s=delay,
                    selected_tick=M if allowed else "", period_s=number(M*rr.tick) if allowed else "",
                    upper_risk=bound_number(answer["upper_components"]["total"]) if M is not None else "",
                    tax_upper=bound_number(v["tax_upper"]) if v else "",
                    peak_upper=bound_number(v["peak_upper"]) if v else "",
                    delay_upper_s=bound_number(v["delay_upper"]) if v else "",
                    lower_fixed_U=bound_number(low["lower"], False) if scenario == "rarity_diagnostic" else "",
                    status=status, physical_qualification="absent", t52_review=cfg["review_56"]["status"]))
        core.append(record)
    # Preregistered selection; all decisions use exact rationals.
    order = sorted(range(len(core)), key=lambda i: (core[i]["ideal_critical_I2_per_bit_s_inverse"],
                                                   core[i]["W"], core[i]["R_eff_bit_s"], core[i]["tax"]))
    selected = {order[0], order[-1]}
    for target in [h["I2_per_bit_s_inverse"], h["S2_per_bit_s_inverse"]]:
        below = [i for i in order if core[i]["ideal_critical_I2_per_bit_s_inverse"] <= target]
        above = [i for i in order if core[i]["ideal_critical_I2_per_bit_s_inverse"] >= target]
        if below:
            boundary = max(core[i]["ideal_critical_I2_per_bit_s_inverse"] for i in below)
            selected.add(next(i for i in order if core[i]["ideal_critical_I2_per_bit_s_inverse"] == boundary))
        if above:
            selected.add(above[0])
    selected = sorted(selected, key=lambda i: (core[i]["W"], core[i]["R_eff_bit_s"], core[i]["tax"]))
    counts = {}
    for row in grid_rows:
        key = row["scenario"]+":"+row["status"]
        counts[key] = counts.get(key, 0)+1
    lo, hi = core[order[0]]["ideal_critical_I2_per_bit_s_inverse"], core[order[-1]]["ideal_critical_I2_per_bit_s_inverse"]
    summary = dict(base_sha=cfg["base_sha"], t52_sha=cfg["t52_sha"], master_sha=cfg["master_sha"],
        review_56=cfg["review_56"], config_sha256=hashlib.sha256((HERE/"config.json").read_bytes()).hexdigest(),
        history=h, parameter_range=dict(ideal_I2_lower=lo, ideal_I2_upper=hi, ratio=hi/lo,
                                      physical_qualification="absent"),
        scope="constant_only_conditional_diagnostics_no_adaptive_comparison",
        grid_rows=len(grid_rows), outcome_counts=counts, reference_indices=selected, core=core)
    lines = ["# Опорные точки T58", "", "Условная модель U, полный одиночный XOR-закон; не физический прогноз.",
             "T52 f7180c5; #56: «ПРИНЯТЬ» условный математический контракт. Начало clean/no-pending условно; D=c, Ds=0.",
             "Общая ресурсная проекция: h=1 мс, пик ≤5%, задержка ≤3 мкс, σ=g=0.1 мкс, u=50%.", "",
             "| W | R_eff, Мбит/с | Налог, % | Критический I2, 1/с на бит² | Исторический τ_cert, с | Λ-диагностика τ_cert, с | Lower постоянного U |",
             "|---:|---:|---:|---:|---:|---:|---:|"]
    for i in selected:
        row = core[i]
        periods = [number(row[k]["selected_tick"]*F(cfg["actions"]["tick_s"]))
                   if row[k]["selected_tick"] is not None else "нет сертификата"
                   for k in ["historical_moments", "rarity_diagnostic"]]
        lines.append(f'| {row["W"]} | {row["R_eff_bit_s"]//1000000} | {number(row["tax"]*100)} | '
                     f'{number(row["ideal_critical_I2_per_bit_s_inverse"])} | {periods[0]} | {periods[1]} | {bound_number(row["lower_fixed_U"]["lower"], False)} |')
    lines += ["", "Вторая таблица: при успехе — выбранный Λ-период; при отказе — минимальный ресурсный период.",
              "Начальный риск, ошибка исполнения, direct, начальные грязные слова, cross и чувствительный сервис",
              "равны нулю **только по условиям диагностической модели**. Поэтому здесь upper = парное слагаемое.", "",
              "| W | R_eff | Налог, % | Проверенный τ, с | Upper пары | Налог upper, % | Пик upper, % | Задержка upper, мкс |",
              "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for i in selected:
        row = core[i]
        x = row["rarity_diagnostic_evaluated"]
        v = x["resource"]
        lines.append(f'| {row["W"]} | {row["R_eff_bit_s"]//1000000} | {number(row["tax"]*100)} | '
                     f'{number(v["tau_lo"])} | {bound_number(x["upper"]["pairs"])} | {bound_number(v["tax_upper"]*100)} | '
                     f'{bound_number(v["peak_upper"]*100)} | {bound_number(v["delay_upper"]*1000000)} |')
    lines += ["", "Lower использует один допустимый начальный пик диагностического Λ и необходимый пол U: r=c.",
              "Он не относится к исторической траектории как единственному элементу класса, к C с меньшим read-floor,",
              "к адаптации или к смесям с налогом лишь в среднем по seed. Сравнение ведётся с полным ε=0.01.", "",
              "Все составляющие upper и рациональные границы — summary.json; полная сетка — grid.csv.",
              "Отказ сертификата не исключает класс. Параметры физического Λ/Θ остаются неизвестными.", ""]
    return {"summary.json": json.dumps(serialize(summary), ensure_ascii=False, indent=2)+"\n",
            "grid.csv": csv_text(grid_rows), "reference_points.md": "\n".join(lines)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master-repo", type=Path, required=True)
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--limit-core", type=int, default=None, help="smoke only; never checks/publishes full results")
    args = parser.parse_args()
    cfg = json.loads((HERE/"config.json").read_text(encoding="utf-8"))
    h, source = load_sources(args.master_repo, ROOT, cfg)
    tests = run_tests(source)
    artifacts = compute(cfg, h, args.limit_core)
    if args.emit:
        print(json.dumps(artifacts, ensure_ascii=False))
    elif args.limit_core:
        print(f"Smoke: {tests} checks, {args.limit_core} core point(s); no artifacts written")
    else:
        for name, content in artifacts.items():
            if (HERE/name).read_text(encoding="utf-8") != content:
                raise SystemExit(f"result mismatch: {name}")
        print(f"T58: {tests} checks; source hashes; 54 core points / 2916 diagnostic rows reproduced. No files changed.")


if __name__ == "__main__":
    main()

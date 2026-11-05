"""Two fixed calendars, PR383 (11)/(14). No simulation or spectrum calculation."""
import argparse
from decimal import Decimal, localcontext
from fractions import Fraction as F
from hashlib import sha256
import json
from math import inf, isfinite, nextafter
from pathlib import Path

from verify import verify_decimal

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def lf_hash(path):
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def fixed(q, places, up=False):
    """Exact decimal floor/ceiling, without floating-point formatting."""
    scale = 10 ** places
    z = q * scale
    k = -((-z.numerator) // z.denominator) if up else z.numerator // z.denominator
    sign = "-" if k < 0 else ""
    k = abs(k)
    return f"{sign}{k // scale}.{k % scale:0{places}d}"


def enclosure(q, places):
    return {"lower": fixed(q, places), "upper": fixed(q, places, up=True)}


def terminating_decimal(q):
    with localcontext() as ctx:
        ctx.prec = 120
        text = str(Decimal(q.numerator) / Decimal(q.denominator))
    assert F(text) == q
    return text


def binary64_ceiling(q):
    value = float(q)
    if F(value) < q:
        value = nextafter(value, inf)
    assert isfinite(value) and F(value) >= q
    assert F(nextafter(value, -inf)) < q
    return value


def minus_log_one_minus(p, terms):
    """Sum p^k/k <= -ln(1-p) <= sum + p^(K+1)/((K+1)*(1-p))."""
    assert 0 <= p < 1 and terms > 0
    lo = sum((p ** k / k for k in range(1, terms + 1)), F(0))
    remainder = p ** (terms + 1) / ((terms + 1) * (1 - p))
    return lo, lo + remainder


def issued_certificate(u, epsilon, places, terms, log_places):
    u_up = F(fixed(u, places, up=True))
    p = epsilon - u_up
    assert 0 < p < 1  # Both fixed calendars in this task have a positive budget.
    lo, hi = minus_log_one_minus(p, terms)
    first = F(fixed(p, places))
    poisson = F(fixed(lo, places))
    assert u_up + first <= epsilon
    assert poisson <= lo <= hi
    return {
        "U_C_upper": fixed(u_up, places),
        "p_D_allow_down": fixed(first, places),
        "Lambda_D_first_moment_down": fixed(first, places),
        "Lambda_D_Poisson_down": fixed(poisson, places),
        "log_at_issued_probability_interval": {
            "lower": fixed(lo, log_places), "upper": fixed(hi, log_places, up=True)
        },
    }


def calculate(cfg):
    for source in cfg["sources"]:
        if lf_hash(ROOT / source["path"]) != source["sha256_lf"]:
            raise ValueError(f"Pinned accepted source changed: {source['path']}")
    obj, srv, env, ar = (cfg[x] for x in ("object", "service", "environment", "arithmetic"))
    W, n = obj["W"], obj["n_code_bits"]
    T, epsilon = F(obj["T_s"]), F(obj["epsilon"])
    c, delta, rho = (F(srv[x]) for x in ("c_s", "Delta_s", "rho_bus"))
    assert srv["rule"] == "C" and F(srv["delta_execution"]) == 0
    b = F(env["background_reference_per_s"]) * n * W / env["D_ref_bits"]
    B = b * F(env["B_over_b"])
    E = (B - b) * F(env["excess_equivalent_s"])
    candidates = [B * B * T, B * min(B * T, b * T + E), b * b * T + (B + b) * E]
    S = min(candidates)
    beta = F(n - 1, 2 * n * W)

    def upper(P):
        return beta * S * ((1 + F(1, W)) * P + delta)

    # Required gate: exact published period before calculating the second row.
    published = F(cfg["calendars"]["published_period_s"])
    assert published == F(86, 5)
    anchor = cfg["accepted_A_check"]
    accepted_upper, unit = F(anchor["U_upper"]), F(anchor["last_printed_unit"])
    assert accepted_upper - unit < upper(published) <= accepted_upper

    minimum = W * c / rho
    assert minimum > delta  # Strict bound is inactive for this fixed object.
    fastest_float = binary64_ceiling(minimum)
    fastest = F(fastest_float)
    result = {
        "status": cfg["status"],
        "input_sha256_lf": lf_hash(HERE / "inputs.json"),
        "code_sha256_lf": {p: lf_hash(HERE / p) for p in ("reproduce.py", "verify.py")},
        "shared_exact": {
            "b_per_s": str(b), "B_per_s": str(B), "E_count": str(E),
            "S_candidates_per_s": [str(x) for x in candidates],
            "S_A_per_s": str(S), "active_S_branch": candidates.index(S) + 1,
            "beta": str(beta), "resource_floor_s": str(minimum),
        },
        "accepted_A_check": {
            "exact_period_s": str(published), "U_C_exact": str(upper(published)),
            "published_upper": anchor["U_upper"], "PASS": True,
        },
        "binary64_minimum": {
            "selected_hex": fastest_float.hex(), "selected_exact_s": str(fastest),
            "predecessor_exact_s": str(F(nextafter(fastest_float, -inf))),
            "predecessor_below_resource_floor": True,
            "hardware_timer_qualified": False,
        },
        "rows": [],
    }
    for name, P in (("published_17_2", published), ("resource_minimum", fastest)):
        assert P >= minimum and P > delta and 0 < delta <= c
        assert P / W >= c and W * c / P <= rho
        u, load = upper(P), W * c / P
        p = epsilon - u
        lo, hi = minus_log_one_minus(p, ar["log_series_terms"])
        row = {
            "calendar": name, "P_exact_s": str(P), "P_decimal_exact_s": terminating_decimal(P),
            "slot_spacing_exact_s": str(P / W),
            "resource_period_margin_exact_s": str(P - minimum),
            "U_C_exact": str(u), "p_D_allow_exact": str(p),
            "interface_fraction_exact": str(load),
            "interface_fraction_interval": enclosure(load, ar["machine_decimal_places"]),
            "interface_percent_upper": fixed(100 * load, ar["table_decimal_places"], up=True),
            "log_at_exact_probability_interval": {
                "lower": fixed(lo, ar["log_enclosure_places"]),
                "upper": fixed(hi, ar["log_enclosure_places"], up=True),
            },
        }
        for key, places in (("machine", ar["machine_decimal_places"]), ("table", ar["table_decimal_places"])):
            row[key] = issued_certificate(u, epsilon, places, ar["log_series_terms"], ar["log_enclosure_places"])
        result["rows"].append(row)
    result["numeric_cross_check"] = verify_decimal(cfg, result)
    return result


def table(result):
    lines = ["# Два календаря: достаточный бюджет за T=315576000 с", "",
             "U_C и резерв интерфейса округлены вверх; разрешённые p_D и Λ_D — вниз.",
             "Все вероятности и ожидаемые количества относятся к полному массиву и всему сроку.", "",
             "| Календарь, P (с) | U_C, верх | Резерв интерфейса, %, верх | p_D,allow = Λ_D,allow по первому моменту | Λ_D,allow только при пуассоновском D |",
             "|---|---:|---:|---:|---:|"]
    for row in result["rows"]:
        title = "Опубликованный, 17,2 точно" if row["calendar"] == "published_17_2" else "Ресурсный минимум, ≈0,2097152¹"
        v = row["table"]
        lines.append(f"| {title} | {v['U_C_upper']} | {row['interface_percent_upper']} | {v['p_D_allow_down']} | {v['Lambda_D_Poisson_down']} |")
    p = result["rows"][1]["P_decimal_exact_s"]
    lines += ["", f"¹ Точный выбранный binary64: `{p}` с; предыдущий binary64 нарушает P≥Wc/ρ_ш.",
              "17,2 с проверено как 86/5, без двоичного округления. Аппаратный таймер не квалифицирован.",
              "Пуассоновский порог в таблице посчитан от уже округлённого вниз p_D,allow; общий бюджет сохранён.",
              "Физические значения p_D и Λ_D для CY62167 неизвестны. Положительный остаток не подтверждает изделие."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="recompute and compare saved outputs without writing")
    args = parser.parse_args()
    cfg = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
    result = calculate(cfg)
    outputs = {"results.json": json.dumps(result, ensure_ascii=False, indent=2) + "\n", "TABLE.md": table(result)}
    for name, text in outputs.items():
        target = HERE / name
        if args.check:
            if target.read_text(encoding="utf-8") != text:
                raise ValueError(f"Reproduction differs: {name}")
        else:
            target.write_text(text, encoding="utf-8", newline="\n")
    print("PASS: 2 fixed calendars; accepted A anchor; binary64 resource minimum; directed budgets; Decimal cross-check; 14 source hashes.")
    if not args.check:
        print(outputs["TABLE.md"])


if __name__ == "__main__":
    main()

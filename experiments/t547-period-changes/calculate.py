"""Assemble the SEPEM transition ledger from the issued 256 KiB receipts."""
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from fractions import Fraction
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXP = HERE.parent


def source(rel):
    return json.loads((EXP / rel).read_bytes(), parse_float=Decimal)


def display(value, places, rounding=None):
    value = Decimal(value)
    value = value.quantize(Decimal(1).scaleb(-places), rounding=rounding)
    return f"{value:,.{places}f}".replace(",", " ").replace(".", ",")


def ledger():
    receipt = source("t534-archive-comparison/sepem-256.json")
    whole = source("t525-two-phases/result.json")
    assert len(receipt["rows"]) == 1
    row = receipt["rows"][0]
    cfg = receipt["contract"]
    assert (row["name"], cfg["KiB"], cfg["words"], cfg["addresses"]) == ("SEPEM", 256, 65536, 131072)
    assert cfg["words"] == whole["word_count"] and cfg["scan_ns"] == Fraction(whole["local_scan_s"])*10**9
    n = row["replications"]
    assert n == 128 and row["history"]["unobserved_s"] == 0
    assert row["history"]["measured_s"] == 315576000
    levels = cfg["thresholds"]
    assert 0 < levels[0] and levels == sorted(set(levels)) == whole["zero_cell_counts"]
    height = len(levels)
    cap = cfg["top_steps"]
    assert height == 7 and cap == 2**height
    # All slow strides divide the common cell; an upward step can occur only
    # on that boundary. A return therefore starts fast on the following round.
    assert all(cap % 2**i == 0 for i in range(height+1))
    last, suffix = divmod(row["history"]["measured_s"]*10**9, cfg["scan_ns"])
    assert (last, suffix) == (6879010881, 31948800) and last % cap == 65
    assert last % 2 == 1 and 0 < suffix < cfg["scan_ns"]-100

    ladder, fixed = (row["policies"][name] for name in ("ladder", "geo"))
    g = cfg["classes"]["geo"]
    assert g["fixed_read_floor_s"] == whole["best_fixed_s_lower"]
    assert g["fixed_s_upper"] == whole["sufficient_fixed_candidate_s_upper"]
    assert g["ladder"]["s_upper"] == whole["price_s_upper"]
    assert g["class_ratio_lower"] == whole["fixed_over_ladder_lower"]
    assert fixed["period_ns"] == g["period_ns"] == 86429000
    assert ladder["unresolved_trials"] == fixed["unresolved_trials"] == 0
    assert ladder["branching_trials"] == 6 and fixed["returns_to_fast"]["mean"] == [0, 0]
    down = ladder["returns_to_fast"]
    lo, hi = down["mean"]
    # The averaged integer counts are exact here: multiples of 1/128 have
    # at most seven decimal places; #535 stores nine. Endpoint equality holds
    # over all weak-write continuations of this sample.
    assert lo == hi and n*lo == (n*lo).to_integral_value()
    lower_mean = 2*lo
    upper_mean = (height+1)*hi+height
    r_lo, r_hi = down["nominal_t95"]
    # The input interval has rounded endpoints at 8 decimals. Expand each
    # by a final unit there before reporting outward at 2 decimals.
    unit = Decimal("0.00000001")
    lower_t = 2*(r_lo-unit)
    upper_t = (height+1)*(r_hi+unit)+height

    def bus(policy):
        a, b = policy["busy_s"]["mean"]
        p, q = policy["mean_pct"]
        assert display(a, 2) == display(b, 2) and display(p, 6) == display(q, 6)
        return display(a, 2)+" ("+display(p, 6)+"%)"

    peak = "≤"+display(whole["peak_sliding_1400ns_percent_upper"], 6)+"%"
    lines = [
        ("Начальное назначение периода, отдельно от смен", "1, период L", "1, период 86,429 мс"),
        ("Возвраты с редкой ступени на L, среднее в выборке",
         display(lo, 5)+" (стандартная ошибка "+display(down["se"][0], 4)+")", "0"),
        ("Все фактические смены, границы среднего в выборке",
         "**"+display(lower_mean, 4)+" … "+display(upper_mean, 2)+"**", "0"),
        ("Все смены, номинальная 95%-я внешняя оценка среднего на этой истории",
         display(lower_t, 2, ROUND_FLOOR)+" … "+display(upper_t, 2, ROUND_CEILING), "0"),
        ("Время действия L, верх ожидания на всём ГСО, с",
         "≤"+display(whole["fast_s_upper"], 3)+" ("+display(whole["fast_percent_upper"], 6)+"%)",
         "0 в режиме L"),
        ("Занятость защитного порта на SEPEM, выборочное среднее, с", bus(ladder), bus(fixed)),
        ("Занятость порта на той же истории, аналитический верх ожидания, с",
         "≤"+display(ladder["analytic"]["s_upper"], 3), "≤"+display(fixed["analytic"]["s_upper"], 3)),
        ("Занятость порта на всём ГСО, аналитический верх ожидания, с",
         "≤"+display(whole["price_s_upper"], 3), "≤"+display(g["fixed_s_upper"], 3)),
        ("Пиковая доля защитных обращений, скользящее окно 1,4 мкс", peak, peak),
    ]
    return "\n".join(["| За десять лет | Лестница | Постоянный кандидат ГСО |", "|---|---:|---:|",
                      *("| "+" | ".join(line)+" |" for line in lines)])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    if parser.parse_args().check:
        report = (HERE / "README.md").read_text(encoding="utf-8")
        printed = "\n".join(s for s in report.splitlines() if s.startswith("|"))
        if printed != ledger():
            raise SystemExit("The report differs from the ledger.")
        print("SEPEM 256 KiB: counts, right edge, sample, full-class costs and printed table verified.")
    else:
        print(ledger())

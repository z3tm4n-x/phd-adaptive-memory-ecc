#!/usr/bin/env python3
"""Таблица чисел главы 2 — сборка из принятых источников (служебный файл).

Ни одно число не переносится вручную без проверки:
  * J — значение читается из JSON принятой поставки;
  * C — значение читается из CSV принятой поставки;
  * M — дословная запись ищется в Markdown-источнике; цифры значения
        сверяются с найденной записью;
  * D — значение вычисляется из уже прочитанных чисел или из принятой
        формулы (RES-001), с контрольными сравнениями.

Повтор из корня репозитория:
    python3 thesis/ch2/data/build_numbers.py
Выход: thesis/ch2/data/ch2_numbers.csv и thesis/ch2/data/res001_exact.csv.
Код возврата 1, если хотя бы одна проверка не прошла.
Верхние оценки округляются вверх, нижние — вниз (столбец «округление»).
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FAIL: list[str] = []

# --------------------------------------------------------------- утилиты


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return ""


def blob(rel: str) -> str:
    sha = git("hash-object", str(ROOT / rel))
    return sha or "sha256:" + hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def dec(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    if isinstance(x, bool):
        raise TypeError("bool")
    if isinstance(x, int):
        return Decimal(x)
    if isinstance(x, float):
        return Decimal(repr(x))
    s = str(x).strip().replace(",", ".").replace("\u00a0", "").replace(" ", "")
    if "/" in s:
        f = Fraction(s)
        with localcontext() as c:
            c.prec = 60
            return Decimal(f.numerator) / Decimal(f.denominator)
    return Decimal(s)


def same(a, b) -> bool:
    try:
        return dec(a) == dec(b)
    except Exception:
        return str(a) == str(b)


def jget(rel: str, sel: str):
    cur = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    for part in sel.split("/"):
        m = re.fullmatch(r"([^\[]+)(?:\[(.+)\])?", part)
        cur = cur[m.group(1)]
        cond = m.group(2)
        if cond is None:
            continue
        if "=" in cond:
            f, v = cond.split("=", 1)
            hits = [r for r in cur if same(r.get(f), v)]
            if len(hits) != 1:
                raise KeyError(f"{rel}:{part}: совпадений {len(hits)}")
            cur = hits[0]
        else:
            cur = cur[int(cond)]
    return cur


def crows(rel: str, flt: dict) -> list[dict]:
    with open(ROOT / rel, encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh) if all(same(r[k], v) for k, v in flt.items())]


def cget(rel: str, flt: dict, col: str):
    hits = crows(rel, flt)
    if len(hits) != 1:
        raise KeyError(f"{rel}: {flt}: совпадений {len(hits)}")
    return hits[0][col]


def mdfind(rels, lits):
    for rel in rels:
        p = ROOT / rel
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for lit in lits:
                if lit in line:
                    return rel, i, lit
    raise KeyError(f"не найдено {lits} в {rels}")


SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def fmt(x: Decimal, rnd: str, sig: int) -> str:
    """Запись для текста: десятичная запятая, направленное округление."""
    if x == 0:
        return "0"
    mode = {"up": ROUND_CEILING, "down": ROUND_FLOOR, "none": ROUND_HALF_EVEN}[rnd]
    with localcontext() as c:
        c.prec = 80
        e = x.adjusted()
        y = x.quantize(Decimal(1).scaleb(e - sig + 1), rounding=mode)
        e = y.adjusted()
        if -2 <= e <= 5:
            s = format(y, "f")
            ip, _, fr = s.partition(".")
            neg = ip.startswith("-")
            ip = ip.lstrip("-")
            if len(ip) > 4:
                g = []
                while ip:
                    g.insert(0, ip[-3:])
                    ip = ip[:-3]
                ip = "\u00a0".join(g)
            return ("-" if neg else "") + ip + ("," + fr if fr else "")
        m = format(y.scaleb(-e), "f").replace(".", ",")
        return f"{m}·10{str(e).translate(SUP)}"


# ------------------------------------------------------- принятые источники

T127 = "experiments/t127-cy62167-pdi/outputs/inputs-126.json"
T127S = "experiments/t127-cy62167-pdi/outputs/service.json"
T127R = "experiments/t127-cy62167-pdi/REPORT.md"
T127P = "experiments/t127-cy62167-pdi/DATA_PASSPORT.md"
T141S = "experiments/t141-radiation-chain/outputs/shield-summary.csv"
T141D = "experiments/t141-radiation-chain/outputs/discrepancies.csv"
T110 = "theory/t110-err-write-service.md"
T114 = "theory/t114-two-stage-err.md"
T119 = "theory/t119-err-joint-bound.md"
T113 = "experiments/t113-onset-growth/RESULTS.md"
T58 = "experiments/t58-fixed-baseline-r0b/README.md"
T58R = "experiments/t58-fixed-baseline-r0b/reference_points.md"
T89 = "experiments/t89-test-requirement/METHOD.md"
ADDR = "experiments/RE-CY62167-ADDRESS-MAPPING-01/REPORT.md"
ALIAS = "docs/validation/CY62167-ECC-ALIAS-TEST.md"
EXP1 = "experiments/manifests/EXP-001/analytical-validation.json"
RES1 = "results/RES-001-exp001-four-word-identified-set.md"
MAP = "MAP.md"
PLAN = "thesis/RESEARCH_PLAN.md"

CY = "CY62167, внутреннее слово 32+6, W=524288, ГСО, T=10 лет"
A141 = "MAP 13.10.2026: T141 принят как параметрический тракт; физическая П=0,1, D и нижний сигнал не установлены"
A127 = "MAP 08.10.2026: условные входы T127 приняты; прежние 6940 с⁻¹ не заменены"
A150 = "MAP 14.10.2026: T150 принят в параметрической области; не физическая П=0,1"
A110 = "MAP 07.10.2026: T110 — условная теорема обслуживания с записью по сигналу исправления"
A114 = "MAP 07.10.2026: T114 принят при A1–A7"
A119 = "MAP 08.10.2026: T119/#121 принят при A1–A7 T114"
A58 = "MAP: принятые T52/T58 — диагностический класс большой памяти"
ARES1 = "RES-001: все 14 условий применимости"
AADDR = "Отчёт RE-CY62167-ADDRESS-MAPPING-01: XY→внешний адрес; внутренний слой ECC не восстановлен"
AALIAS = "Решение автора 12.10.2026: протокол будущей проверки; опыт не выполнен"
A89 = "MAP 03.10.2026: T88/T89 приняты в условной области internal38"
A113 = "MAP 07.10.2026: T113 — инженерное дополнение без полной научной рецензии"
APLAN = "RESEARCH_PLAN 3.9: сверка не выполнена"

SPEC: list[dict] = []


def add(i, sec, name, unit, typ, rnd, sig, cond, area, **src):
    SPEC.append(dict(id=i, sec=sec, name=name, unit=unit, typ=typ, rnd=rnd, sig=sig,
                     cond=cond, area=area, **src))


# 2.1 — обстановка
add("N2.1-01", "2.1", "Срок T", "с", "ЗАДАНО", "none", 9, CY, A127,
    J=(T127, "rows[shield_g_cm2=3.0]/T_s"))
add("N2.1-02", "2.1", "Допустимая вероятность Q_доп (исследовательское требование)", "—",
    "ЗАДАНО", "none", 1, CY, A127, J=(T127, "rows[shield_g_cm2=3.0]/epsilon"))
for h in ("2.5", "3.0", "3.5", "4.0"):
    c = f"{CY}; защита {h} г/см²; прямоугольная форма r=1, геометрия aH=1, COSRAD; условный конверт"
    k = h.replace(".", "")
    add(f"N2.1-b{k}", "2.1", f"Фон λ_ф, {h} г/см²", "с⁻¹", "ВЕРХ (условный конверт)", "up", 4,
        c, A141, C=(T141S, {"shield_g_cm2": h}, "background_s_inv"))
    add(f"N2.1-p{k}", "2.1", f"Пик λ_пик, {h} г/см²", "с⁻¹", "ВЕРХ (условный конверт)", "up", 4,
        c, A141, C=(T141S, {"shield_g_cm2": h}, "peak_upper_s_inv"))
    add(f"N2.1-F{k}", "2.1", f"∫λdt за срок, {h} г/см²", "битовых инверсий массива",
        "ВЕРХ (условный конверт)", "up", 4, c, A141,
        C=(T141S, {"shield_g_cm2": h}, "N_total_upper"))
    add(f"N2.1-S{k}", "2.1", f"S₂=∫λ²dt, {h} г/см²", "с⁻¹", "ВЕРХ (условный конверт)", "up", 4,
        c, A141, C=(T141S, {"shield_g_cm2": h}, "S2_upper_s_inv"))
for i, (nm, lit, val, unit) in enumerate([
        ("Верх фона прежнего класса", "\\bar b=0.000154704", "0.000154704", "с⁻¹"),
        ("Пик прежнего класса", "B=0.244682704", "0.244682704", "с⁻¹"),
        ("Надфоновая экспозиция прежнего класса N_соб", "F_S=28310.473728", "28310.473728",
         "родительских событий"),
        ("Скорость нарастания ρ прежнего класса", ".048(t-u)", ".048", "с⁻¹"),
        ("Порог ℓ прежнего класса", "\\ell=.001", ".001", "с⁻¹")], 1):
    add(f"N2.1-old{i}", "2.1", nm, unit, "ЗАДАНО (условный класс прежнего примера)", "none", 9,
        CY + "; 3 г/см²; прежние входы", A119, M=([T119], [lit]), val=val)
add("N2.1-D", "2.1", "Верхняя граница D, 3 г/см² (условно задана)", "событий за срок",
    "ЗАДАНО (условная)", "none", 7, CY + "; прежние входы", A114,
    M=([T114], ["0.0002802445"]), val="0.0002802445")
add("N2.1-ev1", "2.1", "Частота эпизодов по выборке SEPEM", "событий за 10 лет",
    "ДАННЫЕ (выборка 131 эпизода, порог и слияние 24 ч)", "none", 7,
    "SEPEM RDS v2.00", A127, M=([T127R], ["31.56392"]), val="31.56392")
add("N2.1-ev2", "2.1", "Число событий по модели ГОСТ (числа Вольфа SILSO V2)", "событий за 10 лет",
    "МОДЕЛЬ", "none", 8, "тот же интервал, ГОСТ Р 25645.165-2025", A127,
    M=([T127R], ["100.56812"]), val="100.56812")
add("N2.1-ev3", "2.1", "Среднее число событий в расчёте по ГОСТ (уточнить смысл)", "событий за 10 лет",
    "ЗАДАНО (расчётный параметр)", "none", 6, "3 г/см²", A127,
    M=([T127R], ["92.5548"]), val="92.5548")
add("N2.1-ev4", "2.1", "Длительность ряда SEPEM в выборке", "лет", "ДАННЫЕ", "none", 7,
    "SEPEM RDS v2.00", A127, M=([T127R], ["41.50308"]), val="41.50308")
add("N2.1-g1", "2.1", "Время роста в e раз, случай 19.01.2026 (минутные GOES)", "с",
    "ДАННЫЕ (исторический случай; не граница класса)", "none", 3,
    "GOES-19 SGPS, отклик data32/протоны/10 мм Al", A113, M=([MAP], ["≈42,4 с"]), val="42.4")
for i, (lit, nm) in enumerate([("0,007118", "подтверждённый подход"),
                               ("0,009883", "повтор после длинного спада"),
                               ("0,023585", "весь охват")], 1):
    add(f"N2.1-g{i+1}", "2.1", f"Наибольшая скорость роста H при ℓ=0,001 с⁻¹: {nm}", "с⁻¹",
        "ДАННЫЕ (исторический максимум; не граница)", "none", 4,
        "GOES SGPS, отклик data32/протоны/10 мм Al", A113, M=([T113], [lit]),
        val=lit.replace(",", "."))
add("N2.1-sh1", "2.1", "S₂ при модельной форме событий, 3 г/см²", "с⁻¹",
    "МОДЕЛЬ (перенос формы — допущение)", "none", 6, CY + "; те же COSRAD b,p,F", A150,
    M=([MAP], ["35865,11529071494"]), val="35865.11529071494")
add("N2.1-sh2", "2.1", "Снижение S₂ от формы событий", "%", "МОДЕЛЬ", "none", 6,
    CY + "; 3 г/см²", A150, M=([MAP], ["67,8324169055"]), val="67.8324169055")
add("N2.1-sh3", "2.1", "q90 модельного S₂, абсолютная модель SEPEM", "с⁻¹", "МОДЕЛЬ (МК)", "none", 5,
    CY + "; 3 г/см²; другие входы — не смешивать", A150,
    M=([MAP], ["q90(S₂)=35708,05"]), val="35708.05")

# 2.2 — от потоков к частоте сбоев
for r in crows(T141D, {"shield_g_cm2": "3.0"}):
    add(f"N2.2-d{r['step'][:2]}", "2.2", f"S₂ после шага «{r['step']}»", "с⁻¹",
        "АРИФМ (замена одного компонента на общих входах)", "none", 7,
        CY + "; 3 г/см²; " + r["scope"], A141,
        C=(T141D, {"shield_g_cm2": "3.0", "step": r["step"]}, "S2_s_inv"))
for h in ("2.5", "3.0", "3.5", "4.0"):
    k = h.replace(".", "")
    c = f"{CY}; {h} г/см²; отклик PROTON main_loglog с прямой ионизацией; геометрия 1/2; P_мин"
    add(f"N2.2-Q{k}", "2.2", f"Часть достаточного выражения без D, {h} г/см²", "—",
        "АРИФМ (часть верхнего выражения; не нижняя граница Q)", "down", 3, c, A127,
        J=(T127, f"rows[shield_g_cm2={h}]/Q_without_D_arithmetic"))
    add(f"N2.2-S{k}", "2.2", f"S₂ с прямой ионизацией, {h} г/см²", "с⁻¹",
        "АРИФМ (условные входы)", "none", 6, c, A127,
        J=(T127, f"rows[shield_g_cm2={h}]/S2_total_conditional"))
add("N2.2-B30", "2.2", "Пик с прямой ионизацией, 3 г/см², геометрия 1/2", "с⁻¹",
    "ВЕРХ (условные входы)", "up", 4, CY, A127, J=(T127, "rows[shield_g_cm2=3.0]/B_conditional_s"))
add("N2.2-x1", "2.2", "Сечение прямой ионизации в максимуме (0,8–1 МэВ перед BEOL)", "см²/бит",
    "ЛИТЕРАТУРА [Coronetti 2021], порядок величины", "none", 2,
    "CY62167GE30-45ZXI, нормальное падение, ECC выключена", A127,
    M=([T127P], ["1.2e-9 cm²/bit"]), val="1.2e-9")
add("N2.2-x2", "2.2", "Сечение для протонов высоких энергий", "см²/бит",
    "ЛИТЕРАТУРА [Coronetti 2021], порядок величины", "none", 1,
    "то же", A127, M=([T127P], ["HEP порядка 8e-14"]), val="8e-14")

# 2.3 — организация памяти
add("N2.3-W", "2.3", "Число внутренних слов W", "слов", "ЗАДАНО", "none", 6, CY, A127,
    J=(T127, "rows[shield_g_cm2=3.0]/W"))
add("N2.3-n", "2.3", "Разрядность полного слова n", "разрядов", "ЗАДАНО", "none", 2, CY, A127,
    J=(T127, "rows[shield_g_cm2=3.0]/n"))
add("N2.3-a1", "2.3", "Несовпадений при проверке отображения XY→адрес", "записей",
    "ДАННЫЕ (замороженная проверка)", "none", 6, "открытые данные Zenodo 10.5281/zenodo.8314389",
    AADDR, M=([ADDR], ["0/143590"]), val="143590", nocheck=False)
add("N2.3-a2", "2.3", "Ранг признаков GF(2)", "—", "ДАННЫЕ", "none", 2, "модель отображения",
    AADDR, M=([ADDR], ["25/25"]), val="25")
add("N2.3-al", "2.3", "Запас принятого достаточного расчёта демонстратора", "% от Q_доп",
    "ЗАПАС (условный)", "down", 4, CY + "; известная пара x16-адресов, 2¹⁹ слов за проход", AALIAS,
    M=([ALIAS], ["1,695% ε"]), val="1.695")
add("N2.3-mc", "2.3", "Предельная полуширина интервала Уилсона в МК-проверке RES-001", "—",
    "МК (заранее заданный допуск)", "none", 1, "RES-001", ARES1,
    J=(EXP1, "analytical_statistical_check/predeclared_limit"))

# 2.5 — последовательный контроль
add("N2.5-R", "2.5", "Чтение слова без сигнала исправления", "нс", "ВЕРХ (проектный, условный)",
    "up", 8, CY, A110, M=([T110], ["R^+=92,500920"]), val="92.500920")
add("N2.5-E", "2.5", "Чтение с исправлением по сигналу", "нс", "ВЕРХ (проектный, условный)",
    "up", 9, CY, A110, M=([T110], ["E^+=148,501480"]), val="148.501480")
add("N2.5-o1", "2.5", "Занятость обхода без сигналов", "мс", "ВЕРХ", "up", 6, CY, A110,
    M=([MAP], ["≤48,497122345"]), val="48.497122345")
add("N2.5-o2", "2.5", "Занятость обхода при сигнале в каждом слове", "мс", "ВЕРХ", "up", 6, CY, A110,
    M=([MAP], ["≤77,857543946"]), val="77.857543946")
add("N2.5-P", "2.5", "Наименьший период P_мин в семействе календарей", "с",
    "ВЕРХ (не глобальный аппаратный минимум)", "up", 4,
    CY + "; кадры по 8 слов, c=164, шаг g=196, наблюдаемая запись приложения", A127,
    J=(T127S, "P_min_s"))
add("N2.5-wr", "2.5", "Полная запись с предварительным наблюдением", "с", "ВЕРХ (проектный)", "up", 8,
    CY, A127, J=(T127S, "write_time_s"))
add("N2.5-rd", "2.5", "Атомарное чтение 32 разрядов", "с", "ВЕРХ (проектный)", "up", 8, CY, A127,
    J=(T127S, "read32_time_s"))

# 2.6 — оценки (прежние входы, постоянный период P_мин, запись по сигналу)
O = "old_6940_accepted_D_arithmetic/"
co = CY + "; 3 г/см²; прежние условные входы (S₂=6940 с⁻¹, D=2,802445·10⁻⁴); постоянный период P_мин"
add("N2.6-Qu", "2.6", "Верхняя оценка Q(T), постоянный период", "—", "ВЕРХ", "up", 3, co, A127,
    J=(T127S, O + "Q_conditional_upper"))
add("N2.6-Q0", "2.6", "То же без члена D", "—", "ВЕРХ (часть выражения)", "up", 3, co, A127,
    J=(T127S, O + "Q_without_D_arithmetic"))
add("N2.6-Dm", "2.6", "Наибольшее D, при котором достаточное неравенство выполняется", "—",
    "НИЗ (допустимое D)", "down", 3, co, A127, J=(T127S, O + "D_max_for_sufficient_inequality"))
add("N2.6-in", "2.6", "Член начального состояния", "—", "ВЕРХ", "up", 2, co, A127,
    J=(T127S, O + "initial_term"))
add("N2.6-ap", "2.6", "Член пар через незавершённое исправление", "—", "ВЕРХ", "up", 2, co, A127,
    J=(T127S, O + "aperture_cross"))
add("N2.6-qt", "2.6", "Сумма квот (начало, исполнение, обслуживание)", "—", "ЗАДАНО", "none", 1,
    co, A127, J=(T127S, O + "fixed_quota_total"))
add("N2.6-b0", "2.6", "Коэффициент пар β₀ = 1/(2W)", "—", "ЗАДАНО (консервативный)", "none", 6, co,
    A127, J=(T127S, O + "beta0"))
add("N2.6-L1", "2.6", "Большая память: достаточный период", "с", "ДОСТАТОЧНЫЙ (верхняя оценка проходит)",
    "none", 10, "диагностический класс; W=262144, слово 39, 64 Мбит/с", A58,
    M=([T58], ["20.18037184"]), val="20.18037184")
add("N2.6-L2", "2.6", "Большая память: нижняя оценка Q(T) постоянного класса", "—", "НИЗ", "down", 4,
    "диагностический класс; W=1935832, 256 Мбит/с, загрузка 1%", A58,
    M=([T58], ["0.0113836583418"]), val="0.0113836583418")
add("N2.6-L3", "2.6", "Большая память: загрузка при достаточном периоде", "%", "ВЕРХ", "up", 6,
    "W=262144, 64 Мбит/с", A58, M=([T58R, T58, MAP], ["0.791582", "0,791582"]), val="0.791582")

# 2.7 — требования к данным
add("N2.7-D0", "2.7", "Целевое D₀ в методе требований (точка автора)", "событий за срок",
    "ЗАДАНО", "none", 1, CY + "; 3 г/см²", A89, M=([T89], ["D₀=5·10⁻⁵"]), val="5e-5", nocheck=True)
add("N2.7-fl", "2.7", "Источник для полётной сверки (Sánchez-Cano и др., 2023)", "DOI", "ИСТОЧНИК (план)",
    "none", 1, "Solar Orbiter, Venus Express", APLAN, M=([PLAN], ["10.1029/2023SW003540"]),
    val="0", nocheck=True)


# --------------------------------------------------------------- сборка
def main() -> int:
    base = git("rev-parse", "HEAD") or "unknown"
    vals: dict[str, Decimal] = {}
    rows = []
    for s in SPEC:
        try:
            if "J" in s:
                rel, sel = s["J"]
                v, loc = dec(jget(rel, sel)), sel
            elif "C" in s:
                rel, flt, col = s["C"]
                v = dec(cget(rel, flt, col))
                loc = ";".join(f"{k}={x}" for k, x in flt.items()) + f" → {col}"
            else:
                rels, lits = s["M"]
                rel, line, lit = mdfind(rels, lits)
                v, loc = dec(s["val"]), f"строка {line}: «{lit}»"
                norm = lit.replace(",", ".").replace("\u00a0", "").replace(" ", "")
                if not s.get("nocheck") and s["val"] not in norm:
                    raise ValueError(f"цифры {s['val']} не совпадают с «{lit}»")
            vals[s["id"]] = v
            rows.append(dict(s, value=v, rel=rel, loc=loc, status="OK"))
        except Exception as ex:  # noqa: BLE001
            FAIL.append(f"{s['id']}: {ex}")
            rows.append(dict(s, value=None, rel="", loc=str(ex), status="FAIL"))

    def derived(i, sec, name, unit, typ, rnd, sig, cond, area, v, srcs):
        vals[i] = v
        rows.append(dict(id=i, sec=sec, name=name, unit=unit, typ=typ, rnd=rnd, sig=sig,
                         cond=cond, area=area, value=v, rel=" + ".join(srcs),
                         loc="вычислено build_numbers.py", status="OK"))

    # отношение пика к фону (масштаб изменчивости, 3 г/см²)
    derived("N2.1-ratio", "2.1", "Отношение пика к фону, 3 г/см²", "раз",
            "АРИФМ (отношение двух верхних подстановок)", "none", 2,
            CY + "; условный конверт", A141, vals["N2.1-p30"] / vals["N2.1-b30"], ["N2.1-p30", "N2.1-b30"])
    # учёт прямой ионизации при тех же входах: 03 / 01
    derived("N2.2-ratio", "2.2", "Рост S₂ при учёте прямой ионизации (те же входы)", "раз",
            "АРИФМ", "none", 2, CY + "; 3 г/см²; геометрия 1/2", A141,
            vals["N2.2-d03"] / vals["N2.2-d01"], ["N2.2-d03", "N2.2-d01"])
    derived("N2.2-xr", "2.2", "Отношение сечений PDI/HEP", "раз", "АРИФМ (порядок величины)", "none", 2,
            "литература", A127, vals["N2.2-x1"] / vals["N2.2-x2"], ["N2.2-x1", "N2.2-x2"])
    # член пар прежнего примера и контроль β₀·P_мин·6940
    pairs = vals["N2.6-Q0"] - vals["N2.6-in"] - vals["N2.6-ap"] - vals["N2.6-qt"]
    check = vals["N2.6-b0"] * vals["N2.5-P"] * Decimal(6940)
    if abs(pairs - check) > Decimal("1e-12") * abs(check):
        FAIL.append(f"N2.6-pr: член пар {pairs} не равен β₀·P_мин·6940 = {check}")
    derived("N2.6-pr", "2.6", "Член накопления пар β₀·P_мин·S₂", "—", "ВЕРХ (составляющая)", "up", 3, co,
            A127, pairs, ["N2.6-Q0", "N2.6-in", "N2.6-ap", "N2.6-qt"])
    derived("N2.6-sh", "2.6", "Доля члена пар в верхней оценке", "%", "АРИФМ", "none", 3, co, A127,
            100 * pairs / vals["N2.6-Qu"], ["N2.6-pr", "N2.6-Qu"])

    # RES-001: точные значения по формуле и таблица решений
    lam, T, taus = 0.5, 4.0, (0.5, 1.0, 2.0, 4.0)
    models = {"J-A": 0.5, "J-B": 1.0 / 6.0}
    exact = []
    for mname, q in models.items():
        for tau in taus:
            m, k = lam * tau, T / tau
            S = math.exp(-m) * (1 + m + q * m * m / 2)
            exact.append((mname, q, tau, m, int(k), 1 - S ** k))
    with open(OUT / "res001_exact.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["модель", "q", "период", "m=λ·период", "k", "Q_точн"])
        for e in exact:
            w.writerow([e[0], f"{e[1]:.12g}", e[2], e[3], e[4], f"{e[5]:.12g}"])
    table = {0.15: ("0.5", "нет"), 0.25: ("1.0", "0.5"), 0.35: ("2.0", "1.0"), 0.55: ("4.0", "4.0")}
    for eps, (ja, jb) in table.items():
        for mname, ref in (("J-A", ja), ("J-B", jb)):
            ok = [e[2] for e in exact if e[0] == mname and e[5] <= eps]
            got = f"{max(ok):.1f}" if ok else "нет"
            if got != ref:
                FAIL.append(f"RES-001 ε={eps} {mname}: вычислено {got}, в карточке {ref}")
            rows.append(dict(id=f"N2.3-r{mname[-1]}{int(eps*100)}", sec="2.3",
                             name=f"RES-001: наибольший допустимый период, {mname}, ε={eps}",
                             unit="ед. модельного времени", typ="ТОЧН (формула RES-001)", rnd="none",
                             sig=2, cond="четыре слова, λ=0,5, T=4, периоды {0,5;1;2;4}", area=ARES1,
                             value=None if got == "нет" else dec(got), text=got.replace(".", ","),
                             rel=RES1, loc="таблица решений; пересчёт по S(q,m)", status="OK"))

    with open(OUT / "ch2_numbers.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["id", "раздел", "величина", "значение_источника", "значение_для_текста",
                    "округление", "единицы", "тип_оценки", "условия", "источник", "локатор",
                    "blob_sha", "область_принятия", "статус", "база_main"])
        for r in rows:
            v = r["value"]
            text = r.get("text") or ("" if v is None else fmt(v, r["rnd"], r["sig"]))
            src = r["rel"]
            sha = blob(src) if src and (ROOT / src).exists() else ""
            w.writerow([r["id"], r["sec"], r["name"], "" if v is None else str(v), text, r["rnd"],
                        r["unit"], r["typ"], r["cond"], src, r["loc"], sha, r["area"], r["status"], base])
    print(f"чисел: {len(rows)}; ошибок: {len(FAIL)}; база {base[:12]}")
    for f in FAIL:
        print("  FAIL", f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

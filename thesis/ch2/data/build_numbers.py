#!/usr/bin/env python3
"""Таблица чисел главы 2 — сборка из закреплённых принятых источников.

Все входы читаются не из рабочей копии, а из закреплённой версии PIN
(``git show PIN:путь``); хеш объекта Git записывается в таблицу.
Движущиеся документы (MAP, STATUS, RESEARCH_PLAN) источниками чисел не служат.

Способ получения значения:
  J — поле JSON;  C — поле CSV (строка по фильтру, при необходимости — по правилу выбора);
  R — группа регулярного выражения: смысл полей задаётся шаблоном, а не догадкой;
  M — дословная запись в тексте; цифры значения сверяются с записью;
  D — вычисление из уже полученных чисел или по принятой формуле (RES-001).

Повтор из корня репозитория (нужен Git с объектом PIN):
    python3 thesis/ch2/data/build_numbers.py
Выход: thesis/ch2/data/ch2_numbers.csv и thesis/ch2/data/res001_exact.csv.
Код возврата 1 — источник недоступен, значение не найдено или контроль не прошёл.
Верхние оценки округляются вверх, нижние — вниз (столбец «округление»).
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
import subprocess
import sys
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from pathlib import Path

PIN = "140f8d36751f117cfc96969d7732f85456476a5d"  # база принятых входов пакета плана
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FAIL: list[str] = []
_CACHE: dict[str, str] = {}


def show(rel: str) -> str:
    if rel not in _CACHE:
        r = subprocess.run(["git", "-C", str(ROOT), "show", f"{PIN}:{rel}"], capture_output=True)
        if r.returncode != 0:
            raise FileNotFoundError(f"{rel} отсутствует в {PIN[:12]}")
        _CACHE[rel] = r.stdout.decode("utf-8")
    return _CACHE[rel]


def blob(rel: str) -> str:
    r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", f"{PIN}:{rel}"], capture_output=True, text=True)
    sha = r.stdout.strip()
    if r.returncode != 0 or re.fullmatch(r"[0-9a-f]{40}", sha) is None:
        raise FileNotFoundError(f"Объект источника {rel} отсутствует в {PIN[:12]}")
    return sha


def dec(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    if isinstance(x, int) and not isinstance(x, bool):
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
    cur = json.loads(show(rel))
    for part in sel.split("/"):
        m = re.fullmatch(r"([^\[]+)(?:\[(.+)\])?", part)
        cur = cur[m.group(1)]
        if m.group(2) is None:
            continue
        f, v = m.group(2).split("=", 1)
        hits = [r for r in cur if same(r.get(f), v)]
        if len(hits) != 1:
            raise KeyError(f"{rel}:{part}: совпадений {len(hits)}")
        cur = hits[0]
    return cur


def crows(rel: str, flt: dict) -> list[dict]:
    return [r for r in csv.DictReader(io.StringIO(show(rel))) if all(same(r[k], v) for k, v in flt.items())]


SUPMAP = str.maketrans("⁻⁰¹²³⁴⁵⁶⁷⁸⁹", "-0123456789")


def norm(s: str) -> str:
    s = s.replace(",", ".").replace("\u00a0", "").replace(" ", "").translate(SUPMAP)
    return re.sub(r"·10(-?\d+)", r"e\1", s)


def lineno(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def fmt(x: Decimal, rnd: str, sig: int) -> str:
    """Запись для текста: десятичная запятая, неразрывные пробелы, направленное округление."""
    if x == 0:
        return "0"
    mode = {"up": ROUND_CEILING, "down": ROUND_FLOOR, "none": ROUND_HALF_EVEN}[rnd]
    with localcontext() as c:
        c.prec = 80
        y = x.quantize(Decimal(1).scaleb(x.adjusted() - sig + 1), rounding=mode)
        e = y.adjusted()
        if -2 <= e <= 5:
            ip, _, fr = format(y, "f").partition(".")
            neg, ip = ip.startswith("-"), ip.lstrip("-")
            if len(ip) > 4:
                g = []
                while ip:
                    g.insert(0, ip[-3:])
                    ip = ip[:-3]
                ip = "\u00a0".join(g)
            return ("-" if neg else "") + ip + ("," + fr if fr else "")
        m = format(y.scaleb(-e), "f").replace(".", ",")
        return f"{m}·10{str(e).translate(str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹'))}"


# ------------------------------------------------------------------ источники
T127 = "experiments/t127-cy62167-pdi/outputs/inputs-126.json"
T127S = "experiments/t127-cy62167-pdi/outputs/service.json"
T127R = "experiments/t127-cy62167-pdi/REPORT.md"
T127P = "experiments/t127-cy62167-pdi/DATA_PASSPORT.md"
T141S = "experiments/t141-radiation-chain/outputs/shield-summary.csv"
T141D = "experiments/t141-radiation-chain/outputs/discrepancies.csv"
T141M = "experiments/t141-radiation-chain/outputs/profile-missions.csv"
T150T = "experiments/t150-event-shape/outputs/shape-transfer.csv"
T110 = "theory/t110-err-write-service.md"
T114 = "theory/t114-two-stage-err.md"
T119 = "theory/t119-err-joint-bound.md"
T113 = "experiments/t113-onset-growth/RESULTS.md"
T135 = "experiments/t135-demo-operating-point/report-r4.json"
T58 = "experiments/t58-fixed-baseline-r0b/README.md"
T58R = "experiments/t58-fixed-baseline-r0b/reference_points.md"
T89 = "experiments/t89-test-requirement/METHOD.md"
ADDR = "experiments/RE-CY62167-ADDRESS-MAPPING-01/REPORT.md"
EXP1 = "experiments/manifests/EXP-001/analytical-validation.json"
RES1 = "results/RES-001-exp001-four-word-identified-set.md"

CY = "CY62167, внутреннее слово 32+6, W=524288, ГСО, T=10 лет"
OLD = CY + "; 3 г/см²; прежние условные входы"
A141 = "MAP 13.10.2026: T141 — параметрический тракт; физическая П=0,1, D и нижний сигнал не установлены"
A127 = "MAP 08.10.2026: условные входы T127; прежние 6940 с⁻¹ не заменены"
A150 = "MAP 14.10.2026: T150 — параметрическая область; не физическая П=0,1"
A110 = "MAP 07.10.2026: T110 — условная теорема обслуживания с записью по сигналу"
A114 = "MAP 07.10.2026: T114 при A1–A7"
A119 = "MAP 08.10.2026: T119 при A1–A7 T114"
A135 = "MAP 12.10.2026: Б и T135 приняты в границах варианта D (выбранная точка r3)"
A58 = "MAP: T52 — договор для безусловной записи и записи после исправимой ошибки; T58 — его применение к диагностическому классу"
ARES1 = "RES-001: все 14 условий применимости"
AADDR = "MAP «CY62167: проверенный задел»: отображение XY→внешний адрес; внутренний слой ECC не восстановлен"
A89 = "MAP 03.10.2026: T88/T89 в условной области internal38"
A113 = "MAP 07.10.2026: T113 — инженерное дополнение без полной научной рецензии"

SPEC: list[dict] = []


def add(i, sec, name, unit, typ, rnd, sig, cond, area, **src):
    SPEC.append(dict(id=i, sec=sec, name=name, unit=unit, typ=typ, rnd=rnd, sig=sig, cond=cond,
                     area=area, **src))


# 2.1 — обстановка
add("N2.1-01", "2.1", "Срок T", "с", "ЗАДАНО", "none", 9, CY, A127, J=(T127, "rows[shield_g_cm2=3.0]/T_s"))
add("N2.1-02", "2.1", "Допустимая вероятность Q_доп (исследовательское требование, не требование изделия)", "—",
    "ЗАДАНО", "none", 1, CY, A127, J=(T127, "rows[shield_g_cm2=3.0]/epsilon"))
for h in ("2.5", "3.0", "3.5", "4.0"):
    c = f"{CY}; защита {h} г/см²; прямоугольная форма, геометрия a_H=1, COSRAD; условный конверт"
    k = h.replace(".", "")
    for key, col, nm, unit in (("b", "background_s_inv", "Фон (верх подстановки)", "с⁻¹ битовых инверсий массива"),
                               ("p", "peak_upper_s_inv", "Пик (верх)", "с⁻¹ битовых инверсий массива"),
                               ("F", "N_total_upper", "Верх ∫λdt за срок", "битовых инверсий массива"),
                               ("S", "S2_upper_s_inv", "Верх S₂", "с⁻¹")):
        add(f"N2.1-{key}{k}", "2.1", f"{nm}, {h} г/см²", unit, "ВЕРХ (условный конверт)", "up", 4, c, A141,
            C=(T141S, {"shield_g_cm2": h}, col))
for i, (nm, lit, val, unit) in enumerate([
        ("Верх фона прежнего класса", "\\bar b=0.000154704", "0.000154704", "с⁻¹ касаний слов"),
        ("Наибольшая интенсивность касаний слов прежнего класса", "B=0.244682704", "0.244682704", "с⁻¹ касаний слов"),
        ("Надфоновая экспозиция прежнего класса", "F_S=28310.473728", "28310.473728", "касаний слов за срок"),
        ("Ограничение роста ρ прежнего класса", ".048(t-u)", ".048", "с⁻¹"),
        ("Порог ℓ прежнего класса", "\\ell=.001", ".001", "с⁻¹")], 1):
    sig = len(val.lstrip("0.").replace(".", ""))
    add(f"N2.1-old{i}", "2.1", nm, unit, "ЗАДАНО (условный класс)", "none", sig, OLD, A119, M=([T119], [lit]), val=val)
add("N2.1-D", "2.1", "Верхняя граница D, 3 г/см² (условно задана)", "событий за срок", "ЗАДАНО (условная)",
    "none", 7, OLD, A114, M=([T114], ["0.0002802445"]), val="0.0002802445")
add("N2.1-ev1", "2.1", "Частота эпизодов по выборке SEPEM", "событий за 10 лет",
    "ДАННЫЕ (131 эпизод; порог и слияние 24 ч)", "none", 7, "SEPEM RDS v2.00", A127,
    M=([T127R], ["31.56392"]), val="31.56392")
add("N2.1-ev2", "2.1", "Число событий по модели ГОСТ (числа Вольфа SILSO V2)", "событий за 10 лет", "МОДЕЛЬ",
    "none", 8, "тот же интервал", A127, M=([T127R], ["100.56812"]), val="100.56812")
add("N2.1-ev3", "2.1", "Среднее число событий в расчёте по ГОСТ (смысл уточнить при 2.1)", "событий за 10 лет",
    "ЗАДАНО (расчётный параметр)", "none", 6, "3 г/см²", A127, M=([T127R], ["92.5548"]), val="92.5548")
add("N2.1-ev4", "2.1", "Длительность ряда SEPEM в выборке", "лет", "ДАННЫЕ", "none", 7, "SEPEM RDS v2.00", A127,
    M=([T127R], ["41.50308"]), val="41.50308")
add("N2.1-g1", "2.1", "Время роста в e раз для пары минутных точек с наибольшим наклоном (весь охват)", "с",
    "ДАННЫЕ (исторический случай; не граница класса)", "none", 5, "GOES SGPS; отклик data32/протоны/10 мм Al",
    A113, M=([T113], ["42,400 с"]), val="42.400")
for i, (lit, nm) in enumerate([("0,007118", "подтверждённый подход"), ("0,009883", "повтор после длинного спада"),
                               ("0,023585", "весь охват")], 2):
    add(f"N2.1-g{i}", "2.1", f"Наибольшая скорость роста в шкале H при ℓ=0,001 с⁻¹: {nm}", "с⁻¹",
        "ДАННЫЕ (исторический максимум; не граница)", "none", 4, "GOES SGPS; отклик data32/протоны/10 мм Al",
        A113, M=([T113], [lit]), val=lit.replace(",", "."))
add("N2.1-sh1", "2.1", "S₂ при модельной форме событий (выборочная 0,9-квантиль коэффициента формы)", "с⁻¹",
    "МОДЕЛЬ (перенос формы — допущение)", "none", 6, CY + "; 3 г/см²; те же COSRAD b, p, F", A150,
    CP=(T150T, {"shield_g_cm2": "3.0", "response_case": "full", "choice": "model_r_q90"}, "mean_events", "S2_s_inv"))
add("N2.1-sh3", "2.1", "Модельная 0,9-квантиль S₂ в абсолютной модели SEPEM", "с⁻¹",
    "МОДЕЛЬ (МК; другие входы — не смешивать)", "none", 5, CY + "; 3 г/см²", A141,
    CP=(T141M, {"shield_g_cm2": "3.0"}, "mean_events", "S2_q90_s_inv"))

TNN = "experiments/tNN-sepem-profiles/config.json"
add("N2.1-kG", "2.1", "Коэффициент среднего числа событий СКЛ по ГОСТ Р 25645.165-2025 (ряд Вольфа версии 1.0)",
    "событий на сумму среднемесячных чисел Вольфа", "НОРМАТИВНЫЙ ПАРАМЕТР (перенос в коде цепочки; текст ГОСТ не сверен)",
    "none", 3, "формула числа событий популяции Φ(≥30 МэВ) ≥ 10⁵ см⁻²", A127,
    R=("experiments/tNN-sepem-profiles/gost.py", r'"1\.0": (0\.\d+)', 1))
add("N2.1-kO", "2.1", "Коэффициент среднего числа событий СКЛ по формуле (Б.2) ОСТ 134-1044-2007",
    "событий на сумму среднемесячных чисел Вольфа", "НОРМАТИВНЫЙ ПАРАМЕТР (сверен с копией ОСТ 15.10)", "none", 3,
    "ОСТ 134-1044-2007, переиздание по изм. № 2 с изм. 1, прил. Б", A127,
    M=(["experiments/t50-lambda-inputs/inputs.md"], ["0.0135 ΣW_i"]), val="0.0135")

# 2.2 — от потоков к частоте сбоев
for r in crows(T141D, {"shield_g_cm2": "3.0"}):
    add(f"N2.2-d{r['step'][:2]}", "2.2", f"S₂ после шага «{r['step']}»", "с⁻¹",
        "АРИФМ (замена одного компонента на общих входах)", "none", 7, CY + "; 3 г/см²; " + r["scope"], A141,
        C=(T141D, {"shield_g_cm2": "3.0", "step": r["step"]}, "S2_s_inv"))
for h in ("2.5", "3.0", "3.5", "4.0"):
    k = h.replace(".", "")
    c = f"{CY}; {h} г/см²; отклик с прямой ионизацией (PROTON main_loglog); геометрия 1/2; P_мин"
    add(f"N2.2-Q{k}", "2.2", f"Часть достаточного выражения без D, {h} г/см²", "—",
        "АРИФМ (часть верхнего выражения; не нижняя граница Q)", "down", 3, c, A127,
        J=(T127, f"rows[shield_g_cm2={h}]/Q_without_D_arithmetic"))
    add(f"N2.2-S{k}", "2.2", f"S₂ с прямой ионизацией, {h} г/см²", "с⁻¹", "АРИФМ (условные входы)", "none", 6,
        c, A127, J=(T127, f"rows[shield_g_cm2={h}]/S2_total_conditional"))
add("N2.2-B30", "2.2", "Пик с прямой ионизацией, 3 г/см², геометрия 1/2", "с⁻¹", "ВЕРХ (условные входы)", "up", 4,
    CY, A127, J=(T127, "rows[shield_g_cm2=3.0]/B_conditional_s"))
add("N2.2-x1", "2.2", "Сечение прямой ионизации в максимуме (0,8–1 МэВ перед слоями металлизации)", "см²/бит",
    "ЛИТЕРАТУРА [Coronetti 2021], порядок величины", "none", 2, "CY62167GE30-45ZXI, нормальное падение, ECC выкл.",
    A127, M=([T127P], ["1.2e-9 cm²/bit"]), val="1.2e-9")
add("N2.2-x2", "2.2", "Сечение для протонов высоких энергий", "см²/бит",
    "ЛИТЕРАТУРА [Coronetti 2021], порядок величины", "none", 1, "то же", A127,
    M=([T127P], ["HEP порядка 8e-14"]), val="8e-14")

# 2.3 — организация памяти
add("N2.3-W", "2.3", "Число внутренних слов W", "слов", "ЗАДАНО", "none", 6, CY, A127, J=(T127, "rows[shield_g_cm2=3.0]/W"))
add("N2.3-n", "2.3", "Разрядность полного слова n", "разрядов", "ЗАДАНО", "none", 2, CY, A127,
    J=(T127, "rows[shield_g_cm2=3.0]/n"))
VAL = r"frozen validation gives `(\d+)/(\d+)` mismatches"
TRN = r"training residuals are `(\d+)/(\d+)`"
RNK = r"GF\(2\) feature rank is `(\d+)/(\d+)`"
ac = "открытые данные Zenodo 10.5281/zenodo.8314389; модель XY→внешний адрес ×8"
add("N2.3-a1", "2.3", "Отображение адресов: записей в замороженной проверке", "записей", "ДАННЫЕ", "none", 6, ac,
    AADDR, R=(ADDR, VAL, 2))
add("N2.3-a2", "2.3", "Отображение адресов: несовпадений в замороженной проверке", "записей", "ДАННЫЕ", "none", 1,
    ac, AADDR, R=(ADDR, VAL, 1))
add("N2.3-a3", "2.3", "Отображение адресов: записей обучения", "записей", "ДАННЫЕ", "none", 4, ac, AADDR, R=(ADDR, TRN, 2))
add("N2.3-a4", "2.3", "Отображение адресов: несовпадений на обучении", "записей", "ДАННЫЕ", "none", 1, ac, AADDR,
    R=(ADDR, TRN, 1))
add("N2.3-a5", "2.3", "Ранг системы признаков над GF(2) (из возможных 25)", "—", "ДАННЫЕ", "none", 2, ac, AADDR,
    R=(ADDR, RNK, 1))
add("N2.3-al", "2.3", "Относительный запас вероятности выбранной точки демонстратора", "% от Q_доп",
    "НИЗ (точное значение, округлено вниз)", "down", 5,
    CY + "; известная пара x16-адресов, 2¹⁹ слов за проход; точка selected_r3_original", A135,
    J=(T135, "rows/selected_r3_original/relative_slack"), scale=100)
add("N2.3-mc1", "2.3", "RES-001: заранее заданный предел абсолютного расхождения МК и точного значения", "—",
    "КРИТЕРИЙ ПРОВЕРКИ (не погрешность МК)", "none", 1, "RES-001; поточечные 95%-интервалы Уилсона не совместные",
    ARES1, J=(EXP1, "analytical_statistical_check/predeclared_limit"))
add("N2.3-mc2", "2.3", "RES-001: пройдено заранее объявленных проверок", "проверок", "ДАННЫЕ ПРОВЕРКИ", "none", 1,
    "RES-001", ARES1, J=(EXP1, "analytical_statistical_check/checks_passed"))

# 2.5 — последовательный контроль (сквозной пример: запись по сигналу исправления)
add("N2.5-R", "2.5", "Чтение слова без сигнала исправления", "нс", "ВЕРХ (проектный, условный)", "up", 4, CY, A110,
    M=([T110], ["R^+=92,500920"]), val="92.500920")
add("N2.5-E", "2.5", "Чтение с исправлением по сигналу", "нс", "ВЕРХ (проектный, условный)", "up", 4, CY, A110,
    M=([T110], ["E^+=148,501480"]), val="148.501480")
cP = CY + "; запись по сигналу; кадры по 8 слов, c=164, g=196; наблюдаемая запись приложения"
add("N2.5-P", "2.5", "Наименьший период P_мин в семействе календарей (верх)", "с",
    "ВЕРХ (не глобальный аппаратный минимум)", "up", 4, cP, A127, J=(T127S, "P_min_s"))
add("N2.5-Pl", "2.5", "Тот же период, нижняя граница", "с", "НИЗ", "down", 4, cP, A127, J=(T127S, "P_lower_s"))
add("N2.5-wr", "2.5", "Полная запись с предварительным наблюдением", "с", "ВЕРХ (проектный)", "up", 4, cP, A127,
    J=(T127S, "write_time_s"))
add("N2.5-rd", "2.5", "Атомарное чтение 32 информационных разрядов", "с", "ВЕРХ (проектный)", "up", 4, cP, A127,
    J=(T127S, "read32_time_s"))

# 2.6 — оценки (прежние входы, постоянный период P_мин, запись по сигналу)
O = "old_6940_accepted_D_arithmetic/"
co = OLD + " (S₂=6940 с⁻¹, D=2,802445·10⁻⁴); постоянный период P_мин; запись по сигналу (набор T110)"
add("N2.6-Qu", "2.6", "Верхняя оценка Q(T), постоянный период", "—", "ВЕРХ", "up", 3, co, A127,
    J=(T127S, O + "Q_conditional_upper"))
add("N2.6-Q0", "2.6", "То же без члена D", "—", "ВЕРХ (часть выражения)", "up", 3, co, A127,
    J=(T127S, O + "Q_without_D_arithmetic"))
add("N2.6-Dm", "2.6", "Наибольшее D, при котором достаточное неравенство выполняется", "—", "НИЗ (допустимое D)",
    "down", 3, co, A127, J=(T127S, O + "D_max_for_sufficient_inequality"))
add("N2.6-in", "2.6", "Член начального состояния K₀B(P+d)/W", "—", "ВЕРХ", "up", 2, co, A127, J=(T127S, O + "initial_term"))
add("N2.6-ap", "2.6", "Член пар через незавершённое исправление", "—", "ВЕРХ", "up", 2, co, A127,
    J=(T127S, O + "aperture_cross"))
add("N2.6-qt", "2.6", "Сумма квот: начало, исполнение, обслуживание", "—", "ЗАДАНО", "none", 1, co, A127,
    J=(T127S, O + "fixed_quota_total"))
add("N2.6-b0", "2.6", "Консервативный коэффициент пар β₀=χ/2 при η_w=q_w², q_w=1/W", "—", "ЗАДАНО", "none", 6, co,
    A127, J=(T127S, O + "beta0"))
add("N2.6-L1", "2.6", "Большая память: достаточный период", "с", "ДОСТАТОЧНЫЙ (верхняя оценка проходит)", "none", 10,
    "диагностический класс; внешнее слово (39, 32), W=262144, 64 Мбит/с, безусловная запись", A58,
    M=([T58], ["20.18037184"]), val="20.18037184")
add("N2.6-L2", "2.6", "Большая память: нижняя оценка Q(T) постоянного класса", "—", "НИЗ", "down", 4,
    "диагностический класс; W=1935832, 256 Мбит/с, загрузка 1 %, безусловная запись", A58,
    M=([T58], ["0.0113836583418"]), val="0.0113836583418")
# Загрузка при достаточном периоде большой памяти — взять из grid.csv/summary.json T58 при работе над 2.6.


# 2.7 — требования к данным
add("N2.7-D0", "2.7", "Целевое D₀ в методе требований (точка автора, не измерение)", "событий за срок", "ЗАДАНО",
    "none", 1, CY + "; 3 г/см²", A89, M=([T89], ["D₀=5·10⁻⁵"]), val="5e-5")


def main() -> int:
    vals: dict[str, Decimal] = {}
    rows = []
    for s in SPEC:
        try:
            if "J" in s:
                rel, sel = s["J"]
                v, loc = dec(jget(rel, sel)), sel
            elif "C" in s:
                rel, flt, col = s["C"]
                hits = crows(rel, flt)
                if len(hits) != 1:
                    raise KeyError(f"{rel}: {flt}: совпадений {len(hits)}")
                v = dec(hits[0][col])
                loc = ";".join(f"{k}={x}" for k, x in flt.items()) + f" → {col}"
            elif "CP" in s:
                rel, flt, key, col = s["CP"]
                hits = crows(rel, flt)
                if not hits:
                    raise KeyError(f"{rel}: {flt}: нет строк")
                best = max(hits, key=lambda r: dec(r[key]))
                v = dec(best[col])
                loc = ";".join(f"{k}={x}" for k, x in flt.items()) + f"; наибольшее {key}={best[key]} → {col}"
            elif "R" in s:
                rel, pat, grp = s["R"]
                text = show(rel)
                m = re.search(pat, text)
                if not m:
                    raise KeyError(f"шаблон не найден: {pat}")
                v, loc = dec(m.group(grp)), f"строка {lineno(text, m.start())}: шаблон «{pat}», группа {grp}"
            else:
                (rels, lits), v, found = s["M"], dec(s["val"]), None
                for rel in rels:
                    try:
                        text = show(rel)
                    except FileNotFoundError:
                        continue
                    for lit in lits:
                        p = text.find(lit)
                        if p >= 0:
                            found = (rel, lineno(text, p), lit)
                            break
                    if found:
                        break
                if not found:
                    raise KeyError(f"не найдено {lits} в {rels}")
                rel, ln, lit = found
                if s["val"] not in norm(lit):
                    raise ValueError(f"цифры {s['val']} не совпадают с «{lit}»")
                loc = f"строка {ln}: «{lit}»"
            if "scale" in s:
                v = v * Decimal(s["scale"])
            vals[s["id"]] = v
            rows.append(dict(s, value=v, rel=rel, loc=loc, status="OK"))
        except Exception as ex:  # noqa: BLE001
            FAIL.append(f"{s['id']}: {ex}")
            rows.append(dict(s, value=None, rel="", loc=str(ex), status="FAIL"))

    def derived(i, sec, name, unit, typ, rnd, sig, cond, area, v, srcs):
        vals[i] = v
        rows.append(dict(id=i, sec=sec, name=name, unit=unit, typ=typ, rnd=rnd, sig=sig, cond=cond, area=area,
                         value=v, rel=" + ".join(srcs), loc="вычислено build_numbers.py", status="OK"))

    if FAIL:
        print("\n".join("  FAIL " + f for f in FAIL))
        return 1
    with localcontext() as c:
        c.prec = 40
        derived("N2.1-ratio", "2.1", "Отношение пика к фону, 3 г/см²", "раз",
                "АРИФМ (отношение двух верхних подстановок)", "none", 2, CY + "; условный конверт", A141,
                vals["N2.1-p30"] / vals["N2.1-b30"], ["N2.1-p30", "N2.1-b30"])
        derived("N2.1-sh2", "2.1", "Снижение S₂ от модельной формы событий", "%", "МОДЕЛЬ", "none", 6,
                CY + "; 3 г/см²", A150, 100 * (1 - vals["N2.1-sh1"] / vals["N2.1-S30"]), ["N2.1-sh1", "N2.1-S30"])
        wolf = [dec(x) for x in json.loads(show(TNN))["wolf_v1_annual_mean_cycle"]]
        sumW = sum(wolf)
        cw = "среднегодовые числа Вольфа среднего цикла, годы 1–10 (табл. Г.1 ОСТ 134-1044-2007; сверено check_ost_g1.py)"
        derived("N2.1-W10", "2.1", "Сумма среднегодовых чисел Вольфа среднего цикла за годы 1–10", "—", "ДАННЫЕ", "none", 4,
                cw, A127, sumW, [TNN])
        mu1 = vals["N2.1-kG"] * 12 * sumW
        if mu1 != vals["N2.1-ev3"]:
            FAIL.append(f"N2.1-mu1: {mu1} не равно N2.1-ev3 = {vals['N2.1-ev3']}")
        derived("N2.1-mu1", "2.1", "Среднее число событий СКЛ за 10 лет среднего цикла по ГОСТ Р 25645.165-2025", "событий",
                "МОДЕЛЬ (нормативная формула)", "none", 6, cw + "; годовые значения повторены помесячно", A127, mu1,
                ["N2.1-kG", "N2.1-W10"])
        mu2 = vals["N2.1-kO"] * 12 * sumW
        derived("N2.1-mu2", "2.1", "То же по формуле (Б.2) ОСТ 134-1044-2007", "событий", "МОДЕЛЬ (нормативная формула)",
                "none", 6, cw + "; годовые значения повторены помесячно", A127, mu2, ["N2.1-kO", "N2.1-W10"])
        derived("N2.1-mu3", "2.1", "Отношение средних чисел событий по ОСТ и ГОСТ 2025", "раз", "АРИФМ", "none", 4, cw, A127,
                mu2 / mu1, ["N2.1-mu2", "N2.1-mu1"])
        derived("N2.7-z1", "2.7", "Доверительная вероятность верхней границы σ < 1/Φ при нулевом счёте, 1 − e⁻¹", "—",
                "АРИФМ (пуассоновский счёт)", "down", 3,
                "правило (В.3) РД 134-0139-2005 (копия вне репозитория); для сравнения с −ln α/E метода требований",
                "РД 134-0139-2005 с изм. 3, прил. В", Decimal(1) - Decimal(math.exp(-1)), ["вычислено"])
        derived("N2.2-ratio", "2.2", "Рост ∫λ²dt при учёте протонов низких энергий (те же входы)", "раз", "АРИФМ",
                "none", 2, CY + "; 3 г/см²; геометрия 1/2", A141, vals["N2.2-d03"] / vals["N2.2-d01"],
                ["N2.2-d03", "N2.2-d01"])
        derived("N2.2-xr", "2.2", "Отношение сечений прямой ионизации и протонов высоких энергий", "раз",
                "АРИФМ (порядок величины)", "none", 2, "литература", A127, vals["N2.2-x1"] / vals["N2.2-x2"],
                ["N2.2-x1", "N2.2-x2"])
        W, R, E, P = vals["N2.3-W"], vals["N2.5-R"], vals["N2.5-E"], vals["N2.5-P"]
        B, b = vals["N2.1-old2"], vals["N2.1-old1"]
        derived("N2.5-o1", "2.5", "Занятость интерфейса операциями контроля за проход без сигналов, W·R⁺", "мс",
                "ВЕРХ", "up", 4, CY, A110, W * R / Decimal(10**6), ["N2.3-W", "N2.5-R"])
        derived("N2.5-o2", "2.5", "То же при сигнале в каждом слове, W·E⁺", "мс", "ВЕРХ", "up", 4, CY, A110,
                W * E / Decimal(10**6), ["N2.3-W", "N2.5-E"])
        cex = OLD + "; ν ≤ B — верх интенсивности непрямых касаний, для слова ≤ ν/W; окна длины P_мин, k ≥ 1; прямые события не входят"
        derived("N2.5-x1", "2.5", "Верхняя граница среднего числа непрямых касаний во всех окнах наблюдения одного прохода на пике класса, B·P_мин", "касаний",
                "ВЕРХ", "up", 3, cex, A119, B * P, ["N2.1-old2", "N2.5-P"])
        pairs = vals["N2.6-Q0"] - vals["N2.6-in"] - vals["N2.6-ap"] - vals["N2.6-qt"]
        check = vals["N2.6-b0"] * P * Decimal(6940)
        if abs(pairs - check) > Decimal("1e-12") * abs(check):
            FAIL.append(f"N2.6-pr: член пар {pairs} не равен β₀·P_мин·6940 = {check}")
        derived("N2.6-pr", "2.6", "Член накопления пар β₀·P_мин·S₂", "—", "ВЕРХ (составляющая)", "up", 3, co, A127,
                pairs, ["N2.6-Q0", "N2.6-in", "N2.6-ap", "N2.6-qt"])
        derived("N2.6-sh", "2.6", "Доля члена пар в верхней оценке", "%", "АРИФМ", "none", 3, co, A127,
                100 * pairs / vals["N2.6-Qu"], ["N2.6-pr", "N2.6-Qu"])

    # RES-001: точные значения по принятой формуле и таблица решений карточки
    lam, T, taus = 0.5, 4.0, (0.5, 1.0, 2.0, 4.0)
    exact = []
    for mname, q in (("J-A", 0.5), ("J-B", 1.0 / 6.0)):
        for tau in taus:
            m, k = lam * tau, T / tau
            exact.append((mname, q, tau, m, int(k), 1 - (math.exp(-m) * (1 + m + q * m * m / 2)) ** k))
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
            rows.append(dict(id=f"N2.3-r{mname[-1]}{int(eps * 100)}", sec="2.3",
                             name=f"RES-001: наибольший допустимый период, {mname}, ε={eps}",
                             unit="ед. модельного времени", typ="ТОЧН (формула RES-001)", rnd="none", sig=2,
                             cond="четыре слова, λ=0,5, T=4, периоды {0,5; 1; 2; 4}", area=ARES1,
                             value=None if got == "нет" else dec(got), text=got.replace(".", ","), rel=RES1,
                             loc="таблица решений карточки; пересчёт по S(q, m)", status="OK"))

    with open(OUT / "ch2_numbers.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["id", "раздел", "величина", "значение_источника", "значение_для_текста", "округление",
                    "единицы", "тип_оценки", "условия", "источник", "локатор", "blob_sha", "закреплённая_версия",
                    "область_принятия", "статус"])
        for r in rows:
            v = r["value"]
            text = r.get("text") or ("" if v is None else fmt(v, r["rnd"], r["sig"]))
            src = r["rel"]
            sha = blob(src) if src and "N2." not in src and src != "вычислено" else ""
            w.writerow([r["id"], r["sec"], r["name"], "" if v is None else str(v), text, r["rnd"], r["unit"],
                        r["typ"], r["cond"], src, r["loc"], sha, PIN, r["area"], r["status"]])
    print(f"чисел: {len(rows)}; ошибок: {len(FAIL)}; закреплено на {PIN[:12]}")
    for f in FAIL:
        print("  FAIL", f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

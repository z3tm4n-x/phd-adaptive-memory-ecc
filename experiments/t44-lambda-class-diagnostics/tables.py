"""Human-readable numerical appendix generated from the same T44 result."""


def f(x):
    return "—" if x is None else f"{x:.10g}"


def table(lines, headings, rows):
    lines += ["| " + " | ".join(headings) + " |", "| " + " | ".join(["---"] * len(headings)) + " |"]
    lines += ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    lines.append("")


def render(result):
    lines = ["# Численное приложение T44", "", "Создано `reproduce.py`; условия и выводы — в [conditions.md](conditions.md).",
             "Округление таблиц — для чтения; полные значения, рациональный S и все переходы — в `summary.json`.", "",
             "## 1. Вечный пик", "", "Источник: T36 (Д4), G16/central/published_valid/native из T37 либо округлённый r автора.",
             "Сценарий: W=1048576, n=39, T=157788000 с, P=0,3145728 с, фиксированные фазы; одиночный пуассоновский закон.",
             "S_pair — приближение, S_safe — доказательная нижняя сумма; вероятность округлена вниз.",
             "Доказывает большой риск этого модельного расписания, не всех адаптивных политик и не реального полёта.", ""]
    rows = []
    for risk in result["peak_risk"]:
        for cells in risk["cells"]:
            rows.append([risk["r_bit_per_s"], f(risk["beta_singleton_parent_per_s"]), cells["gap_s"],
                         f(risk["S_author_pair_approximation"]), cells["S_safe_floor_12dp"], cells["probability_lower_reported_down"]])
    table(lines, ["r, бит⁻¹с⁻¹", "β=λ, с⁻¹", "Зазор, с", "S_pair, 1", "S_safe ≥, 1", "P(A_T) ≥, 1"], rows)
    lines += ["## 2. Два разных пола", "", "Источник: T36 (В1–В2) и кандидат R7 из Issue #44; входы T37 G16/central/published_valid.",
              "Сценарий: одиночная интерпретация, a_min=P, N=501594543; g — выборочная разность, условно используемая как граница.",
              "Единицы U: с⁻¹. Числа — вычисления формул, не оценки истинной λ. Кандидат канала требует доказательства #45.",
              "В строках долей α_* и α_info численно совпадают только для сопоставления: это разные ошибки разных каналов.",
              "Проценты относятся к своему пику: 300 с — B=0,9831128857 с⁻¹; час — B=0,5773020336 с⁻¹.", ""]
    rows = []
    for r in result["counter_and_external"]:
        scale = "300 с" if r["source"].endswith("native") else "час"
        rows.append([scale, r["scenario"], f(r["alpha_star_aux"]), f(r["H"]), f(r["T36_zero_min_upper_s_1"]),
                     f(r["T36_zero_min_upper_percent_of_own_peak"]), f(r["info_zero_candidate_s_1"]),
                     f(r["info_candidate_percent_of_own_peak"]), f(r["T36_zero_point_latency_threshold_s"]),
                     f(r["info_zero_point_latency_threshold_s"])])
    table(lines, ["Масштаб g", "Настройка", "α_*, α_info", "H", "U_T36", "% B", "U_info", "% B", "L*_T36, с", "L*_info, с"], rows)
    lines += ["### Конечные доступные интервалы и ненулевой счётчик", "", "Те же источник/сценарий; α_*=ε/4, H=28,3273523081.",
              "Верхние концы U (с⁻¹) при c=0/1/10, с отсечением по B. Это свойства конструкции, не истинные интенсивности.", ""]
    rows = []
    chosen = [r for r in result["counter_and_external"] if r["scenario"] == "fraction=0.25"]
    for r in chosen:
        for item in r["finite_actions"]:
            rows.append(["300 с" if r["source"].endswith("native") else "час", f(item["a_s"]),
                         *[f(item["upper_s_1_by_count"][str(c)]) for c in (0, 1, 10)]])
    table(lines, ["Масштаб g", "a, с", "U(c=0), с⁻¹", "U(c=1), с⁻¹", "U(c=10), с⁻¹"], rows)
    lines += ["## 3. Внешнее наблюдение", "", "Источник: контракт T37 §5 и те же два G16-входа; идеальные y=e=0, без дополнительных потерь доставки.",
              "Все уровни в с⁻¹. gL — вычисленная добавка; остальные столбцы — условные верхние огибающие с отсечением по B.",
              "Для среднего показана допустимая, не обязательно тесная формула T37 g(h/2+L); GOES-бин не является точкой.",
              "Доказывает только сравнение этих огибающих, не выигрыш полной стоимости η_I и не невозможность улучшить среднюю огибающую.", ""]
    rows = []
    for r in chosen:
        for item in r["latencies"]:
            rows.append(["300 с" if r["source"].endswith("native") else "час", item["L_s"], f(item["gL_s_1"]),
                         f(item["gL_percent_of_own_peak"]), f(item["mean_zero_error_zero_upper_by_h_s_1"]["300"]),
                         f(item["mean_zero_error_zero_upper_by_h_s_1"]["3600"])])
    table(lines, ["Масштаб g", "L, с", "gL (здесь также U_point)", "% своего B", "U_mean, h=300 с", "U_mean, h=3600 с"], rows)
    lines += ["## 4. Относительный рост", "", "Источник: ровно ряды, версии и маски T37. Нативный шаг 300 с; x — модельный отклик на бит, а не непосредственно измеренная λ.",
              "Тип: эмпирический максимум [ln(x₂/x₁)]₊/300. Непрерывновременной/будущей границы он не доказывает.",
              "Для каждой строки обе точки ≥ x_min=f B_sample>0. Числа пар и пересечений точны для выбранных файлов.",
              "Все UTC — начала бинов, не моменты точечного измерения. Список каждого пересечения порога и максимум среди исключённых по порогу — в JSON.", ""]
    for r in result["relative_growth"]:
        a = r["pair_audit"]
        lines += [f"### {r['series']} / {r['direction']} / {r['mask']}", "",
                  f"B_sample={f(r['B_sample_per_bit_s'])} бит⁻¹с⁻¹. Всего соседей {a['total_pairs']}; допустимых положительных {a['valid_positive_same_version_pairs']}; исключено: разрыв {a['excluded_gap']}, версия {a['excluded_version']}, маска {a['excluded_mask']}, неположительные {a['excluded_nonpositive']}.", ""]
        rows = []
        for t in r["thresholds"]:
            w, c = t["maximum"], t["counts"]
            rows.append([f(t["threshold_fraction"]), f(t["threshold_per_bit_s"]), f(w["log_growth_s_1"]) if w else "—",
                         c["both_above"], f"{c['up_crossing']}/{c['down_crossing']}/{c['both_below']}",
                         f"{w['from_utc']} → {w['to_utc']}" if w else "—",
                         f"{f(w['from_per_bit_s'])} → {f(w['to_per_bit_s'])}" if w else "—"])
        table(lines, ["f", "x_min, бит⁻¹с⁻¹", "ρ_sample, с⁻¹", "Пар выше", "Вверх/вниз/обе ниже", "UTC свидетеля", "x₁ → x₂, бит⁻¹с⁻¹"], rows)
    lines += ["## 5. Направление эффекта защиты", "", "Источник: существующий GOES19 proton_rate_5min.csv, те же спектр/время/отклик; маски T37.",
              "Тип: проверка сериализованных модельных выходов, не физическая теорема монотонности и не перенос G19 на G16.",
              "Интенсивности ниже — для старого массива 2²⁴ бит (с⁻¹); отношение безразмерно. В строках с нулевым знаменателем отношение не вычисляется.", ""]
    rows = []
    for r in result["shielding"]:
        p = r["at_1mm_peak"]
        rows.append([r["direction"], r["mask"], r["valid_rows"], r["violations_r1_lt_r3"],
                     r["zero_3mm_rows_ratio_undefined"], f(r["minimum_ratio_1mm_to_3mm"]),
                     p["utc"], f(p["rate_1mm_old_array_s_1"]), f(p["rate_3mm_old_array_s_1"]), f(p["ratio"])])
    table(lines, ["Напр.", "Маска", "Строк", "r1<r3", "r3=0", "min r1/r3", "UTC пика 1 мм", "1 мм, с⁻¹", "3 мм, с⁻¹", "Пиковое отношение"], rows)
    lines += ["## 6. Редкость", "", "Первичный закон числа событий не подтверждён доступным полным текстом: физические среднее, K и δ_K не назначены.",
              "Зарезервированная сетка Пуассона не экспортируется как результат. Функция `poisson_k` и её минимальность проверены модульными тестами; это не принятие закона среды.",
              "Состояние источников, формула условного K и бюджет хвостов — в `conditions.md`, уточнение для автора — в `cosrad_request_draft.md`.", ""]
    return "\n".join(lines)

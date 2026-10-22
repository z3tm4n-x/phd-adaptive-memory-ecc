"""T206: bounded integration, not a second code comparison or physics solver."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def exact(value):
    return None if value is None else str(F(str(value)))


def slack(value, limit):
    if value is None or limit is None:
        return None
    if F(str(limit)) <= 0:
        raise ValueError("a positive declared limit is required")
    return str(1 - F(str(value)) / F(str(limit)))


def decision(upper, lower, epsilon, *, upper_applies=False,
             lower_applies=False, resources=None, incompatible=False):
    """The caller must carry the proved scope; an upper failure proves nothing."""
    eps = F(str(epsilon))
    if eps <= 0 or eps >= 1:
        raise ValueError("epsilon must lie in (0,1)")
    if lower_applies and lower is not None and F(str(lower)) > eps:
        return "PROVED_EXCLUSION_IN_DECLARED_SCOPE"
    if incompatible:
        return "PROVED_EXCLUSION_IN_DECLARED_SCOPE"
    if (upper_applies and upper is not None and F(str(upper)) <= eps
            and resources and all(v is True for v in resources.values())):
        return "SUFFICIENT_IN_DECLARED_SCOPE"
    return "UNKNOWN"


def checks():
    # Decision-critical guards, not a repeat of the accepted scientific tests.
    cases = [
        (decision("0.02", None, ".01", upper_applies=True, resources={"bus": True}), "UNKNOWN"),
        (decision(None, None, ".01", resources={"bus": True}), "UNKNOWN"),
        (decision(".001", None, ".01", upper_applies=True, resources={"bus": None}), "UNKNOWN"),
        (decision(".001", None, ".01", upper_applies=True, resources={}), "UNKNOWN"),
        (decision(".01", None, ".01", upper_applies=True, resources={"bus": True}), "SUFFICIENT_IN_DECLARED_SCOPE"),
        (decision(None, ".01", ".01", lower_applies=True), "UNKNOWN"),
        (decision(None, ".010001", ".01", lower_applies=True), "PROVED_EXCLUSION_IN_DECLARED_SCOPE"),
        (decision(None, ".1", ".01", lower_applies=False), "UNKNOWN"),
        (slack(None, ".8"), None),
        (slack(".64", ".8"), "1/5"),
    ]
    for actual, expected in cases:
        if actual != expected:
            raise AssertionError((actual, expected))
    return len(cases)


def read_sources():
    manifest = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
    data, refs = {}, {}
    for entry in manifest:
        path = ROOT / entry["path"]
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if digest != entry["sha256"] or blob != entry["git_blob"]:
            raise ValueError("pinned source changed: " + entry["path"])
        data[entry["id"]] = raw.decode("utf-8")
        refs[entry["id"]] = {k: entry[k] for k in ("url", "sha256", "git_blob")}
    return data, refs


def unique(rows, predicate, description):
    selected = [r for r in rows if predicate(r)]
    if len(selected) != 1:
        raise ValueError(f"{description}: expected one source row, got {len(selected)}")
    return selected[0]


def blank_resources():
    return {"useful_bytes": None, "active_code_bytes": None,
            "allocated_bus_bytes": None, "installed_device_bytes": None,
            "full_bus_average_upper": None, "full_bus_peak_upper": None,
            "application_delay_upper_s": None, "codec_latency_s": None,
            "codec_memory_bytes": None, "controller_memory_bytes": None,
            "CPU_fraction": None, "LUT": None, "BRAM": None, "energy_J": None}


def build():
    test_count = checks()
    inp = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
    raw, refs = read_sources()
    old = json.loads(raw["map126"])
    basis = json.loads(raw["basis"])
    a2source = json.loads(raw["a2"])
    cfg1 = json.loads(raw["a1_config"])
    common = json.loads(raw["common"])
    a1 = unique(old["rows"], lambda r: r["id"] == inp["selectors"]["A1"], "A1")
    a1lower = unique(old["rows"], lambda r: r["id"] == inp["selectors"]["A1_exclusion"], "A1 lower")
    a2 = unique(basis["entries"], lambda r: r["id"] == inp["selectors"]["A2"], "A2")
    if a1["status"] != "constant_sufficient" or not a1lower["constant_excluded_T58"]:
        raise ValueError("source status is not the selected accepted status")
    if F(a1lower["Q_lower_at_budget"]) <= F(a1lower["epsilon"]):
        raise ValueError("an exclusion needs a strict applicable lower")

    r1 = blank_resources()
    r1.update(useful_bytes=a1["W"] * 4, active_code_bytes=exact(F(a1["W"] * a1["n"], 8)),
              full_bus_average_upper=a1["full_bus_mission_upper"],
              full_bus_peak_upper=a1["all_bus_peak_upper"],
              application_delay_upper_s=a1["resource"]["delay_upper"])
    a1limits = cfg1["reference_point_rule"]["table_resources"]
    r2 = blank_resources()
    r2.update(useful_bytes=a2["radiation"]["W"]["value"] * 4,
              active_code_bytes=exact(F(a2["radiation"]["W"]["value"] * 39, 8)),
              full_bus_average_upper=a2source["budgets"]["full_bus_fixed_upper"],
              application_delay_upper_s=a2["fixed"]["metrics"]["response"]["value"])

    def unknown_group(group, name, scope, missing, source):
        return dict(group=group, name=name, status="UNKNOWN", scope=scope,
                    physical_status="UNKNOWN", Q_upper=None, Q_lower=None,
                    probability_slack=None, time_margin=None, resource_margin=None,
                    resources=blank_resources(), missing=missing, source=refs[source])

    groups = [
        dict(group="A1", name="Малая память: постоянный U", status="SUFFICIENT_IN_SOURCE_SCOPE",
             scope=a1["domain"], physical_status=a1["qualification"], source_id=a1["id"],
             source=refs["map126"], T_s=a1["T"], epsilon=a1["epsilon"],
             Q_upper=a1["Q_upper"], Q_lower=a1["Q_lower_at_budget"],
             Q_lower_scope=a1["Q_lower_scope"], period_s=a1["selected_period"],
             probability_slack=str(F(a1["epsilon"]) - F(a1["Q_upper"])),
             probability_margin=slack(a1["Q_upper"], a1["epsilon"]),
             time_margin=slack(a1["resource"]["delay_upper"], a1limits["delay_s"]),
             resource_margin={"protection_peak": slack(a1["resource"]["peak_upper"], a1limits["peak"]),
                              "whole_bus": None, "hardware": None},
             resources=r1, application=a1["application"], cost_scope=a1["cost_scope"],
             missing=a1["missing_inputs"],
             exclusion_witness={"source_id": a1lower["id"], "status": "PROVED_EXCLUSION_IN_SOURCE_FIXED_CLASS",
                                "Q_lower": a1lower["Q_lower_at_budget"], "epsilon": a1lower["epsilon"],
                                "scope": a1lower["Q_lower_scope"], "quiet_budget": a1lower["quiet_budget"],
                                "is_new_206_exclusion": False}),
        dict(group="A2", name="Большая диагностическая память", status="SUFFICIENT_FIXED_IN_SOURCE_SCOPE",
             scope=a2["fixed"]["class_name"], physical_status="conditional_diagnostic",
             source=refs["basis"], source_id=a2["id"], T_s=a2["radiation"]["T"]["value"],
             epsilon=a2["radiation"]["epsilon"]["value"],
             Q_upper=a2["fixed"]["metrics"]["Q_upper"]["value"], Q_lower=None,
             probability_slack=str(F(a2["radiation"]["epsilon"]["value"]) - F(a2["fixed"]["metrics"]["Q_upper"]["value"])),
             probability_margin=slack(a2["fixed"]["metrics"]["Q_upper"]["value"], a2["radiation"]["epsilon"]["value"]),
             time_margin=None, resource_margin={"protection_peak": slack(a2["fixed"]["metrics"]["peak"]["value"], a2source["inputs"]["peak"]), "whole_bus": None, "hardware": None},
             resources=r2, fixed_price_interval={"lower": a2["fixed"]["metrics"]["L_fixed"], "upper": a2["fixed"]["metrics"]["witness_price"]},
             adaptive_status="UNKNOWN_COMPLETE_CONTROLLER", layer_gain_upper=a2["metrics"]["pointwise_gain_upper"],
             layer_scope="T57 pointwise layer only; excludes 5x within that layer, not all adaptive methods",
             application=a2["useful_work"], missing=a2["gaps"]),
        unknown_group("A3", "CY: новый полный отклик", "new physical candidate; old R0-A contracts separate",
                      inp["physical_candidate"]["blockers"], "passport141"),
        unknown_group("A4", "Другая SRAM: EV30LL-45ZXA/1843", "source candidate; 1525 is not pooled",
                      ["same-datecode numerical HEP/PDI upper with counts/fluence", "package-angle transfer", "external full-word marks and service"], "sources126"),
        unknown_group("A5", "LEO/положение: SAC-C", "position/time online; ICARE offline validation only",
                      list(old["missing_orbital_inputs"]), "sources126"),
    ]
    # No imported sufficiency is silently extended to unknown hardware coordinates.
    for row in groups:
        row["hardware_choice_complete"] = False
        row["scope_of_status"] = "original declared model; not physical qualification or new hardware acceptance"

    p = inp["physical_candidate"]
    for row in groups[2:4]:
        row["T_s"] = p["mission_s"]
        row["epsilon"] = p["epsilon"]
        row["requirement_status"] = "proposed search candidate, not a device property"
    if p["useful_bytes"] * 8 != p["selected_words"] * p["data_bits"]:
        raise ValueError("useful capacity/whole-word mismatch")
    factor = F(p["selected_words"], p["source_words"])
    shape_rows = list(csv.DictReader(io.StringIO(raw["shape"])))
    sensitivity = []
    for shield in inp["selectors"]["shields"]:
        for choice in ("rectangle", inp["selectors"]["shape_choice"]):
            s = unique(shape_rows, lambda r: F(r["shield_g_cm2"]) == F(shield)
                       and r["response_case"] == "full" and r["choice"] == choice
                       and (choice == "rectangle" or r["mean_events"] == inp["selectors"]["shape_mean_events"]), "T150 full row")
            sensitivity.append(dict(shield_g_cm2=shield, choice=choice, source_words=p["source_words"],
                                    source_F=s["F"], source_S2_s_inv=s["S2_s_inv"],
                                    conditional_selected_F=str(F(s["F"]) * factor),
                                    conditional_selected_S2_s_inv=str(F(s["S2_s_inv"]) * factor * factor),
                                    evidence="OWN_RESULT_ALGEBRA_ON_SAVED_DECIMALS_UNDER_ASSUMPTION",
                                    basis=s["basis"], Q_upper=None, physical_sufficient=False))
    selected_active_bytes = p["selected_words"] * p["code_bits"] // 8
    groups[2]["resources"].update(useful_bytes=p["useful_bytes"], active_code_bytes=selected_active_bytes,
                                  allocated_bus_bytes=p["useful_bytes"], installed_device_bytes=p["installed_data_bytes"])
    groups[3]["resources"].update(useful_bytes=p["alternative"]["useful_bytes"],
                                  allocated_bus_bytes=p["alternative"]["allocated_bytes"])
    # 90% environment coverage is a diagnostic total-probability calculation only.
    coverage_diagnostic = F(1, 10) + F(9, 10) * F(p["epsilon"])

    if [x["id"] for x in common["codes"]] != inp["common_comparison"]["code_row_ids"]:
        raise ValueError("the single upstream comparison changed identity")
    if common["useful_bytes"] != p["useful_bytes"] or common["words"] != p["selected_words"]:
        raise ValueError("common useful capacity mismatch")
    if common["environment"]["physical_group2_rate"] is not None:
        raise ValueError("this snapshot must retain the unknown physical group rate")
    integrated = dict(inp["common_comparison"])
    integrated["input_sha256"] = refs["common"]["sha256"]
    integrated["status"] = "UNKNOWN_PENDING_NUMERICAL_TABLE_AND_MATCHING_THEORY_SIGNATURE"
    integrated["table_url"] = ("https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/"
                               + integrated["head"] + "/" + integrated["table_path"])
    integrated["blocking_nulls_in_snapshot"] = [
        path for path, val in {
            "initial.K0": common["initial"]["K0"],
            "lifetime_other_budget": common["lifetime_other_budget"],
            "service.decode39_ns": common["service"]["decode39_ns"],
            "service.decode44_ns": common["service"]["decode44_ns"],
            "adaptive.new_n39_risk_certificate": common["adaptive"]["new_n39_risk_certificate"],
            "fixed.period39_s": common["fixed"]["period39_s"],
            "fixed.period44_s": common["fixed"]["period44_s"],
            "fixed.class_lower39": common["fixed"]["class_lower39"],
            "fixed.class_lower44": common["fixed"]["class_lower44"],
        }.items() if val is None]
    integrated["null_semantics"] = "unknown coefficients may remain parameters with proved thresholds; absent certificate is not sufficiency"
    return dict(task=206, status=inp["status"], plan_commit=inp["plan_commit"],
                groups=groups, source_grid_summary=old["summary"],
                preserved_accepted_anchors=[{k: r[k] for k in ("id", "status", "environment", "service", "price_metric", "gaps")} for r in basis["entries"]],
                physical_candidate=p, conditional_capacity_scaling={"factor_lambda_F": str(factor),
                "factor_S2": str(factor * factor), "selected_active_code_bytes": selected_active_bytes,
                "installed_active_code_bytes_if_full38": p["source_words"] * p["code_bits"] // 8,
                "assumption": p["capacity_scaling_assumption"], "source": refs["shape"], "rows": sensitivity},
                coverage_diagnostic={"formula": "delta+(1-delta)*q", "delta": "1/10", "q": p["epsilon"],
                                     "upper": str(coverage_diagnostic), "physical_bound_claimed": False},
                common_comparison=integrated, known_schemes=inp["known_schemes"],
                checks={"pinned_sources": len(refs), "decision_guards": test_count, "unique_full_response_rows": len(sensitivity)},
                sources=refs)


def approx(x):
    return "UNKNOWN" if x is None else f"{float(F(str(x))):.9g}"


def render(result):
    lines = ["# #206 — первый срез карты", "", "Сгенерировано reproduce.py; научная приёмка не заявлена.",
             "Статусы A1/A2 сохранены в исходных условных областях. Цифры ниже округлены для чтения; точные исходные значения — map.json.", "",
             "| Группа | Статус и область | Q upper / ε | Следующее решение |",
             "|---|---|---|---|"]
    actions = {"A1": "Достаточно постоянного в исходной модели; полный hardware выбор открыт",
               "A2": "Постоянный допустим; 5× исключено только в слое T57",
               "A3": "Полная физическая цепочка не замкнута; общий кодовый эталон отдельный",
               "A4": "Нужен numerical upper/marks ревизии 1843; не объединять с 1525",
               "A5": "Нет общего численного и online договора положения"}
    for row in result["groups"]:
        lines.append(f"| {row['group']} | {row['status']} | {approx(row['Q_upper'])} / {row.get('epsilon','UNKNOWN')} | {actions[row['group']]} |")
    lines += ["", "Полные поля ёмкости, цены, ограничений и неизвестных — map.json. Неизвестный hardware ресурс не считается нулевым.",
              "A1 включает также ссылку на принятое необходимое исключение другой ячейки; оно не переносится на достаточную ячейку.", "",
              "## Отдельная чувствительность физического кандидата", "",
              "Условие: те же per-bit отклик и целые однородные full38 слова; W меняется 524288→131072.",
              "λ и F умножены на 1/4, S₂ — на 1/16. Это алгебра над готовыми T150, не новая Q и не физический перенос.", "",
              "| Al, г/см² | Форма | F исходное → выбранная область | S₂ исходное → выбранная область, с⁻¹ |",
              "|---|---|---|---|"]
    for row in result["conditional_capacity_scaling"]["rows"]:
        lines.append(f"| {row['shield_g_cm2']} | {row['choice']} | {approx(row['source_F'])} → {approx(row['conditional_selected_F'])} | {approx(row['source_S2_s_inv'])} → {approx(row['conditional_selected_S2_s_inv'])} |")
    lines += ["", "Все строки full: низкая H-полоса сохранена. model_r_q90 — модельный перенос формы при фиксированных COSRAD b/p/F; не joint-q90 миссии.",
              "У кандидата 4 г/см² Q upper/lower и все физические запасы UNKNOWN. Старый D* не подставлен.", "",
              "## Общая таблица", "", f"[Единственная таблица #186]({result['common_comparison']['table_url']}).",
              "В карту переносится ссылка/версия и состояние входа; копии трёх сравнительных строк здесь нет.",
              "Блокирующие незаполненные поля снимка: " + ", ".join(result["common_comparison"]["blocking_nulls_in_snapshot"]) + ".", "",
              "Неизвестные времена допустимы как параметры с порогами. До подписи области Q и общего бюджета выбор остаётся неизвестным.",
              "Доказательные известные схемы поступают от #186/#196 к03.11, здесь повторный поиск не выполняется.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="write only this task's generated outputs")
    group.add_argument("--check", action="store_true", help="compare generated bytes without changing files")
    args = parser.parse_args()
    result = build()
    outputs = {"map.json": json.dumps(result, ensure_ascii=False, indent=2) + "\n", "map.md": render(result)}
    if args.write:
        (HERE / "outputs").mkdir(exist_ok=True)
        for name, data in outputs.items():
            (HERE / "outputs" / name).write_bytes(data.encode("utf-8"))
    else:
        for name, data in outputs.items():
            if (HERE / "outputs" / name).read_bytes() != data.encode("utf-8"):
                raise ValueError("generated output differs: " + name)
    print(json.dumps({"result": "reproduced", **result["checks"],
                      "outputs_sha256": {name: hashlib.sha256(data.encode()).hexdigest() for name, data in outputs.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()

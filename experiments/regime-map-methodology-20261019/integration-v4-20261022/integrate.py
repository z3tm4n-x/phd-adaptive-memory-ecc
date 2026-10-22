"""Read pinned upstream results; derive map gates, not probability certificates.

Python stdlib only. Sources come from Git objects or an exported byte-exact pack.
No import of numerical/theoretical modules, network access or upstream writes.
"""

import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
IDS = ("t1_constant", "t1_adaptive", "t2_constant")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decimal_down(value, places=12):
    """Exact decimal floor, including negative margins."""
    scale = 10**places
    n = F(value).numerator * scale // F(value).denominator
    sign = "-" if n < 0 else ""
    whole, frac = divmod(abs(n), scale)
    return f"{sign}{whole}.{frac:0{places}d}"


def risk_status(upper, epsilon):
    # No probability lower or proved incompatibility is imported here.
    return "SUFFICIENT_CONDITIONAL_Q" if F(upper) <= epsilon else "UNKNOWN"


def load_sources(manifest, source_dir):
    raw = {}
    for key, pin in manifest["sources"].items():
        if source_dir:
            data = (source_dir / (key + ".source")).read_bytes()
        else:
            data = subprocess.check_output(
                ["git", "cat-file", "blob", pin["commit"] + ":" + pin["path"]], cwd=HERE
            )
        require(hashlib.sha256(data).hexdigest() == pin["sha256"],
                f"source SHA256 mismatch: {key}")
        blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        require(hashlib.sha1(blob).hexdigest() == pin["git_blob"],
                f"source Git blob mismatch: {key}")
        raw[key] = data
    return raw


def build(manifest, raw):
    inp, result, review, sensitivity = (
        json.loads(raw[k]) for k in ("input", "results", "review_result", "sensitivity")
    )
    original = json.loads(raw["original_results"])
    repair = json.loads(raw["repair_validation"])
    pins = manifest["sources"]
    epsilon = F(inp["epsilon"])
    rows = result["rows"]
    require(set(rows) == set(IDS), "three candidate IDs changed")
    require(result["common_input_sha256"] == pins["input"]["sha256"]
            == review["input_sha256"], "input/review identity mismatch")
    require(result["service_contract_sha256"] == pins["service"]["sha256"],
            "result/service identity mismatch")
    require(review["reviewed_head"] == pins["original_results"]["commit"],
            "review applies to another numerical head")
    require(repair["reviewed_snapshot"] == review["reviewed_head"]
            and repair["theory_review"] == pins["review"]["commit"], "R1 review mismatch")
    require(repair["frozen_output_sha256"]["informational.json"] == pins["certificate"]["sha256"]
            and repair["frozen_output_sha256"]["sensitivity.json"] == pins["sensitivity"]["sha256"],
            "certificate or group slices changed")
    require(inp["revision"] == 4 and inp["words"] == 131072
            and inp["useful_bytes"] == 524288, "common geometry changed")
    require(not inp["application"]["read_repair"]
            and not inp["application"]["ordinary_read_publishes_ERR_G"]
            and inp["application"]["prewrite_publishes_ERR_G"],
            "observability/service changed")
    require(inp["environment"]["baseline_p_s"] == {"1": "1"}, "not singleton")
    require(all(v is None for v in inp["constraints"]["capacity_caps"].values()),
            "new hardware caps need an explicit map decision")
    require(inp["risk_budget"]["physical_delta_env"] is None
            and inp["risk_budget"]["physical_delta_init"] is None,
            "physical status requires review")

    gates = {}
    for key in IDS:
        row = rows[key]
        q = F(row["risk"]["upper"])
        require(row["risk"] == review["risk"][key], f"Q signature mismatch: {key}")
        require(all(row[field] == original["rows"][key][field] for field in
                    ("risk", "period", "timing", "k_passes", "mandatory_risk_diagnostic")),
                "R1 changed probability, timing or candidate")
        require(row["cost"]["adaptive"] == original["rows"][key]["cost"]["adaptive"],
                "R1 changed read/hold/timers")
        require(F(row["cost"]["core_SRAM_fraction_upper"]) ==
                F(review["minimal_safe_repair"][key]["safe_SRAM_upper"])
                and F(row["cost"]["repair_count_upper"]) ==
                F(review["minimal_safe_repair"][key]["safe_repair_upper"]),
                "author R1 differs from signed safe coefficients")
        require(row["class_optimum_lower"] is None, "new class lower requires review")
        require(all(row["cost"][flag] for flag in
                    ("after_A_paid", "bad_history_paid", "pending_paid")),
                "lifetime cost scope lost")
        timing = row["timing"]
        response, peak = F(timing["app_response_upper_ns"]), F(timing["peak_bus_core_upper"])
        deadline = F(inp["constraints"]["application_deadline_ns"])
        peak_cap = F(inp["constraints"]["peak_bus_fraction"])
        gates[key] = {
            "source": "results#/rows/" + key,
            "Q_signature": "review_result#/risk/" + key,
            "conditional_Q_status": risk_status(q, epsilon),
            "risk_margin_lower": str(epsilon - q),
            "risk_margin_fraction_lower": str(1 - q / epsilon),
            "risk_target_met": q <= epsilon / 2,
            "risk_target_remaining_lower": str(epsilon / 2 - q),
            "response_margin_fraction_lower": str(1 - response / deadline),
            "peak_margin_fraction_lower": str(1 - peak / peak_cap),
            "response_target_met": response <= inp["constraints"]["map_targets"]["response_ns"],
            "peak_target_met": peak <= F(inp["constraints"]["map_targets"]["peak_bus_fraction"]),
            "core_hard_timing_constraints_met": response <= deadline and peak <= peak_cap,
            "whole_implementation_status": "UNKNOWN",
            "physical_status": "UNKNOWN",
            "class_optimum_lower": None,
            "ordinary_cost_status": "author R1 matches coauthor repair/SRAM coefficients; acceptance pending",
            "candidate_cost_lower_scope": row["cost"]["lower_scope"],
        }

    mandatory = F(rows["t1_adaptive"]["mandatory_risk_diagnostic"]["upper"])
    require(mandatory > epsilon and F(rows["t1_adaptive"]["risk"]["upper"]) < epsilon / 2,
            "information/mandatory distinction changed")
    fixed_lower = F(rows["t1_constant"]["cost"]["core_SRAM_fraction_lower"])
    adaptive_lower = F(rows["t1_adaptive"]["cost"]["core_SRAM_fraction_lower"])
    t2_hard = F(rows["t2_constant"]["cost"]["all_history_SRAM_core_upper"])
    hard_gap = adaptive_lower - t2_hard
    require(hard_gap == F(review["robust_t2_hard_comparison_gap"]), "hard gap mismatch")
    safe_adaptive = F(review["minimal_safe_repair"]["t1_adaptive"]["safe_SRAM_upper"])
    slope = F(rows["t1_adaptive"]["cost"]["veto_core_fraction_slope_per_notification_per_s"])
    adaptive_gap = fixed_lower - safe_adaptive
    require(adaptive_gap / slope == F(review["safe_extra_veto_threshold_per_s"]),
            "reviewed veto threshold mismatch")
    require(F("1057.380") < adaptive_gap / slope and hard_gap > 0,
            "published conservative comparisons no longer follow")

    selected = []
    require(len(sensitivity) == 12, "sensitivity grid changed")
    for pair in manifest["sensitivity_pairs"]:
        matches = [(i, s) for i, s in enumerate(sensitivity)
                   if [F(s["p_s"]["2"]), F(s["p_s"]["3"])] == list(map(F, pair))]
        require(len(matches) == 1, "ambiguous sensitivity locator")
        i, case = matches[0]
        require(F(case["risk"]["t1_adaptive"]["upper"]) > epsilon,
                "diagnostic outcome changed; examine before updating narrative")
        selected.append({
            "source": f"sensitivity#/{i}", "p2": pair[0], "p3": pair[1],
            "Q_review_scope": "author numerical sensitivity; coauthor signed formula applicability, no claim of checking all 12 numbers",
            "fixed_Q_gates": {key: {
                "status": risk_status(case["risk"][key]["upper"], epsilon),
                "risk_target_met": F(case["risk"][key]["upper"]) <= epsilon / 2,
            } for key in ("t1_constant", "t2_constant")},
            "adaptive_mandatory_gate": "UNKNOWN",
            "adaptive_information_gate": "SEE_BASELINE" if pair == ["0", "0"] else "UNKNOWN",
            "price_transfer_from_singleton": False,
            "physical_status": "UNKNOWN", "class_exclusion": False,
        })
    require(F(sensitivity[0]["risk"]["t1_adaptive"]["upper"]) == mandatory,
            "diagnostic singleton substituted for information certificate")

    return {
        "task": 206, "scope": "A3 conditional code/mode overlay; A1-A5 and physical candidate unchanged",
        "publication": manifest["publication"],
        "upstream_table": pins["table"]["url"],
        "numerical_commit": pins["results"]["commit"],
        "coauthor_review_commit": pins["review"]["commit"],
        "input_sha256": pins["input"]["sha256"],
        "source_pointer_syntax": "source key in sources.json, then RFC6901 JSON pointer after #",
        "field_routes": {
            "useful_volume_layout_lifetime_application": "input#/",
            "codeword_and_period": "results#/rows/{candidate}",
            "risk_bounds_terms": "results#/rows/{candidate}/risk",
            "average_bus_and_all_history": "results#/rows/{candidate}/cost",
            "peak_bus_response_and_decode_limits": "results#/rows/{candidate}/timing",
            "codec_architecture_ROM_XOR_unknown_LUT_BRAM": "results#/resources/{t}",
            "CPU_energy_traffic_control_memory": "results#/rows/{candidate}/cost",
            "ordinary_repair_correction": "review_result#/minimal_safe_repair and repair_note",
            "capacity_units_and_packing": "table (the sole comparison table)",
        },
        "candidate_gates": gates,
        "decision_boundaries": {
            "t2_vs_selected_adaptive_SRAM": {
                "condition": "B_controller_average(t2)-B_controller_average(adaptive) < gap",
                "gap_fraction_lower": str(hard_gap),
                "basis": "hard t2 upper versus selected adaptive mandatory lower; independent of R1 and v",
                "global_winner": None,
            },
            "adaptive_vs_selected_t1_fixed_SRAM": {
                "condition": "slope*v + B_controller_average(adaptive)-B_controller_average(t1_fixed) < gap",
                "gap_fraction_lower": str(adaptive_gap), "slope_per_veto_per_second": str(slope),
                "sufficient_veto_rate_if_equal_other_bus_costs": "v < 1057.380 /s",
                "unknown_v_uses": "results#/rows/t1_adaptive/cost/all_history_SRAM_core_upper",
                "basis": "review_result#/minimal_safe_repair/t1_adaptive/safe_SRAM_upper",
                "fixed_class_lower": None,
            },
        },
        "selected_group_slices": selected,
        "unknown_caps": inp["constraints"]["capacity_caps"],
        "physical_unpaid_probabilities": {"delta_env": None, "delta_init": None},
        "new_group_information_theory_requested": False,
        "checks": ["fourteen exact source hashes and blobs", "input/service/review identity",
                   "three Q signatures without recomputation", "whole-horizon candidate scope",
                   "mandatory versus informational singleton", "two signed SRAM gap identities",
                   "four preselected group locators including joint corner", "unknown caps/physical bounds preserved",
                   "R1 matches coauthor repair/SRAM coefficients; Q/timers/groups unchanged"],
    }


def render(out):
    boundaries = out["decision_boundaries"]
    cross = boundaries["t2_vs_selected_adaptive_SRAM"]
    same = boundaries["adaptive_vs_selected_t1_fixed_SRAM"]
    lines = ["# Подключение v4 к карте #206", "",
             "Это указатель и правила выбора; [единственная численная таблица](" + out["upstream_table"] + ") — у #186.",
             "Три Q имеют соавторскую подпись #196 к0111d424; R1 исправлен автором вffb5d29a. Исправленные repair/SRAM коэффициенты совпали с #196. Научная приёмка впереди.", "",
             "## Условия выбора", "",
             "- t2-fixed дешевле предъявленной adaptive по SRAM, если разность дополнительных средних bus-затрат t2−adaptive меньше **"
             + decimal_down(F(cross["gap_fraction_lower"]) * 100, 9)
             + " процентного пункта**. Это консервативный порог hard-upper/lower; сохранять окна и остальные caps обязательно.",
             "- При одинаковом t1 информационная adaptive дешевле предъявленной fixed, если `gamma*v + delta_B < G`. Здесь `G >= "
             + decimal_down(same["gap_fraction_lower"]) + "` полного времени; точная gamma указана в integration.json. При delta_B=0 достаточно v<1057.380/с. Неизвестный v требует hard-upper.",
             "- Ни одно сравнение не использует lower всего fixed-класса. Общая допустимость/победитель по CPU, памяти, LUT/BRAM и энергии — UNKNOWN.", "",
             "## Запасы относятся к условному ядру", ""]
    for key in IDS:
        gate = out["candidate_gates"][key]
        lines.append(f"- {key}: m_Q≥{decimal_down(F(gate['risk_margin_fraction_lower'])*100, 6)}%; "
                     f"m_response≥{decimal_down(F(gate['response_margin_fraction_lower'])*100, 6)}%; "
                     f"m_peak≥{decimal_down(F(gate['peak_margin_fraction_lower'])*100, 6)}%. "
                     "Остальные ресурсные запасы неизвестны.")
    lines += ["", "Все Q проходят цель половины допуска. Опубликованные response-upper не подтверждают20% запаса ни в одной строке; peak-upper t2 тоже. Жёсткие3мкс/80% проходят только для объявленного ядра.", "",
              "## Четыре заранее выбранных среза", ""]
    for case in out["selected_group_slices"]:
        fixed = case["fixed_Q_gates"]
        sufficient = [k for k, v in fixed.items() if v["status"] == "SUFFICIENT_CONDITIONAL_Q"]
        lines.append(f"- p2={case['p2']}, p3={case['p3']} ({case['source']}): fixed-Q достаточен для "
                     + ", ".join(sufficient) + ". Информационная adaptive: " + case["adaptive_information_gate"]
                     + "; mandatory-upper не даёт достаточности и не доказывает невозможность.")
    lines += ["", "При ненулевых группах старые singleton-цены не переносятся. Эти срезы задают область вопросов, а не новую физическую границу p_s.",
              "Числа групповых срезов — авторская поставка; #196 проверил применимость формул, но повтор всех12 численных срезов здесь не заявляется.",
              "Принятые A1–A5 и GE30/full38-кандидат остаются в исходном отчёте. Ни физические UNKNOWN, ни приёмка не заменены численным запасом.", "",
              "Воспроизведение: `python -B experiments/regime-map-methodology-20261019/integration-v4-20261022/integrate.py --check`.", ""]
    return "\n".join(lines).encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--export-sources", type=Path)
    args = parser.parse_args()
    manifest = json.loads((HERE / "sources.json").read_bytes())
    raw = load_sources(manifest, args.source_dir)
    if args.export_sources:
        args.export_sources.mkdir(parents=True, exist_ok=False)
        for key, data in raw.items():
            (args.export_sources / (key + ".source")).write_bytes(data)
    out = build(manifest, raw)
    generated = {"integration.json": (json.dumps(out, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
                 "DECISIONS.md": render(out)}
    for name, data in generated.items():
        path = HERE / name
        if args.write:
            path.write_bytes(data)
        else:
            require(path.read_bytes() == data, f"output differs: {name}; inspect before --write")
    print(json.dumps({"verified_sources": len(raw), "integration_checks": out["checks"],
                      "outputs": {k: hashlib.sha256(v).hexdigest() for k, v in generated.items()}}, indent=2))


if __name__ == "__main__":
    main()

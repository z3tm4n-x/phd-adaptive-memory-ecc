"""Invert an accepted conditional bound; no probability-model/service imports."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sources(manifest, source_dir, pdf_dir):
    raw = {}
    for key, pin in manifest["sources"].items():
        data = ((source_dir / (key + ".source")).read_bytes() if source_dir else
                subprocess.check_output(["git", "cat-file", "blob", pin["commit"] + ":" + pin["path"]], cwd=HERE))
        require(hashlib.sha256(data).hexdigest() == pin["sha256"], "source drift: " + key)
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        require(hashlib.sha1(blob).hexdigest() == pin["git_blob"], "Git blob drift: " + key)
        raw[key] = data
    for name, pin in manifest["pdfs"].items():
        data = (pdf_dir / name).read_bytes()
        require(hashlib.sha256(data).hexdigest() == pin["sha256"], "PDF drift: " + name)
    return raw


def cube_root_bracket(value, places):
    """Adjacent decimal rationals enclosing the positive cube root, exactly."""
    require(value > 0 and 1 <= places <= 18, "invalid root request")
    scale = 10 ** places
    numerator = value.numerator * scale ** 3
    denominator = value.denominator
    lo, hi = 0, 1
    while hi ** 3 * denominator <= numerator:
        hi *= 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if mid ** 3 * denominator <= numerator:
            lo = mid
        else:
            hi = mid
    lower, upper = F(lo, scale), F(hi, scale)
    require(lower ** 3 <= value < upper ** 3, "root is not directed")
    def fmt(integer):
        return f"{integer // scale}.{integer % scale:0{places}d}"
    return lower, upper, fmt(lo), fmt(hi)


def datecode(value):
    require(len(value) == 4 and value.isdigit(), "date-code format")
    year, week = 2000 + int(value[:2]), int(value[2:])
    require(1 <= week <= 53, "date-code week")
    return year, week


def build(inp, raw):
    cfg, app, theory = (json.loads(raw[k]) for k in ("common", "app_result", "theory_result"))
    sha = hashlib.sha256(raw["common"]).hexdigest()
    require(sha == app["common_input_sha256"] == theory["input_sha256"], "input mismatch")
    require(app["Q_upper"] == theory["theorem_substitution"]["Q_upper"], "accepted Q mismatch")
    require(app["risk"]["moments"] == theory["theorem_substitution"]["moment_caps"], "moment caps mismatch")
    admission = inp["physical_admission"]
    require(all(v is None or v is False or v == "UNKNOWN" for v in admission.values()),
            "no physical certificate is supplied by this inversion")
    require(not inp["date_code_evidence"]["conflict_resolved"], "date-code conflict cannot be silently resolved")
    require(inp["date_code_evidence"]["HEP_Fig5_exact_date_code"] is None, "HEP date code needs new source")
    require(not inp["status"]["new_EV30_Q_or_comparison_table"], "no new EV30 Q row")

    epsilon = F(cfg["epsilon"])
    delta = F(app["risk"]["terms"]["lifetime_exceptions"])
    component = F(app["Q_upper"]) - delta
    require(component > 0 and app["risk"]["upper"] == app["risk"]["unclipped"], "need positive unclipped accepted bound")
    require(F(app["risk"]["terms"]["direct"]) == F(app["risk"]["terms"]["initial"]) == 0,
            "reference is not clean singleton")
    rows = []
    for alpha_text in inp["inversion"]["alpha_targets"]:
        alpha = F(alpha_text)
        require(0 < alpha <= 1, "invalid risk target")
        for beta_text in inp["inversion"]["extra_beta_over_epsilon"]:
            beta = epsilon * F(beta_text)
            require(beta >= 0, "negative exception budget")
            available = alpha * epsilon - delta - beta
            require(available > 0, "no remaining singleton budget")
            limit_cube = available / component
            lo, hi, lo_text, hi_text = cube_root_bracket(limit_cube, inp["inversion"]["root_decimal_places"])
            require(delta + beta + component * lo ** 3 <= alpha * epsilon,
                    "lower decimal is not sufficient")
            require(delta + beta + component * hi ** 3 > alpha * epsilon,
                    "upper decimal did not cross certificate boundary")
            rows.append({"target_over_epsilon": alpha_text, "extra_beta": str(beta),
                         "c_limit_cubed": str(limit_cube), "c_limit_lower": lo_text,
                         "c_limit_upper": hi_text, "status": "SUFFICIENT_INPUT_THRESHOLD_ONLY_IF_ALL_PREMISES_CERTIFIED"})

    dc = inp["date_code_evidence"]
    ac = {name: datecode(inp["selected_date_code"]) >= datecode(dc[name])
          for name in ("AN13842_fixed_from", "AN66311_fixed_from")}
    require(all(ac.values()), "selected code precedes cited AC fixes")
    T = F(cfg["mission_s"])
    counts = {name: str(F(app["full_price"]["full_cost_rates"][name]) * T)
              for name in ("application_reads", "application_writes", "decodes", "encodes",
                           "read_beats", "write_beats", "initialization")}
    require(app["full_price"]["post_A_and_bad_history_work_paid"]
            and app["full_price"]["full_started_work_and_pending_paid"], "price horizon is incomplete")
    target = F(inp["cost"]["resource_target_fraction"])
    rom = app["full_price"]["codec_resources"]["lookup_bytes"]
    return {
        "status": inp["status"], "physical_admission": admission,
        "source_identity": {"input_sha256": sha, "accepted_bound": "app_result#/Q_upper",
                            "source_formula": "theory equation(1), fixed P/D and singleton/clean causal E",
                            "reference_Delta": str(delta), "reference_singleton_component": str(component)},
        "thresholds": rows,
        "formula": "c^3 <= (alpha*epsilon - Delta_ref - beta)/(U_ref - Delta_ref)",
        "required_certificate": inp["inversion"],
        "AC_date_code_only": {"published_fix_thresholds_met": ac, "full_die_or_radiation_equivalence_proved": False},
        "source_conflict": dc,
        "cost_boundaries": {"published_ROM_bytes": rom, "ROM_only_capacity_for_20_percent_reserve_bytes": str(F(rom) / target),
                            "full_memory_condition": "ROM + M_other <= 0.8 * M_cap; M_other unknown, specific architecture only",
                            "mission_s": str(T), "imported_core_action_counts_including_prefix": counts,
                            "energy_condition": "T*P_idle + sum(N_i*e_i) + E_other <= alpha_E*E_cap; alpha_E=1 or declared reserve target; all terms disjoint",
                            "action_energy_threshold": "e_j <= (alpha_E*E_cap - T*P_idle - E_other - sum(i!=j,N_i*e_i))/N_j",
                            "EV30_numeric_energy_or_bus": None,
                            "note": "counts imported from #186 for unchanged offered workload/full RMW; controller/grant/frame changes remain with #186"},
        "checks": ["five exact Git sources and six PDF hashes", "accepted input, bound and moment caps agree",
                   "both directed sides of six scalar certificate thresholds", "published date-code limits only",
                   "no asserted physical certificate or date-code reconciliation", "source price covers prefix/post-A/pending"],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pdf-dir", type=Path, required=True)
    p.add_argument("--source-dir", type=Path)
    p.add_argument("--export-sources", type=Path)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = p.parse_args()
    m_bytes, i_bytes = ((HERE / name).read_bytes() for name in ("sources.json", "inputs.json"))
    raw = sources(json.loads(m_bytes), args.source_dir, args.pdf_dir)
    if args.export_sources:
        args.export_sources.mkdir(parents=True, exist_ok=False)
        for key, data in raw.items():
            (args.export_sources / (key + ".source")).write_bytes(data)
    output = build(json.loads(i_bytes), raw)
    output["provenance"] = {"inputs_sha256": hashlib.sha256(i_bytes).hexdigest(),
                            "manifest_sha256": hashlib.sha256(m_bytes).hexdigest()}
    data = (json.dumps(output, ensure_ascii=False, indent=2) + "\n").encode()
    path = HERE / "thresholds.json"
    if args.write:
        path.write_bytes(data)
    else:
        require(path.read_bytes() == data, "output drift")
    print(json.dumps({"output_sha256": hashlib.sha256(data).hexdigest(),
                      "thresholds": output["thresholds"], "checks": output["checks"]}, indent=2))


if __name__ == "__main__":
    main()

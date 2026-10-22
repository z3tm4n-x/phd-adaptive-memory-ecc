"""Engineering arithmetic only; never import/recompute a probability model."""
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


def load_sources(manifest, source_dir, datasheet):
    raw = {}
    for key, pin in manifest["sources"].items():
        data = ((source_dir / (key + ".source")).read_bytes() if source_dir else
                subprocess.check_output(["git", "cat-file", "blob", pin["commit"] + ":" + pin["path"]], cwd=HERE))
        require(hashlib.sha256(data).hexdigest() == pin["sha256"], "source drift: " + key)
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        require(hashlib.sha1(blob).hexdigest() == pin["git_blob"], "Git blob drift: " + key)
        raw[key] = data
    raw["datasheet"] = datasheet.read_bytes()
    require(hashlib.sha256(raw["datasheet"]).hexdigest() == manifest["datasheet"]["sha256"], "datasheet drift")
    return raw


def build(inp, raw):
    cfg = json.loads(raw["common"])
    accepted = json.loads(raw["accepted_results"])
    app_theory = json.loads(raw["app_theory_result"])
    app_numeric = json.loads(raw["app_result"])
    input_sha = hashlib.sha256(raw["common"]).hexdigest()
    require(app_theory["input_sha256"] == app_numeric["common_input_sha256"] == input_sha,
            "app-only deliveries use a different input")
    require(app_theory["theorem_substitution"]["Q_upper"] == app_numeric["Q_upper"],
            "author deliveries disagree; no local Q recomputation allowed")
    require(app_numeric["risk"]["physical_unconditional_probability"] is None,
            "unexpected physical acceptance")
    require(not app_numeric["accepted_table_changed"] and not app_theory["accepted_table_modified"],
            "app-only delivery changes accepted comparison")
    c, f, a = inp["candidate"], inp["source_facts"], inp["alternative"]
    require(c["words"] == cfg["words"] and c["useful_bytes"] == cfg["useful_bytes"], "useful input changed")
    require(c["code_n"] == 44 and c["t"] == 2, "this slice has one physical candidate")
    require(not inp["application_first"]["own_Q_computation"]
            and not inp["application_first"]["new_comparison_row"], "do not create an app-only Q row")
    require(c["physical_Q_upper"] is None and c["transferable_response_upper"] is None,
            "physical evidence cannot be supplied by engineering arithmetic")
    require(a["decode_upper_nominal_ns"] is None and a["encode_upper_nominal_ns"] is None,
            "codec slice must not become a measurement")
    service, cal = cfg["service"], cfg["calendar"]
    xm, xp, J = F(service["clock_lower"]), F(service["clock_upper"]), F(service["operation_endpoint_span_ns"])
    beats = (c["code_n"] + 15) // 16
    allocated = c["words"] * beats * 2
    max_address = beats * c["words"] - 1
    require(max_address < c["chip_x16_addresses"], "candidate does not fit chip")
    aperture = (cal["frame_ticks"] - cal["application_grant_phase_ticks"]) * xm - J
    control = cal["c_ticks"] * xm - J
    spec_cycles = beats * (F(f["read_cycle_min_ns"]) + F(f["write_cycle_min_ns"]))
    require(F(service["read_beat_ns"]) * xp + J < F(f["read_cycle_min_ns"]),
            "direct-import counterexample no longer applies")
    require(spec_cycles > aperture and spec_cycles > control, "old aperture incompatibility changed")

    cycle, turn, slot = map(F, (a["nominal_cycle_ns"], a["turnaround_ns"], a["application_slot_ns"]))
    grid = F(a["design_grid_ns"])
    require((cycle / grid).denominator == (turn / grid).denominator == 1, "off-grid proposed timing")
    cycle_lower, turn_lower = cycle * xm - J, turn * xm - J
    require(cycle_lower >= max(F(f["read_cycle_min_ns"]), F(f["write_cycle_min_ns"])), "too short proposed cycle")
    require(turn_lower >= F(f["OE_disable_max_ns"]), "too short proposed OE-disable wait")
    slot_lower = slot * xm - J
    fixed_nominal = 2 * beats * cycle + turn
    hard_allowance = (slot_lower - J) / xp - fixed_nominal
    target_allowance = (F(4, 5) * slot_lower - J) / xp - fixed_nominal
    illustrative_codec = sum(map(F, a["illustrative_codec_slice_ns"]))
    require(target_allowance > illustrative_codec, "illustrative local slot cannot meet target")
    # Check both sides of the engineering boundary, without invoking a Q function.
    require((fixed_nominal + target_allowance) * xp + J == F(4, 5) * slot_lower,
            "target boundary identity")
    require((fixed_nominal + target_allowance + 1) * xp + J > F(4, 5) * slot_lower,
            "above-boundary witness")
    q_ref = F(accepted["rows"]["t2_constant"]["risk"]["upper"])
    epsilon = F(cfg["epsilon"])
    require(q_ref < epsilon / 2, "accepted reference changed")
    return {
        "scope": inp["scope"],
        "physical_candidate": c,
        "geometry": {"allocated_bytes": allocated, "installed_data_bytes": c["installed_data_bytes"],
                     "last_x16_address": max_address, "unused_chip_addresses": c["chip_x16_addresses"] - max_address - 1,
                     "selected_fraction_of_installed_capacity": str(F(allocated, c["installed_data_bytes"])),
                     "active_code_bytes": c["words"] * c["code_n"] // 8,
                     "chip_idle_cost_scales_with_selected_fraction": False},
        "direct_import": {
            "status": "OUTSIDE_DATASHEET_TIMING_FOR_THIS_SERIAL_CONTRACT",
            "reference_input": "common#/service",
            "old_read_beat_upper_ns": str(F(service["read_beat_ns"]) * xp + J),
            "six_complete_cycles_min_reserved_ns": str(spec_cycles),
            "old_application_aperture_lower_ns": str(aperture),
            "old_control_aperture_lower_ns": str(control),
            "application_deficit_ns": str(spec_cycles - aperture),
            "code_family_excluded": False,
            "note": "complete serial cycles with full RMW; not proof that every physical implementation fails",
        },
        "local_alternative": {
            "status": "PARAMETRIC_WINDOW_ONLY_NOT_FULL_SERVICE_OR_Q",
            "slot_lower_ns": str(slot_lower),
            "cycle_lower_ns": str(cycle_lower),
            "read_board_capture_allowance_ns": str(cycle_lower - F(f["read_access_max_ns"])),
            "bus_release_extra_allowance_ns": str(turn_lower - F(f["OE_disable_max_ns"])),
            "hard_decode_plus_encode_plus_controller_nominal_ns": str(hard_allowance),
            "target_decode_plus_encode_plus_controller_nominal_ns": str(target_allowance),
            "illustrative_controller_target_allowance_nominal_ns": str(target_allowance - illustrative_codec),
            "fixed_nominal_cycle_and_turn_price_ns": str(fixed_nominal),
            "formula": "(6*cycle + turn + decode + encode + controller)*clock_upper + J <= alpha*(slot*clock_lower-J); alpha=1 or 0.8",
            "end_to_end_response_upper_ns": None, "peak_1ms_bus_upper": None,
            "average_bus_upper": None, "physical_Q_upper": None,
            "coherent_E_hardware_proved": False,
        },
        "risk_budget_reference_only": {
            "Q_locator": "accepted_results#/rows/t2_constant/risk/upper",
            "hard_eta_allowance": str(epsilon - q_ref),
            "half_epsilon_eta_allowance": str(epsilon / 2 - q_ref),
            "physical_eta_upper": None,
            "applicable_to_EV_with_changed_service": False,
            "condition": "certified full-horizon coupling to the same accepted model; pay all distinct divergences, not only direct uncorrectable events",
            "warning": "no upper on an unknown response multiplier or on group rate follows from this arithmetic",
        },
        "application_first": inp["application_first"],
        "application_revisit_arithmetic_ns": str(F(cfg["application"]["epoch_ns"]) * cfg["words"]),
        "next_risk_source": "app_result#/Q_upper (author delivery only, pending acceptance)",
        "checks": ["nine pinned Git sources and exact datasheet SHA", "useful volume and complete address range",
                   "old serial service outside datasheet timing", "proposed cycle/turn rounding with clock and endpoint",
                   "both sides of the local 20-percent boundary", "risk headroom is reference only, no physical transfer",
                   "same v4 and exact Q identity in received author deliveries, without re-derivation"],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--datasheet", type=Path, required=True)
    p.add_argument("--source-dir", type=Path)
    p.add_argument("--export-sources", type=Path)
    modes = p.add_mutually_exclusive_group()
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--check", action="store_true")
    args = p.parse_args()
    manifest_bytes = (HERE / "sources.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    raw = load_sources(manifest, args.source_dir, args.datasheet)
    if args.export_sources:
        args.export_sources.mkdir(parents=True, exist_ok=False)
        for key, data in raw.items():
            (args.export_sources / (key + ".source")).write_bytes(data)
    input_bytes = (HERE / "inputs.json").read_bytes()
    result = build(json.loads(input_bytes), raw)
    result["provenance"] = {"inputs_sha256": hashlib.sha256(input_bytes).hexdigest(),
                            "sources_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest()}
    data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    output = HERE / "boundaries.json"
    if args.write:
        output.write_bytes(data)
    else:
        require(output.read_bytes() == data, "output drift: boundaries.json")
    print(json.dumps({"output_sha256": hashlib.sha256(data).hexdigest(), "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    main()

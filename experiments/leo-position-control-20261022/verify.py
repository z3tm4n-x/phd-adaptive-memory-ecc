"""Check this source/input delivery; no orbit propagation or probability model."""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_bytes(raw, record):
    require(len(raw) == record["bytes"], f"size differs: {record}")
    require(sha256(raw) == record["sha256"], f"SHA256 differs: {record}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--fetch-pdfs", action="store_true", help="download missing pinned PDFs only")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    manifest = read_json(folder / "sources.json")
    candidate = read_json(folder / "candidate.json")

    for record in manifest["repo_files"]:
        raw = (args.source_root / record["path"]).read_bytes()
        check_bytes(raw, record)
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(blob == record["blob"], f"Git blob differs: {record['path']}")
        require(record["commit"] == candidate["base_commit"], "mixed repository snapshots")

    for record in manifest["pdfs"]:
        require(Path(record["name"]).name == record["name"], "PDF name must be a basename")
        path = args.pdf_dir / record["name"]
        if not path.exists() and args.fetch_pdfs:
            request = Request(record["url"], headers={"User-Agent": "Mozilla/5.0 (T206 source replay)"})
            with urlopen(request, timeout=30) as response:
                raw = response.read()
            check_bytes(raw, record)
            require(raw.startswith(b"%PDF-"), "download is not a PDF")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        raw = path.read_bytes()
        require(raw.startswith(b"%PDF-"), f"not a PDF: {path}")
        check_bytes(raw, record)

    inherited = candidate["inherited_contract"]
    common = read_json(args.source_root / inherited["source"])
    require(common["revision"] == inherited["revision"] == 4, "wrong common input revision")
    application = {k: v for k, v in common["application"].items() if k != "sensitivity_profile"}
    require(application == inherited["application"], "main application profile changed")
    constraints = {k: v for k, v in common["constraints"].items() if k != "clock_and_reserve"}
    require(constraints == inherited["constraints"], "research constraints changed")
    mem = candidate["memory"]
    for key in ("useful_bytes", "words", "data_bits"):
        require(mem[key] == common[key], f"common {key} changed")
    require(candidate["mission"]["duration_s"] == common["mission_s"], "duration changed")
    require(candidate["mission"]["epsilon"] == common["epsilon"], "epsilon changed")
    require(mem["words"] * mem["data_bits"] == 8 * mem["useful_bytes"], "useful capacity")
    require(mem["chips"] * mem["bits_per_chip_address"] == mem["bus_bits"] == 16, "bus width")
    require(mem["addresses_per_word"] * mem["bus_bits"] == mem["physical_positions_per_word"] == 48, "word layout")
    allocated = mem["words"] * mem["addresses_per_word"] * mem["bus_bits"] // 8
    installed = mem["chips"] * mem["addresses_per_chip"] * mem["bits_per_chip_address"] // 8
    require(allocated == mem["allocated_bytes"] and installed == mem["installed_bytes"], "physical capacity")
    last_address = mem["addresses_per_word"] * mem["words"] - 1
    require(last_address < mem["addresses_per_chip"], "address range exceeds chip")
    code_bytes = {}
    require(len(candidate["comparison"]["code_candidates"]) == 2, "expected two code candidates")
    for code, reference in zip(candidate["comparison"]["code_candidates"], (common["codes"][0], common["codes"][2])):
        require(code == {k: reference[k] for k in ("n", "k", "t")}, "code changed")
        require(code["n"] <= mem["physical_positions_per_word"], "code exceeds allocation")
        code_bytes[str(code["n"])] = mem["words"] * code["n"] // 8
    require(len(code_bytes) == 2, "expected both codes")

    # This frozen delivery has no numerical physical certificate or hardware timing.
    service = candidate["service"]
    for key in ("read_write_turnaround_codec_controller_upper_ns", "P_FAST_s", "P_LOW_s", "H_FAST_s", "measured_hardware_costs"):
        require(service[key] is None, f"unreviewed physical/service number: {key}")
    results = candidate["results"]
    for key in ("Q_upper", "Q_lower", "class_lower", "gain_over_best_constant", "bus_average_peak_response", "codec_navigation_control_cost", "probability_time_resource_margins"):
        require(results[key] is None, f"new result requires a new reviewed input/version: {key}")
    require(results["status"] == "UNKNOWN", "unexpected map classification")
    require(results["physical_point_confirmed"] is False, "physical point not established here")
    require(results["method_applicability_signed"] is False, "method gate not established here")
    require(manifest["numeric_flight_files_obtained"] == [], "flight data not part of this delivery")
    route = candidate["method_route"]
    require(any(r["commit"] == route["source_commit"] and r["path"] == route["path"] for r in manifest["external_repo_references"]), "method reference absent")
    calendar = candidate["mandatory_calendar_proposal"]
    require(all(calendar[k] is None for k in ("g_s", "k_LOW", "guaranteed_E_endpoints", "explicit_J_FAST_intervals")), "new numerical windows require an updated input")

    packet_names = ("PLAN.md", "REPORT.md", "RULE.md", "SOURCES.md", "candidate.json", "sources.json", "verify.py")
    output = {
        "scope": "source_identity_input_inheritance_and_layout_only",
        "repo_source_files_verified": len(manifest["repo_files"]),
        "pdf_files_verified": len(manifest["pdfs"]),
        "web_pages_byte_replayed": False,
        "external_method_references_pinned": len(manifest["external_repo_references"]),
        "external_method_files_byte_replayed": False,
        "source_base_commit": candidate["base_commit"],
        "layout_own_result": {
            "useful_bytes": mem["useful_bytes"],
            "active_code_bytes": code_bytes,
            "allocated_bytes": allocated,
            "installed_bytes": installed,
            "last_address_each_chip": last_address,
            "allocated_fraction_of_installed": "3/4",
        },
        "source_app_and_constraints_unchanged": True,
        "new_physical_Q_computed": False,
        "map_status": "UNKNOWN",
        "independent_scientific_review": False,
        "packet_sha256": {name: sha256((folder / name).read_bytes()) for name in packet_names},
    }
    text = json.dumps(output, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")


if __name__ == "__main__":
    main()

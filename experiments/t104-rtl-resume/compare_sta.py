"""Bounded before/after extraction; same Vivado engine, not independent STA.

Default is a read-only recheck of the published reports. --write packages an
existing read-only checkpoint interrogation, never changes a timing constraint.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

from audit_sta import audit

HERE = Path(__file__).resolve().parent
BASELINE = "cd68afd309cc00a152dca51dd557b76991afdb13"
PART = "xc7z020clg484-1"
SERIES = HERE/"outputs/sta/config-load-01"
DETAIL_FILES = ("hold.tsv", "gray.tsv", "selection.txt", "path_properties.rpt",
                "gray_worst.rpt", "exceptions_coverage.rpt", "exceptions_ignored.rpt")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def reports(path):
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name).decode("utf-8") for name in archive.namelist()}


def paths(text):
    result = []
    for block in re.split(r"(?=Slack \((?:MET|VIOLATED)\))", text)[1:]:
        def field(label):
            match = re.search(r"^  "+re.escape(label)+r":\s*(.+)$", block, re.M)
            if not match:
                raise ValueError(f"path field missing: {label}")
            return match[1].strip()
        slack = re.match(r"Slack \((MET|VIOLATED)\)\s*:\s*(-?[0-9.]+)ns", block)
        if not slack or (float(slack[2]) < 0) != (slack[1] == "VIOLATED"):
            raise ValueError("path slack/sign mismatch")
        result.append({"start": field("Source"), "end": field("Destination"),
                       "slack_ns": float(slack[2]), "type": field("Path Type"),
                       "delay_breakdown": field("Data Path Delay"),
                       "logic_levels": field("Logic Levels")})
    if not result:
        raise ValueError("empty path report")
    return result


def cdc_groups(text):
    summary = {m[0]: int(m[1]) for m in re.findall(
        r"^(CDC-\d+)\s+(?:Critical|Warning|Info)\s+(\d+)\s+", text, re.M)}
    actual = Counter()
    grouped = Counter()
    source = destination = None
    for line in text.splitlines():
        if line.startswith("Source Clock: "):
            source = line.split(": ")[1]
        elif line.startswith("Destination Clock: "):
            destination = line.split(": ")[1]
        elif re.match(r"\s*\d+\s+CDC-", line):
            columns = re.split(r"\s{2,}", line.strip())
            identifier = columns[1]
            if not source or not destination or identifier not in summary:
                raise ValueError("CDC row lacks context")
            actual[identifier] += 1
            # Keep destination register/cone identity, only collapse bit indices.
            endpoint = re.sub(r"\[[0-9:]+\](?=/|$)", "[*]", columns[-1])
            grouped[(source, destination, identifier, endpoint)] += 1
    if dict(actual) != summary:
        raise ValueError("CDC detail/summary mismatch")
    return [{"from_clock": a, "to_clock": b, "id": c, "destination": d, "count": n}
            for (a, b, c, d), n in sorted(grouped.items())]


def detail_summary(detail, timing):
    hold = list(csv.DictReader(io.StringIO(detail["hold.tsv"]), delimiter="\t"))
    gray = list(csv.DictReader(io.StringIO(detail["gray.tsv"]), delimiter="\t"))
    if len(hold) != timing["hold_failing_endpoints"] or len({r["end"] for r in hold}) != len(hold):
        raise ValueError("hold coverage/uniqueness mismatch")
    slacks = [float(row["slack_ns"]) for row in hold]
    if not slacks or max(slacks) >= 0 or min(slacks) != timing["WHS_ns"]:
        raise ValueError("hold direction/worst mismatch")
    # Each printed slack has 0.001-ns resolution; TNS uses unrounded values.
    rounding = (len(hold)+1)*0.0005
    if abs(sum(slacks)-timing["THS_ns"]) > rounding:
        raise ValueError("hold total outside printed-rounding envelope")
    expected = {f"ports[{p}].gt1_reg[{b}]/D" for p in (0, 1) for b in range(62)}
    if len(gray) != 124 or {row["end"] for row in gray} != expected:
        raise ValueError("incomplete dynamic Gray coverage")
    if any(float(row["requirement_ns"]) != 4 or row["exception"] != "MaxDelay Path 4.000ns -datapath_only" for row in gray):
        raise ValueError("Gray settling constraint not applied")
    missing = re.findall(r"^MISSING (.+)$", detail["selection.txt"], re.M)
    if set(missing) != {f"ports[{p}].gt1_reg[{b}]/D" for p in (0, 1) for b in (62, 63)}:
        raise ValueError("unexpected Gray missing paths")
    if re.findall(r"^DRIVER_TYPES (.+)$", detail["selection.txt"], re.M) != ["GND"]*4:
        raise ValueError("missing Gray bits not tied low")
    grouped = defaultdict(list)
    for row in hold:
        grouped[(row["group"], row["start_class"])].append(float(row["slack_ns"]))
    return {"hold": [{"clock": k[0], "source_class": k[1], "failing_endpoints": len(v),
                      "worst_ns": min(v), "sum_printed_slacks_ns": round(sum(v), 3)}
                     for k, v in sorted(grouped.items())],
            "sum_printed_slacks_ns": round(sum(slacks), 3), "total_rounding_envelope_ns": rounding,
            "gray_dynamic_endpoints": len(gray), "gray_constant_inputs_without_timed_path": missing,
            "gray_min_slack_ns": min(float(r["slack_ns"]) for r in gray),
            "gray_max_data_path_ns": max(float(r["data_delay_ns"]) for r in gray)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--detail-dir", type=Path)
    args = parser.parse_args()
    before = audit(PART, source_ref=BASELINE)
    after = audit(PART, SERIES, source_ref="3a3656bdf09b7e99fd5f1de2baabb1b55e6a905d")
    old = json.loads((HERE/"outputs/sta"/PART/"summary.json").read_text())
    new = json.loads((SERIES/PART/"summary.json").read_text())
    if set(old["source_sha256"]) != set(new["source_sha256"]):
        raise ValueError("implementation input set changed")
    changed = sorted(name for name, value in old["source_sha256"].items() if value != new["source_sha256"][name])
    if changed != ["platform_run.py", "rtl/service_config.sv"]:
        raise ValueError(f"unexpected RTL or constraint changes: {changed}")
    zip_path = SERIES/"detail.zip"
    if args.write:
        if not args.detail_dir:
            raise ValueError("write needs existing --detail-dir")
        checkpoint = Path(new["raw_directory"])/"routed.dcp"
        if digest(checkpoint.read_bytes()) != new["routed_checkpoint_sha256"]:
            raise ValueError("checkpoint identity mismatch")
        if zip_path.exists():
            with zipfile.ZipFile(zip_path) as archive:
                if set(archive.namelist()) != set(DETAIL_FILES) or any(
                    archive.read(name) != (args.detail_dir/name).read_bytes() for name in DETAIL_FILES):
                    raise ValueError("refusing to replace an existing different detail archive")
        else:
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name in DETAIL_FILES:
                    archive.writestr(name, (args.detail_dir/name).read_bytes())
    detail = reports(zip_path)
    if set(detail) != set(DETAIL_FILES):
        raise ValueError("detail archive members changed")
    raw = reports(SERIES/PART/"reports.zip")
    details = detail_summary(detail, after["timing"])
    result = {"baseline_commit": BASELINE, "series": "config-load-01", "part": PART,
              "changed_implementation_inputs": changed, "constraints_unchanged": True,
              "before": before, "after": after,
              "differences_after_minus_before": {key: round(after["timing"][key]-before["timing"][key], 3)
                                                  for key in ("WNS_ns", "TNS_ns", "WHS_ns", "THS_ns")},
              "memory_paths": paths(raw["memory_paths.rpt"]),
              "cdc_groups": cdc_groups(raw["cdc.rpt"]), "checkpoint_detail": details,
              "detail_zip_sha256": digest(zip_path.read_bytes()),
              "checkpoint_sha256": new["routed_checkpoint_sha256"],
              "detail_script_sha256": digest((HERE/"sta_detail.tcl").read_bytes()),
              "scope": "same Vivado engine; extraction/coverage only, no CDC waivers or physical qualification"}
    output = SERIES/"comparison.json"
    if args.write:
        output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    elif json.loads(output.read_text()) != result:
        raise ValueError("published comparison differs from re-extraction")
    print(json.dumps({"differences": result["differences_after_minus_before"], "detail": details,
                      "reextracted": True}, indent=2))


if __name__ == "__main__":
    main()

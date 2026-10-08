"""Read-only, standard-library audit of the published bounded Vivado reports.

This checks transfer integrity and independently extracts scalar evidence;
it is NOT an independent STA engine, silicon test or CDC waiver.
"""
import hashlib
import json
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def scalar(text, label):
    rows = re.findall(r"^\|\s*"+re.escape(label)+r"\s*\|\s*(\d+)\s*\|", text, re.M)
    if not rows or len(set(rows)) != 1:
        raise ValueError(f"missing/ambiguous resource {label}")
    return int(rows[0])


def audit(part):
    root = HERE/"outputs/sta"/part
    summary = json.loads((root/"summary.json").read_text(encoding="utf-8"))
    archive = root/"reports.zip"
    if sha(archive.read_bytes()) != summary["reports_zip_sha256"]:
        raise ValueError("archive hash mismatch")
    with zipfile.ZipFile(archive) as z:
        if set(z.namelist()) != set(summary["report_sha256"]):
            raise ValueError("missing or extra report members")
        for name, expected in summary["report_sha256"].items():
            if sha(z.read(name)) != expected:
                raise ValueError(f"report hash mismatch {name}")
        reports = {name: z.read(name).decode("utf-8") for name in z.namelist()}
    for name, expected in summary["source_sha256"].items():
        if sha((HERE/name).read_bytes()) != expected:
            raise ValueError(f"run/source mismatch {name}")
    # Independent positional extraction, not the production parser's regex.
    lines = reports["timing.rpt"].splitlines()
    headers = [i for i, line in enumerate(lines) if line.strip().startswith("WNS(ns)")]
    if len(headers) != 1:
        raise ValueError("timing summary ambiguous")
    values = lines[headers[0]+2].split()
    if len(values) != 12:
        raise ValueError("timing row incomplete")
    for index, key in ((0, "WNS_ns"), (1, "TNS_ns"), (4, "WHS_ns"), (5, "THS_ns")):
        if float(values[index]) != summary["timing"][key]:
            raise ValueError(f"timing extraction disagreement {key}")
    resources = {name: scalar(reports["resources.rpt"], name) for name in
                 ("Slice LUTs", "Slice Registers", "RAMB36/FIFO*", "RAMB18", "DSPs", "BUFGCTRL", "MMCME2_ADV")}
    checks = dict(re.findall(r"^\d+\. checking ([a-z_]+) \((\d+)\)", reports["check_timing.rpt"], re.M))
    cdc = re.findall(r"^(CDC-\d+)\s+(Critical|Warning|Info)\s+(\d+)\s+(.+)$", reports["cdc.rpt"], re.M)
    route_errors = re.findall(r"# of nets with routing errors\.+\s*:\s*(\d+)", reports["route_status.rpt"])
    if len(route_errors) != 1:
        raise ValueError("route status missing")
    return {"part": part, "archive_and_source_hashes_match": True,
            "timing": summary["timing"], "resources": resources, "check_timing": checks,
            "CDC_unwaived_summary": cdc, "routing_errors": int(route_errors[0]),
            "scope": "report integrity/extraction; no independent STA or automatic PASS"}


if __name__ == "__main__":
    results = [audit(part) for part in ("xc7z020clg484-1", "xc7z020clg484-2")]
    sources = [json.loads((HERE/"outputs/sta"/r["part"]/"summary.json").read_text())["source_sha256"] for r in results]
    if sources[0] != sources[1]:
        raise ValueError("-1/-2 used different sources/constraints")
    print(json.dumps({"same_sources_and_constraints": True, "results": results}, indent=2))

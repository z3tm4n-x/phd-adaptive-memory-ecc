"""Read-only, standard-library audit of the published bounded Vivado reports.

This checks transfer integrity and independently extracts scalar evidence;
it is NOT an independent STA engine, silicon test or CDC waiver.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
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


def source_bytes(name, source_ref):
    if not source_ref:
        return (HERE/name).read_bytes()
    root = HERE.parents[1]
    command = ["git"]
    pointer = root/".git"
    if os.name != "nt" and pointer.is_file():
        match = re.fullmatch(r"gitdir: ([A-Za-z]):[/\\](.+)\s*", pointer.read_text().strip())
        if match:
            directory = Path("/mnt")/match[1].lower()/match[2].replace("\\", "/")
            command += [f"--git-dir={directory}", f"--work-tree={root}"]
    path = (HERE/name).relative_to(root).as_posix()
    return subprocess.check_output([*command, "show", f"{source_ref}:{path}"], cwd=root)


def audit(part, output_root=None, source_ref=None):
    root = (output_root or HERE/"outputs/sta")/part
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
        if sha(source_bytes(name, source_ref)) != expected:
            raise ValueError(f"run/source mismatch {name}")
    for name in ("memory_paths.rpt", "resources.rpt", "check_timing.rpt"):
        if sha((root/name).read_bytes()) != summary["report_sha256"][name]:
            raise ValueError(f"plain/archived report mismatch {name}")
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
    cdc = [list(row) for row in re.findall(
        r"^(CDC-\d+)\s+(Critical|Warning|Info)\s+(\d+)\s+(.+)$", reports["cdc.rpt"], re.M)]
    route_errors = re.findall(r"# of nets with routing errors\.+\s*:\s*(\d+)", reports["route_status.rpt"])
    if len(route_errors) != 1:
        raise ValueError("route status missing")
    return {"part": part, "archive_and_source_hashes_match": True,
            "timing": summary["timing"], "resources": resources, "check_timing": checks,
            "CDC_unwaived_summary": cdc, "routing_errors": int(route_errors[0]),
            "scope": "report integrity/extraction; no independent STA or automatic PASS"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--parts", nargs="+", choices=("xc7z020clg484-1", "xc7z020clg484-2"),
                        default=["xc7z020clg484-1", "xc7z020clg484-2"])
    parser.add_argument("--series")
    parser.add_argument("--source-ref", help="exact historical Git SHA; otherwise check current working files")
    args = parser.parse_args()
    if args.series and not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", args.series):
        parser.error("invalid series")
    if args.source_ref and not re.fullmatch(r"[0-9a-f]{40}", args.source_ref):
        parser.error("source-ref must be an exact 40-character SHA")
    output_root = HERE/"outputs/sta"
    if args.series:
        output_root /= args.series
    results = [audit(part, output_root, args.source_ref) for part in args.parts]
    sources = [json.loads((output_root/r["part"]/"summary.json").read_text())["source_sha256"] for r in results]
    if any(source != sources[0] for source in sources[1:]):
        raise ValueError("-1/-2 used different sources/constraints")
    print(json.dumps({"source_ref": args.source_ref or "current working files",
                      "same_sources_and_constraints": True, "results": results}, indent=2))

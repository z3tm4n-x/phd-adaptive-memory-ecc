"""Bounded Vivado experiment and strict report extraction, never an automatic PASS.

Raw Vivado projects/checkpoints stay ignored. Compact, directly inspectable
reports and their hashes are retained for review. No board timing is inferred.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARTS = ("xc7z020clg484-1", "xc7z020clg484-2")
REPORTS = ("timing.rpt", "utilization.rpt", "check_timing.rpt", "cdc.rpt",
           "exceptions.rpt", "exceptions_ignored.rpt", "bus_skew.rpt",
           "clock_interaction.rpt", "clocks.rpt", "route_status.rpt", "drc.rpt",
           "memory_paths.rpt", "longest_paths.rpt", "effective.xdc",
           "design_properties.rpt", "power_operating_conditions.rpt",
           "resources.rpt", "memory_clock_properties.rpt")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    paths = [*(HERE/"rtl").glob("*.sv"), *(HERE/"platform").glob("*.tcl"),
             *(HERE/"platform").glob("*.xdc"), HERE/"platform/config.json",
             Path(__file__)]
    return {p.relative_to(HERE).as_posix(): digest(p) for p in sorted(paths)}


def parse_timing(text):
    """Exactly one Vivado Design Timing Summary row, preserving negative slack."""
    pattern = (r"WNS\(ns\)\s+TNS\(ns\)\s+TNS Failing Endpoints\s+TNS Total Endpoints\s+"
               r"WHS\(ns\)\s+THS\(ns\)\s+THS Failing Endpoints\s+THS Total Endpoints\s+"
               r"WPWS\(ns\)\s+TPWS\(ns\)\s+TPWS Failing Endpoints\s+TPWS Total Endpoints\s*\n"
               r"[- \t]+\n\s*([-0-9.]+)\s+([-0-9.]+)\s+(\d+)\s+(\d+)\s+"
               r"([-0-9.]+)\s+([-0-9.]+)\s+(\d+)\s+(\d+)\s+"
               r"([-0-9.]+)\s+([-0-9.]+)\s+(\d+)\s+(\d+)")
    rows = re.findall(pattern, text)
    if len(rows) != 1:
        raise ValueError("missing/ambiguous complete Design Timing Summary")
    names = ("WNS_ns", "TNS_ns", "setup_failing_endpoints", "setup_total_endpoints",
             "WHS_ns", "THS_ns", "hold_failing_endpoints", "hold_total_endpoints",
             "WPWS_ns", "TPWS_ns", "pulse_failing_endpoints", "pulse_total_endpoints")
    result = {name: (float(value) if name.endswith("_ns") else int(value))
              for name, value in zip(names, rows[0])}
    if result["TNS_ns"] > 0 or result["THS_ns"] > 0:
        raise ValueError("invalid positive total negative slack")
    for slack, count in (("WNS_ns", "setup_failing_endpoints"), ("WHS_ns", "hold_failing_endpoints")):
        if (result[slack] < 0) != (result[count] > 0):
            raise ValueError("slack/count contradiction")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vivado", default="vivado-wsl")
    parser.add_argument("--parts", nargs="+", choices=PARTS, default=list(PARTS))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    aggregate = []
    for part in args.parts:
        run = HERE/".build"/f"sta-{part}-{time.time_ns()}"
        log = run.with_suffix(".log")
        journal = run.with_suffix(".jou")
        run.parent.mkdir(exist_ok=True)
        hashes = source_hashes()
        command = [args.vivado, "-mode", "batch", "-source", str(HERE/"platform/implement.tcl"),
                   "-log", str(log), "-journal", str(journal), "-tclargs", part, str(run)]
        start = time.monotonic()
        print(f"Running {part}; log={log}", flush=True)
        console = run.with_suffix(".console.log")
        with console.open("w", encoding="utf-8") as stream:
            process = subprocess.run(command, cwd=HERE/".build", stdout=stream,
                                     stderr=subprocess.STDOUT, timeout=7200)
        if hashes != source_hashes():
            raise RuntimeError("source changed during run; retain raw evidence but do not publish")
        text = console.read_text(encoding="utf-8", errors="replace")
        if process.returncode or f"T104_IMPLEMENTATION_COMPLETED {part} {run}" not in text:
            raise RuntimeError(f"incomplete Vivado run; inspect {console}")
        result = {"part": part, "scope": "full executor OOC; virtual IO, NOT SRAM pad timing",
                  "source_sha256": hashes, "elapsed_s": round(time.monotonic()-start, 3),
                  "command": command, "exit_code": process.returncode,
                  "log_sha256": digest(log), "console_sha256": digest(console),
                  "routed_checkpoint_sha256": digest(run/"routed.dcp"),
                  "raw_directory": str(run), "timing": parse_timing((run/"timing.rpt").read_text()),
                  "report_sha256": {name: digest(run/name) for name in REPORTS},
                  "board_timing_qualified": False, "full_B_complete": False}
        aggregate.append(result)
        if args.write:
            target = HERE/"outputs/sta"/part
            target.mkdir(parents=True, exist_ok=True)
            # Bounded text reports only; no log, DCP, tool database or raw project.
            with zipfile.ZipFile(target/"reports.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for name in REPORTS:
                    archive.write(run/name, name)
            for name in ("memory_paths.rpt", "resources.rpt", "check_timing.rpt"):
                shutil.copyfile(run/name, target/name)
            result["reports_zip_sha256"] = digest(target/"reports.zip")
            (target/"summary.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only Vivado/part inventory. Missing device support is not a STA result."""
import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def parse_inventory(log, returncode, requested):
    versions = re.findall(r"T104_VERSION_BEGIN\n(.*?)\nT104_VERSION_END", log, re.S)
    counts = re.findall(r"^T104_INSTALLED_PART_COUNT (\d+)$", log, re.M)
    available = re.findall(r"^T104_PART_AVAILABLE (\S+)$", log, re.M)
    missing = re.findall(r"^T104_PART_UNAVAILABLE (\S+)$", log, re.M)
    states = re.findall(r"^T104_PLATFORM_STATUS (\S+)$", log, re.M)
    if len(versions) != 1 or len(counts) != 1 or len(states) != 1:
        raise ValueError("incomplete inventory; not a verified part-support result")
    if sorted(available+missing) != sorted(requested):
        raise ValueError("requested part inventory missing/duplicated")
    expected_status = "BLOCKED_DEVICE_SUPPORT" if missing else "DEVICE_SUPPORT_AVAILABLE_NOT_STA"
    if states[0] != expected_status or returncode != (2 if missing else 0):
        raise ValueError("tool status/exit code contradict inventory")
    version = "\n".join(line for line in versions[0].splitlines()
                        if line.strip() and not line.startswith("# "))
    return {"status": states[0], "vivado_version": version,
            "installed_part_count": int(counts[0]), "available_parts": available,
            "missing_parts": missing, "synthesis_run": False, "STA_run": False,
            "wns_ns": None, "tns_ns": None, "whs_ns": None, "ths_ns": None,
            "resources": None, "device_license_tested": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--vivado", default="vivado-wsl")
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    config = json.loads((HERE/"platform/config.json").read_text(encoding="utf-8"))
    out = HERE/".build/platform-probe"
    out.mkdir(parents=True, exist_ok=True)
    script = HERE/"platform/inspect.tcl"
    command = [args.vivado, "-mode", "batch", "-source", str(script),
               "-log", "inventory.log", "-journal", "inventory.jou"]
    start = time.monotonic()
    process = subprocess.run(command, cwd=out, capture_output=True, text=True, timeout=120)
    log = (process.stdout+process.stderr).replace("\r\n", "\n")
    (out/"console.log").write_text(log, encoding="utf-8")
    report = parse_inventory(log, process.returncode,
                             [config["primary_part"], config["comparison_part"]])
    report.update({"elapsed_s": round(time.monotonic()-start, 3),
                   "inspect_tcl_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
                   "console_sha256": hashlib.sha256((out/"console.log").read_bytes()).hexdigest(),
                   "command": command, "tool_exit_code": process.returncode})
    if args.write:
        (HERE/"outputs/platform.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())

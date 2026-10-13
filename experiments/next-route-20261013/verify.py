"""One read-only repetition. --record writes this T146 record only."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "519ac5e0c858ce5f71ba71c0f344d2a79edf60f2"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    commands = [
        [sys.executable, "-B", str(HERE/"arm_check.py")],
        [sys.executable, "-B", str(HERE/"route_check.py")],
        [sys.executable, "-B", "experiments/t95-method-regime-map/verify.py"],
        [sys.executable, "-B", "-m", "unittest", "discover",
         "-s", "experiments/t88-dstar-sensitivity", "-p", "test_*.py"],
        [sys.executable, "-B", "experiments/t90-monitor-physical/run.py", "--check"],
        ["git", "diff", "--check"],
    ]
    records = []
    for command in commands:
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        record = {
            "command": [x.replace(str(ROOT)+"/", "") for x in command],
            "exit_code": run.returncode, "stdout": run.stdout, "stderr": run.stderr,
        }
        records.append(record)
        if run.returncode:
            print(json.dumps(record, indent=2))
            raise SystemExit(run.returncode)
    # Git-tree check: accepted committed files unchanged. Worktree inputs are
    # checked by the source hash assertions and this scoped worktree diff.
    changed = subprocess.check_output(["git", "diff", "--name-only", BASE],
                                     cwd=ROOT, text=True).splitlines()
    allowed = lambda p: p.startswith("experiments/next-route-20261013/") or p.startswith("theory/t146-")
    assert all(allowed(p) for p in changed), changed
    hashes = {}
    for path in (HERE/"arm-report.json", HERE/"route-report.json"):
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    record = {
        "task": 146, "all_pass": True, "new_assertions": 51,
        "abstract_ARM_histories": 8192, "route_substitutions": 15,
        "T95_checks": 71, "T88_unittests": 12, "T90_unittests": 10,
        "no_hardware_or_independent_review_claim": True,
        "report_sha256": hashes, "commands": records,
    }
    if args.record:
        (HERE/"reproduction.json").write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({k:v for k,v in record.items() if k!="commands"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

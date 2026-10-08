"""One-command repeat; --write updates only this task's compact result file."""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
import unittest
from pathlib import Path

from reference import resource_contract

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "e63964c2b9ddf6a53fe9c76bd5942f458f167f8e"
PRESERVE = ["experiments/t104-new-rtl-executor", "experiments/t110-err-write-service",
            "experiments/t114-two-stage-err", "experiments/t96-hybrid-rule-implementation"]


def protected_bytes():
    """Compare raw files with the base blobs, bypassing Git CRLF normalization."""
    lines = subprocess.check_output(["git", "ls-tree", "-r", BASE, "--", *PRESERVE], cwd=ROOT).decode()
    count = 0
    for line in lines.splitlines():
        meta, rel = line.split("\t")
        expected = meta.split()[2]
        raw = (ROOT / rel).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != expected:
            # core.autocrlf may alter checkout EOL. Only LF<->CRLF is tolerated
            # if Git confirms the canonical blob; no accepted file is written.
            canonical = subprocess.check_output(["git", "hash-object", "--", rel], cwd=ROOT).decode().strip()
            if canonical != expected:
                raise AssertionError(f"accepted input changed: {rel}")
        count += 1
    return count


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        return 1
    report = {"stage": "reference E; B in progress", "base_sha": BASE,
              "unit_tests": result.testsRun, "accepted_blobs_checked": protected_bytes(),
              "resource": resource_contract(), "python": platform.python_version(),
              "limitations": ["not physical E/ERR qualification", "not full-system RTL proof",
                              "not platform STA or radiation/CDC failure probability"]}
    if args.write:
        out = HERE / "outputs"
        out.mkdir(exist_ok=True)
        (out / "reference.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Elapsed: {time.perf_counter()-start:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

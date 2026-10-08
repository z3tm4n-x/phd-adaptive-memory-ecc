"""One-command repeat; --write updates only this task's compact result file."""
import argparse
import hashlib
import json
import platform
import os
import re
import subprocess
import sys
import time
import unittest
from pathlib import Path

from reference import resource_contract
from contract_check import check_contract

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "e63964c2b9ddf6a53fe9c76bd5942f458f167f8e"
PRESERVE = ["experiments/t104-new-rtl-executor", "experiments/t110-err-write-service",
            "experiments/t114-two-stage-err", "experiments/t96-hybrid-rule-implementation"]


def protected_bytes():
    """Audit base blobs; report raw identity separately from checkout CRLF."""
    git = ["git"]
    pointer = ROOT / ".git"
    if os.name != "nt" and pointer.is_file():
        # WSL can read a Windows-created worktree without rewriting its .git
        # pointer or affecting the owning Windows checkout.
        match = re.fullmatch(r"gitdir: ([A-Za-z]):[/\\](.+)\s*", pointer.read_text().strip())
        if match:
            target = Path("/mnt") / match[1].lower() / match[2].replace("\\", "/")
            if not target.is_dir():
                raise RuntimeError("Windows worktree Git directory is not mounted in WSL")
            git += [f"--git-dir={target}", f"--work-tree={ROOT}"]
    lines = subprocess.check_output([*git, "ls-tree", "-r", BASE, "--", *PRESERVE], cwd=ROOT).decode()
    count = 0
    checkout_crlf_only = []
    for line in lines.splitlines():
        meta, rel = line.split("\t")
        expected = meta.split()[2]
        raw = (ROOT / rel).read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != expected:
            # core.autocrlf may alter checkout EOL. Only CRLF->LF is tolerated
            # if it reproduces the base blob exactly; no accepted file is written.
            lf = raw.replace(b"\r\n", b"\n")
            canonical = hashlib.sha1(b"blob " + str(len(lf)).encode()+b"\0"+lf).hexdigest()
            if canonical != expected:
                raise AssertionError(f"accepted input changed: {rel}")
            checkout_crlf_only.append(rel)
        count += 1
    return {"files": count, "raw_identical": count-len(checkout_crlf_only),
            "checkout_crlf_only": checkout_crlf_only}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true")
    p.add_argument("--rtl", action="store_true", help="Icarus/vvp must be on PATH")
    p.add_argument("--formal", action="store_true", help="Yosys and yosys-abc must be on PATH")
    p.add_argument("--regression-A", action="store_true", dest="regression_a")
    args = p.parse_args()
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        return 1
    if args.regression_a:
        subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s",
                        str(ROOT/PRESERVE[3]), "-p", "test_reference.py"], check=True)
    for enabled, script in ((args.rtl, "rtl_check.py"), (args.rtl, "integration_check.py"),
                            (args.formal, "yosys_check.py"), (args.formal, "pdr_check.py")):
        if enabled:
            subprocess.run([sys.executable, "-B", str(HERE/script)]
                           + (["--write"] if args.write else []), check=True)
    accepted = protected_bytes()
    report = {"stage": "integrated E executor; B in progress", "base_sha": BASE,
              "unit_tests": result.testsRun, "accepted_blobs_checked": accepted["files"],
              "accepted_checkout_audit": accepted,
              "resource": resource_contract(), "python": platform.python_version(),
              "integrated_contract": check_contract(),
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

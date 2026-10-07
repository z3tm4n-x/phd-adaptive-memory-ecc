"""Repeat option-2 budget; --write updates ONLY budget.json and handoff.json."""
import argparse
import io
import json
import subprocess
import sys
import unittest

from budget import HERE, ROOT, calculate
from run import names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    old = subprocess.run([sys.executable, "-B", str(HERE/"run.py")], cwd=ROOT,
                         capture_output=True, text=True)
    if old.returncode:
        print(old.stdout+old.stderr, file=sys.stderr)
        return old.returncode
    assert "15/15" in old.stdout and "49/49" in old.stdout and "71/71" in old.stdout
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_budget.py")
    cases = sorted(names(suite))
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    if not result.wasSuccessful():
        print(log.getvalue(), file=sys.stderr)
        return 1
    report, handoff = calculate()
    report["new_test_count"] = result.testsRun
    report["new_tests"] = cases
    report["unchanged_reproductions"] = {"first_timing_gate": 15, "A": 49, "T95": 71,
                                        "original_outputs_rewritten": False}
    for target, payload in ((HERE/"outputs/budget.json", report), (HERE/"handoff.json", handoff)):
        if args.write:
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        if not target.exists() or json.loads(target.read_text(encoding="utf-8")) != payload:
            print(f"Mismatch: {target.name}; inspect before --write", file=sys.stderr)
            return 1
    print(f"T104 option-2 budget: {result.testsRun}/{len(cases)} new checks; old gate15, A49, T9571 unchanged.")
    print("20 pinned blobs; budget.json and handoff.json match. Conditional pin allocation only.")
    print("Scientific recalculation and physical timing qualification pending; main RTL not started.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

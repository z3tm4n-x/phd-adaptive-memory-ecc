"""Offline timing gate; --write changes only this package's reproduction.json."""
import argparse
import io
import json
import subprocess
import sys
import unittest

from timing import HERE, ROOT, calculate


def names(suite):
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            yield from names(t)
        else:
            yield t.id()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    # These accepted executables always run read-only, even for our --write.
    for path in ("experiments/t96-hybrid-rule-implementation/run.py",
                 "experiments/t95-method-regime-map/verify.py"):
        r = subprocess.run([sys.executable, "-B", str(ROOT/path)], cwd=ROOT,
                           text=True, capture_output=True)
        if r.returncode:
            print(r.stdout+r.stderr, file=sys.stderr)
            return r.returncode
        if path.endswith("verify.py"):
            assert json.loads(r.stdout)["checks"] == 71
        else:
            assert "49/49 tests" in r.stdout
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_timing.py")
    cases = list(names(suite))
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    if not result.wasSuccessful():
        print(log.getvalue(), file=sys.stderr)
        return 1
    report = calculate()
    report["test_count"] = result.testsRun
    report["tests"] = sorted(cases)
    report["accepted_reproductions"] = {"stage_A_checks": 49, "T95_checks": 71,
                                       "accepted_outputs_rewritten": False}
    target = HERE / "outputs/reproduction.json"
    if args.write:
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if not target.exists() or json.loads(target.read_text(encoding="utf-8")) != report:
        print("T104 timing report differs; inspect before --write", file=sys.stderr)
        return 1
    print(f"T104 timing gate: {result.testsRun}/{len(cases)}; accepted A 49/49; T95 71/71.")
    print("14 pinned sources; own reproduction.json matches. Main RTL blocked by timing decision.")
    print("No physical WCET/RTL formal proof claimed; accepted service and reference unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

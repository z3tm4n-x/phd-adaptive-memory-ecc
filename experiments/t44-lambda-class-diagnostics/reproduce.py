"""T44 bounded diagnostics. Python 3.11+ and Git; standard library only.

Default: tests + recomputation + comparison, without writing files.
--write regenerates only this task's summary.json and tables.md after tests.
"""
import argparse
import json
from pathlib import Path
import unittest

from diagnostics import compute
from tables import render

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    tests = unittest.TextTestRunner(verbosity=1).run(
        unittest.defaultTestLoader.discover(str(HERE), pattern="test_diagnostics.py"))
    if not tests.wasSuccessful():
        raise SystemExit(1)
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    result = compute(config)
    target = HERE / "summary.json"
    table_target = HERE / "tables.md"
    table_text = render(result)
    if args.write:
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                          encoding="utf-8", newline="\n")
        table_target.write_text(table_text, encoding="utf-8", newline="\n")
    elif json.loads(target.read_text(encoding="utf-8")) != result:
        raise SystemExit("T44 summary mismatch: investigate; do not replace accepted inputs")
    elif table_target.read_text(encoding="utf-8") != table_text:
        raise SystemExit("T44 generated tables differ")
    print(f"T44: {tests.testsRun} tests; T37 summary and input hashes reproduced; deterministic summary verified.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Regression for the Stage-A frozen-input gate only; does not run the science matrix."""
import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK))
import stage_a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--frozen-csv", required=True)
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    src = Path(a.frozen_csv)

    expected = cfg["upstream"]["proton_rate_5min_sha256"]
    actual = hashlib.sha256(src.read_bytes()).hexdigest()
    if actual != expected:
        raise RuntimeError(f"canonical input SHA-256 mismatch before frozen(): {actual} != {expected}")

    # Acceptance verifies canonical bytes, paired-valid row count, and frozen L/H.
    stage_a.frozen(src, cfg)
    print(f"PASS canonical frozen input accepted: sha256={actual}")

    # One-byte mutation must fail at the byte gate before any scientific computation.
    data = bytearray(src.read_bytes())
    if not data:
        raise RuntimeError("cannot mutate empty input")
    data[0] ^= 1
    with tempfile.TemporaryDirectory(prefix="stage-a-input-gate-") as td:
        altered = Path(td) / "proton_rate_5min.altered.csv"
        altered.write_bytes(data)
        try:
            stage_a.frozen(altered, cfg)
        except RuntimeError as exc:
            if not str(exc).startswith("frozen CSV SHA-256 mismatch"):
                raise
        else:
            raise AssertionError("altered frozen input was unexpectedly accepted")
    print("PASS deliberately altered frozen input rejected by SHA-256 gate")


if __name__ == "__main__":
    main()

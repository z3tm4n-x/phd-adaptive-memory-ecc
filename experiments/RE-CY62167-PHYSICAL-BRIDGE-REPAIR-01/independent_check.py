#!/usr/bin/env python3
"""Independent repair cross-check; intentionally does not import repair_checks."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--rate-summary")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    c = json.loads(Path(a.config).read_text())
    checks = {}
    err = 1 << 0
    mark2 = (1 << 0) | (1 << 1)
    mark3 = (1 << 0) | (1 << 1) | (1 << 2)
    checks["two_toggle_cancellation"] = (err ^ mark2).bit_count() == 1
    checks["three_toggle_from_single_exceeds"] = (err ^ mark3).bit_count() >= 2
    result = {"checks": checks, "rate_qualification": "NOT_ESTABLISHED", "bound": None}
    if a.rate_summary:
        r = json.loads(Path(a.rate_summary).read_text())
        if r["slice"] != c["slice"]:
            raise SystemExit("slice mismatch")
        W = c["registered_model"]["words"]
        n = c["registered_model"]["data_bits_per_word"]
        tau = c["slice"]["tau_s"]
        I1 = float(r["integral_r"])
        I2 = float(r["integral_r2"])
        pair = W * (n * (n - 1) // 2) * tau * I2
        coeff = (n - 1) * W * I1 / tau
        result["bound"] = {"u_pair_upper": pair, "delta_exec_coefficient_per_s": coeff}
        result["rate_qualification"] = "QUALIFIED_BY_SUPPLIED_FROZEN_SUMMARY"
    if not all(checks.values()):
        raise SystemExit("independent semantic check failed")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Minimal row-level causality extraction for RE-GOES-CAUSAL-INPUT-CONTRACT-01.

This helper does NOT run RADAR, sigma(E), transport, reliability, or control.
It requires the exact 59-file PI-controlled GOES archive already declared by
RE-GOES19-PROTON-RATE-01, verifies those file hashes against input_manifest.json,
loads only the historical GOES adapter, and identifies the rows/directions for
which the historical 390--500 MeV bridge would require its direction-global
median fallback.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import h5py


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--goes-dir", required=True, type=Path,
                    help="directory containing the exact 59 controlled .nc files")
    ap.add_argument("--historical-dir", type=Path,
                    default=Path(__file__).resolve().parents[1] / "RE-GOES19-PROTON-RATE-01")
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--metadata-output", type=Path,
                    help="optional JSON dump of raw source time attrs/bounds discovery")
    args = ap.parse_args()

    hist = args.historical_dir.resolve()
    manifest = json.loads((hist / "input_manifest.json").read_text(encoding="utf-8"))
    expected = {x["name"]: x["sha256"] for x in manifest["goes_archive"]["files"]}
    actual_paths = {p.name: p for p in sorted(args.goes_dir.glob("*.nc"))}
    if set(actual_paths) != set(expected):
        missing = sorted(set(expected) - set(actual_paths))
        extra = sorted(set(actual_paths) - set(expected))
        raise SystemExit(f"controlled-file set mismatch; missing={missing}, extra={extra}")
    for name, want in expected.items():
        got = sha256(actual_paths[name])
        if got != want:
            raise SystemExit(f"hash mismatch for {name}: {got} != {want}")

    if args.metadata_output:
        def dec(v):
            if isinstance(v, bytes):
                return v.decode(errors="replace")
            try:
                if hasattr(v, "tolist"):
                    return v.tolist()
            except Exception:
                pass
            return v
        meta = {"files": [], "note": "raw source metadata only; date_created is not operational availability"}
        for name in sorted(actual_paths):
            with h5py.File(actual_paths[name], "r") as f:
                tds = f["time"]
                bounds_attr = dec(tds.attrs.get("bounds")) if "bounds" in tds.attrs else None
                candidates = [k for k in f.keys() if "time" in k.lower() and ("bound" in k.lower() or "bnd" in k.lower())]
                meta["files"].append({
                    "name": name,
                    "time_coverage_resolution": dec(f.attrs.get("time_coverage_resolution")),
                    "date_created": dec(f.attrs.get("date_created")),
                    "time_attrs": {str(k): dec(v) for k, v in tds.attrs.items()},
                    "time_bounds_attr": bounds_attr,
                    "candidate_time_bounds_datasets": candidates,
                })
        args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
        args.metadata_output.write_text(json.dumps(meta, indent=2, sort_keys=True, default=str)+"\n", encoding="utf-8")

    sys.path.insert(0, str(hist))
    from goes19_adapter import load_directory  # noqa: E402

    goes = load_directory(args.goes_dir)
    rows = []
    counts = {"E": 0, "W": 0}
    for t, timestamp in enumerate(goes.times):
        for d, direction in enumerate(("E", "W")):
            if not bool(goes.valid[t, d]):
                continue
            p10 = float(goes.flux[t, d, -1])
            p11 = float(goes.p11[t, d])
            # Historical _solve_high_gamma() returns None exactly when either
            # input is nonfinite/nonpositive. Positive finite inputs always
            # produce a fitted gamma by bisection. Therefore this is the exact
            # predicate that triggers used_fallback[t,d] in high_energy_gap_bridge().
            local_fit_available = (
                math.isfinite(p10) and p10 > 0.0 and
                math.isfinite(p11) and p11 > 0.0
            )
            fallback = not local_fit_available
            if fallback:
                counts[direction] += 1
                rows.append({
                    "timestamp_utc": timestamp.isoformat(),
                    "direction": direction,
                    "algorithm_version": str(goes.version[t]),
                    "p10_positive_finite": int(math.isfinite(p10) and p10 > 0.0),
                    "p11_positive_finite": int(math.isfinite(p11) and p11 > 0.0),
                    "historical_direction_median_fallback": 1,
                })

    diag = json.loads((hist / "rate_diagnostics.json").read_text(encoding="utf-8"))
    want_counts = diag["high_energy_gap_bridge"]["diagnostic"]["fallback_rows"]
    if counts != {"E": int(want_counts["E"]), "W": int(want_counts["W"])}:
        raise SystemExit(f"fallback count mismatch: extracted={counts}, historical={want_counts}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "timestamp_utc", "direction", "algorithm_version",
        "p10_positive_finite", "p11_positive_finite",
        "historical_direction_median_fallback",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(json.dumps({"fallback_rows": counts, "rows_written": len(rows), "status": "PASS"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

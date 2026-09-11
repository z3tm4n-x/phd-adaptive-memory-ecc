#!/usr/bin/env python3
"""Bounded checks fixed before RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01 execution.

No environment reconstruction is implemented. Numerical registered-risk qualification
requires a provenance-checked frozen summary for the exact preregistered slice.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path


def semantic_checks() -> dict:
    out = {}
    # Clean read: the check is identity; with no correcting write a post-check hit persists.
    clean = frozenset()
    post = clean.symmetric_difference({3})
    out["clean_no_write_post_hit_persists"] = post == frozenset({3})
    # Singleton read: physical storage stays erroneous until correction write completes.
    physical = frozenset({0})
    ideal_at_check = frozenset()
    after_distinct = physical.symmetric_difference({1})
    out["rmw_distinct_hit_first_passage"] = len(after_distinct) >= 2 and len(ideal_at_check) == 0
    # Same-bit toggle can cancel.
    out["rmw_same_bit_cancellation"] = len(physical.symmetric_difference({0})) == 0
    # First passage remains historical even if writeback later clears the word.
    first_passed = len(after_distinct) >= 2
    after_write = frozenset()
    out["first_passage_persists_after_write"] = first_passed and len(after_write) == 0
    return out


def compute_bound(cfg: dict, integral_r: float, integral_r2: float, boundary_term: float = 0.0) -> dict:
    W = cfg["registered_model"]["words"]
    n = cfg["registered_model"]["data_bits_per_word"]
    tau = cfg["slice"]["tau_s"]
    eps = cfg["slice"]["epsilon_analysis"]
    pair = W * math.comb(n, 2) * tau * integral_r2
    coeff = (n - 1) * W * integral_r / tau
    rows = []
    for delta in cfg["executor"]["sensitivity_delta_s"]:
        de = coeff * delta + boundary_term
        total = min(1.0, pair + de)
        rows.append({"delta_s": delta, "delta_exec_upper": de, "u_reg_cw_upper": total, "passes_epsilon": total <= eps})
    delta_max = None
    if coeff > 0 and eps > pair + boundary_term:
        delta_max = (eps - pair - boundary_term) / coeff
    return {
        "integral_r": integral_r,
        "integral_r2": integral_r2,
        "u_pair_upper": pair,
        "delta_exec_coefficient_per_s": coeff,
        "boundary_term": boundary_term,
        "delta_max_for_epsilon_s": delta_max,
        "sensitivity": rows
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--rate-summary", help="JSON with integral_r, integral_r2, source_identity and exact slice")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text())
    result = {"semantic_checks": semantic_checks(), "rate_qualification": "NOT_ESTABLISHED", "bound": None}
    if not all(result["semantic_checks"].values()):
        raise SystemExit("semantic check failed")
    if args.rate_summary:
        p = Path(args.rate_summary)
        rs = json.loads(p.read_text())
        required = {"integral_r", "integral_r2", "source_identity", "slice"}
        if not required.issubset(rs):
            raise SystemExit("rate summary missing provenance fields")
        if rs["slice"] != cfg["slice"]:
            raise SystemExit("rate summary slice mismatch")
        result["rate_input_sha256"] = sha256(p)
        result["rate_source_identity"] = rs["source_identity"]
        result["bound"] = compute_bound(cfg, float(rs["integral_r"]), float(rs["integral_r2"]), float(rs.get("boundary_term", 0.0)))
        result["rate_qualification"] = "QUALIFIED_BY_SUPPLIED_FROZEN_SUMMARY"
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

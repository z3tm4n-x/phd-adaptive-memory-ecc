#!/usr/bin/env python3
"""T50: bounded, read-only transformations of pinned inputs. Standard library only."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta
from fractions import Fraction as F
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PAPER = "experiments/RE-CY62167-PAPER-COMPLETION-01/"
EXECUTOR = "experiments/RE-CY62167-EXECUTOR-TIMING-GATE-01/reference-continuation-01/"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_bytes(manifest):
    """Never use worktree copies of accepted sources (including CRLF variants)."""
    out = {}
    for path, expected in manifest["files"].items():
        data = subprocess.check_output(
            ["git", "show", manifest["base_sha"] + ":" + path], cwd=ROOT)
        require(sha(data) == expected["sha256"], "source SHA256 mismatch: " + path)
        require(len(data) == expected["bytes"], "source length mismatch: " + path)
        out[path] = data
    return out


def csv_rows(data):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


def number(x, unit):
    x = F(x)
    return {"exact_from_serialized_model": str(x),
            "decimal_approx": format(float(x), ".17g"), "unit": unit}


def integrals(rates, durations):
    require(len(rates) == len(durations) and bool(rates), "empty/misaligned series")
    rates, durations = list(map(F, rates)), list(map(F, durations))
    require(all(x >= 0 for x in rates), "negative rate")
    require(all(x > 0 for x in durations), "nonpositive duration")
    T = sum(durations, F(0))
    I1 = sum((r * dt for r, dt in zip(rates, durations)), F(0))
    I2 = sum((r * r * dt for r, dt in zip(rates, durations)), F(0))
    J = T * I2 / I1**2 if I1 else None
    require(J is None or J >= 1, "Cauchy check failed")
    return T, I1, I2, J


def validate_selected(rows, spec):
    require(len(rows) == spec["rows"], "selected row count")
    t = datetime.fromisoformat(spec["start_utc"])
    for row in rows:
        require(datetime.fromisoformat(row["timestamp_utc"]) == t, "gap/duplicate/order")
        require(F(row["duration_s"]) == spec["dt_s"], "bin width")
        for k in ("shield_mm", "sigma_model", "direction_scenario", "scenario", "mapping"):
            require(row[k] == spec[k], "scenario mismatch: " + k)
        require(F(row[spec["rate_column"]]) ==
                spec["array_bits"] * F(row[spec["r_column"]]), "bit/array normalization")
        require(F(row[spec["direct_column"]]) >= 0, "negative direct rate")
        t += timedelta(seconds=spec["dt_s"])
    require(t == datetime.fromisoformat(spec["end_exclusive_utc"]), "wrong horizon")


def one(rows, selector):
    matches = [r for r in rows if all(r[k] == v for k, v in selector.items())]
    require(len(matches) == 1, "nonunique/missing selector: " + str(selector))
    return matches[0]


def is_target(row, shields):
    return F(row["shield_g_cm2"]) in {F(str(d)) for d in shields}


def normalized_orbit(archive, spec):
    """Parse supplied spectra only; no transport, interpolation or convolution."""
    data = Path(archive).read_bytes()
    require(sha(data) == spec["archive_sha256"], "COSRAD archive SHA256 mismatch")
    outputs = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member, meta in spec["members"].items():
            raw = z.read(member)
            require(sha(raw) == meta["sha256"], "COSRAD member SHA256 mismatch")
            text = raw.decode("ascii")
            require("FLUENCE [particles/(MeV/nuclon*cm2)]" in text, "not orbit fluence")
            require("10 year(s)" in text and "in orbit" in text, "wrong domain")
            if member.endswith("sfn.txt"):
                require("Probability = 0.100" in text, "wrong SEP probability label")
            numeric = []
            for line in text.splitlines():
                cells = line.split()
                if len(cells) != meta["species"] + 1:
                    continue
                try:
                    vals = list(map(F, cells))
                except ValueError:
                    continue
                require(all(v >= 0 for v in vals), "negative spectrum entry")
                numeric.append(cells)  # original scientific-decimal tokens preserved
            require(len(numeric) == meta["rows"], "wrong spectrum shape")
            require(all(F(b[0]) > F(a[0]) for a, b in zip(numeric, numeric[1:])),
                    "energy grid not strictly increasing")
            buf = io.StringIO(newline="")
            writer = csv.writer(buf, lineterminator="\n")
            writer.writerow(["energy_MeV_per_nucleon"] +
                            [f"Z{z:02}" for z in range(1, meta["species"] + 1)])
            writer.writerows(numeric)
            outputs[meta["output"]] = buf.getvalue()
    return outputs


def orbit_summary(spec):
    out = []
    for member, meta in spec["members"].items():
        data = (HERE / meta["output"]).read_bytes()
        require(sha(data) == meta["normalized_sha256"], "normalized fluence SHA256")
        rows = csv_rows(data)
        require(len(rows) == meta["rows"], "normalized fluence shape")
        require(len(rows[0]) == meta["species"] + 1, "normalized species count")
        out.append({"member": member, "member_sha256": meta["sha256"],
                    "normalized_input": meta["output"], "rows": len(rows),
                    "Z_columns": [1, meta["species"]],
                    "energy_min_MeV_n": rows[0]["energy_MeV_per_nucleon"],
                    "energy_max_MeV_n": rows[-1]["energy_MeV_per_nucleon"],
                    "unit": spec["units"], "location": spec["location"],
                    "status": spec["status"], "parent_exposure_behind_shield": None})
    return out


def build(config, blobs):
    jobs = config["conversion_jobs"]
    spec = jobs["historical_series"]
    rows = csv_rows(blobs[spec["path"]])
    validate_selected(rows, spec)
    dt = [r["duration_s"] for r in rows]
    T, I1, I2, J = integrals([r[spec["rate_column"]] for r in rows], dt)
    _, R1, R2, _ = integrals([r[spec["r_column"]] for r in rows], dt)
    _, D1, _, _ = integrals([r[spec["direct_column"]] for r in rows], dt)
    previous = json.loads(blobs[EXECUTOR + "bounds.json"])
    require(R1 == F(previous["I1"]["exact"]) and R2 == F(previous["I2"]["exact"]),
            "accepted per-bit I1/I2 not reproduced")
    hist = {"source": spec["path"], "scope": spec, "T_s": str(T),
            "I1_nu": number(I1, "model bit inversions on data32 array"),
            "I2_nu": number(I2, "(model bit inversions)^2 / s"),
            "I1_r": number(R1, "model bit inversions / bit"),
            "I2_r": number(R2, "(model bit inversions / bit)^2 / s"),
            "I1_registered_direct": number(D1, "registered direct surrogate exposure"),
            "J": number(J, "1") if J is not None else None,
            "accepted_I1_I2_exact_match": True, "full39_R0A_eligible": False}

    background_spec = jobs["stationary_background"]
    geo = csv_rows(blobs[background_spec["path"]])
    shields = config["scenario"]["shield_g_cm2"]
    geo = [r for r in geo if is_target(r, shields) and
           r["rate_reconstruction_route"] == background_spec["route"]]
    require(len(geo) == 10, "target GCR row count")
    backgrounds = []
    for row in geo:
        if (row["mapping_id"] != background_spec["mapping_id"] or
                row["estimate_type"] not in background_spec["estimate_types"]):
            continue
        nu = F(row["nu_accumulation_total_bit_s-1"])
        t, b1, b2, bj = integrals([nu], [config["scenario"]["nominal_T_s"]])
        backgrounds.append({"source_row": row, "T_s": str(t),
                            "original_tau_certificate_T_s": config["scenario"]["historical_article_T_s"],
                            "I1_nu": number(b1, "model bit inversions on data32 array"),
                            "I2_nu": number(b2, "(model bit inversions)^2 / s"),
                            "J": number(bj, "1"), "status": background_spec["status"],
                            "full39_R0A_eligible": False})

    sep = [r for r in csv_rows(blobs[PAPER + "sep_peak_rates.csv"]) if is_target(r, shields)]
    require(len(sep) == 10 and all("NO-MISSION-INTEGRATION" in r["status"] for r in sep),
            "SEP peak cannot be integrated as a mission series")
    components = [r for r in csv_rows(blobs[PAPER + "cosrad_rates_pi_reconstructed.csv"])
                  if is_target(r, shields) and r["mapping_id"] == "W_00_01" and
                  r["estimate_type"] == "POINT" and
                  r["rate_reconstruction_route"] == "SPECTRAL_EXTERNAL_CONVOLUTION"]
    require(len(components) == 2 and
            {r["environment_scenario"] for r in components} == {"GCR_ONLY"},
            "unexpected committed GCR component split")

    gs = jobs["goes_growth"]
    t44 = json.loads(blobs[gs["path"]])
    t37 = json.loads(blobs["experiments/t37-lambda-recipe/summary.json"])
    require(t44["source_sha256"] == t37["source_sha256"], "T37/T44 source identity")
    growth = []
    for row in t44["relative_growth"]:
        if row["direction"] not in gs["directions"] or row["mask"] not in gs["masks"]:
            continue
        for threshold in row["thresholds"]:
            require(threshold["threshold_fraction"] in gs["threshold_fractions"], "threshold grid")
            growth.append({k: row[k] for k in ("series", "direction", "mask", "pair_audit",
                                               "B_sample_per_bit_s", "unit_growth", "type")} |
                          {k: v for k, v in threshold.items() if k != "crossings"})
    require(len(growth) == 12, "growth selection")

    r3 = jobs["r3"]
    groups = csv_rows(blobs[r3["groupings_path"]])
    counts = dict(Counter(r["N_direct_all_series"] for r in groups))
    require(len(groups) == 55 and counts == r3["groupings_expected"], "45/9/1 regression")
    certificate = []
    for mapping in r3["certificate_mappings"]:
        row = one(geo, {"shield_g_cm2": r3["certificate_shield_g_cm2"],
                        "mapping_id": mapping, "estimate_type": r3["certificate_estimate"]})
        certificate.append({"source_row": row,
                            "probe_s": r3["certificate_probe_s"],
                            "passes_saved_sufficient_period_bound":
                            F(r3["certificate_probe_s"]) <= F(row["tau_max_U_s"])})
    witness = one(csv_rows(blobs[r3["transition_path"]]), r3["transition_selector"])
    require(F(witness["F_exact_tau_to"]) < F(witness["epsilon_analysis"]) <
            F(witness["F_exact_tau_from"]), "saved action witness does not straddle epsilon")
    coverage = jobs["coverage_sensitivity"]
    e = F(coverage["conditional_epsilon_including_env_and_channel"])
    sensitivity = [{"delta_theta_illustrative": d,
                    "union_upper": number(min(F(1), e + F(d)), "probability"),
                    "remaining_conditional_budget_signed": number(e - F(d), "probability")}
                   for d in coverage["delta_theta_grid"]]
    W = config["scenario"]["useful_bytes"] * 8 // 32
    return {"base_sha": config["base_sha"], "issue_updated_at": config["issue_updated_at"],
            "configuration_sha256_canonical_json": sha(json.dumps(
                config, sort_keys=True, separators=(",", ":")).encode()),
            "input_sha256": {p: sha(b) for p, b in blobs.items()},
            "arithmetic": "exact fractions of serialized decimals; approximate displays, no physical CI",
            "architecture": {"words": W, "external_active_bits": 39 * W,
                             "data_bits": 32 * W, "padding_bits": 9 * W,
                             "addressed_bytes": 48 * W // 8, "installed_bytes": 3 * 2**21,
                             "counter_bits_outer": W.bit_length(),
                             "counter_bits_ERR_sum": (3 * W).bit_length(),
                             "counter_bits_all_flags": (4 * W).bit_length()},
            "orbit_fluence": orbit_summary(jobs["orbit_fluence"]),
            "historical_integrals": hist, "stationary_background_integrals": backgrounds,
            "target_GCR_saved_rows": geo, "target_SEP_peak_saved_rows": sep,
            "target_particle_component_saved_rows": components,
            "GOES_growth_diagnostics_reused": growth,
            "R3": {"groupings": counts, "probability_over_groupings": None,
                   "saved_certificate_comparison": certificate,
                   "saved_GOES_transition": witness,
                   "zero_count_demo": {"alpha": r3["zero_count_alpha_demo"],
                                       "Poisson_mean_upper_approx": -math.log(float(r3["zero_count_alpha_demo"])),
                                       "sigma_upper_cm2": None,
                                       "status": "conditional statistical formula; aligned fluence and detection completeness absent"}},
            "theta_coverage_sensitivity": sensitivity,
            "R0A_full39": {"I1": None, "I2": None, "J": None,
                           "lambda_inputs": config["lambda_parent_inputs"],
                           "ready_for_algorithm_comparison": False,
                           "decisive_contract": "joint full39 post-embedded-ECC marked response / observation domination with a justified Theta"}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--emit", action="store_true", help="print regenerated summary JSON; do not write files")
    p.add_argument("--archive", help="also verify normalized fluence inputs against the original results.zip")
    p.add_argument("--extract-orbit", help="print normalized input text as JSON from pinned results.zip")
    args = p.parse_args()
    config = read_json(HERE / "config.json")
    if args.extract_orbit:
        print(json.dumps(normalized_orbit(args.extract_orbit, config["conversion_jobs"]["orbit_fluence"])))
        return
    manifest = read_json(HERE / "sources.json")
    require(manifest["base_sha"] == config["base_sha"], "base mismatch")
    blobs = source_bytes(manifest)
    if args.archive:
        for path, text in normalized_orbit(args.archive, config["conversion_jobs"]["orbit_fluence"]).items():
            require((HERE / path).read_bytes() == text.encode(), "normalized input differs: " + path)
    result = build(config, blobs)
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return
    require(result == read_json(HERE / "summary.json"), "summary differs; inspect with --emit")
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_*.py")
    require(unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful(), "tests failed")
    print(f"T50 PASS: {len(blobs)} pinned sources; exact historical I1/I2; 45/9/1; "
          "R0-A full39 remains NOT_QUALIFIED.")
    print("Runtime:", sys.version.split()[0], sys.platform)


if __name__ == "__main__":
    main()

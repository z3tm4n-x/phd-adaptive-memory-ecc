#!/usr/bin/env python3
"""T152: audit two actual PSI matrices and unchanged contract arithmetic.

This is not a physical-response estimator, fit, calendar search or Monte Carlo.
--check never overwrites the published report. --write is explicit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
import re
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHANNELS = "tc1 s12 s13 s14 s15 tc2 s25 c1 c2 c3 c4 tc3 s32 s33 s34".split()


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def decimal_interval(value, digits=15):
    """Exact enclosing decimal endpoints, no binary floats or hidden tolerance."""
    value = F(value)
    scale = 10 ** digits
    low = value.numerator * scale // value.denominator
    high = -((-value.numerator * scale) // value.denominator)

    def display(n):
        sign = "-" if n < 0 else ""
        n = abs(n)
        return f"{sign}{n // scale}.{n % scale:0{digits}d}"

    return [display(low), display(high)]


def matrix_audit(spec, data):
    if hashlib.sha256(data).hexdigest() != spec["sha256"]:
        raise ValueError(f"changed source: {spec['cache_name']}")
    text = data.decode("ascii")
    if "IREM including spacecraft" not in text or "September 2002" not in text:
        raise ValueError("wrong variant/version")
    columns = re.findall(r"column\s+(\d+):\s+([a-z0-9]+)\s+\[counts\]", text)
    if columns != [(f"{i:02}", name) for i, name in enumerate(CHANNELS, 5)]:
        raise ValueError("channel order/units mismatch")
    angles = {}
    for axis, bound, value in re.findall(r"(Theta|Phi)\s+(min|max)\s+\[Degrees\]\s+([\d.]+)", text):
        angles[f"{axis}_{bound}"] = str(F(value))
    if angles != {"Theta_min": "0", "Theta_max": "180", "Phi_min": "0", "Phi_max": "360"}:
        raise ValueError("different angular domain")
    rows = [[F(x.strip()) for x in line.split(",")]
            for line in text.splitlines() if "," in line]
    if len(rows) != spec["expected_rows"] or any(len(r) != 19 for r in rows):
        raise ValueError("wrong matrix dimensions")
    if [rows[0][0], rows[-1][1]] != list(map(F, spec["expected_range_MeV"])):
        raise ValueError("energy range mismatch")
    if any(a[1] != b[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("gap/overlap in energy bins")
    for r in rows:
        if not (0 < r[0] < r[1] and r[2] > 0 and r[3] > 0):
            raise ValueError("invalid energy/exposure")
        if any(c < 0 or c.denominator != 1 for c in r[4:]):
            raise ValueError("noninteger/negative simulated count")
    zero_tc3 = sum(r[15] == 0 for r in rows)
    all_zero = sum(all(c == 0 for c in r[4:]) for r in rows)
    if (zero_tc3, all_zero) != (spec["expected_zero_TC3_rows"], spec["expected_all_zero_rows"]):
        raise ValueError("zero-row audit mismatch")
    selected = []
    for energy in spec["sample_energy_min_MeV"]:
        r, = [r for r in rows if r[0] == F(energy)]
        selected.append({
            "energy_MeV_exact": [str(r[0]), str(r[1])],
            "simulated_N": str(r[2]), "tabulated_f_per_cm2": str(r[3]),
            "TC3_simulated_count": str(r[15]),
            "TC3_over_f_cm2_exact": str(r[15] / r[3]),
            "TC3_over_f_cm2_decimal_enclosure": decimal_interval(r[15] / r[3]),
            "kind": "normalised table entry, NOT a confidence lower, angular lower, or memory ratio"
        })
    return {"source": spec["id"], "sha256": spec["sha256"],
            "rows": len(rows), "columns": 19, "channels": CHANNELS,
            "energy_range_MeV": spec["expected_range_MeV"], "angle_header_degrees": angles,
            "angular_resolved_axis_in_file": False, "other_particle_species_in_file": False,
            "zero_TC3_rows": zero_tc3, "all_zero_rows": all_zero,
            "sample_rows": selected}


def run(cache, fetch):
    sources = json.loads((HERE / "sources.json").read_text())
    contract = json.loads((HERE / "contract.json").read_text())
    pins = json.loads((HERE / "pinned_inputs.json").read_text())
    checks = []

    def check(name, good):
        if not good:
            raise AssertionError(name)
        checks.append(name)

    for name, expected in pins["blob_sha1"].items():
        check("unchanged accepted input: " + name,
              git_blob_sha((ROOT / name).read_bytes()) == expected)
    accepted = json.loads((ROOT / "experiments/next-route-20261013/final-report.json").read_text())
    check("accepted theorem still N=5.25 and no E transfer",
          accepted["proved_N"] == "5.25" and accepted["E_transfer_proved"] is False)
    req = contract["requirements_not_device_properties"]
    check("epsilon/D*/horizon unchanged", (req["epsilon"], req["D_star"], req["T_s"]) ==
          ("0.001", "0.0002802445", "315576000"))
    check("selected a/mu/window/stride/d unchanged", tuple(req[x] for x in
          ["a_lower", "quiet_MGF_mu_upper_per_window", "window_nominal_s", "stride_nominal_s", "post_window_nominal_s"])
          == ("100000", "15.471554714", "1", "0.5", "1"))
    check("lifetime quotas/outage/full X retained", tuple(req[x] for x in
          ["lifetime_delta_M", "lifetime_alpha_M", "expanded_outage_fraction_upper", "X_rate", "time_margin_fraction"])
          == ("0.000001", "0.000001", "0.001", "0.0011", "0.1"))
    matrices = []
    for spec in sources["sources"]:
        if "cache_name" not in spec:
            continue
        path = cache / spec["cache_name"]
        if not path.exists():
            if not fetch:
                raise FileNotFoundError(f"{path}: supply cache or --fetch; no guessed response")
            with urllib.request.urlopen(spec["url"], timeout=25) as stream:
                data = stream.read()
            if hashlib.sha256(data).hexdigest() != spec["sha256"]:
                raise ValueError(f"download hash mismatch: {spec['id']}; no replacement accepted")
            cache.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        matrices.append(matrix_audit(spec, path.read_bytes()))
        check("matrix hash/schema/dimensions/ranges/counts: " + spec["id"], True)
    check("one primary instrument, distinct p/e arrays", len(matrices) == 2)

    a, b, B = (F(req[k]) for k in ["a_lower", "nu_quiet_upper_per_s", "nu_peak_per_s"])
    check("required ideal peak arithmetic", a * B == F("24468.2704"))
    check("quiet ideal arithmetic", a * b == F("15.4704"))
    # This diagnostic does not assign eta or Poisson to IREM.
    ideal_mu = (a * b + F("0.001")) * F(req["clock_scale"][1])
    check("accepted ideal quiet sufficient example", ideal_mu == F(req["quiet_MGF_mu_upper_per_window"]))

    period = F(contract["published_device_facts"]["IREM_TDB_period_s"])
    stride, deadline = F(req["stride_nominal_s"]), F(req["post_window_nominal_s"])
    check("8s broadcasts exceed stride plus deadline", period > stride + deadline)
    # Witness: broadcast at 0, requested window [0,1], next broadcast at 8.
    delay = period - F(req["window_nominal_s"])
    check("causal requested-window deadline missed", delay > deadline)
    budgets = {label: str(F(req["X_burst_s"]) + F(req["X_rate"]) * F(h))
               for label, h in [("1ms", "0.001"), ("0.5s", "0.5"), ("1s", "1")]}
    check("all-chain 1ms shared-bus allowance is 1200ns", F(budgets["1ms"]) == F("0.0000012"))
    check("outage allowance is not a fresh risk budget",
          F(req["expanded_outage_fraction_upper"]) * F(req["T_s"]) == 315576)
    unknown_names = [k for k in contract["same_Y_candidate"] if k not in
                     ["name", "definition", "onboard_access_and_mapping_verified"]]
    check("physical unknowns remain null", all(contract["same_Y_candidate"][k] is None for k in unknown_names))
    check("same-Y raw-mode verification not asserted", contract["same_Y_candidate"]["onboard_access_and_mapping_verified"] is False)
    check("outward interval regression, inexact fraction enclosed",
          F(decimal_interval(F(1, 3))[0]) <= F(1, 3) <= F(decimal_interval(F(1, 3))[1]))
    check("outward interval regression, exact value preserved",
          decimal_interval(F(0)) == ["0.000000000000000", "0.000000000000000"])
    corrupted = bytearray((cache / "IREM_eresp.drm").read_bytes()); corrupted[-2] ^= 1
    try:
        matrix_audit(next(s for s in sources["sources"] if s["id"] == "P2"), bytes(corrupted))
    except ValueError:
        check("changed matrix rejected before use", True)
    else:
        raise AssertionError("corrupted matrix accepted")

    return {"task": 152, "checked_date": sources["checked_date"],
            "base_sha": contract["base_sha"], "science_sha": contract["accepted_science_sha"],
            "kind": "external-file audit and exact requirement arithmetic, not a new physical certificate",
            "matrices": matrices,
            "requirement_arithmetic": {
                "ideal_peak_lower_counts_per_s": str(a * B),
                "ideal_peak_lower_counts_per_s_decimal": "24468.2704",
                "ideal_quiet_example_mu": str(ideal_mu),
                "broadcast_period_over_required_stride": str(period / stride),
                "specific_requested_window_wait_s": str(delay),
                "required_post_window_s": str(deadline),
                "X_all_chain_budget_seconds": budgets,
                "expanded_outage_allowance_s": "315576",
                "note": "All numbers here are mathematical requirements/diagnostics, not measured channel properties."},
            "candidate_physical_parameters": {k: None for k in unknown_names},
            "joint_channel_contract_confirmed": False,
            "standard_IREM_broadcast_meets_unchanged_window_deadlines": False,
            "physical_U100_qualified": False,
            "instrument_specific_gain": None,
            "decision": contract["decision"],
            "checks": checks, "check_count": len(checks), "all_audit_checks_pass": True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache", type=Path, required=True,
                   help="external scratch cache; full source files are not distributed")
    p.add_argument("--fetch", action="store_true", help="download only missing two pinned numeric files")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="compare, never overwrite report.json")
    group.add_argument("--write", action="store_true", help="explicitly create/update this task's report")
    args = p.parse_args()
    data = canonical(run(args.cache, args.fetch))
    path = HERE / "report.json"
    if args.check:
        if path.read_text() != data:
            raise SystemExit("report differs; not overwritten")
        print(f"PASS: {json.loads(data)['check_count']} addressed checks; report matches byte-for-byte")
    elif args.write:
        path.write_text(data)
        print(f"WROTE: {path}; {json.loads(data)['check_count']} addressed checks")
    else:
        sys.stdout.write(data)


if __name__ == "__main__":
    main()

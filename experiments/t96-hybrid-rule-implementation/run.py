"""One-command Stage-A reproduction; default verifies, --write refreshes own output."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction as F
import io
import json
import sys
import unittest

from reference import (HERE, ROOT, Calendar, Gate, Parameters, Rule, load_inputs,
                       mapping_report, resource_bounds)
from test_reference import packet


def encode(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    return value


def names(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from names(test)
        else:
            yield test.id()


def trace(p):
    """Directed interface points; NOT the Stage-G SGPS campaign."""
    r, g, c = Rule(p), Gate(p), Calendar(p)
    r.epoch_begin(1, 0, p.config_id)
    events = []
    for i in range(7):
        now = p.deadline(i)
        if i == 3:
            r.missing(i, now)
            g.loss(now)
            status = "missing"
        else:
            status = r.message(packet(p, i), now)
        g.receive(r.permission(now), now)
        j = now // p.g
        while c.slot(j).decision < now or c.slot(j).mandatory:
            j += 1
        d = g.freeze(c.slot(j), c.slot(j).decision)
        events.append({"window": i, "deadline": now, "status": status,
                       "LOW": r.low, "holdM": r.holdM,
                       "decision": asdict(d), "certificate": r.lifetime_certificate})
    return events


def build(test_names):
    cfg, h, row = load_inputs()
    p = Parameters.accepted()
    prior = json.loads((ROOT / "experiments/t95-method-regime-map/report.json")
                       .read_text(encoding="utf-8"))
    anchor = next(r for r in prior["rows"] if r["name"] == "anchor")
    # Carried with provenance, NOT re-estimated from a finite trace.
    accepted = {k: anchor[k] for k in ("risk_upper", "normal_price_upper",
                    "loss_forever_risk_upper", "S_full_price_upper")}
    accepted["probability_margin"] = F(h["fixed_contract"]["epsilon"]) - F(anchor["risk_upper"])
    accepted["source"] = "accepted T95 anchor; not inferred from Stage-A tests"
    resource = resource_bounds(row)
    assert resource["peak_upper"] <= F(h["resources"]["peak_limit"])
    assert resource["application_delay_margin_upper_s"] <= F(h["resources"]["app_delay_with_margin_limit_s"])
    m = mapping_report(p, h, row, cfg["clock_mapping"]["core_period_virtual_ticks"])
    assert m["joint_U_required_s"] == F(h["conditional_timing"]["joint_U_WCET_required_s"])
    assert m["alarm_to_first_fence_upper_s"] == F(h["conditional_timing"]["alarm_to_first_new_fence_s"])
    return encode({"task": 96, "stage": "A", "issue": 103,
        "base_sha": cfg["base_sha"], "science_sha": cfg["science_sha"],
        "scope": "executable specification, not RTL/firmware/physical qualification",
        "source_blobs_checked": cfg["sources"],
        "parameters": asdict(p), "address_inverse": Calendar(p).inverse,
        "test_count": len(test_names), "tests": sorted(test_names),
        "coverage": {"full_W_address_residues": p.W,
                     "full_W_phase_residues": p.W,
                     "small_W": 8, "small_ka": 3,
                     "small_boolean_masks": 256, "small_slots_per_mask": 16,
                     "small_model_probability_transfer": False,
                     "formal_RTL_proof_performed": False},
        "accepted_reference": accepted, "independent_resource_substitution": resource,
        "clock_representation": m, "directed_trace": trace(p),
        "not_confirmed": {"physical_full38_clean_U": None, "physical_Dstar": None,
            "physical_monitor": None, "physical_joint_WCET": None,
            "FPGA_or_flight_CPU": None, "STA_CDC": None,
            "mission_probability_proved_by_simulation": False,
            "stages_B_C_D_started": False}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write only T96-A outputs/reproduction.json")
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_reference.py")
    test_names = list(names(suite))
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=1).run(suite)
    if not result.wasSuccessful():
        print(log.getvalue(), file=sys.stderr)
        return 1
    report = build(test_names)
    path = HERE / "outputs/reproduction.json"
    if args.write:
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not path.exists() or json.loads(path.read_text(encoding="utf-8")) != report:
        print("Stage-A output differs; inspect changes before using --write", file=sys.stderr)
        return 1
    print(f"T96-A: {result.testsRun}/{len(test_names)} tests; 8 pinned inputs; reproduction.json matches")
    print("Full W address/phase residues checked; 256 small-model masks. RTL/formal/WCET not claimed.")
    bounds = report["independent_resource_substitution"]
    print(f"Conditional resource upper: peak {float(F(bounds['peak_upper']))*100:.9f}%; "
          f"application delay with margin {float(F(bounds['application_delay_margin_upper_s']))*1e6:.9f} us")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

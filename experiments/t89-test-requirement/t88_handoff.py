"""Read the immutable T88 delivery; check the transfer, not rerun its search.

No threshold is inferred, interpolated or replaced by its upper endpoint.
Risk certificates remain conditional on all T88 channel/resource contracts.
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction as Q

from fluence import REPO, decimal_text, rational, validate_threshold_handoff

T88_SHA = "da4de9c6684efa20de155b422dd0b25f50930108"
KEYS = {(s, v) for s in ("3", "2.5")
        for v in ("combined", "monitor-only", "ERR-only")}


def require(condition, message):
    if not condition:
        raise ValueError("T88 transfer: " + message)


def read_bundle(cfg):
    bundle = {}
    for name, path in cfg["T88_handoff"]["snapshots"].items():
        data = (REPO/path).read_bytes()
        require(hashlib.sha256(data).hexdigest() == cfg["source_sha256"][path],
                "snapshot checksum mismatch: " + path)
        bundle[name] = json.loads(data)
    return bundle


def price_fields(risk, slack, cost, eps, require_one_percent=False):
    risk, slack, cost = map(rational, (risk, slack, cost))
    require(0 <= risk <= eps and slack >= 0 and risk+slack == eps,
            "risk upper + slack must equal epsilon exactly")
    require(0 <= cost <= 1, "invalid occupied-time fraction")
    require(not require_one_percent or cost <= Q(".01"), "1% certificate exceeded")
    return {"T88_risk_upper_exact": str(risk), "T88_risk_slack_exact": str(slack),
            "T88_risk_slack_lower": decimal_text(slack, 18, False),
            "T88_quiet_tax_upper_exact": str(cost),
            "T88_quiet_tax_upper_pct": decimal_text(100*cost, 9),
            "one_percent_certificate": cost <= Q(".01")}


def validate_bundle(cfg, bundle):
    """Cross-check exact supplied fractions, context and lower endpoints."""
    pinned = cfg["T88_handoff"]
    require(pinned["source_sha"] == T88_SHA, "unexpected numerical SHA")
    h, summary = bundle["handoff"], bundle["summary"]
    contract, protocol = h["contract"], bundle["protocol"]
    require(h["issue"] == 88 and h["to_issue"] == 89, "wrong handoff")
    require(h["only_safe_lower_ends_for_test_request"] is True, "safe-end policy missing")
    require(contract == protocol["versions"], "protocol/context mismatch")
    require(h["engineering_source_sha256"] == protocol["source_hashes"], "source hash mismatch")
    require(h["versions"]["architecture_sha"] == cfg["T81_sha"], "wrong T81")
    require(h["versions"]["theory_sha"] == pinned["theory_sha"]
            and h["versions"]["engineering_sha"] == pinned["T82_sha"], "wrong T80/T82")
    require(all(h["versions"][k] == contract[k] for k in h["versions"]), "version mismatch")
    require(contract["architecture"] == "internal38" and contract["input_set"] == "T73_published"
            and rational(contract["margin"]) == Q(".1"), "architecture/input set/margin mismatch")
    require(set(contract["shields_g_cm2"]) == {"3", "2.5"}
            and set(contract["modes"]) == {v for _, v in KEYS}, "wrong family")
    require(contract["search"]["full_method_completeness_claimed"] is False,
            "do not promote finite-family results to global optima")
    require(rational(contract["D_bracket_tolerance"]) == Q("1e-9")
            and rational(contract["cost_limit"]) == Q(".01"), "threshold contract changed")
    require(h["physical_qualification"] is False and protocol["physical_qualification"] is False
            and contract["physical_qualification"] is False, "physical qualification not supplied")
    require(all(contract[k] is None for k in ("physical_D_upper", "physical_ERR_lower",
                "physical_monitor_lower", "physical_joint_WCET_s")), "physical null replaced")
    path = pinned["snapshots"]["effective_inputs"]
    require(h["effective_inputs_sha256"] == cfg["source_sha256"][path], "effective-input hash mismatch")
    require(protocol["accepted_files_unchanged"] is True
            and protocol["independent_checks"]["success"] is True
            and all(r["returncode"] == 0 for r in protocol["regressions"]), "source verification failed")
    eps = rational(cfg["scenario"]["memory_epsilon_conditional"])
    effective = bundle["effective_inputs"]
    require(len(effective) == 2 and {r["shield"] for r in effective} == {"3", "2.5"}, "effective shields")
    for row in effective:
        env = row["environment"]
        require(env["n"] == 38 and env["W"] == cfg["scenario"]["W"]
                and rational(env["T"]) == cfg["scenario"]["mission_seconds"]
                and rational(env["eps"]) == eps, "mission/word/risk mismatch")
        require(row["physical_qualification"] is False
                and row["service"]["physical_joint_U_WCET_s"] is None
                and row["mark_contract"]["unknown_full38_smu_upper"] is None, "physical input changed")
        require(row["channel"] == contract["monitor"], "diagnostic channel mismatch")
    indexed = {(r["shield"], r["mode"]): r for r in summary}
    require(len(summary) == 6 and set(indexed) == KEYS, "six distinct summary rows required")
    declared = {(r["shield_g_cm2"], r["variant"]): r
                for r in validate_threshold_handoff(pinned)}
    require(all(r["global_optimum_claimed"] is False for r in summary), "global claim forbidden")
    require(h["unresolved"] == [r for r in summary if r["D_1pct_lower"] is None], "empty statuses mismatch")
    raw = {(r["shield"], r["mode"], r["purpose"]): r for r in h["thresholds"]}
    expected = {(s, v, purpose) for (s, v), r in indexed.items()
                for purpose, field in (("cost_threshold", "D_1pct_lower"),
                                       ("certificate_threshold", "D_certificate_lower")) if r[field] is not None}
    require(len(raw) == len(h["thresholds"]) == 9 and set(raw) == expected, "threshold rows missing/duplicated")
    targets = []
    for (shield, mode), sr in indexed.items():
        base = {"variant": mode, "shield_g_cm2": shield, "T88_sha": T88_SHA,
                "T88_input_set": contract["input_set"], "timing_margin": contract["margin"],
                "physical_qualification": False, "physical_F_required": None}
        require(declared[shield, mode]["Dcrit_1pct_safe"] ==
                (None if sr["D_1pct_lower"] is None else decimal_text(rational(sr["D_1pct_lower"]), 9)),
                "configured D is not the exact safe lower endpoint")
        if sr["D_1pct_lower"] is None:
            require(declared[shield, mode]["status"] == sr["status_1pct"], "empty status changed")
        else:
            require(declared[shield, mode]["threshold_kind"] == "largest_found_certified_1pct",
                    "finite-family point is not a global threshold")
        for purpose, field, label in (("cost_threshold", "1pct", "T88_largest_found_certified_1pct"),
                                     ("certificate_threshold", "certificate", "T88_certificate_only")):
            d = sr["D_"+field+"_lower"]
            ref = "inputs/t88-handoff.json#"+shield+"/"+mode+"/"+purpose
            target = dict(base, target_kind=label, D0_exact=d, certificate_ref=ref,
                          T88_source_status=sr["status_"+field])
            if d is None:
                require(sr["D_"+field+"_upper"] is None and sr["status_"+field].startswith("empty_established"),
                        "empty region is not a zero or an awaiting-delivery value")
                target.update(status=sr["status_"+field], F_required=None)
            else:
                rr = raw[shield, mode, purpose]
                lower, upper = map(rational, (rr["D_safe_lower"], rr["bracket_upper"]))
                require(lower == rational(d) >= rational(contract["D_min"])
                        and upper == rational(sr["D_"+field+"_upper"])
                        and 0 < upper-lower <= rational(sr["threshold_tolerance"]), "unsafe/changed bracket")
                witness = rr["witness"]
                require(witness["ka"] > 1 and witness["ka"] % 2 == 1 and witness["g"] > 0,
                        "always-short is not the two-mode threshold")
                target.update(T88_bracket_upper_exact=str(upper),
                              T88_witness_json=json.dumps(witness, sort_keys=True),
                              T88_scope=rr["upper_scope"],
                              **price_fields(rr["risk_upper"], rr["risk_slack"], rr["full_quiet_tax_upper"],
                                             eps, purpose == "cost_threshold"))
            targets.append(target)
        working = dict(base, target_kind="T88_working_risk_reserve_proposal", D0_exact=sr["working_D"],
                       certificate_ref="inputs/t88-summary.json#"+shield+"/"+mode+"/working")
        if sr["working_D"] is None:
            working.update(status="working_reserve_not_established", F_required=None)
        else:
            require(rational(contract["D_min"]) <= rational(sr["working_D"]) < rational(sr["D_certificate_lower"]),
                    "working D outside certificate")
            require(rational(sr["working_risk_slack"]) >= rational(contract["working_risk_reserve_proposal"]),
                    "working reserve not met")
            working.update(T88_witness_json=json.dumps({"g": sr["working_g"], "ka": sr["working_ka"]}),
                           **price_fields(sr["working_risk_upper"], sr["working_risk_slack"], sr["working_cost_upper"], eps))
        targets.append(working)
        if "interior_1pct_D" in sr:
            require(rational(sr["interior_1pct_D"]) == rational(sr["working_D"]), "interior D mismatch")
            # Same D (therefore same fluence), but retain the threshold policy, not working_g/ka.
            witness = raw[shield, mode, "cost_threshold"]["witness"]
            targets.append(dict(base, target_kind="T88_interior_1pct_other_policy", D0_exact=sr["interior_1pct_D"],
                                certificate_ref="inputs/t88-summary.json#"+shield+"/"+mode+"/interior_1pct",
                                T88_witness_json=json.dumps(witness, sort_keys=True),
                                **price_fields(eps-rational(sr["interior_1pct_risk_slack"]),
                                               sr["interior_1pct_risk_slack"], sr["interior_1pct_cost"], eps, True)))
    return targets


def accepted_targets(cfg):
    return validate_bundle(cfg, read_bundle(cfg))

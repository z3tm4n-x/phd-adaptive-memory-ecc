"""Pinned handoff transfer and new fluences, not an independent T88 review."""
import copy
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import json
import unittest

from fluence import HERE
from run import calculate, mission_weights
from t88_handoff import T88_SHA, accepted_targets, read_bundle, validate_bundle

CFG = json.loads((HERE/"config.json").read_text(encoding="utf-8"))


class TestT88Transfer(unittest.TestCase):
    def test_four_safe_lower_endpoints_not_upper(self):
        targets = accepted_targets(CFG)
        cost = [r for r in targets if r["target_kind"] == "T88_largest_found_certified_1pct"]
        expected = {("3", "combined"): ".000510489", ("3", "monitor-only"): ".000511489",
                    ("2.5", "combined"): ".000059073", ("2.5", "monitor-only"): ".000060073"}
        self.assertEqual(len(cost), 6)
        for r in cost:
            self.assertEqual(r["T88_sha"], T88_SHA)
            if r["D0_exact"] is not None:
                self.assertEqual(Q(r["D0_exact"]), Q(expected[r["shield_g_cm2"], r["variant"]]))
                self.assertEqual(Q(r["T88_bracket_upper_exact"])-Q(r["D0_exact"]), Q("1e-9"))
                self.assertTrue(r["one_percent_certificate"])
            else:
                self.assertEqual(r["variant"], "ERR-only")
                self.assertEqual(r["status"], "empty_established_region_D_ge_5e-5")

    def test_config_rejects_upper_endpoint_and_unpinned(self):
        for delta in ("1e-9", "0.0001"):
            cfg = copy.deepcopy(CFG)
            cfg["T88_handoff"]["rows"][0]["Dcrit_1pct_safe"] = str(Q(".000510489")+Q(delta))
            with self.assertRaisesRegex(ValueError, "safe lower"):
                accepted_targets(cfg)
        cfg = copy.deepcopy(CFG)
        cfg["T88_handoff"]["source_sha"] = "a"*40
        with self.assertRaisesRegex(ValueError, "SHA"):
            accepted_targets(cfg)

    def test_rejects_snapshot_hash_corruption(self):
        cfg = copy.deepcopy(CFG)
        path = cfg["T88_handoff"]["snapshots"]["summary"]
        cfg["source_sha256"][path] = "0"*64
        with self.assertRaisesRegex(ValueError, "checksum"):
            read_bundle(cfg)

    def test_rejects_wrong_context_and_qualification(self):
        for key, val in (("margin", ".05"), ("architecture", "external39"),
                         ("input_set", "T72"), ("physical_D_upper", "0")):
            b = read_bundle(CFG)
            b["handoff"]["contract"][key] = val
            b["protocol"]["versions"][key] = val
            with self.assertRaises(ValueError):
                validate_bundle(CFG, b)
        b = read_bundle(CFG)
        b["effective_inputs"][0]["environment"]["n"] = 32
        with self.assertRaisesRegex(ValueError, "word"):
            validate_bundle(CFG, b)

    def test_rejects_bad_risk_or_price(self):
        for key, val in (("risk_upper", "0.002"), ("risk_slack", "0"),
                         ("full_quiet_tax_upper", "0.011")):
            b = read_bundle(CFG)
            b["handoff"]["thresholds"][0][key] = val
            with self.assertRaises(ValueError):
                validate_bundle(CFG, b)

    def test_rejects_always_short_and_duplicate(self):
        b = read_bundle(CFG)
        b["handoff"]["thresholds"][0]["witness"]["ka"] = 1
        with self.assertRaisesRegex(ValueError, "always-short"):
            validate_bundle(CFG, b)
        b = read_bundle(CFG)
        b["handoff"]["thresholds"].append(copy.deepcopy(b["handoff"]["thresholds"][0]))
        with self.assertRaisesRegex(ValueError, "duplicated"):
            validate_bundle(CFG, b)

    def test_supplementary_targets_never_promoted_to_one_percent(self):
        targets = accepted_targets(CFG)
        cert = [r for r in targets if r["target_kind"] == "T88_certificate_only" and r["D0_exact"]]
        work = [r for r in targets if r["target_kind"] == "T88_working_risk_reserve_proposal" and r["D0_exact"]]
        self.assertEqual(len(cert), 5)
        self.assertEqual(len(work), 5)
        self.assertTrue(all(not r["one_percent_certificate"] for r in cert))
        self.assertEqual(sum(r["one_percent_certificate"] for r in work), 2)
        self.assertTrue(all(Q(r["T88_risk_slack_exact"]) >= Q(".00005") for r in work))

    def test_same_D_different_policy_cost_and_reserve(self):
        targets = accepted_targets(CFG)
        for mode in ("combined", "monitor-only"):
            rs = {r["target_kind"]: r for r in targets if r["shield_g_cm2"] == "2.5" and r["variant"] == mode}
            w, i = rs["T88_working_risk_reserve_proposal"], rs["T88_interior_1pct_other_policy"]
            self.assertEqual(w["D0_exact"], i["D0_exact"])
            self.assertFalse(w["one_percent_certificate"])
            self.assertTrue(i["one_percent_certificate"])
            self.assertGreaterEqual(Q(w["T88_risk_slack_exact"]), Q(".00005"))
            self.assertLess(Q(i["T88_risk_slack_exact"]), Q(".00005"))
            self.assertNotEqual(w["T88_witness_json"], i["T88_witness_json"])

    def test_all_new_fluences_Decimal100(self):
        rows, *_ = calculate(CFG, Q(".00005"))
        weights, _ = mission_weights()
        checked = 0
        for r in rows:
            if not r["target_kind"].startswith("T88_") or not r.get("F_required"):
                continue
            C = weights[Q(r["shield_g_cm2"])]; a = Q(r["alpha_cap_exact"]); d = Q(r["D0_exact"])
            with localcontext() as ctx:
                ctx.prec = 100
                dec = lambda x: Decimal(x.numerator)/Decimal(x.denominator)
                mu = -dec(a).ln()
                f = Decimal(r["F_required"])
                self.assertLessEqual(mu*dec(C)/(Decimal(".7")*f), dec(d))
                self.assertGreater(mu*dec(C)/(Decimal(".7")*(f-Decimal(".001"))), dec(d))
            self.assertIsNone(r["physical_F_required"])
            self.assertFalse(r["physical_qualification"])
            checked += 1
        self.assertEqual(checked, 54)


if __name__ == "__main__":
    unittest.main()

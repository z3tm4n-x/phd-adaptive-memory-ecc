"""Local regression + independent high-precision and degenerate-case tests."""
import copy
import csv
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import json
import math
import unittest

from fluence import (HERE, REPO, T81_ALLOCATION, allocation_budget, ceil_quantum,
                     log_mean_bounds, rational, validate_threshold_handoff, zero_fluence)
from run import calculate, mission_weights, verify_sources

CFG = json.loads((HERE/"config.json").read_text(encoding="utf-8"))


class TestT89(unittest.TestCase):
    def test_source_hashes(self):
        self.assertEqual(len(verify_sources(CFG)), 6)

    def test_exact_T81_reuse(self):
        self.assertEqual(T81_ALLOCATION.__code__.co_filename,
                         str(REPO/"experiments/t81-direct-architecture/run.py")+":zero_count_functions")
        self.assertEqual(T81_ALLOCATION(3, .001, .05), -math.log(.05)*3000)

    def test_T81_published_regression(self):
        weights, _ = mission_weights()
        p = REPO/"experiments/t81-direct-architecture/outputs/prospective_fullword_exposure.csv"
        with p.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        checked = 0
        for r in rows:
            if r["architecture"] != "internal38":
                continue
            ans = zero_fluence(weights[Q(r["shield_g_cm2"])], r["target_D"], r["alpha_for_uniform_cap"],
                               0, r["theta"], 1, 1)
            self.assertTrue(math.isclose(ans["T81_double"], float(r["required_new_zero_F_cm2_inv"]), rel_tol=2e-14))
            checked += 1
        self.assertEqual(checked, 16)

    def test_log_enclosure_Decimal100(self):
        for a in (Q(1,20), Q(1,60), Q(1,120), Q(1,6000000), Q(1,33000)):
            lo, hi = log_mean_bounds(a)
            with localcontext() as ctx:
                ctx.prec = 100
                val = -(Decimal(a.numerator)/Decimal(a.denominator)).ln()
                self.assertLess(lo, Q(val))
                self.assertGreater(hi, Q(val))

    def test_rounded_requirement_Decimal100_matrix(self):
        weights, _ = mission_weights()
        checked = 0
        for C in weights.values():
            for b in (".000025", ".00005", ".0001"):
                for a in (".05", ".000001"):
                    for t in ("0", ".3"):
                        for q in ("1", ".9"):
                            for old in ("0", "1000"):
                                x = zero_fluence(C, b, a, old, t, q, 1)
                                with localcontext() as ctx:
                                    ctx.prec = 100
                                    c = Decimal(C.numerator)/Decimal(C.denominator)
                                    mu = -Decimal(a).ln()
                                    scale = (1-Decimal(t))*Decimal(q)
                                    F = Decimal(x["F_required"])
                                    risk = mu*c/(Decimal(old)+scale*F)
                                    self.assertLessEqual(risk, Decimal(b))
                                    self.assertGreater(mu*c/(Decimal(old)+scale*(F-Decimal(".001"))), Decimal(b))
                                checked += 1
        self.assertEqual(checked, 96)

    def test_unknown_not_zero(self):
        base = dict(C=20, b=".00005", alpha=".05", E_old=0, theta=".3", q=1, g=1)
        for key in base:
            v = dict(base, **{key: None})
            x = zero_fluence(**v)
            self.assertEqual(x["status"], "undefined")
            self.assertIsNone(x["F_required"])
        self.assertEqual(allocation_budget(".00005", None, [{"b": ".00005", "alpha": ".05"}], ".05")["status"], "undefined")

    def test_q_g_zero(self):
        for q, g in ((0, 1), (1, 0)):
            x = zero_fluence(20, ".00005", ".05", 0, ".3", q, g)
            self.assertEqual(x["status"], "no_finite_exposure")
        self.assertEqual(zero_fluence(20, ".00005", ".05", "1e9", ".3", 0, 1)["F_required"], "0.000")

    def test_residual_boundary(self):
        for R in (".00005", ".00006"):
            x = allocation_budget(".00005", R, [{"b": ".00001", "alpha": ".05"}], ".05")
            self.assertEqual(x["status"], "no_positive_covered_budget")

    def test_config_residual_is_charged(self):
        c = copy.deepcopy(CFG)
        c["conditional_scale"]["R"] = ".00001"
        rows, *_ = calculate(c, Q(".00005"))
        r = next(x for x in rows if x.get("coverage") == "point95_single_cap" and x["shield_g_cm2"] == "3")
        self.assertTrue(math.isclose(r["T81_double"], 2014297.9598942855*1.25, rel_tol=1e-14))
        for R, status in ((None, "undefined"), (".00005", "no_positive_covered_budget")):
            c["conditional_scale"]["R"] = R
            rows, *_ = calculate(c, Q(".00005"))
            self.assertTrue(all(x["status"] == status for x in rows if x["target_kind"] == "baseline"))

    def test_invalid_inputs(self):
        base = dict(C=20, b=".00005", alpha=".05", E_old=0, theta=".3", q=1, g=1)
        for key, values in {"C": [-1, "nan"], "b": [0,-1], "alpha": [0,1],
                            "E_old": [-1], "theta": [-1,1], "q": [-1,2], "g": [-1]}.items():
            for value in values:
                with self.assertRaises(ValueError):
                    zero_fluence(**dict(base, **{key: value}))
        with self.assertRaises(ValueError):
            zero_fluence(**base, n_new=1)

    def test_budget_validation(self):
        strata = [{"b": Q(1,60000), "alpha": Q(1,60)}]*3
        self.assertEqual(allocation_budget(".00005", 0, strata, ".05")["status"], "valid_conditional_budget")
        for key, val in (("b", ".0001"), ("alpha", ".06")):
            bad = [dict(strata[0], **{key: val})] + strata[1:]
            with self.assertRaises(ValueError):
                allocation_budget(".00005", 0, bad, ".05")

    def test_monotonicity(self):
        f = lambda **kw: T81_ALLOCATION(**dict(dict(weight=20, budget=.00005, alpha=.05,
                                  old_effective=0, theta=.3, efficiency=1, geometry=1), **kw))
        baseline = f()
        for kw in (dict(weight=21), dict(budget=.00004), dict(alpha=.01),
                   dict(theta=.4), dict(efficiency=.9), dict(geometry=.9)):
            self.assertGreater(f(**kw), baseline)
        self.assertLess(f(old_effective=1000), baseline)
        self.assertEqual(f(old_effective=1e10), 0)

    def test_inverse_target_and_residual(self):
        f = lambda b: T81_ALLOCATION(20, b, .05, theta=.3)
        self.assertAlmostEqual(f(.000025)/f(.00005), 2)
        self.assertAlmostEqual(f(.00005*.8)/f(.00005), 1.25)

    def test_units_and_no_55_factor(self):
        # Changing cm to m: C and E_old scale by 1e4, fluence follows 1e4.
        a = T81_ALLOCATION(20, .00005, .05, old_effective=100, theta=.3)
        b = T81_ALLOCATION(20*1e4, .00005, .05, old_effective=100*1e4, theta=.3)
        self.assertAlmostEqual(b/a, 1e4)
        rows, *_ = calculate(CFG, Q(".00005"))
        base = next(r for r in rows if r.get("coverage") == "point95_single_cap" and r["shield_g_cm2"] == "3")
        self.assertEqual(base["F_required"], "2014297.960")
        self.assertEqual(base["E_old_credit_cm2_inv"], "0")
        self.assertEqual(base["alpha_cap_exact"], "1/20")

    def test_unknown_physical_handoff_preserved(self):
        cfg = copy.deepcopy(CFG)
        for row in cfg["T88_handoff"]["rows"]:
            row["Dcrit_1pct_safe"] = None
        rows, angular, *_ = calculate(cfg, Q(".00005"))
        physical = [r for r in rows if r["target_kind"] == "baseline_physical"]
        pending = [r for r in rows if r["target_kind"] == "T88_Dcrit_1pct"]
        self.assertEqual(len(physical), 2)
        self.assertEqual(len(pending), 6)
        self.assertTrue(all(r["F_required"] is None for r in physical+pending))
        self.assertTrue(all(r["physical_Fnew"] is None for r in angular))
        self.assertTrue(all(v is None for v in CFG["physical_contract"].values()))

    def test_threshold_rejects_unpinned_unsafe_and_zero(self):
        for value in ("0", ".0001"):
            h = copy.deepcopy(CFG["T88_handoff"])
            h["rows"][0]["Dcrit_1pct_safe"] = value
            with self.assertRaises(ValueError):
                validate_threshold_handoff(h)
        h = copy.deepcopy(CFG["T88_handoff"])
        h["source_sha"] = "a"*40
        h["rows"][0].update(Dcrit_1pct_safe=".0001", safe_endpoint_confirmed=True,
                             architecture="internal38", timing_margin=".1",
                             threshold_kind="Dcrit_1pct", certificate_ref="test fixture only")
        self.assertEqual(len(validate_threshold_handoff(h)), 6)
        h["rows"][0]["threshold_kind"] = "largest_found_certified_1pct"
        self.assertEqual(len(validate_threshold_handoff(h)), 6)
        h["rows"][0]["threshold_kind"] = "Dcert"
        with self.assertRaises(ValueError):
            validate_threshold_handoff(h)

    def test_ceiling_exact(self):
        self.assertEqual(ceil_quantum(Q(1,3), ".001"), Q(".334"))
        self.assertEqual(ceil_quantum(Q(".334"), ".001"), Q(".334"))


if __name__ == "__main__":
    unittest.main()

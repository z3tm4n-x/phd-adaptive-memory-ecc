"""Independent identities, numerical integration, regressions and fail-closed contracts."""
import csv
import json
import math
import unittest

import numpy as np
from scipy.integrate import quad

import run as r


class Statistics(unittest.TestCase):
    def test_zero_boundary_probability(self):
        for alpha in (.05, .05/6, .05/330, 1e-6/6):
            self.assertAlmostEqual(math.exp(-r.mu_upper(0, alpha))/alpha, 1., places=13)
        self.assertAlmostEqual(r.mu_upper(0, .05), 2.995732273553991)

    def test_nonzero_inversion_without_chi2(self):
        # Independent Poisson CDF recurrence, not the chi-square implementation.
        for n in (1, 2, 4, 6):
            for alpha in (.05, .05/330, 1e-6/6):
                mu = r.mu_upper(n, alpha)
                term = math.exp(-mu)
                cdf = term
                for k in range(1, n+1):
                    term *= mu/k
                    cdf += term
                self.assertLess(abs(cdf/alpha-1), 5e-13)

    def test_units_and_efficiency(self):
        base = r.sigma_upper(0, 1000, .05)
        self.assertAlmostEqual(r.sigma_upper(0, 1000, .05, .3)/base, 1/.7)
        self.assertAlmostEqual(r.sigma_upper(0, 1000, .05, efficiency=.5)/base, 2)
        self.assertAlmostEqual(r.sigma_upper(0, 1000, .05, geometry=.5)/base, 2)
        self.assertAlmostEqual(r.sigma_upper(0, 10000, .05)/base, .1)

    def test_fail_closed_invalid_or_unobserved_exposure(self):
        for f, theta, q, g in [(0, 0, 1, 1), (10, 1, 1, 1), (10, 0, 0, 1), (10, 0, 1, 0)]:
            with self.assertRaises(ValueError):
                r.sigma_upper(0, f, .05, theta, q, g)
        for n, a in [(-1, .05), (.5, .05), (0, 0), (0, 1)]:
            with self.assertRaises(ValueError):
                r.mu_upper(n, a)

    def test_multiple_comparisons_no_independence_required(self):
        m = 330
        self.assertAlmostEqual(m*(.05/m), .05)
        self.assertGreater(r.mu_upper(0, .05/m), r.mu_upper(0, .05))

    def test_probability_and_xor_counterexample(self):
        d = .003
        self.assertLess(-math.expm1(-d), d)
        old, mark = {0}, {0, 1}
        self.assertEqual(old ^ mark, {1})  # SMU is not necessarily absorbing.
        for old in (set(), {0}, {1}, {3}):
            self.assertGreater(len(old ^ {0, 1, 2}), 1)


class Numerics(unittest.TestCase):
    def test_interpolant_analytic_limits(self):
        self.assertAlmostEqual(r.segment_integral(1, 10, 1, .1, 1, 10), math.log(10))
        self.assertAlmostEqual(r.segment_integral(1, 10, 4, 4, 2, 7), 20.)
        self.assertEqual(r.segment_integral(1, 10, 0, 0, 2, 7), 0.)

    def test_zero_endpoint_independent_quadrature(self):
        for a, b in ((0., 5.), (5., 0.)):
            expected = quad(lambda x: a+(b-a)*math.log(x)/math.log(10), 2, 7)[0]
            self.assertAlmostEqual(r.segment_integral(1, 10, a, b, 2, 7), expected, places=13)

    def test_unit_change_conserves_integral(self):
        tab = np.asarray([[1000., .001], [2000., .001]])
        self.assertAlmostEqual(r.integrate_spectrum(tab, 1, 1, 2), 1.)

    def test_no_spectral_extrapolation(self):
        with self.assertRaises(ValueError):
            r.integrate_spectrum(np.asarray([[1000., 1.], [2000., 1.]]), 1, .5, 3.)

    def test_root_and_limit(self):
        target = .001
        result = r.additional_fluence([1., 2.], [100., 10.], target, .05, .3)
        f = result["upper_cm2_inv"]
        independent = r.mu_upper(0, .05)/.7*(1/(100+f)+2/(10+f))
        self.assertLessEqual(independent, target*(1+1e-14))
        self.assertLess(result["upper_cm2_inv"]-result["lower_cm2_inv"], 1e-9)
        self.assertEqual(result["limit_D"], 0.)
        blocked = r.additional_fluence([1., 2.], [100., 10.], target, .05, .3, "last")
        self.assertIsNone(blocked["upper_cm2_inv"])
        self.assertAlmostEqual(blocked["limit_D"], r.mu_upper(0, .05)/70)

    def test_root_degeneracies(self):
        self.assertEqual(r.additional_fluence([0., 0.], [1., 1.], 1e-5, .05, .3)["upper_cm2_inv"], 0.)
        with self.assertRaises(ValueError):
            r.additional_fluence([1.], [0.], 1e-5, .05, .3)
        with self.assertRaises(ValueError):
            r.additional_fluence([1.], [1.], 0, .05, .3)
        for weights, pools, theta in [([1], [1, 2], .3), ([1], [1], 1), ([float("nan")], [1], .3)]:
            with self.assertRaises(ValueError):
                r.additional_fluence(weights, pools, 1e-5, .05, theta)

    def test_budget_allocation(self):
        c, budget, alpha = 20., 1e-5, .05/6
        f = r.allocation_fluence(c, budget, alpha, theta=.3, efficiency=.8, geometry=.5)
        self.assertAlmostEqual(c*r.sigma_upper(0, f, alpha, .3, .8, .5)/budget, 1.)
        f2 = r.allocation_fluence(c, budget, alpha, old_effective=100, theta=.3)
        self.assertAlmostEqual(.7*f2+100, r.mu_upper(0, alpha)*c/budget)


class AcceptedInputs(unittest.TestCase):
    def test_hashes(self):
        self.assertEqual(len(r.verify_sources()), 21)

    def test_exposure_normalization(self):
        for row in r.read_csv(r.OUT / "fluence_normalization.csv"):
            self.assertLess(abs(float(row["relative_difference"])), 2e-13)
            self.assertEqual(row["F_independently_measured"], "False")

    def test_legacy_regressions_and_quad(self):
        expected = {2.5: (.003463085545709634, .01536626872599612),
                    3.: (.002772537646709901, .012299573120944566)}
        for row in r.read_csv(r.OUT / "T68_reproduction.csv"):
            ur, ua0 = expected[float(row["shield_g_cm2"])]
            self.assertLess(abs(float(row["reproduced_UR"])/ur-1), 2e-14)
            self.assertLess(abs(float(row["reproduced_UA0"])/ua0-1), 2e-14)
            a, q = float(row["analytic_UR_numerator3"]), float(row["independent_quad_UR_numerator3"])
            self.assertLess(abs(a/q-1), 2e-10)
            self.assertLess(abs(float(row["analytic_vs_grid_relative"])), .003)

    def test_selected_groupings_and_row_constraint(self):
        rows = r.grouping_audit()
        self.assertEqual(len(rows), 55)
        self.assertEqual(sum(x["merged_data32_SMU"] == 0 for x in rows), 45)
        self.assertEqual({x["address_bits"] for x in rows if x["same_transformed_y"]}, {"2,3", "2,8", "3,8"})
        self.assertFalse(any(x["same_transformed_y"] and x["H_low_contains_x16_pair"] for x in rows))
        self.assertFalse(any(x["H_pin_contains_x16_pair"] for x in rows))
        self.assertTrue(all(x["merged_data32_SMU"] == 6 for x in rows if x["H_low_contains_x16_pair"]))

    def test_x16_projection_is_not_DQ_error_count(self):
        rows = r.read_csv(r.T68 / "outputs/raw_x16_hypotheses.csv")
        for selector, raw, merged in [(0, 4, 6), (20, 0, 0)]:
            group = [x for x in rows if int(x["assumed_raw_byte_selector_bit"]) == selector]
            self.assertEqual(sum(int(x["raw_same_x16_registered_objects"]) for x in group), raw)
            self.assertEqual(sum(int(x["raw_same_x16_merged_objects"]) for x in group), merged)
            self.assertTrue(all(x["external39_uncorrectable_events"] == "unknown" for x in group))

    def test_external_all_seven_checks_and_pins(self):
        pinmap = json.loads((r.REPO / "experiments/RE-CY62167-EXECUTOR-TIMING-GATE-01/reference-continuation-01/pinmap.json").read_text())
        p = {s["port"]: s for s in pinmap["signals"]}
        for bit in range(48):
            chip = bit//16
            self.assertEqual(len(p[f"dq[{bit}]"]["sram_pins"]), 1)
            self.assertTrue(p[f"dq[{bit}]"]["sram_pins"][0].startswith(f"M{chip}."))
        self.assertEqual(len(range(32, 39)), 7)
        self.assertEqual(pinmap["straps_each_sram"]["BYTE_pin47"], "VADJ")
        self.assertEqual(pinmap["straps_each_sram"]["A19_pin9"], "GND")
        self.assertEqual(3*16-39, 9)

    def test_no_unknown_promoted_to_zero(self):
        data = json.loads((r.OUT / "handoff.json").read_text())
        self.assertEqual(len(data["architectures"]), 4)
        for row in data["architectures"]:
            for key in ("fullword_D_upper", "fullword_sigma_upper_cm2", "fullword_observed_direct_count", "joint_coverage"):
                self.assertIsNone(row[key])
        self.assertFalse(data["impossibility_of_any_policy_established"])

    def test_budget_sums_and_monotonic_exposure(self):
        rows = r.read_csv(r.OUT / "LET_budget.csv")
        for rho in (2.5, 3.):
            for target in (5e-5, 1e-4):
                subtotal = sum(float(x["uniform_cap_budget_bj"]) for x in rows if float(x["shield_g_cm2"]) == rho and float(x["target_D"]) == target)
                self.assertAlmostEqual(subtotal/target, 1., places=13)
        forecasts = r.read_csv(r.OUT / "additional_exposure.csv")
        by_key = {(x["shield_g_cm2"], x["coverage"], x["theta"], x["target_D"], x["reuse"]): x for x in forecasts}
        for x in forecasts:
            if x["reuse"] == "monotone_pool_all_nodes" and float(x["target_D"]) == 5e-5:
                y = by_key[(x["shield_g_cm2"], x["coverage"], x["theta"], "0.0001", x["reuse"])]
                self.assertGreater(float(x["upper_cm2_inv"]), float(y["upper_cm2_inv"]))

    def test_angular_unknowns_and_family_budget(self):
        rows = r.read_csv(r.OUT / "angular_requirements.csv")
        self.assertEqual(len(rows), 24)
        for x in rows:
            self.assertEqual(x["required_actual_Fnew_cm2_inv"], "")
            self.assertEqual(x["unknown_remainder_R"], "")
            self.assertAlmostEqual(float(x["alpha_per_stratum"])*6, .05)
            target = float(x["target_D"])
            self.assertAlmostEqual(float(x["Fnew_per_C_optimistic_R0_q1_g1_theta03"])*.7*target/3,
                                   -math.log(.05/6))

    def test_full38_pair_types_not_a_cross_section_multiplier(self):
        self.assertEqual(math.comb(38, 2)-math.comb(32, 2), 32*6+math.comb(6, 2))
        self.assertEqual(32*6, 192)
        self.assertEqual(math.comb(6, 2), 15)

    def test_fullword_forecast_does_not_credit_raw_exposure(self):
        for row in r.read_csv(r.OUT / "prospective_fullword_exposure.csv"):
            self.assertEqual(float(row["existing_qualified_fullword_F"]), 0)
            self.assertIn("conditional", row["status"])


if __name__ == "__main__":
    unittest.main()

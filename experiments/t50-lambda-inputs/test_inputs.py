"""Small falsification/regression checks; no radiation or controller simulation."""
import copy
import json
from fractions import Fraction as F
import unittest

import reproduce as r


class ArithmeticTests(unittest.TestCase):
    def test_constant(self):
        self.assertEqual(r.integrals([2, 2], [3, 7]), (10, 20, 40, 1))

    def test_pulse_square_not_square_of_mean(self):
        T, I1, I2, J = r.integrals([0, 4], [5, 5])
        self.assertEqual((T, I1, I2, J), (10, 20, 80, 2))
        self.assertNotEqual(I2, I1**2 / T)

    def test_zero_J_is_undefined_not_one(self):
        self.assertEqual(r.integrals([0, 0], [5, 5]), (10, 0, 0, None))

    def test_units_array_scaling_is_squared_for_I2(self):
        _, a1, a2, aj = r.integrals(["0.1", "0.3"], [2, 3])
        _, b1, b2, bj = r.integrals(["3.2", "9.6"], [2, 3])
        self.assertEqual((b1, b2, bj), (32 * a1, 32**2 * a2, aj))

    def test_invalid_values_fail_closed(self):
        for rates, dt in [([], []), ([1], []), ([-1], [1]), ([1], [0]), ([1], [-1])]:
            with self.subTest(rates=rates, dt=dt), self.assertRaises(ValueError):
                r.integrals(rates, dt)

    def test_row_selector_must_be_unique(self):
        for rows in [[], [{"k": "v"}, {"k": "v"}]]:
            with self.assertRaises(ValueError):
                r.one(rows, {"k": "v"})


class PinnedInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = r.read_json(r.HERE / "config.json")
        cls.manifest = r.read_json(r.HERE / "sources.json")
        cls.blobs = r.source_bytes(cls.manifest)
        cls.result = r.build(cls.cfg, cls.blobs)
        cls.spec = cls.cfg["conversion_jobs"]["historical_series"]
        cls.rows = r.csv_rows(cls.blobs[cls.spec["path"]])

    def test_summary_regeneration(self):
        self.assertEqual(self.result, r.read_json(r.HERE / "summary.json"))

    def test_accepted_integrals(self):
        h = self.result["historical_integrals"]
        old = json.loads(self.blobs[r.EXECUTOR + "bounds.json"])
        self.assertEqual(F(h["I1_r"]["exact_from_serialized_model"]), F(old["I1"]["exact"]))
        self.assertEqual(F(h["I2_r"]["exact_from_serialized_model"]), F(old["I2"]["exact"]))
        self.assertEqual(h["T_s"], "86400")
        self.assertFalse(h["full39_R0A_eligible"])

    def test_missing_row_and_time_gap_rejected(self):
        with self.assertRaises(ValueError):
            r.validate_selected(self.rows[:-1], self.spec)
        rows = copy.deepcopy(self.rows)
        rows[1]["timestamp_utc"] = rows[0]["timestamp_utc"]
        with self.assertRaises(ValueError):
            r.validate_selected(rows, self.spec)

    def test_cannot_relabel_shield_or_normalization(self):
        for field, value in [("shield_mm", "3"), (self.spec["r_column"], "0")]:
            rows = copy.deepcopy(self.rows)
            rows[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                r.validate_selected(rows, self.spec)

    def test_capacities_and_counter_widths(self):
        a = self.result["architecture"]
        self.assertEqual(a["words"], 524288)
        self.assertEqual(a["external_active_bits"], 20447232)
        self.assertEqual(a["data_bits"], 16777216)
        self.assertEqual(a["addressed_bytes"], 3 * 2**20)
        self.assertEqual(a["installed_bytes"], 6 * 2**20)
        self.assertEqual([a[k] for k in ("counter_bits_outer", "counter_bits_ERR_sum",
                                       "counter_bits_all_flags")], [20, 21, 22])
        parity = [1, 2, 4, 8, 16, 32, 39]
        data = [p for p in range(1, 39) if p not in parity]
        self.assertEqual(len(data), 32)
        self.assertEqual(sorted(data + parity), list(range(1, 40)))

    def test_zero_observations_are_not_zero_upper(self):
        z = self.result["R3"]["zero_count_demo"]
        self.assertGreater(z["Poisson_mean_upper_approx"], 0)
        self.assertIsNone(z["sigma_upper_cm2"])
        self.assertIsNone(self.result["R3"]["probability_over_groupings"])

    def test_saved_decisions_really_differ(self):
        rr = self.result["R3"]
        self.assertEqual(rr["groupings"], {"0": 45, "4": 9, "5": 1})
        self.assertEqual([x["passes_saved_sufficient_period_bound"]
                          for x in rr["saved_certificate_comparison"]], [True, False])
        w = rr["saved_GOES_transition"]
        self.assertLess(F(w["F_exact_tau_to"]), F(w["epsilon_analysis"]))
        self.assertGreater(F(w["F_exact_tau_from"]), F(w["epsilon_analysis"]))

    def test_coverage_is_not_hidden_inside_epsilon(self):
        last = self.result["theta_coverage_sensitivity"][-1]
        self.assertEqual(F(last["union_upper"]["exact_from_serialized_model"]), F("0.051"))
        self.assertLess(F(last["remaining_conditional_budget_signed"]["exact_from_serialized_model"]), 0)
        self.assertIsNone(self.cfg["theta_full39"]["delta_theta"])

    def test_parent_bounds_stay_unknown(self):
        for key, value in self.cfg["lambda_parent_inputs"].items():
            if key != "status":
                self.assertIsNone(value, key)
        self.assertIsNone(self.result["R0A_full39"]["I1"])
        self.assertFalse(self.result["R0A_full39"]["ready_for_algorithm_comparison"])

    def test_fluence_is_orbital_and_contains_solar_ions(self):
        sep, gcr = self.result["orbit_fluence"]
        self.assertEqual((sep["rows"], sep["Z_columns"]), (42, [1, 28]))
        self.assertEqual((gcr["rows"], gcr["Z_columns"]), (50, [1, 92]))
        self.assertIn("NOT behind", sep["location"])
        self.assertIsNone(sep["parent_exposure_behind_shield"])
        self.assertIsNone(self.cfg["conversion_jobs"]["orbit_fluence"]["joint_coverage_error"])

    def test_growth_masks_and_thresholds_preserved(self):
        growth = self.result["GOES_growth_diagnostics_reused"]
        self.assertEqual(len(growth), 12)
        for row in growth:
            self.assertEqual(sum(row["counts"].values()),
                             row["pair_audit"]["valid_positive_same_version_pairs"])
            self.assertEqual(row["direction"], "central")

    def test_peak_rows_are_not_integrated(self):
        for row in self.result["target_SEP_peak_saved_rows"]:
            self.assertIn("NO-MISSION-INTEGRATION", row["status"])
            self.assertFalse(any(k.startswith("I1") or k.startswith("I2") for k in row))


if __name__ == "__main__":
    unittest.main()

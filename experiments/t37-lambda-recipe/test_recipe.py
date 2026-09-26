"""Small synthetic tests, independent of historical scientific models."""
import math
import json
import unittest
from fractions import Fraction

from reproduce import HERE, aggregate, audit, describe, frame, numeric, source_tables, stamp, truth


class RecipeTests(unittest.TestCase):
    def test_positive_growth_and_decline(self):
        rows = frame([0, 300, 600], ["a"] * 3, [2., 5., 1.], [True] * 3, 300)
        r = describe(rows, 300)
        self.assertEqual(r["eligible_adjacent_pairs"], 2)
        self.assertEqual(r["max_positive_increment"]["positive_increment"], 3.)
        self.assertEqual(r["max_positive_increment"]["increment_divided_by_step_s"], float(Fraction(3, 300)))

    def test_invalid_does_not_become_zero_or_bridge(self):
        rows = frame([0, 300, 600], ["a"] * 3, [2., math.nan, 100.], [True, False, True], 300)
        self.assertEqual(describe(rows, 300)["eligible_adjacent_pairs"], 0)

    def test_missing_time_does_not_bridge(self):
        rows = frame([0, 600], ["a"] * 2, [2., 100.], [True] * 2, 300)
        self.assertIsNone(describe(rows, 300)["max_positive_increment"])

    def test_version_boundary_does_not_bridge(self):
        rows = frame([0, 300], ["a", "b"], [2., 100.], [True] * 2, 300)
        self.assertEqual(describe(rows, 300)["eligible_adjacent_pairs"], 0)
        self.assertFalse(aggregate(rows, 300, 600)[0][3])

    def test_hour_alignment_complete_only(self):
        rows = frame(list(range(0, 7200, 300)), ["a"] * 24, list(range(24)), [True] * 24, 300)
        result = aggregate(rows, 300, 3600)
        self.assertEqual([r[2] for r in result], [5.5, 17.5])
        self.assertEqual(describe(result, 3600)["max_positive_increment"]["positive_increment"], 12.)
        self.assertFalse(aggregate(rows[1:12], 300, 3600)[0][3])

    def test_hour_with_invalid_bin_rejected(self):
        rows = frame(list(range(0, 3600, 300)), ["a"] * 12, [1.] * 12, [False] + [True] * 11, 300)
        self.assertFalse(aggregate(rows, 300, 3600)[0][3])

    def test_empty_and_flat_are_distinct(self):
        self.assertIsNone(describe([], 300)["max"])
        rows = frame([0, 300], ["a"] * 2, [0., 0.], [True] * 2, 300)
        self.assertTrue(describe(rows, 300)["zero_growth_when_pairs_but_no_increase"])

    def test_bad_inputs_fail(self):
        for times, values in [([0, 0], [1., 2.]), ([0, 299], [1., 2.]), ([0, 300], [1., -1.]), ([0, 300], [1., math.inf])]:
            with self.assertRaises(ValueError):
                frame(times, ["a"] * 2, values, [True] * 2, 300)
        with self.assertRaises(ValueError):
            frame([0], [], [1.], [True], 300)

    def test_boolean_and_timezone(self):
        self.assertTrue(truth("True"))
        self.assertFalse(truth("0"))
        with self.assertRaises(ValueError):
            truth("")
        self.assertEqual(stamp("1970-01-01T04:00:00+04:00"), 0)
        with self.assertRaises(ValueError):
            stamp("1970-01-01T00:00:00")

    def test_exact_bit_normalization(self):
        self.assertEqual(Fraction(40894464, 16777216), Fraction(39, 16))
        self.assertEqual(Fraction(3600, 300), 12)

    def test_blank_is_missing_not_zero(self):
        self.assertTrue(math.isnan(numeric("")))
        self.assertEqual(numeric("0"), 0.)
        with self.assertRaises(ValueError):
            frame([0], ["a"], [numeric("")], [True], 300)

    def test_source_hash_guard(self):
        config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
        first = next(iter(config["source_hashes"]))
        config["source_hashes"][first] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Source hash mismatch"):
            source_tables(config)

    def test_wrong_normalization_config_rejected(self):
        config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
        config["historical_array_bits"] = 40894464
        with self.assertRaisesRegex(ValueError, "frozen source products"):
            audit(config)

    def test_native_witness_by_rational_arithmetic(self):
        # Separate exact arithmetic over serialized decimal source values.
        # This checks the two headline native central diagnostics, not physics.
        config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
        tables = source_tables(config)
        result = audit(config)
        for name, filename, column, denominator in [
            ("GOES16_3mm", "derived_rates.csv", "lambda_bit_central_s_1", 1),
            ("GOES19_1mm", "proton_rate_5min.csv", "d1_lambda_central_s-1", 16777216),
        ]:
            rows = tables[filename]
            candidates = []
            for a, b in zip(rows, rows[1:]):
                valid = all(r["valid"] == "True" for r in (a, b)) if name.startswith("GOES16") else all(r["east_valid"] == "1" and r["west_valid"] == "1" for r in (a, b))
                if not valid or (stamp(b["timestamp_utc"]) - stamp(a["timestamp_utc"])) != 300:
                    continue
                if a.get("algorithm_version") != b.get("algorithm_version"):
                    continue
                delta = (Fraction(b[column]) - Fraction(a[column])) / (denominator * 300)
                candidates.append((delta, a["timestamp_utc"], b["timestamp_utc"]))
            exact, start, end = max(candidates, key=lambda c: c[0])
            reported = result["series"][name]["diagnostics"]["central"]["published_valid"]["native"]["max_positive_increment"]
            self.assertEqual((start, end), (reported["from_bin_start_utc"], reported["to_bin_start_utc"]))
            self.assertTrue(math.isclose(float(exact), reported["increment_divided_by_step_s"], rel_tol=1e-14))


if __name__ == "__main__":
    unittest.main()

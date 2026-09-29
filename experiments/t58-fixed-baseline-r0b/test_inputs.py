import csv
import io
import unittest
from fractions import Fraction as F
from unittest.mock import patch
from inputs import history, blob


def fixture():
    cfg = {"scenario": {"calendar_start": "2021-01-01T00:00:00Z",
                        "calendar_end_exclusive": "2021-01-01T04:00:00Z",
                        "n": 39, "W_reference": 2}}
    rows = [dict(hour_index=i, timestamp_utc=f"2021-01-01T0{i}:00:00Z",
                 upsets_total_nu=str(x), background_proton_gp="1",
                 event_proton_sp="1", upsets_proton_raw=str(x),
                 is_missing_proton="false", fill_method="raw")
            for i, x in enumerate([12, 24, 12, 48])]
    return cfg, rows


def encode(rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode()


class InputChecks(unittest.TestCase):
    def test_display_bounds_are_outward(self):
        from reproduce import bound_number
        for x in [F(1, 3), F(9999999999999, 10**12), F(1, 10**40), F(0)]:
            self.assertLessEqual(F(bound_number(x, False)), x)
            self.assertGreaterEqual(F(bound_number(x, True)), x)

    def test_hour_units_and_full_word_scaling(self):
        cfg, rows = fixture()
        result = history(encode(rows), cfg)
        self.assertEqual(result["T_s"], 14400)
        self.assertEqual(result["I1_nu"], 96)
        self.assertEqual(result["I2_nu_s_inverse"], F(12**2+24**2+12**2+48**2, 3600))
        self.assertEqual(result["I1_per_bit"], F(96, 78))
        self.assertEqual(result["I2_per_bit_s_inverse"], result["I2_nu_s_inverse"]/78**2)

    def test_missing_is_not_zero_and_masks_keep_exposure(self):
        cfg, rows = fixture()
        rows[1].update(upsets_proton_raw="", is_missing_proton="true", fill_method="linear_interpolation")
        result = history(encode(rows), cfg)
        self.assertEqual(result["missing_hours"], 1)
        self.assertEqual(result["I1_nu"], 96)
        self.assertEqual(result["masks"]["not_imputed"]["I1_nu"], 72)
        self.assertEqual(result["hourly_growth_diagnostic"]["raw_neighbors"]["pairs"], 1)

    def test_gaps_duplicates_and_bad_hash_fail(self):
        cfg, rows = fixture()
        rows[1]["timestamp_utc"] = rows[0]["timestamp_utc"]
        with self.assertRaises(ValueError):
            history(encode(rows), cfg)
        with patch("inputs.subprocess.check_output", return_value=b"abc"):
            with self.assertRaises(ValueError):
                blob("unused", "sha", "file", "wrong_hash")

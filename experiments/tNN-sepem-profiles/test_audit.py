import io
import math
import unittest
import zipfile
import uuid
from pathlib import Path
from audit import scan_reference, input_files
from baseline import calculate


def scan(rows):
    return scan_reference(io.BytesIO(("header\n" + "\n".join(rows) + "\n").encode()), 2)


class AuditTests(unittest.TestCase):
    def test_directory_zip_case_sensitive_order(self):
        root=Path(__file__).parent/".cache"/("audit-"+uuid.uuid4().hex)
        source=root/"input"
        source.mkdir(parents=True)
        for name in ("Z.txt","a.txt","A.txt"):
            # Windows cannot store A.txt and a.txt simultaneously; distinct
            # base names still exercise Windows-vs-ZIP collation.
            name={"a.txt":"aa.txt"}.get(name,name)
            (source/name).write_text(name)
        archive=root/"fixture.zip"
        with zipfile.ZipFile(archive,"w") as z:
            for p in source.iterdir():
                z.write(p,p.name)
        with input_files(source) as a, input_files(archive) as b:
            self.assertEqual([x[0] for x in a],[x[0] for x in b])

    def test_existing_envelope_scope(self):
        r = calculate()
        self.assertEqual(r["protected_bits"], 19922944)
        self.assertGreater(float(r["historical_S2_sum_per_s"]), 6939)
        self.assertLess(float(r["historical_S2_sum_per_s"]), 6940)
        self.assertGreater(float(r["PDI_formula_diagnostic_per_s"]), 5*6940)
        self.assertIsNone(r["new_S2_A_per_s"])
        self.assertIsNone(r["new_S2_B_per_s"])
        self.assertIsNone(r["freed_probability"])

    def test_regular(self):
        r = scan(["2000-01-01 00:00:00,1,2", "2000-01-01 00:05:00,3,0"])
        self.assertTrue(r["numerically_complete"])
        self.assertEqual(r["end_exclusive"], "2000-01-01T00:10:00")
        self.assertEqual(r["zeros_by_channel"], [0, 1])

    def test_gap_preserved(self):
        r = scan(["2000-01-01 00:00:00,1,2", "2000-01-01 00:10:00,3,4"])
        self.assertEqual(r["gap_count"], 1)
        self.assertFalse(r["numerically_complete"])

    def test_bad_values_not_zero(self):
        r = scan(["2000-01-01 00:00:00,nan,-1"])
        self.assertEqual(r["nonfinite_values"], 1)
        self.assertEqual(r["negative_values"], 1)
        self.assertEqual(r["zeros_by_channel"], [0, 0])
        self.assertFalse(r["numerically_complete"])

    def test_duplicates(self):
        r = scan(["2000-01-01 00:00:00,1,2"] * 2)
        self.assertEqual(r["duplicate_or_reverse_count"], 1)

    def test_wrong_columns(self):
        with self.assertRaises(ValueError):
            scan(["2000-01-01 00:00:00,1"])

    def test_off_grid(self):
        self.assertEqual(scan(["2000-01-01 00:01:00,0,0"])["off_grid_records"], 1)

    def test_all_zero_helium_is_valid_numeric_data(self):
        r = scan(["2000-01-01 00:00:00,0,0"])
        self.assertEqual(r["allzero_records"], 1)
        self.assertTrue(r["numerically_complete"])

    def test_bin_average_does_not_bound_squared_integral(self):
        # Two profiles have equal bin average (1), peak cap (10), and fluence.
        # Their squared integrals differ by factor ten. No interpolation test
        # can convert the mean-square-of-bins into a physical upper bound.
        width = 300
        smooth = width * 1 ** 2
        pulse = (width / 10) * 10 ** 2
        self.assertEqual(smooth * 10, pulse)
        self.assertEqual(width * 1, (width / 10) * 10)

    def test_product_marginal_quantiles_not_joint_quantile(self):
        # Each threshold (peak 2, exposure 2) is exceeded with probability .1.
        # The product threshold 4 is exceeded on disjoint .1 tails: .2 total.
        states = [(0.8, 2, 2), (0.1, 10, 2), (0.1, 2, 10)]
        self.assertAlmostEqual(sum(p for p, b, n in states if b > 2), .1)
        self.assertAlmostEqual(sum(p for p, b, n in states if n > 2), .1)
        self.assertAlmostEqual(sum(p for p, b, n in states if b*n > 4), .2)


if __name__ == "__main__":
    unittest.main()

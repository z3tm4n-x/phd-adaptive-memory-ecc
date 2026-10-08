"""Numerical unit/normalization regressions, not new transport validation."""
import math
import unittest
import numpy as np

from check_legacy import (DATA32_BITS, FULL38_BITS, PINNED_EVENTS, _table_with_cut,
                          csda_common_fold, legacy_event_rows, matrix_fold)
from transport import RangeTable


class LegacyTests(unittest.TestCase):
    def test_identity_known_spectrum_known_lambda(self):
        e = np.array([1.,2.,4.])
        value = matrix_fold(e, np.eye(3), np.full(3,3.), np.full(3,2.), bits=10)
        self.assertAlmostEqual(value, 10*4*math.pi*18)

    def test_per_bit_and_4pi_applied_once(self):
        e = np.array([1.,2.,4.])
        a = matrix_fold(e, np.eye(3), np.ones(3), np.ones(3), DATA32_BITS)
        b = matrix_fold(e, np.eye(3), np.ones(3), np.ones(3), FULL38_BITS)
        self.assertEqual(b/a, 38/32)
        self.assertAlmostEqual(a/DATA32_BITS/(4*math.pi), 3)
        self.assertFalse(np.isclose(b, 4*math.pi*a*38/32))

    def test_linearity_and_secondary_separation(self):
        e = np.array([1.,2.,4.])
        primary = np.eye(3)*.8
        secondary = np.array([[.1,.2,.1],[0,.1,.1],[0,0,.1]])
        source = np.array([3.,2.,1.])
        s = np.array([1.,2.,4.])
        p = matrix_fold(e, primary, source, s)
        q = matrix_fold(e, secondary, source, s)
        total = matrix_fold(e, primary+secondary, source, s)
        self.assertAlmostEqual((p+q)/total, 1)
        self.assertAlmostEqual(matrix_fold(e, primary+secondary, 2*source, s)/total, 2)

    def test_wrong_orientation_sentinel(self):
        e = np.array([1.,2.,4.])
        m = np.array([[.1,.2,.1],[0,.1,.1],[0,0,.1]])
        source, s = np.array([3.,2.,1.]), np.array([1.,2.,4.])
        good = matrix_fold(e, m, source, s)
        wrong = matrix_fold(e, m.T, source, s)
        self.assertNotEqual(good, wrong)

    def test_invalid_matrix_rejected(self):
        with self.assertRaises(ValueError):
            matrix_fold([1,2], np.eye(3), [1,1], [1,1])
        with self.assertRaises(ValueError):
            matrix_fold([1,2], -np.eye(2), [1,1], [1,1])

    def test_added_cut_preserves_range_law(self):
        original = RangeTable()
        split = _table_with_cut(original, 390.)
        e = np.geomspace(.01, 9999., 1001)
        np.testing.assert_allclose(original.range(e), split.range(e), rtol=4e-15)
        self.assertIn(390., split.energy)

    def test_real_T67_peaks_are_explicitly_scaled_not_recomputed(self):
        rows = legacy_event_rows()
        self.assertEqual(tuple(r["event_id"] for r in rows), PINNED_EVENTS)
        self.assertTrue(all(r["cadence_s"] == 300 for r in rows))
        for row in rows:
            self.assertEqual(row["same_chain_scaled_full38_s-1"], row["T67_peak_data32_s-1"]*38/32)
            self.assertEqual(row["shield_g_cm2_al"], 2.7)

    def test_csda_common_support_positive_and_bit_scaling(self):
        table = RangeTable()
        a = csda_common_fold(table, 1.5, bits=DATA32_BITS)
        b = csda_common_fold(table, 1.5, bits=FULL38_BITS)
        self.assertGreater(a, 0)
        self.assertAlmostEqual(b/a, 38/32)


if __name__ == "__main__":
    unittest.main()

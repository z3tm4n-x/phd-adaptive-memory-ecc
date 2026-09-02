#!/usr/bin/env python3
import math
import unittest

import numpy as np

from digitize_published_physics import digitized_rows
from sigma_closure import sigma_phys
from sigma_model import SigmaPoint


class SigmaClosureTests(unittest.TestCase):
    def test_digitized_curve_has_expected_support_and_shape(self):
        rows = digitized_rows()
        self.assertEqual(len(rows), 13)
        e = np.array([r['energy_mev'] for r in rows])
        s = np.array([r['sigma_cm2_per_bit'] for r in rows])
        self.assertTrue(np.all(np.diff(e) > 0))
        self.assertGreater(s.max(), 1.0e-9)
        self.assertLess(s[9], 1.0e-14)  # FLUKA valley near 5 MeV
        self.assertGreater(s[10], 5.0e-14)  # recovered high-energy response
        self.assertTrue(0.79 < e[0] < 0.82)
        self.assertTrue(180 < e[-1] < 190)

    def test_digitization_uncertainty_separate_from_source_model_uncertainty(self):
        rows = digitized_rows()
        self.assertTrue(all(r['source_model_relative_uncertainty'] == 0.35 for r in rows))
        self.assertGreater(rows[1]['sigma_digitization_rel_error'], rows[0]['sigma_digitization_rel_error'])
        self.assertLess(rows[0]['sigma_digitization_rel_error'], 0.07)
        self.assertLess(rows[1]['sigma_digitization_rel_error'], 0.11)

    def test_published_model_keeps_low_boundary_and_holds_high_endpoint(self):
        pts = (
            SigmaPoint(0.9, 9e-10, 'x', 'digitized'),
            SigmaPoint(1.0, 1.2e-9, 'x', 'digitized'),
            SigmaPoint(5.0, 7e-14, 'x', 'digitized'),
            SigmaPoint(40.0, 1e-13, 'x', 'digitized'),
            SigmaPoint(186.0, 8e-14, 'x', 'digitized'),
        )
        pe = np.array([0.8, 1.0, 5.0, 40.0, 185.0])
        ps = np.array([7e-10, 1.1e-9, 5e-15, 1e-13, 6.5e-14])
        x = np.array([0.7, 1.0, 600.0])
        y = sigma_phys(x, pe, ps, pts)
        self.assertGreaterEqual(y[0], 0.0)
        self.assertTrue(math.isclose(y[1], 1.1e-9, rel_tol=1e-12))
        self.assertTrue(math.isclose(y[2], 6.5e-14, rel_tol=1e-12))


if __name__ == '__main__':
    unittest.main()

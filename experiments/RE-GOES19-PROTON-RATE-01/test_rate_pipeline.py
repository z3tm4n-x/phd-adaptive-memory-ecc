import math
import unittest
from types import SimpleNamespace

import numpy as np

from rate_pipeline import (
    _gap_integral_from_anchor,
    _gap_integral_from_p11,
    _solve_high_gamma,
    low_energy_extension,
)
from sigma_model import SigmaPoint, sigma_hat, zero_crossing_low


class LowExtensionTests(unittest.TestCase):
    def test_anchor_and_support(self):
        g = SimpleNamespace(
            times=[0, 1],
            lower=np.array([[0.92], [0.92]]),
            valid=np.array([[True, True], [False, True]]),
            flux=np.zeros((2, 2, 1)),
            uncert=np.zeros((2, 2, 1)),
        )
        g.flux[:, :, 0] = [[10, 20], [30, 40]]
        g.uncert[:, :, 0] = [[1, 2], [3, 4]]
        grid = np.array([0.5, 0.7, 0.8, 0.919, 0.92, 1.0])
        out, u = low_energy_extension(g, grid, 0.6, 2.0)
        self.assertEqual(out[0, 0, 0], 0.0)
        self.assertGreater(out[0, 0, 1], 10.0)
        self.assertGreater(out[0, 0, 3], 10.0)
        self.assertEqual(out[0, 0, 4], 0.0)
        self.assertTrue(np.all(out[1, 0] == 0.0))
        self.assertGreater(out[1, 1, 2], 40.0)
        self.assertGreater(u[0, 1, 2], 2.0)


class HighEnergyBridgeTests(unittest.TestCase):
    def test_power_law_index_recovery(self):
        gamma = 2.5
        j390 = 0.012
        p11 = j390 * 500.0 * (390.0 / 500.0) ** gamma / (gamma - 1.0)
        recovered = _solve_high_gamma(j390, p11)
        self.assertIsNotNone(recovered)
        self.assertAlmostEqual(recovered, gamma, places=10)

    def test_gap_integral_anchor_and_p11_agree(self):
        gamma = 1.8
        j390 = 0.004
        p11 = j390 * 500.0 * (390.0 / 500.0) ** gamma / (gamma - 1.0)
        a = _gap_integral_from_anchor(j390, gamma)
        b = _gap_integral_from_p11(p11, gamma)
        self.assertAlmostEqual(a / b, 1.0, places=12)

    def test_invalid_high_energy_inputs_are_not_fitted(self):
        self.assertIsNone(_solve_high_gamma(0.0, 1.0))
        self.assertIsNone(_solve_high_gamma(1.0, 0.0))


class SigmaModelTests(unittest.TestCase):
    def setUp(self):
        self.points = (
            SigmaPoint(0.9, 9.41e-10, "test", "experimental"),
            SigmaPoint(1.0, 1.27e-9, "test", "experimental"),
            SigmaPoint(1.1, 4.02e-10, "test", "experimental"),
            SigmaPoint(5.0, 6.82e-14, "test", "experimental"),
            SigmaPoint(40.0, 1.00e-13, "test", "experimental"),
            SigmaPoint(186.0, 8.20e-14, "test", "experimental"),
        )

    def test_experimental_anchors_are_preserved(self):
        e = np.array([p.energy_mev for p in self.points])
        y = sigma_hat(e, self.points, "main_loglog")
        expected = np.array([p.sigma_cm2_bit for p in self.points])
        np.testing.assert_allclose(y, expected, rtol=1e-14, atol=0.0)

    def test_low_continuation_reaches_zero_without_negative_sigma(self):
        e0 = zero_crossing_low(self.points)
        y = sigma_hat(np.array([e0 * 0.9, e0, 0.8]), self.points, "main_loglog")
        self.assertEqual(y[0], 0.0)
        self.assertLess(abs(y[1]), 1e-22)
        self.assertGreater(y[2], 0.0)


if __name__ == "__main__":
    unittest.main()

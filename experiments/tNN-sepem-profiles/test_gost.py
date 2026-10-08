import json
import math
from types import SimpleNamespace
import unittest

import numpy as np

from gost import expected_event_count, spectral_parameters, spectrum, summary


class GostTests(unittest.TestCase):
    def test_event_count_both_wolf_versions(self):
        annual = [7.1, 19.4, 63.2, 98.4, 107.4, 104.9, 82, 55.1, 34.5, 21.3]
        self.assertAlmostEqual(expected_event_count(np.repeat(annual, 12)), 92.5548, places=11)
        self.assertAlmostEqual(expected_event_count([100] * 120, "1.0"), 156.0)
        self.assertAlmostEqual(expected_event_count([100] * 120, "2.0"), 111.0)
        self.assertEqual(expected_event_count([0]), 0)
        # Version factors belong to different Wolf scales, not interchangeable.
        self.assertNotEqual(expected_event_count([100], "1.0"),
                            expected_event_count([100], "2.0"))

    def test_all_sixteen_source_anchors(self):
        # Independently transcribed published tables 1--8, n=64/128, Pi=0.1.
        anchors = {
            ("fluence", 64): [9.671, 14.645, 1.392, 2.620],
            ("fluence", 128): [9.942, 14.276, 1.400, 2.602],
            ("peak_flux", 64): [3.500, 16.85, 1.366, 2.520],
            ("peak_flux", 128): [3.684, 16.06, 1.390, 2.457],
        }
        keys = ("log10_c", "break_energy_mev", "gamma1", "gamma2")
        for (product, nbar), values in anchors.items():
            result = spectral_parameters(nbar, product)
            self.assertEqual([result[k] for k in keys], values)

    def test_logarithmic_midpoint_and_break(self):
        nbar = math.sqrt(64 * 128)
        p = spectral_parameters(nbar, "fluence")
        self.assertAlmostEqual(p["log10_c"], (9.671 + 9.942) / 2)
        self.assertAlmostEqual(p["break_energy_mev"], (14.645 + 14.276) / 2)
        c = 10 ** p["log10_c"]
        self.assertAlmostEqual(spectrum(p["break_energy_mev"], nbar, "fluence") / c, 1)

    def test_spectrum_independent_scalar_formula(self):
        # No production spectral-parameter/helper call in this scalar reference.
        c, ek, g1, g2 = 10 ** 9.671, 14.645, 1.392, 2.620
        energies = [1., 10., ek, 30., 1000.]
        expected = [c * (e / ek) ** -g1 if e < ek else
                    c * (math.sqrt(e * (e + 1876)) /
                         math.sqrt(ek * (ek + 1876))) ** (-2 * g2)
                    for e in energies]
        np.testing.assert_allclose(spectrum(energies, 64, "fluence"), expected, rtol=3e-15)

    def test_infinite_fluence_reference_and_json(self):
        result = summary(SimpleNamespace(quadratures={}), 92.5548)
        value = result["incident_integrals_to_infinity"]["fluence"]["30"]["value"]
        # Independent direct scalar quadrature recorded before this module was
        # written, using published cells and the declared log2 interpolation.
        self.assertAlmostEqual(value / 1.68089989379e10, 1., delta=2e-11)
        self.assertIn("conditional", result["status"])
        json.dumps(result, allow_nan=False)

    def test_solid_angle_and_bit_normalization_sentinel(self):
        e, weight = 64., 2e-12
        result = summary(SimpleNamespace(quadratures={"one_node": ([e], [weight])}), 64)
        measured = result["gost"]["one_node"]
        bits = 2 ** 19 * 38
        # Hard-coded separate scalar formula catches duplicate 4pi, missing
        # memory normalization, and accidental 32-bit/data-only normalization.
        phi = 10 ** 9.671 * (e * (e + 1876) / (14.645 * (14.645 + 1876))) ** -2.620
        peak = 10 ** 3.500 * (e * (e + 1876) / (16.85 * (16.85 + 1876))) ** -2.520
        expected_n = bits * weight * phi
        expected_peak = 4 * math.pi * bits * weight * peak
        self.assertAlmostEqual(measured["N_expected_upsets"] / expected_n, 1., delta=2e-15)
        self.assertAlmostEqual(measured["peak_lambda_s-1"] / expected_peak, 1., delta=2e-15)
        wrong_repeated_angle = 4 * math.pi * measured["N_expected_upsets"]
        with self.assertRaises(AssertionError):
            np.testing.assert_allclose(wrong_repeated_angle, expected_n, rtol=1e-12)

    def test_invalid_inputs_rejected(self):
        for nbar in (63.9, 128.1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                spectral_parameters(nbar, "fluence")
        with self.assertRaises(ValueError):
            spectral_parameters(92.5548, "ambiguous_flux")
        for wolf in ([], [-1], [float("nan")], [[1]]):
            with self.assertRaises(ValueError):
                expected_event_count(wolf)
        with self.assertRaises(ValueError):
            expected_event_count([1], "unknown")
        for energies in ([.5], [float("nan")], [float("inf")]):
            with self.assertRaises(ValueError):
                spectrum(energies, 92.5548, "fluence")
        for energy, weight in (([30], [-1]), ([30], [float("nan")]), ([30, 40], [1])):
            with self.assertRaises(ValueError):
                summary(SimpleNamespace(quadratures={"bad": (energy, weight)}), 92.5548)


if __name__ == "__main__":
    unittest.main()

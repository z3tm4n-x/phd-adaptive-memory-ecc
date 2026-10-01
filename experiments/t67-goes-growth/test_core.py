import itertools
import math
import unittest
import numpy as np
from growth import h_l, segments, window_extreme, fastest_e_fold, transitions
from sgps import clean, corrected_energy, directions, lut_matches, OLD_LO, OLD_HI, CORR_LO, CORR_HI, CORR


class GrowthTests(unittest.TestCase):
    def test_h_zero_boundary_and_relative(self):
        np.testing.assert_allclose(h_l([0, .5, 1, math.e], 1), [0, .5, 1, 2])
        self.assertEqual(float(h_l(0, 1)), 0)
        with self.assertRaises(ValueError):
            h_l([1], 0)

    def test_no_cross_gap_version_or_bad_bin(self):
        t = np.array([0, 60, 120, 240, 300, 360])
        sig = np.array(["a", "a", "a", "a", "b", "b"])
        self.assertEqual(list(segments(t, np.array([1, 0, 1, 1, 1, 1], bool), sig, 60)), [(0, 1), (2, 3), (3, 4), (4, 6)])

    def test_exact_exponential_windows(self):
        t = np.arange(10)*60
        x = np.exp(t / 300)
        result = window_extreme(t, x, np.ones(10, bool), np.zeros(10), 60, 300, 1)
        self.assertEqual(result["pairs"], 5)
        self.assertAlmostEqual(result["h"][0], 1/300)
        self.assertAlmostEqual(result["log"][0], 1/300)

    def test_resolution_and_zero_background(self):
        r = window_extreme(np.arange(3)*300, np.array([0, 1, 2]), np.ones(3, bool), np.zeros(3), 300, 60, 1)
        self.assertEqual(r["status"], "unresolved_at_native_resolution")
        r = window_extreme(np.arange(3)*60, np.array([0, 1, 2]), np.ones(3, bool), np.zeros(3), 60, 60, 1)
        self.assertEqual(r["log_pairs_above_level"], 1)

    def test_heap_against_independent_exhaustive(self):
        # Exhaust all non-monotonic small traces, not another implementation of heap.
        for values in itertools.product([.5, 1, 3], repeat=5):
            x, t = np.array(values), np.arange(5)*60
            expected = []
            for i in range(5):
                if x[i] < 1:
                    continue
                for j in range(i+1, 5):
                    if x[j] < 1:
                        break
                    if x[j] >= math.e*x[i]:
                        expected.append((float(t[j]-t[i]), i, j))
                        break
            got = fastest_e_fold(t, x, np.ones(5, bool), np.zeros(5), 60, 1)
            self.assertEqual(got["fastest"], min(expected) if expected else None)

    def test_recross_cancel_then_complete(self):
        x = np.array([0., 1., .5, 1., 2., 3., 2., .5, 1., 3.])
        out = transitions(np.arange(len(x))*60, x, np.ones(len(x), bool), np.zeros(len(x)), 60, 1, 3)
        self.assertEqual([(q["start_index"], q["end_index"]) for q in out], [(3, 5), (8, 9)])
        self.assertEqual([q["binned_expected_inversions"] for q in out], [180, 60])

    def test_initial_above_and_same_bin_are_censored(self):
        x = np.array([2., 3., 0., 4.])
        out = transitions(np.arange(4)*60, x, np.ones(4, bool), np.zeros(4), 60, 1, 3)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0]["unresolved_same_bin"])
        self.assertIsNone(out[0]["binned_expected_inversions"])

    def test_transition_does_not_bridge_bad_bin(self):
        x = np.array([0., 1., 2., 3.])
        self.assertEqual(transitions(np.arange(4)*60, x, np.array([1, 1, 0, 1], bool), np.zeros(4), 60, 1, 3), [])


class AdapterTests(unittest.TestCase):
    def test_lut_polarity_follows_metadata_not_variable_name(self):
        for good in (0, 1):
            attrs = {"long_name": f"A boolean indicator: {good} if all input files' specified lookup tables matched the tables that were used, {1-good} otherwise."}
            self.assertTrue(lut_matches(good, attrs))
            self.assertFalse(lut_matches(1-good, attrs))
        with self.assertRaises(ValueError):
            lut_matches(0, {})

    def test_units_fill_zero_and_range(self):
        a = clean([0, -1e31, -1, 9000, 10], {"_FillValue": -1e31, "valid_min": 0, "valid_max": 8000})
        self.assertEqual(a[0], 0)
        self.assertEqual(a[-1]*1000, 10000)
        self.assertTrue(np.all(np.isnan(a[1:4])))

    def test_yaw_keeps_sensor_identity(self):
        a = np.array([[[10], [20]], [[30], [40]], [[50], [60]]])
        r = directions(a, np.array([0, 2, 1]))
        np.testing.assert_equal(r[:2, :, 0], [[20, 10], [30, 40]])
        self.assertTrue(np.all(np.isnan(r[2])))

    def test_correction_once(self):
        lo = np.tile(np.r_[OLD_LO, np.arange(7)+30], (2, 1))
        hi = np.tile(np.r_[OLD_HI, np.arange(7)+40], (2, 1))
        eff = np.sqrt(lo*hi)
        a = corrected_energy(lo, hi, eff)
        np.testing.assert_equal(a[3][:6], CORR)
        b = corrected_energy(a[0], a[1], a[2])
        np.testing.assert_equal(b[3], np.ones(13))

    def test_missing_effective_energy_is_explicit_model_choice(self):
        lo = np.tile(np.r_[OLD_LO, np.arange(7)+30], (2, 1))
        hi = np.tile(np.r_[OLD_HI, np.arange(7)+40], (2, 1))
        r = corrected_energy(lo, hi, np.full_like(lo, np.nan))
        self.assertTrue(r[5])
        np.testing.assert_allclose(r[2], np.sqrt(r[0]*r[1]))


class ResponseTests(unittest.TestCase):
    def test_vectorized_gap_against_upstream_scalar_reference(self):
        from types import SimpleNamespace
        from response import gap_bridge, NS
        rng = np.random.default_rng(67)
        f = np.exp(rng.uniform(-9, 2, size=(37, 2, 14)))
        f[::7, :, 12] = 0
        f[::11, :, 13] = 0
        v = np.ones((37, 2), bool)
        a, fallback, diag = gap_bridge(f, v)
        g = SimpleNamespace(times=np.arange(37), valid=v, flux=f[:, :, :13], p11=f[:, :, 13],
                            uncert=np.zeros((37, 2, 13)), p11_uncert=np.zeros((37, 2)))
        b = NS['high_energy_gap_bridge'](g)
        np.testing.assert_allclose(a, b[0], rtol=3e-14)
        self.assertEqual(diag['fallback_rows'], b[4]['fallback_rows'])

    def test_gap_all_missing_is_missing_not_zero(self):
        from response import gap_bridge
        a, _, _ = gap_bridge(np.full((3, 2, 14), np.nan), np.zeros((3, 2), bool))
        self.assertTrue(np.all(np.isnan(a)))

    def test_linear_kernel_against_full_transport(self):
        from types import SimpleNamespace
        from response import Response, BITS, sigma
        r=Response()
        lo=np.tile(np.r_[CORR_LO, [25.9,41,83,98.6,113.4,155.2,267]], (2,1))
        hi=np.tile(np.r_[CORR_HI, [35.2,74,100.7,120.6,142.4,231.5,390]], (2,1))
        s=SimpleNamespace(signature='synthetic', lower=lo, upper=hi, energy=np.sqrt(lo*hi))
        kp,ks,basis=r.channel_kernel(s,0,'main_loglog')
        flux=np.arange(1,14,dtype=float)**1.2
        spectrum=basis@flux
        behind=(r.primary+r.secondary)@(4*math.pi*spectrum)
        direct=BITS*np.trapezoid(behind*sigma.sigma_hat(r.energy,r.points,'main_loglog'),r.energy)
        self.assertAlmostEqual(float(flux@(kp+ks)), float(direct), places=13)
        np.testing.assert_equal(kp[:6]+ks[:6], 0)


if __name__ == "__main__":
    unittest.main()

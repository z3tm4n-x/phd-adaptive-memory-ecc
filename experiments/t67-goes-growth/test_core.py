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

    def test_all_pair_slopes_bounded_by_native_increment(self):
        rng=np.random.default_rng(67)
        x=np.r_[0.,np.exp(rng.uniform(-6,2,19))]
        t=np.arange(len(x))*60
        r=window_extreme(t,x,np.ones(len(x),bool),np.zeros(len(x)),60,60,.01)
        independent=[]
        def scalar(v):
            return v/.01 if v<=.01 else 1+math.log(v/.01)
        for i in range(len(x)):
            for j in range(i+1,len(x)):
                independent.append((scalar(x[j])-scalar(x[i]))/(t[j]-t[i]))
        self.assertAlmostEqual(r['h'][0],max(independent))

    def test_rescale_intensity_and_threshold_together(self):
        x=np.array([0.,.01,.1,1.])
        np.testing.assert_allclose(h_l(x,.1),h_l(x*39/32,.1*39/32))

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
        np.testing.assert_equal(clean([2,-999],{'_FillValue':-999,'scale_factor':.5,'add_offset':1}),[2,np.nan])

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

    def test_missing_unused_channel_cannot_mark_nan_response_usable(self):
        from types import SimpleNamespace
        from response import Response
        lo=np.tile(np.r_[CORR_LO,[25.9,41,83,98.6,113.4,155.2,267]],(2,1))
        hi=np.tile(np.r_[CORR_HI,[35.2,74,100.7,120.6,142.4,231.5,390]],(2,1))
        f=np.ones((2,2,14));f[0,0,0]=np.nan
        src=SimpleNamespace(signature='missing',lower=lo,upper=hi,energy=np.sqrt(lo*hi),
                            time=np.arange(2)*60,yaw=np.zeros(2),corrected=f,uncertainty=np.ones_like(f),
                            screened=np.isfinite(f),strict=np.isfinite(f))
        r=Response().calculate(src)
        self.assertTrue(np.isnan(r['main_loglog'][0,0]))
        self.assertFalse(r['screened'][0,0])
        self.assertFalse(r['core_strict'][0,0])


class SelectionTests(unittest.TestCase):
    def test_union_exposure_excludes_missing_response_and_overlap(self):
        from analyze import union_summary
        group={'time':np.array([0.,60.]),'main_loglog':np.array([[1.,np.nan],[np.nan,2.]]),
               'screened':np.ones((2,2),bool),'strict':np.zeros((2,2),bool)}
        e={'analysis_start':'1970-01-01T00:00:00+00:00','analysis_end_exclusive':'1970-01-01T00:02:00+00:00'}
        r=union_summary(group,[e,e],19,60)
        self.assertEqual(r[1]['sum_model_inversions'],60)
        self.assertEqual(r[1]['unique_retained_s'],60)
        self.assertEqual(r[4]['sum_model_inversions'],120)
        self.assertIsNone(r[2]['peak_model_s-1'])

    def test_atomic_cache_round_trip_including_nan_and_masks(self):
        import tempfile
        from pathlib import Path
        from analyze import save_series
        arrays={'x':np.array([0.,np.nan,2.]),'mask':np.array([True,False,True])}
        with tempfile.TemporaryDirectory(prefix='t67-test-') as d:
            p=Path(d)/'tiny.npz';save_series(p,arrays)
            with np.load(p) as z:
                for k,v in arrays.items():np.testing.assert_equal(z[k],v)

    def test_catalogue_not_limited_and_author_date_not_duplicate(self):
        from selection import select
        rows=[{'onset_utc':f'2025-06-{d:02d}T00:00:00+00:00','peak_utc':f'2025-06-{d:02d}T12:00:00+00:00'} for d in range(1,16)]
        rows.append({'onset_utc':'2026-01-18T22:55:00+00:00','peak_utc':'2026-01-19T19:15:00+00:00'})
        cfg={'author_dates':['2026-01-19'],'cutoff_exclusive_utc':'2026-10-01T00:00:00Z',
             'days_before_onset':2,'days_after_peak':2,'background_hours':24}
        r=select({'catalogue':{'rows':rows},'files':[]},cfg)
        self.assertEqual(len(r['events']),17) # all 16 catalogue rows + full month
        self.assertEqual(sum(bool(e.get('author_dates')) for e in r['events']),1)
        self.assertFalse(next(e for e in r['events'] if e.get('author_dates'))['holdout'])
        self.assertTrue(r['files'][0]['name'].startswith('se_'))


class FigureTests(unittest.TestCase):
    def test_atomic_figures_round_trip(self):
        import tempfile
        from pathlib import Path
        from figures import plt, save, validate_image
        with tempfile.TemporaryDirectory(prefix='t67-figure-test-') as d:
            p=Path(d)/'tiny'
            fig,ax=plt.subplots();ax.plot([0,1],[1,2])
            save(fig,p)
            for extension in ('.png','.svg'):
                validate_image(p.with_suffix(extension).read_bytes(),extension)
            self.assertEqual(len(list(Path(d).iterdir())),2)

    def test_truncated_figures_fail_validation(self):
        import xml.etree.ElementTree as ET
        from figures import validate_image
        with self.assertRaises(ET.ParseError):
            validate_image(b'<svg xmlns="http://www.w3.org/2000/svg"><path', '.svg')
        with self.assertRaises(ValueError):
            validate_image(b'\x89PNG\r\n\x1a\n', '.png')


if __name__ == "__main__":
    unittest.main()

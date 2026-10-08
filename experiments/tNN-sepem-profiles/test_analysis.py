"""Small deterministic checks of event statistics and empirical mission model."""
import unittest
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy.ndimage import maximum_filter1d
from scipy.stats import poisson

from analysis import (analyze, compound_poisson, detect_events, event_metrics, moments,
                      quantile_order_interval, rolling_ten_year_windows,
                      validate_series, _calendar_plus_ten_years)


class EventTests(unittest.TestCase):
    def test_rectangular(self):
        peak, n, s2, r = moments([4, 4, 4], 300)
        self.assertEqual((peak, n, s2, r), (4, 3600, 14400, 1))

    def test_triangular_limit(self):
        # Independent midpoint Riemann sum of a unit triangle converges to 2/3.
        x = (np.arange(100000)+.5)/100000
        y = 1-np.abs(2*x-1)
        peak, n, s2, r = moments(y, 1/100000)
        self.assertAlmostEqual(n, .5, places=12)
        self.assertAlmostEqual(s2, 1/3, places=9)
        # The sampled peak is 1-1/n; its exact finite-bin r is 2/3+2/(3n).
        self.assertAlmostEqual(r, 2/3+2/(3*100000), places=12)
        self.assertLess(abs(r-2/3), 1e-5)

    def test_zero_exposure(self):
        self.assertEqual(moments([0, 0], 300), (0., 0., 0., None))
        self.assertEqual(detect_events(np.zeros(30)), [])

    def test_peak_and_bin_moments(self):
        t = np.datetime64("2000-01-01T00:00:00", "s") + np.arange(4)*np.timedelta64(300, "s")
        y = np.array([1., 2., 5., 2.])
        f = np.full((4, 4), 2.)
        e = event_metrics(t, y, [(0, 4)], f)[0]
        self.assertEqual(e["N_expected_upsets"], 3000)
        self.assertEqual(e["S2_s-1"], 10200)
        self.assertEqual(e["peak_utc"], "2000-01-01T00:10:00Z")
        self.assertEqual(e["end_exclusive_utc"], "2000-01-01T00:20:00Z")
        self.assertAlmostEqual(e["fluence_gt30_omni_cm-2"], 2400*4*np.pi)
        self.assertEqual(e["peak_flux_gt30_cm-2_s-1_sr-1"], 2.)

    def test_merge_equal_boundary_and_minimum_after_merge(self):
        y = np.ones(30)
        y[1:7] = 20
        y[13:19] = 20
        self.assertEqual(detect_events(y, baseline=1, merge_hours=.5), [(1, 19)])
        self.assertEqual(detect_events(y, baseline=1, merge_hours=.499), [])

    def test_strict_threshold(self):
        y = np.r_[np.ones(12), np.full(12, 10.), np.ones(12)]
        self.assertEqual(detect_events(y, baseline=1, multiplier=10), [])

    def test_internal_gap_counts_toward_integral(self):
        y = np.r_[np.full(12, 20.), np.ones(12), np.full(12, 20.)]
        intervals = detect_events(y, baseline=1, merge_hours=1)
        self.assertEqual(intervals, [(0, 36)])
        self.assertEqual(moments(y)[1], (24*20+12)*300)

    def test_efold_and_censoring(self):
        t = np.datetime64("2000-01-01", "s") + np.arange(6)*np.timedelta64(300, "s")
        e = event_metrics(t, np.array([.01,.2,.3,.4,.8,1.]), [(0, 6)])[0]
        self.assertEqual(e["early_efold_s"], 300)
        e = event_metrics(t, np.array([.2,.2,.3,.4,.8,1.]), [(0, 6)])[0]
        self.assertIsNone(e["early_efold_s"])
        # A later re-crossing must not turn a left-censored initial rise into
        # an observed one. This catches the defect found in E0043/E0081/E0083.
        e = event_metrics(t, np.array([.2,.01,.2,.4,.8,1.]), [(0, 6)])[0]
        self.assertIsNone(e["early_efold_s"])

    def test_missing_data_not_zero_exposure(self):
        t = np.array(["2000-01-01T00:00", "2000-01-01T00:10"], dtype="datetime64[s]")
        with self.assertRaises(ValueError):
            validate_series(t, [1, 1])
        with self.assertRaises(ValueError):
            detect_events([1, np.nan, 1])


class MissionTests(unittest.TestCase):
    def test_zero_count(self):
        sample, count = compound_poisson([2, 4], 0, missions=30)
        self.assertTrue(np.all(sample == 0))
        self.assertTrue(np.all(count == 0))

    def test_one_event_population_and_nbar(self):
        sample, count = compound_poisson([[3., 5.]], 4, missions=30000, seed=34)
        np.testing.assert_array_equal(sample[:, 0], 3*count)
        np.testing.assert_array_equal(sample[:, 1], 5*count)
        self.assertLess(abs(np.mean(count)-4), .06)
        q = quantile_order_interval(sample[:, 0])
        truth = 3*poisson.ppf(.9, 4)
        self.assertLessEqual(q["lower"], truth)
        self.assertGreaterEqual(q["upper"], truth)

    def test_batch_invariance(self):
        a, ac = compound_poisson([[1.,2.], [3.,6.], [5.,10.]], 3.5, 300, 18, batch=9)
        b, bc = compound_poisson([[1.,2.], [3.,6.], [5.,10.]], 3.5, 300, 18, batch=31)
        np.testing.assert_array_equal(ac, bc)
        np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(a[:, 1], 2*a[:, 0])

    def test_invalid_population_rejected(self):
        with self.assertRaises(ValueError):
            compound_poisson([], 3)
        with self.assertRaises(ValueError):
            compound_poisson([1], -1)

    def test_interval_ranks_have_binomial_coverage(self):
        from scipy.stats import binom
        x = np.arange(20000.)
        r = quantile_order_interval(x)
        lo, hi = r["lower_order_rank_1_based"], r["upper_order_rank_1_based"]
        coverage = binom.cdf(hi-1, len(x), .9)-binom.cdf(lo-1, len(x), .9)
        self.assertGreaterEqual(coverage, .95)


class WindowTests(unittest.TestCase):
    def test_calendar_leap_rule(self):
        actual = _calendar_plus_ten_years(np.array(["1980-02-28", "1980-02-29", "1980-03-01"], dtype="datetime64[D]"))
        np.testing.assert_array_equal(actual, np.array(["1990-02-28", "1990-02-28", "1990-03-01"], dtype="datetime64[D]"))

    def test_forward_maximum_alignment_odd_even(self):
        y = np.array([1,4,1,2,8,3,1,1,7,2.])
        for length in (3, 4):
            got = maximum_filter1d(y, size=length, origin=-(length//2), mode="constant", cval=0)
            want = np.array([np.max(y[i:i+length]) for i in range(len(y))])
            np.testing.assert_array_equal(got, want)

    def test_all_grid_windows_against_independent_daily_loop(self):
        # Daily grid keeps this synthetic ten-year check small; the production
        # contract passes dt=300 and includes every such start, not just days.
        t = np.arange(np.datetime64("1974-07-01"), np.datetime64("1985-01-01"), np.timedelta64(1, "D")).astype("datetime64[s]")
        y = np.ones(len(t))
        y[15:25] = 4
        intervals = [(0, 30), (len(t)-50, len(t))]
        daily, result = rolling_ten_year_windows(t, y, intervals, dt=86400)
        z = np.zeros(len(t))
        for a, b in intervals:
            z[a:b] = y[a:b]
        self.assertEqual(result["all_grid_window_count"], len(daily))
        for row in daily:
            a = np.datetime64(row["start_utc"].removesuffix("Z"))
            b = np.datetime64(row["end_exclusive_utc"].removesuffix("Z"))
            inside = z[(t >= a) & (t < b)]
            peak, total, square, r = moments(inside, 86400)
            self.assertEqual(row["peak_lambda_s-1"], peak)
            self.assertEqual(row["N_expected_upsets"], total)
            self.assertEqual(row["S2_s-1"], square)
            self.assertEqual(row["multi_event_ratio"], r)

    def test_two_events_reduce_rectangle_ratio(self):
        peak, total, square, r = moments([4,4,1,1], 300)
        self.assertEqual(r, 34/40)
        self.assertLess(r, 1)


class IntegrationTests(unittest.TestCase):
    def test_analysis_includes_model_scope_and_empty_GOST_cells(self):
        t = np.datetime64("2000-01-01", "s") + np.arange(7*288)*np.timedelta64(300, "s")
        y = np.ones(len(t))
        for start in (24, 2*288, 4*288, 6*288):
            y[start:start+36] = 20
        flux = np.full((len(t), 4), 2.)
        config = {"mission_mean_events": 2., "monte_carlo_missions": 1000, "mission_seed": 35}
        cache = Path(__file__).resolve().parent / ".cache"
        cache.mkdir(exist_ok=True)
        # Stable ignored directory avoids Windows sandbox ACL incompatibility
        # of tempfile's restricted mode; it contains only synthetic test data.
        with patch("analysis._figures"):
            out = cache / "test-analysis"
            out.mkdir(exist_ok=True)
            summary = analyze(t, {"csda_3_pdi": y, "scaled": y*2}, flux, out, config)
            self.assertEqual(summary["mission_model_B"]["status"], "conditional_empirical_model")
            self.assertEqual(summary["ten_year_windows"]["all_grid_window_count"], 0)
            reread = json.loads((out/"analysis_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(reread["bootstrap_eligible_event_ids"], ["E0001", "E0002", "E0003", "E0004"])
            self.assertIn("matched_GOST_convolution_not_supplied", (out/"design-model-A.csv").read_text())
            import csv
            with (out/"mission-model-B.csv").open() as f:
                rows = list(csv.DictReader(f))
            q = {r["variant"]: float(r["q90"]) for r in rows}
            self.assertAlmostEqual(q["scaled"], 4*q["csda_3_pdi"])

    def test_machine_configuration_is_not_silently_ignored(self):
        t = np.datetime64("2000-01-01", "s") + np.arange(288)*np.timedelta64(300, "s")
        y = np.ones(len(t))
        y[24:36] = 7
        config = {"nominal_rate_key": "custom", "event_threshold_factor": 5,
                  "event_merge_gap_hours": 6, "event_min_above_hours": .5,
                  "gost_population_fluence_30_cm2": 1e20,
                  "mission_mean_events": 2, "bootstrap_missions": 15, "bootstrap_seed": 3}
        out = Path(__file__).resolve().parent / ".cache" / "test-config"
        with patch("analysis._figures"):
            summary = analyze(t, {"custom": y}, np.ones((len(t), 4)), out, config)
        self.assertEqual(summary["nominal_rate"], "custom")
        self.assertEqual(summary["threshold_nominal_s-1"], 5)
        self.assertEqual(summary["event_population_summaries"]["threshold_5_merge_6h"]["event_count"], 1)
        self.assertEqual(summary["mission_model_B"]["eligible_events"], 0)
        config["event_baseline_quantile"] = .2
        with self.assertRaisesRegex(ValueError, "baseline q10"):
            analyze(t, {"custom": y}, np.ones((len(t), 4)), out, config)


if __name__ == "__main__":
    unittest.main()

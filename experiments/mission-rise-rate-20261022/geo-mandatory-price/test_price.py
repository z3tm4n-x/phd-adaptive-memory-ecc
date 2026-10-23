"""Directed checks of the new bounds; no accepted campaign is repeated."""
from fractions import Fraction as F
from pathlib import Path
import unittest
from unittest.mock import patch

import run


class PriceGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run.evaluate()
        c = cls.result['constants']
        cls.A, cls.D = c['app39_lower'], c['W_read_lower_s']
        cls.T = cls.result['unchanged']['T_s']
        cls.Ps, cls.Cf = c['fast_pass_upper_s'], c['fixed44_upper']
        cls.gate = cls.result['gate']

    def test_exact_acceptance_boundary_and_two_sides(self):
        p = self.gate['support_period_min_s']
        f = lambda x: run.support_floor(self.A, self.D, self.T, x)
        self.assertEqual(f(p), self.Cf / 5)
        self.assertGreater(f(p * F(999, 1000)), self.Cf / 5)
        self.assertLess(f(p * F(1001, 1000)), self.Cf / 5)
        self.assertLess(abs(p - F('10883.43497399815')), F(1, 10**10))

    def test_exact_startup_boundary_and_two_sides(self):
        h = self.gate['startup_duration_max_s']
        f = lambda x: run.startup_floor(self.A, self.D, self.T, self.Ps, x)
        self.assertEqual(f(h), self.Cf / 5)
        self.assertLess(f(h * F(999, 1000)), self.Cf / 5)
        self.assertGreater(f(h * F(1001, 1000)), self.Cf / 5)

    def test_period_constraints_have_empty_intersection(self):
        self.assertGreater(self.gate['support_period_min_s'],
                           self.gate['relaxed_period_max_s'])
        self.assertFalse(self.gate['passes_necessary_price'])
        self.assertGreater(self.gate['startup_at_period_min'], self.Cf)
        self.assertGreater(self.result['geometry']['minimum_h_minus_over_P_margin_s'], 0)

    def test_horizon_clipping_zero_and_invalid_durations(self):
        f = lambda x: run.startup_floor(self.A, self.D, self.T, self.Ps, x)
        self.assertEqual(f(0), self.A)
        self.assertEqual(f(self.T), f(2 * self.T))
        self.assertGreater(f(self.T), self.Cf / 5)
        with self.assertRaises(ValueError):
            f(-1)
        with self.assertRaises(ValueError):
            run.support_floor(self.A, self.D, self.T, 0)

    def test_application_floor_is_not_zero(self):
        self.assertGreater(self.A, 0)
        out = run.gate(self.A, self.D, self.T, self.Ps, 5 * self.A)
        self.assertEqual(out['status'], 'excluded_by_application_floor')

    def test_lower_goal_can_pass_necessary_gate(self):
        out = run.gate(self.A, self.D, self.T, self.Ps, self.Cf, F(1))
        self.assertTrue(out['passes_necessary_price'])
        p = (out['support_period_min_s'] + out['relaxed_period_max_s']) / 2
        self.assertLessEqual(max(run.support_floor(self.A, self.D, self.T, p),
                                run.startup_floor(self.A, self.D, self.T, self.Ps, p)), self.Cf)

    def test_independent_batched_calendar_count(self):
        # Enumerate actual starts of a small calendar, including arbitrary
        # one-pass initial phase and the latest allowed endpoint displacement.
        # This oracle does not call either floor function or its count formula.
        xi, jitter, g, c = F(100001, 100000), F(1, 2), 196, 164
        checks = 0
        for W in (8, 16, 32):
            ps = W * g * xi + jitter
            for phase in (F(0), ps / 7, ps):
                for edge in (0, 1, 2, 3, 5):
                    for offset in (-jitter, F(0), jitter):
                        duration = max(F(0), edge * ps + offset)
                        starts = [phase + (8 * g * (j // 8) + c * (j % 8)) * xi + jitter
                                  for j in range(8 * W)]
                        actual = sum(t < duration for t in starts)
                        lower = W * max(F(0), duration / ps - 2)
                        self.assertLessEqual(lower, actual)
                        checks += 1
        self.assertEqual(checks, 135)

    def test_no_double_counting_support_and_startup(self):
        p = self.gate['support_period_min_s']
        support = run.support_floor(self.A, self.D, self.T, p)
        start = run.startup_floor(self.A, self.D, self.T, self.Ps, p)
        self.assertEqual(self.gate['startup_at_period_min'], max(support, start))
        self.assertLess(max(support, start), support + start - self.A)

    def test_changed_environment_refuses_frozen_fixed_price(self):
        original = Path.read_bytes
        def changed(path):
            data = original(path)
            return data + b' ' if path == run.ROOT / run.COMMON else data
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'recertify fixed/OFF'):
                run.load()

    def test_strong_code_off_and_no_new_campaign(self):
        rows = self.result['competitors']
        self.assertTrue(rows['fixed44']['sufficient'])
        self.assertLessEqual(rows['fixed44']['Q_upper'], self.result['unchanged']['epsilon'])
        for name in ('OFF39', 'OFF44'):
            self.assertEqual(rows[name]['Q_upper'], 1)
            self.assertFalse(rows[name]['sufficient'])
        self.assertEqual(set(self.result['computations'].values()), {0})


if __name__ == '__main__':
    unittest.main()

"""Small deterministic checks; no research campaign or statistical sampling."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
import math
import unittest
from types import SimpleNamespace

import diagnostics as d


class CellTests(unittest.TestCase):
    def test_compression_against_explicit_phases_and_endpoints(self):
        for words in (1, 2, 3, 7):
            P = F(7, 3)
            for T in (P, P + P / words / 2, 2 * P, 7 * P + P / 3):
                for gap in (F(0), P / words / 2, P / words):
                    lengths = []
                    for j in range(words):
                        reads, t = [], j * P / words
                        while t <= T:
                            reads.append(t)
                            t += P
                        lengths.append(reads[0])
                        lengths += [b - a - gap for a, b in zip(reads, reads[1:])]
                        lengths.append(max(F(0), T - reads[-1] - gap))
                    compressed = d.fixed_cells(words, P, T, gap)
                    self.assertEqual(sum(h * h for h in lengths), compressed["sum_h2"])

    def test_d4_and_linear_witness(self):
        n, r, h = 39, Decimal("2.4e-8"), Decimal("0.3145728")
        with localcontext() as ctx:
            ctx.prec = 60
            x = n * r * h
            p = Decimal(n - 1) / n * (-x).exp() * x * x / 2
            alternate = Decimal(math.comb(n, 2)) * (r * h) ** 2 * (-x).exp()
            self.assertLess(abs(p - alternate), Decimal("1e-65"))
            safe = Decimal(math.comb(n, 2)) * (r * h) ** 2 * (1 - x)
            self.assertLess(safe, p)
            # Starting with one bad bit: exactly one new, different bit suffices.
            dirty = (-x).exp() * (n - 1) * r * h
            self.assertGreater(dirty, p)

    def test_directed_probability_report(self):
        for s in (F(0), F(1, 1000), F(22), F(222222222222229, 10**13)):
            report, floored = d.probability_lower_from_rational_s(s)
            with localcontext() as ctx:
                ctx.prec = 90
                exact = 1 - (-d.decimal_fraction(s)).exp()
                self.assertLessEqual(Decimal(report), exact)
                self.assertLessEqual(F(floored), s)

    def test_invalid_timing(self):
        for args in ((0, "1", "2", "0"), (2, "1", ".9", "0"), (2, "1", "2", ".6")):
            with self.assertRaises((ValueError, ZeroDivisionError)):
                d.fixed_cells(*args)


class CounterTests(unittest.TestCase):
    def test_mu_integral_and_branches(self):
        P, a, g = .3, 5., .7
        for v in (0., g * P, 1., g * a, 7.):
            # Integral of [v-g*t]_+ on [P,a], using its exact support.
            stop = min(a, v / g)
            expected = 0. if stop <= P else (stop - P) * (v - g * (P + stop) / 2)
            self.assertAlmostEqual(d.mu(v, a, P, g), expected, places=13)
        self.assertEqual(d.mu(8, P, P, g), 0)
        self.assertEqual(d.mu(8, a, P, 0), 8 * (a - P))

    def test_nonzero_count_roots(self):
        for c in (0, 1, 10, 100):
            m = d.poisson_chernoff_root(c, 28)
            j = m if c == 0 else m - c - c * math.log(m / c)
            self.assertAlmostEqual(j, 28, places=11)
            self.assertGreater(m, c)

    def test_upper_inverse_clipping_and_finite_actions(self):
        P, g, H, B = .3, .001, 28., 1.
        self.assertEqual(d.t36_upper(0, H, P, P, g, B), B)
        self.assertEqual(d.t36_upper(0, H, 1, P, g, B), B)
        floor = g * P + math.sqrt(2 * g * H)
        for c in (0, 1, 10):
            for a in (1., 60., 300., 3600.):
                u = d.t36_upper(c, H, a, P, g, B)
                self.assertGreaterEqual(u + 1e-14, min(B, floor))
                if u < B:
                    self.assertAlmostEqual(d.mu(u, a, P, g), d.poisson_chernoff_root(c, H), places=11)
        self.assertAlmostEqual(d.t36_upper(0, H, 3600, P, g, B), floor)
        self.assertGreater(d.t36_upper(1, H, 3600, P, g, B), floor)
        self.assertAlmostEqual(d.t36_upper(0, H, 3600, P, 0, B), H / (3600 - P))
        self.assertGreater(d.t36_upper(0, H, 300, P, 0, B), 0)


class DataTests(unittest.TestCase):
    def test_log_pairs_no_gap_version_invalid_or_zero_bridging(self):
        rows = [(0, "a", .1, True), (300, "a", 1., True),
                (600, "b", 2., True), (1200, "b", 3., True),
                (1500, "b", math.nan, False), (1800, "b", 4., True),
                (2100, "b", 0., True), (2400, "b", 5., True),
                (2700, "b", 10., True)]
        out = d.relative_growth(rows, 10, [.05], str)
        audit = out["pair_audit"]
        self.assertEqual(audit["valid_positive_same_version_pairs"], 2)
        self.assertEqual(audit["excluded_gap"], 1)
        self.assertEqual(audit["excluded_version"], 1)
        self.assertEqual(audit["excluded_mask"], 2)
        self.assertEqual(audit["excluded_nonpositive"], 2)
        self.assertEqual(sum(v for k, v in audit.items() if k != "total_pairs"), audit["total_pairs"])
        item = out["thresholds"][0]
        self.assertEqual(item["counts"]["up_crossing"], 1)
        self.assertEqual(len(item["crossings"]), 1)
        self.assertEqual(item["maximum"]["from_utc"], "2400")
        self.assertAlmostEqual(item["maximum"]["log_growth_s_1"], math.log(2) / 300)
        self.assertEqual(item["excluded_threshold_maximum"]["from_utc"], "0")

    def test_threshold_equality_and_no_eligible_pairs(self):
        out = d.relative_growth([(0, "a", 1., True), (300, "a", 1., True)], 1., [1., 2.], str)
        self.assertEqual(out["thresholds"][0]["maximum"]["log_growth_s_1"], 0)
        self.assertIsNone(out["thresholds"][1]["maximum"])

    def test_shielding_zero_denominator_and_same_time_pairing(self):
        source = [{"timestamp_utc": "0"}, {"timestamp_utc": "300"}]
        frames = {}
        for direction in ("E", "W", "central"):
            source[0].update({f"d1_lambda_{direction}_s-1": "1", f"d3_lambda_{direction}_s-1": "0"})
            source[1].update({f"d1_lambda_{direction}_s-1": "3", f"d3_lambda_{direction}_s-1": "2"})
            frames[("GOES19_1mm", direction, "published_valid")] = ([(0, "a", 1., True), (300, "a", 3., True)], None)
        module = SimpleNamespace(source_tables=lambda _: {"proton_rate_5min.csv": source}, stamp=int)
        result = d.shielding_check(module, {"policies": ["published_valid"]}, frames)
        self.assertEqual(result[0]["zero_3mm_rows_ratio_undefined"], 1)
        self.assertEqual(result[0]["minimum_ratio_1mm_to_3mm"], 1.5)
        source[1]["timestamp_utc"] = "600"
        with self.assertRaises(ValueError):
            d.shielding_check(module, {"policies": ["published_valid"]}, frames)


class RarityTests(unittest.TestCase):
    def test_poisson_tail_independent_finite_sum(self):
        with localcontext() as ctx:
            ctx.prec = 60
            for mean in (1, 16, 64, 128):
                k = mean
                term, cdf = (-Decimal(mean)).exp(), (-Decimal(mean)).exp()
                for j in range(1, k + 1):
                    term *= Decimal(mean) / j
                    cdf += term
                self.assertLess(abs(d.poisson_sf(k, mean) - (1 - cdf)), Decimal("1e-55"))

    def test_quantile_minimality_and_zero_mean(self):
        self.assertEqual(d.poisson_k(0, .00025)["K"], 0)
        for mean in (1, 16, 64, 128):
            for delta in ("0.00001", "0.0001", "0.00025"):
                q = d.poisson_k(mean, delta)
                self.assertLessEqual(Decimal(q["tail_at_K"]), Decimal(delta))
                self.assertGreater(Decimal(q["tail_at_K_minus_1"]), Decimal(delta))
        self.assertEqual(d.poisson_k(1, .00025)["K"], 6)


if __name__ == "__main__":
    unittest.main()

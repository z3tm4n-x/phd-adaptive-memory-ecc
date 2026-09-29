#!/usr/bin/env python3
"""Small deterministic checks for T57; no radiation/R0 campaign or optimizer.

Run: python3 -B theory/check_t57_uniform_count.py
Fraction is used for phase/packing identities. Elementary floating functions
are used only for one regression check, not as a certified implementation
of statistical tests, Poisson quantiles, or the controller.
"""

from fractions import Fraction as F
from itertools import combinations
import math
import unittest


def phases(words, ticks, tick=F(1), latch=F(0), fence=F(0)):
    starts = [F(w * ticks // words) * tick for w in range(words)]
    return starts, [t + latch for t in starts], [t + fence for t in starts]


def lower_weight(t, reads, qwords):
    return max(F(0), 1 - sum(q for r, q in zip(reads, qwords) if r <= t))


def residual_weight(t, fences, qwords):
    return min(F(1), sum(q for f, q in zip(fences, qwords) if f <= t))


def proxy(a, words, q, tick):
    spacing = a / words
    A, beta = 1 - q * (1 + tick / spacing), q / spacing
    stop = min(a, max(F(0), A / beta))
    exposure = A * stop - beta * stop * stop / 2
    return A, beta, stop, exposure


def integrate_steps(a, points, fun):
    cuts = sorted({F(0), a} | {p for p in points if 0 < p < a})
    return sum((v - u) * fun((u + v) / 2)
               for u, v in zip(cuts, cuts[1:]))


def busy_window(starts, length, left, h):
    return sum(max(F(0), min(t + length, left + h) - max(t, left))
               for t in starts)


def packing(length, gap, h):
    k = h // gap
    return k * length + min(length, h - k * gap)


def token_trace(words, periods, tick, latch, fence, events, initial=None):
    """Exact auxiliary token trace; events are (time, set of touched words)."""
    tokens = list(initial or [0] * words)
    timeline, cycles, start = [], [], F(0)
    for i, ticks in enumerate(periods):
        a = ticks * tick
        _, reads, fences = phases(words, ticks, tick, latch, fence)
        reads, fences = [start + r for r in reads], [start + f for f in fences]
        cycles.append((start, start + a, reads, fences))
        timeline.extend((r, 1, i, w) for w, r in enumerate(reads))
        timeline.extend((f, 2, i, w) for w, f in enumerate(fences))
        timeline.append((start + a, 3, i, -1))
        start += a
    timeline.extend((t, 0, -1, marks) for t, marks in events)
    counts, tails = [0] * len(cycles), [0] * len(cycles)
    for t, kind, i, arg in sorted(timeline, key=lambda row: (row[0], row[1])):
        if kind == 0:
            for w in arg:
                tokens[w] += 1
        elif kind == 1:
            counts[i] += tokens[arg]
        elif kind == 2:
            tokens[arg] = 0
        else:
            tails[i] = sum(tokens)
    visible, residual = [], []
    for start, end, reads, fences in cycles:
        fresh = [(t, z) for t, z in events if start <= t < end]
        visible.append(sum(any(t < reads[w] for w in z) for t, z in fresh))
        residual.append(sum(any(fences[w] < t for w in z) for t, z in fresh))
    return counts, tails, visible, residual


class T57Checks(unittest.TestCase):
    def test_mark_weight_without_word_independence(self):
        marks = [set(z) for k in (1, 2, 3) for z in combinations(range(3), k)]
        probabilities = [F(1, 7)] * 7
        qwords = [sum(p for p, z in zip(probabilities, marks) if w in z)
                  for w in range(3)]
        for k in range(4):
            remaining = set(range(k, 3))
            true = sum(p for p, z in zip(probabilities, marks) if z & remaining)
            lower = max(F(0), 1 - sum(qwords[:k]))
            self.assertLessEqual(lower, true)
        self.assertEqual(qwords, [F(4, 7)] * 3)

    def test_uniform_integral_uses_reads_not_busy_sum(self):
        for words in (2, 3, 7):
            a, latch = F(21), F(1, 10)
            reads = [F(w, words) * a + latch for w in range(words)]
            q = [F(1, words)] * words
            actual = integrate_steps(a, reads, lambda t: lower_weight(t, reads, q))
            self.assertEqual(actual, a * F(words - 1, 2 * words) + latch)
            self.assertGreater(actual, 0)  # Old idle test at P=a is zero.

    def test_quantized_affine_weights_bound_exact_phases(self):
        for words in range(2, 9):
            for ticks in (8 * words, 8 * words + 3):
                a = F(ticks)
                _, reads, fences = phases(words, ticks, latch=F(1), fence=F(2))
                qwords = [F(1, words)] * words
                A, beta, _, E = proxy(a, words, F(1, words), F(1))
                cuts = sorted({F(0), a} | set(reads) | set(fences))
                points = cuts + [(x + y) / 2 for x, y in zip(cuts, cuts[1:])]
                for u in points:
                    p = max(F(0), A - beta * u)
                    self.assertLessEqual(p, lower_weight(u, reads, qwords))
                    self.assertGreaterEqual(1 - p, residual_weight(u, fences, qwords))
                exact = integrate_steps(a, reads, lambda t: lower_weight(t, reads, qwords))
                self.assertLessEqual(E, exact)

    def test_residual_phase_integral(self):
        words, a = 4, F(20)
        _, _, fences = phases(words, 20, fence=F(2))
        qwords = [F(1, words)] * words
        actual = integrate_steps(a, fences, lambda t: residual_weight(t, fences, qwords))
        self.assertEqual(actual, sum(a - f for f in fences) / words)

    def test_token_domination_on_small_transition_trace(self):
        events = [(F(3, 10), {0, 2}), (F(7, 2), {1}),
                  (F(13, 2), {0}), (F(29, 3), {1, 2}),
                  (F(15), {0, 1}), (F(19), {2})]
        counts, tails, visible, rem = token_trace(
            3, [9, 12], F(1), F(1, 10), F(1, 5), events, [1, 0, 1])
        for C, V, K, R in zip(counts, visible, tails, rem):
            self.assertGreaterEqual(C, V)
            self.assertLessEqual(K, 2 * R)

    def test_pending_arrival_can_be_erased_without_count(self):
        values = token_trace(2, [2], F(1), F(1, 10), F(1, 5),
                             [(F(23, 20), {1})])
        self.assertEqual(values, ([0], [0], [0], [0]))

    def test_one_parent_can_appear_in_two_cycle_counts(self):
        counts, _, visible, _ = token_trace(
            2, [2, 2], F(1), F(1, 10), F(1, 5), [(F(1, 2), {0, 1})])
        self.assertEqual(counts, [1, 1])
        self.assertEqual(visible, [1, 0])

    def test_xor_cancellation_requires_coupling_break(self):
        events = [(F(1, 2), {1}), (F(3, 4), {1})]
        counts, _, visible, _ = token_trace(
            2, [2], F(1), F(1, 10), F(1, 5), events)
        self.assertEqual(counts, [2])
        self.assertEqual(visible, [2])
        physical_bit = 0 ^ 1 ^ 1
        self.assertEqual(physical_bit, 0)  # Physical corrected count is not Pois.

    def test_period_change_has_old_period_word_age(self):
        words, tick = 4, F(1, 10)
        _, old, _ = phases(words, 80, tick)
        _, new, _ = phases(words, 160, tick)
        word_age = F(8) + new[3] - old[3]
        self.assertEqual(word_age, F(14))
        self.assertNotEqual(word_age, F(16))

    def test_minimum_gap_includes_cycle_boundaries(self):
        words, tick, periods = 5, F(1, 10), [40, 83, 41, 120, 40]
        g = min(F(M // words) * tick for M in periods)
        offset, all_starts = F(0), []
        for M in periods:
            starts, _, _ = phases(words, M, tick)
            all_starts.extend(offset + s for s in starts)
            offset += M * tick
        self.assertTrue(all(y - x >= g for x, y in zip(all_starts, all_starts[1:])))

    def test_nonperiodic_packing_bound_at_all_extreme_windows(self):
        gap, length = F(2), F(1)
        for starts in combinations(map(F, range(9)), 3):
            if any(y - x < gap for x, y in zip(starts, starts[1:])):
                continue
            for h in (F(1, 2), F(1), F(3), F(7, 2), F(5)):
                endpoints = [t + v for t in starts for v in (F(0), length)]
                lefts = endpoints + [t - h for t in endpoints]
                for left in lefts:
                    self.assertLessEqual(busy_window(starts, length, left, h),
                                         packing(length, gap, h))

    def test_service_curve_supports_fifo_completion_bound(self):
        b, gap, sigma, app_rate = F(3), F(10), F(5), F(1, 2)
        R = 1 - b / gap
        delay = b + sigma / R
        for t in (F(k, 3) for k in range(181)):
            self.assertGreaterEqual(t - packing(b, gap, t), max(F(0), R * (t - b)))
            self.assertLessEqual(sigma + app_rate * t, R * (t + delay - b))

    def test_exposure_budget_is_additive_on_adaptive_partition(self):
        # A deterministic realized partition suffices to check pathwise identity.
        cuts = [F(0), F(2), F(7), F(9), F(14)]
        integral = lambda a, b: (b * b - a * a) / 2
        summed = sum(integral(a, b) for a, b in zip(cuts, cuts[1:]))
        self.assertEqual(summed, integral(F(0), F(14)))

    def test_affine_exposure_and_remainder_monotonicity(self):
        W, tick, a_b = 8, F(1), F(128)
        _, _, _, E_b = proxy(a_b, W, F(1, W), tick)
        for multiplier in (1, 2, 3, 7):
            a = multiplier * a_b
            _, _, _, E = proxy(a, W, F(1, W), tick)
            self.assertGreaterEqual(E, E_b)
            self.assertGreaterEqual(E / a, E_b / a_b)
        _, _, _, E_2 = proxy(2 * a_b, W, F(1, W), tick)
        self.assertLessEqual((2 * a_b - E_2) / 2, a_b - E_b)

    def test_nonempty_symbolic_construction_regression(self):
        # Dimensionless witness of E.2; not R0 inputs or physical numbers.
        W, N, nu, alpha_total, zeta_total = 2**24, 8, 256, 0.001, 0.001
        a_b, tick = F(16 * W), F(1)
        _, _, _, E_b = proxy(a_b, W, F(1, W), tick)
        H = math.log(N / alpha_total)
        self.assertGreater(nu, 16 * H)
        self.assertGreaterEqual(E_b, a_b / 4)
        B = nu / float(a_b)
        tail_mean = B * float(a_b - E_b)
        K = math.ceil(math.expm1(1) * tail_mean + math.log(N / zeta_total))
        omega = (K + 0.75 * nu) / W
        gamma = omega * nu
        self.assertLess(alpha_total + zeta_total + gamma, 0.1)
        self.assertLess((K + nu / 2) / W, omega)
        self.assertGreater((K + nu) / W, omega)
        U = H / float(E_b)
        self.assertLess(U, B / 4)
        self.assertLess((K + U * float(a_b)) / W, omega)
        _, _, _, E_2 = proxy(2 * a_b, W, F(1, W), tick)
        self.assertLess(U * float(2 * a_b - E_2), tail_mean)

    def test_positive_growth_lower_integral_against_piecewise_formula(self):
        # Below threshold L_h=l(kappa-rho*h)+: exact polynomial integration.
        l, v, rho, a, A, beta = F(2), F(1), F(1, 10), F(4), F(3, 4), F(1, 4)
        stop = min(a, A / beta)
        low, high = a - stop, a
        kappa = v / l
        self.assertGreaterEqual(kappa - rho * high, 0)
        I0 = l * (kappa * (high - low) - rho * (high**2 - low**2) / 2)
        I1 = l * (kappa * (high**2 - low**2) / 2 - rho * (high**3 - low**3) / 3)
        converted = (A - beta * a) * I0 + beta * I1
        p0, p1, p2 = A * (v - l * rho * a), A * l * rho - beta * (v - l * rho * a), -beta * l * rho
        direct = p0 * stop + p1 * stop**2 / 2 + p2 * stop**3 / 3
        self.assertEqual(converted, direct)
        self.assertGreater(converted, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

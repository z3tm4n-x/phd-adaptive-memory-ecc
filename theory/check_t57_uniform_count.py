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
import t57_uniform_budget as budget


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




class T57StrengtheningChecks(unittest.TestCase):
    """Addressed regression; all acceptance comparisons are rational."""

    def test_original_snapshot_and_same_per_bit_scaling(self):
        data = budget.snapshot()
        self.assertEqual(data["source_sha"], "ff705de22012fb8e6481436483150a1472879b0a")
        self.assertEqual(len(data["grid"]["W"]), 6)
        for W in data["grid"]["W"]:
            p = budget.model(W)
            self.assertEqual(p.F0/p.W, budget.model().F0/budget.model().W)
            self.assertEqual(p.S2/(39*W)**2,
                             F(data["history"]["S2_per_bit_s_inverse"]))

    def test_old_integer_barrier_all_original_sizes(self):
        for W in budget.snapshot()["grid"]["W"]:
            d = budget.old_barriers(budget.model(W))
            self.assertTrue(d["no_positive_integer_cap"])
            self.assertGreater(d["beta_T"], 1)
            self.assertGreater(d["exact_quantile_union_lower"], F(1, 4))
            self.assertGreater(d["F0q"], F("0.32301607221069"))
            self.assertLess(d["F0q"], F("0.32301607221070"))

    def test_old_pair_barrier_original_array(self):
        d = budget.old_barriers(budget.model(1935832, 256000000))
        self.assertLess(d["pair_ab_upper"], F("0.186688384"))
        self.assertGreater(d["pair_ab_upper"], F("0.186688383"))
        self.assertEqual(d["full_busy_pass"], F("0.29491190625"))
        self.assertLess(d["pair_ab_upper"], d["full_busy_pass"])

    def test_exp_enclosure_against_independent_decimal(self):
        from decimal import Decimal, localcontext
        with localcontext() as ctx:
            ctx.prec = 100
            for x in map(F, ("0", "0.001", "0.25", "1", "12", "15", "80", "200")):
                lo, hi = budget.exp_neg(x)
                reference = (-Decimal(x.numerator)/Decimal(x.denominator)).exp()
                self.assertLessEqual(Decimal(lo.numerator)/Decimal(lo.denominator), reference)
                self.assertGreaterEqual(Decimal(hi.numerator)/Decimal(hi.denominator), reference)

    def test_affine_cap_matches_endpoint_infimum(self):
        for b in (F(0), F(1), F(3)):
            for u, v in ((F(1), F(0)), (F(1), F(10)), (F(5), F(1))):
                previous = None
                for n in range(1, 50):
                    x = F(n, 10)
                    cap = budget.price_cap(x, b, F(1, 3), u, v)
                    if previous is not None:
                        self.assertLessEqual(cap, previous)
                    previous = cap
                    for k in range(1, 21):
                        z = x*k/20
                        quotient = 6*(u+v*max(F(0), z-b))/(z*z)
                        self.assertLessEqual(cap, quotient)

    def test_prospective_cells_cover_word_lifetime_and_bound_transition(self):
        W, tick, fence = 7, F(1, 10), F(1, 5)
        periods = [56, 113, 57, 159, 56]
        t, byword = F(0), [[F(0)] for _ in range(W)]
        for M in periods:
            a = M*tick
            _, _, fs = phases(W, M, tick, fence=fence)
            for w, f in enumerate(fs):
                byword[w].append(t+f)
            t += a
        for w in range(W):
            seq = byword[w]+[t]
            self.assertEqual(sum(v-u for u, v in zip(seq, seq[1:])), t)
            for i in range(len(periods)-1):
                length = byword[w][i+2]-byword[w][i+1]
                self.assertLessEqual(length, max(periods[i:i+2])*tick+tick)

    def test_squared_exposure_cost_uses_same_partition(self):
        # Piecewise positive intensity entirely within one certified interval.
        lam = [F(1, 10), F(1, 2), F(1, 5)]
        width = [F(1, 10), F(1, 5), F(1, 10)]
        b, u, v, chi = F(1, 10), F(1, 20), F(1, 2), F(1, 3)
        length = sum(width)
        cap = budget.price_cap(max(lam), b, chi, u, v)
        self.assertLessEqual(length, cap)
        mean = sum(x*h for x, h in zip(lam, width))
        price = sum((u+v*max(F(0), x-b))*h for x, h in zip(lam, width))
        self.assertLessEqual(chi*mean*mean/2, price)

    def test_positive_growth_threshold_and_saturation(self):
        self.assertEqual(budget.psi_upper(F(0), F(2), F(10), F(1), F(1, 4)), F(1, 2))
        exponential = budget.psi_upper(F(1, 2), F(4), F(10), F(1), F(1, 4))
        lo, _ = budget.exp_neg(F(1, 2))
        self.assertEqual(exponential, 1/lo)
        self.assertEqual(budget.psi_upper(F(1), F(100), F(2), F(1), F(1)), F(2))
        self.assertEqual(budget.psi_upper(F(1), F(100), F(2), F(1), F(0)), F(1))

    def test_integer_choice_agrees_with_small_complete_domain(self):
        p = budget.Model(3, 100000, F(10), F(1, 2), F(1, 10), F(1),
                         eps=F(3, 10), gamma=F(1, 5), tick=F(1, 100))
        ab, cap, rho, l = F(1, 10), F(2), F(1, 20), F(1, 10)
        for x in (F(0), p.b, p.B):
            answer = budget.choose_tick(p, x, ab, ab, cap, l, rho)
            safe = [M for M in range(10, 201) if budget.action_admitted(
                p, x, ab, M*p.tick, ab, cap, l, rho)]
            self.assertEqual(answer, max(safe))
            nxt = answer*p.tick
            future_x = budget.psi_upper(x, ab, p.B, l, rho)
            self.assertTrue(budget.action_admitted(p, future_x, nxt, ab, ab, cap, l, rho))

    def test_scalar_exposure_lower_on_entire_action_range(self):
        p = budget.model()
        ab, ac, block = budget.design(p)
        kappa = (1-F(1, p.W)-p.tick/ab)**2/2
        for a in (ab, (ab+ac)/2, ac):
            _, _, _, E = proxy(a, p.W, F(1, p.W), p.tick)
            self.assertGreaterEqual(E, kappa*a)
        self.assertGreater(block, 6*ac)

    def test_predictable_whole_cycles_leave_only_two_boundary_fragments(self):
        acap, L = F(7), F(50)
        periods = [F(3), F(7), F(5), F(4), F(6)]*30
        cuts = [F(0)]
        for a in periods:
            cuts.append(cuts[-1]+a)
        for j in range(10):
            included = [(u,v) for u,v in zip(cuts,cuts[1:]) if j*L<=u and v<=(j+1)*L]
            self.assertGreaterEqual(sum(v-u for u,v in included), L-2*acap)

    def test_each_parent_contributes_at_most_m_counts_across_cycles(self):
        events = [(F(7, 2), {0, 1, 2}), (F(5), {0, 2}), (F(10), {1})]
        counts, _, _, _ = token_trace(3, [9, 12, 15], F(1), F(1,10), F(1,5), events)
        self.assertLessEqual(sum(counts), sum(len(mark) for _, mark in events))

    def test_batch_alpha_and_poisson_tail_are_certified(self):
        p = budget.model()
        d = budget.count_and_tax(p)
        self.assertLessEqual(d["epochs"]*budget.exp_neg(F(d["H"]))[1], p.alpha)
        z = F(1,4)
        exp_upper = 1/budget.exp_neg(z)[0]
        self.assertGreaterEqual(z*d["count_threshold"]-d["mean_count_upper"]*(exp_upper-1), 12)
        self.assertLess(d["tail_upper"], F("0.000006145"))

    def test_reference_launch_usefulness_and_resource(self):
        p = budget.model()
        d = budget.count_and_tax(p)
        self.assertTrue(budget.length_admitted(d["ab"]+p.tick,p.B,p))
        self.assertTrue(d["informative_and_long_action"])
        resource = budget.resource(p,d["ab"])
        self.assertTrue(resource["ok"])
        self.assertEqual(resource["peak"], F("0.020109375"))
        self.assertLess(resource["delay"], F("0.000000812"))
        self.assertEqual(resource["decision_slack"], F("0.000029900625"))

    def test_reference_tax_compares_upper_to_fixed_lower(self):
        p = budget.model()
        d = budget.count_and_tax(p)
        self.assertEqual(d["fixed_tick"], 2018037184)
        self.assertLess(d["nominal_tax_upper"], F("0.00330592"))
        self.assertGreater(d["fixed_tax_lower"], F("0.007915809"))
        self.assertGreater(d["reduction_vs_presented_fixed_lower"], F("0.5823"))
        self.assertGreater(p.b*p.T, 70000)  # Not a whole-mission zero-event argument.

    def test_all_four_accepted_fixed_candidates_are_preserved(self):
        accepted = [r for r in budget.snapshot()["fixed_grid"] if r["selected_tick"] is not None]
        self.assertEqual(len(accepted), 4)
        for row in accepted:
            p = budget.model(row["W"], row["R_eff_bit_s"])
            self.assertEqual(budget.count_and_tax(p)["fixed_tick"], row["selected_tick"])

    def test_reference_positive_growth_domain_and_failure(self):
        p = budget.model()
        lo, hi = budget.rho_threshold(p)
        self.assertGreaterEqual(lo, F("0.0000042468684"))
        self.assertLessEqual(hi, F("0.0000042468687"))
        self.assertTrue(budget.count_and_tax(p,lo)["informative_and_long_action"])
        self.assertFalse(budget.count_and_tax(p,hi)["informative_and_long_action"])
        self.assertFalse(budget.count_and_tax(p,F("0.0009"))["informative_and_long_action"])
        self.assertIsNone(budget.count_and_tax(p,F("0.0009"))["nominal_tax_upper"])
        self.assertFalse(budget.count_and_tax(p,overcount=10000)["informative_and_long_action"])

    def test_A_and_B_witnesses_use_original_sizes_and_positive_growth(self):
        from dataclasses import replace
        for W, speed in ((262144,64000000),(262144,256000000),(524288,256000000)):
            p = budget.model(W,speed)
            d = budget.count_and_tax(p)
            self.assertTrue(d["informative_and_long_action"])
            self.assertTrue(budget.resource(p,d["ab"])["ok"])
            self.assertLess(d["nominal_tax_upper"], F("0.01"))
        for W,speed in ((262144,16000000),(524288,64000000),(1048576,256000000)):
            p = replace(budget.model(W,speed),theta=F("0.7"))
            d = budget.count_and_tax(p,rho=F("0.0000005"),policy=budget.alternate_design(p))
            self.assertTrue(d["informative_and_long_action"])
            self.assertTrue(budget.length_admitted(d["ab"]+p.tick,p.B,p))
            self.assertTrue(budget.resource(p,d["ab"],F("0.25"))["ok"])
            self.assertLess(d["nominal_tax_upper"],F("0.01"))

    def test_affine_launch_ceiling_and_peak_barrier(self):
        p = budget.model(1935832,256000000)
        self.assertGreater(budget.launch_ceiling(p),F("2.3964199183"))
        self.assertLess(budget.launch_ceiling(p),F("2.3964199184"))
        amin = budget.first_resource_tick(p,F("0.05"))*p.tick
        self.assertEqual(amin,F("5.9042876"))
        self.assertGreater(amin,budget.launch_ceiling(p))
        for peak in (F("0.25"),F("0.5")):
            self.assertLess(budget.first_resource_tick(p,peak)*p.tick+p.tick,
                            budget.launch_ceiling(p))

    def test_nominal_lower_excludes_only_price_density_layer(self):
        p = budget.model(1935832,256000000)
        lower = budget.count_and_tax(p)["price_layer_nominal_tax_lower"]
        self.assertGreater(lower,F("0.01839329883"))
        for peak in (F("0.05"),F("0.25"),F("0.5")):
            self.assertFalse(budget.price_tradeoff(p,peak,F("0.01"))["possible"])
        self.assertFalse(budget.price_tradeoff(budget.model(1048576,256000000),
                                               F("0.05"),F("0.01"))["possible"])
        self.assertTrue(budget.price_tradeoff(budget.model(1048576,256000000),
                                              F("0.25"),F("0.01"))["possible"])

    def test_all_original_1458_resource_tuples(self):
        rows = budget.grid_diagnostic()
        self.assertEqual(len(rows),1458)
        keys = {(r["W"],r["rate"],r["tax"],r["peak"],r["h"],r["delay"]) for r in rows}
        self.assertEqual(len(keys),1458)
        self.assertEqual(sum(r["A"] for r in rows),135)
        self.assertEqual(sum(r["B"] for r in rows),237)
        self.assertEqual(sum(r["layer_not_excluded"] for r in rows),237)
        self.assertTrue(all(not (r["A"] or r["B"]) or r["layer_not_excluded"] for r in rows))



class T57ReviewCorrectionChecks(unittest.TestCase):
    def setUp(self):
        self.p = budget.model()
        self.d = budget.count_and_tax(self.p)
        self.c = self.d["numerical_certificate"]

    def test_zero_lower_channel_quota_preserves_price(self):
        from dataclasses import replace
        zero = budget.count_and_tax(replace(self.p, delta_o_minus=F(0)))
        self.assertEqual(zero["nominal_tax_upper"], self.d["nominal_tax_upper"])
        self.assertEqual(zero["quiet_coupling_upper"],
                         self.p.chi*(self.d["acap"]+self.p.tick)*self.p.b**2*self.p.T/2)

    def test_whole_horizon_undercount_paid_once_not_per_block(self):
        from dataclasses import replace
        q = budget.count_and_tax(replace(self.p, delta_o_minus=F("0.02"), eps=F("0.03")))
        self.assertEqual(q["quiet_coupling_upper"]-self.d["quiet_coupling_upper"], F("0.02"))
        expected = F("0.02")*(self.d["fast_density"]-self.d["slow_density"])
        self.assertEqual(q["nominal_tax_upper"]-self.d["nominal_tax_upper"], expected)
        self.assertGreater(q["nominal_tax_upper"], F("0.0036414715179"))
        self.assertLess(q["nominal_tax_upper"], F("0.0036414715180"))
        self.assertTrue(q["conditional_price_valid"])  # alpha+gamma+delta == epsilon.

    def test_undercount_requires_risk_allocation_but_not_double_payment(self):
        from dataclasses import replace
        bad_budget = budget.count_and_tax(replace(self.p, delta_o_minus=F("0.02")))
        self.assertIsNone(bad_budget["nominal_tax_upper"])
        corrected = replace(self.p, delta_o_minus=F("0.02"), eps=F("0.03"))
        self.assertEqual(corrected.alpha+corrected.gamma+corrected.delta_o_minus, corrected.eps)
        self.assertIsNotNone(budget.count_and_tax(corrected)["nominal_tax_upper"])

    def test_probability_is_capped_at_one(self):
        from dataclasses import replace
        q = budget.count_and_tax(replace(self.p, delta_o_minus=F("0.999")))
        self.assertEqual(q["quiet_coupling_upper"], 1)
        self.assertEqual(q["bad_time_fraction"], 1)
        self.assertEqual(q["candidate_tax_expression"],
                         q["fast_density"]+4*self.p.c*(q["epochs"]+1)/self.p.T)
        with self.assertRaises(ValueError):
            budget.count_and_tax(replace(self.p, delta_o_minus=F("1.01")))

    def test_review_counterexample_is_covered(self):
        from dataclasses import replace
        p, d = self.p, self.d
        mu_pre = p.b*d["kappa"]*(d["block"]/2-2*d["acap"])
        branch_lower = F("0.02")*(1-budget.exp_neg(mu_pre)[1]-d["quiet_coupling_upper"])
        DB = budget.price_cap(p.B,p.b,p.chi,p.u,p.v)
        cost_lower = (p.W*p.c/d["acap"]-p.W*p.c/p.T
                      +branch_lower*p.W*p.c*(1/DB-1/d["acap"]))
        fixed = budget.count_and_tax(replace(p, delta_o_minus=F("0.02"), eps=F("0.03")))
        self.assertGreater(branch_lower, F("0.01992315295"))
        self.assertGreater(cost_lower, F("0.003436430933"))
        self.assertGreater(cost_lower, d["nominal_tax_upper"])
        self.assertLess(cost_lower, fixed["nominal_tax_upper"])

    def test_fixed_term_log_enclosure_independently(self):
        from decimal import Decimal, localcontext
        with localcontext() as ctx:
            ctx.prec = 100
            for x in map(F, ("0.001","0.9","1","1.01","2","7.5","1000")):
                lo, hi = budget.log_interval(x, 10)
                truth = (Decimal(x.numerator)/Decimal(x.denominator)).ln()
                self.assertLessEqual(Decimal(lo.numerator)/Decimal(lo.denominator), truth)
                self.assertGreaterEqual(Decimal(hi.numerator)/Decimal(hi.denominator), truth)
                self.assertLessEqual(hi-lo, (abs(budget.log2_floor(x))+1)*budget.log_tail(10))

    def test_dyadic_exposure_error_and_fixed_memory(self):
        p, c = self.p, self.c
        exact_total = down_total = F(0)
        for a in [c["ab"],c["acap"],(c["ab"]+c["acap"])/2]*7:
            exact_total += a*(1-F(1,p.W)-p.tick/a)**2/2
            down_total = budget.accumulate_exposure(down_total,a,p,c["exposure_bits"])
        self.assertLessEqual(down_total,exact_total)
        self.assertLess(exact_total-down_total,21*F(1,1<<c["exposure_bits"]))
        self.assertEqual((down_total*(1<<c["exposure_bits"])).denominator,1)

    def test_reference_finite_certificate_has_proved_precision_and_margin(self):
        c = self.c
        self.assertTrue(c["success"])
        self.assertEqual(c["log_terms"],10)
        self.assertEqual(c["rational_operation_bound"],500)
        self.assertGreater(c["normalized_log_rational_bit_bound"],0)
        self.assertLess(c["relative_input_error"],F("2.277e-13"))
        self.assertLess(c["total_H_error_bound"],2*c["eta"])
        self.assertLess(c["exposure_error"],F("1.137e-8"))
        self.assertLess(c["inverse_error_bound"],F("8.674e-19"))
        self.assertGreater(c["margin"],F("2.38432829"))
        self.assertEqual(c["extra_reserve_fraction"],0)
        self.assertTrue(budget.numerical_witness(self.p,self.d)["success"])

    def test_all_good_extremes_install_and_accept_in_finite_arithmetic(self):
        p, c = self.p, self.c
        _, initial = budget.H_interval(p.B,c["l"],c["log_terms"])
        E_min = budget.dyadic(c["exposure_min"],c["exposure_bits"],True)
        for start in (F(0), c["block"], 1000*c["block"]):
            issue = start+c["block"]+c["acap"]
            for count in (F(0),F(1),c["count_max"]):
                for E_down in (E_min,budget.dyadic(c["block"],c["exposure_bits"])):
                    update = budget.install_block_bound(c,count,E_down,start,issue,initial)
                    self.assertTrue(update["installed"])
                    self.assertLessEqual(update["intercept"],initial)
                    for current in (c["ab"],c["acap"]):
                        t = start+2*c["block"]+c["acap"]
                        action = budget.guarded_action(p,c,update["intercept"],t,current)
                        self.assertTrue(action["long_accepted"])
                        self.assertEqual(action["period"],c["acap"])

    def test_safe_skip_failure_and_late_update_do_not_claim_good_block_price(self):
        p, c = self.p, self.c
        _, initial = budget.H_interval(p.B,c["l"],c["log_terms"])
        E_down = budget.dyadic(c["exposure_min"],c["exposure_bits"],True)
        args = (c,c["count_max"],E_down,F(0),c["block"],initial)
        for flags in (dict(skip=True),dict(numeric_failure=True),dict(valid=False)):
            update = budget.install_block_bound(*args,**flags)
            self.assertFalse(update["installed"])
            self.assertEqual(update["intercept"],initial)
            action = budget.guarded_action(p,c,initial,c["block"],c["ab"])
            self.assertEqual(action["period"],c["ab"])
        late = budget.install_block_bound(c,c["count_max"],E_down,F(0),
                                          c["block"]+c["acap"]+p.tick,initial)
        self.assertFalse(late["installed"])
        no_contract = budget.count_and_tax(p,numerical_contract=False)
        self.assertIsNone(no_contract["nominal_tax_upper"])
        reserve_price_lower = p.W*p.c/c["ab"]-p.W*p.c/p.T
        self.assertGreater(reserve_price_lower,F("0.01996799898"))
        self.assertGreater(reserve_price_lower,self.d["nominal_tax_upper"])
        self.assertGreater(no_contract["hard_mask_tax_upper"],reserve_price_lower)

    def test_numerical_precision_failure_has_no_strong_price(self):
        for precision in (dict(anchor_bits=4),dict(exposure_bits=0)):
            d = budget.count_and_tax(self.p,precision=precision)
            self.assertFalse(d["numerical_certificate"]["success"])
            self.assertIsNone(d["nominal_tax_upper"])
            self.assertGreater(d["hard_mask_tax_upper"],F("0.0199"))

    def test_guard_boundary_is_exact_not_float_tolerance(self):
        p,c = self.p,self.c
        time,current = c["block"],c["ab"]
        boundary = c["S_guard"]-c["rho"]*(time+current+c["acap"]+c["ab"])
        at = budget.guarded_action(p,c,boundary,time,current)
        above = budget.guarded_action(p,c,boundary+F(1,1<<80),time,current)
        self.assertTrue(at["long_accepted"])
        self.assertFalse(above["long_accepted"])
        self.assertEqual(above["period"],c["ab"])

    def test_zero_length_margin_is_not_a_positive_numerical_certificate(self):
        # An isolated exact-boundary unit check, not a changed T58 input row.
        from dataclasses import replace
        p,c = self.p,self.c
        boundary_model = replace(p,tick=c["D_guard"]-c["acap"])
        edge = budget.finite_price_certificate(
            boundary_model,c["ab"],c["acap"],c["block"],c["H"],c["count_max"],
            self.d["exposure_lower"],c["l"],c["rho"],c["eta"])
        self.assertEqual(edge["margin"],0)
        self.assertFalse(edge["success"])

    def test_reserve_promise_survives_numerical_failure_after_long_action(self):
        p,c = self.p,self.c
        _, initial = budget.H_interval(p.B,c["l"],c["log_terms"])
        issue = c["block"]+c["acap"]
        update = budget.install_block_bound(
            c,c["count_max"],budget.dyadic(c["exposure_min"],c["exposure_bits"],True),
            F(0),issue,initial)
        first = budget.guarded_action(p,c,update["intercept"],issue,c["ab"])
        second = budget.guarded_action(
            p,c,update["intercept"],issue+c["ab"],c["acap"],
            promise=first["promise"],numeric_failure=True)
        third = budget.guarded_action(
            p,c,update["intercept"],issue+c["ab"]+c["acap"],c["ab"],
            promise=second["promise"],numeric_failure=True)
        self.assertEqual((first["period"],second["period"],third["period"]),
                         (c["acap"],c["ab"],c["ab"]))
        self.assertLessEqual(c["acap"]+p.tick,c["D_guard"])
        self.assertTrue(budget.length_admitted(c["ab"]+p.tick,p.B,p))
        with self.assertRaises(ValueError):
            budget.guarded_action(p,c,initial,issue,c["acap"],numeric_failure=True)

    def _certificate_at_H(self, H):
        c = self.c
        return budget.finite_price_certificate(
            self.p,c["ab"],c["acap"],c["block"],H,c["count_max"],
            self.d["exposure_lower"],c["l"],c["rho"],c["eta"])

    def _assert_good_log_sizes(self, c, count, exposure):
        x = (count+c["H"])/(c["phi_lower"]*exposure*c["l"])
        if x <= 1:
            self.assertEqual(budget.H_interval(x*c["l"],c["l"],c["log_terms"]),
                             (x,x))
            return 0  # The linear branch does not evaluate a logarithm.
        z = x/F(2)**budget.log2_floor(x)
        v = (z-1)/(z+1)
        self.assertLessEqual(v.denominator.bit_length(),c["reduced_ratio_bit_bound"])
        lo,hi = budget.log_interval(x,c["log_terms"])
        actual_bits = max(max(abs(a.numerator).bit_length(),a.denominator.bit_length())
                          for a in (lo,hi))
        self.assertLessEqual(actual_bits,c["normalized_log_rational_bit_bound"])
        return actual_bits

    def test_rational_H_review_counterexample_has_valid_bit_bound(self):
        c = self._certificate_at_H(F(15)+F(1,1 << 1024))
        self.assertTrue(c["success"])
        exposure = budget.dyadic(c["exposure_min"],c["exposure_bits"],True)
        actual_bits = self._assert_good_log_sizes(c,c["count_max"],exposure)
        self.assertEqual(actual_bits,22639)
        self.assertGreater(actual_bits,12609)  # The reviewed bound was too small.
        self.assertEqual(c["normalized_log_rational_bit_bound"],61761)

    def test_rational_H_bit_bounds_cover_dyadic_and_odd_denominators(self):
        for denominator in (3,7,10,1 << 257,(1 << 512)+1):
            c = self._certificate_at_H(F(15)+F(1,denominator))
            self.assertTrue(c["success"])
            exposures = (budget.dyadic(c["exposure_min"],c["exposure_bits"],True),
                         budget.dyadic(self.d["exposure_lower"],c["exposure_bits"],True),
                         3*c["block"]/4)
            for count in (F(0),F(1),c["count_max"]):
                for exposure in exposures:
                    with self.subTest(denominator=denominator,count=count,exposure=exposure):
                        self._assert_good_log_sizes(c,count,exposure)

    def test_integer_H_keeps_A_and_B_bit_bounds(self):
        from dataclasses import replace
        pb = replace(budget.model(262144,16000000),theta=F("0.7"))
        cb = budget.count_and_tax(pb,rho=F("0.0000005"),
                                  policy=budget.alternate_design(pb))["numerical_certificate"]
        for c,H,reduced_bits,log_bits in ((self.c,15,260,12609),(cb,14,261,12657)):
            with self.subTest(H=H):
                self.assertEqual(c["H"],H)
                self.assertTrue(c["success"])
                self.assertEqual(c["reduced_ratio_bit_bound"],reduced_bits)
                self.assertEqual(c["normalized_log_rational_bit_bound"],log_bits)
        self.assertEqual(self._certificate_at_H(F(15)),self.c)

if __name__ == "__main__":
    unittest.main(verbosity=2)

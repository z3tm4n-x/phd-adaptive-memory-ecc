"""T52: small deterministic formula checks; no radiation campaign or optimizer.

Run: python3 theory/check_fixed_period_resource_contract.py
All algebra/geometry checks use Fraction. Transcendental probability bounds
are proved in the text; this file is not certified interval arithmetic.
"""
from fractions import Fraction as F
from itertools import product
from math import ceil, floor, comb
import unittest


def rarity(B, b, FS, T):
    exposure = min(B * T, b * T + FS)
    square = min(B * B * T, B * exposure, b * b * T + (B + b) * FS)
    return exposure, square


def integral(segments, left, right, power=1):
    return sum((max(F(0), min(v, right) - max(u, left)) * rate**power
                for u, v, rate in segments), F(0))


def mask_bound(b, a, h):
    if b >= a:
        return h
    k = h // a
    return k * b + min(b, h - k * a)


def mask_integral(b, a, h, start):
    return sum((max(F(0), min(j * a + b, start + h) - max(j * a, start))
                for j in range(-2, ceil((start + h) / a) + 2)), F(0))


def triples(p, conditional, sensitive):
    T, B, b, FS, exposure, square, chi, eta, q, Q, D, Ds, k0, base = p
    common = (chi * square / 2, base, F(0))
    initial = [(k0 * B, F(0), F(0)), (F(0), k0 * exposure, F(0))]
    cross = [(F(0), F(0), F(0))]
    if conditional and D:
        cross = [(eta * square / 2, chi * D * square / 2, F(0))]
        v = chi * D
        for L, R in [(B*v*T, B*v), (b*v*T, b*v+eta*FS), (F(0), eta*exposure)]:
            cross += [(B*R, B*L, F(0)), (F(0), exposure*R, exposure*L)]
    service = [(F(0), F(0), F(0))]
    if sensitive:
        v = Q * Ds
        service = [(F(0), B*v, B*v*T), (F(0), b*v+q*FS, b*v*T),
                   (F(0), q*exposure, F(0))]
    return [tuple(sum(xs) for xs in zip(common, i, x, s))
            for i, x, s in product(initial, cross, service)]


def direct_bound(p, tau, conditional, sensitive):
    T, B, b, FS, exposure, square, chi, eta, q, Q, D, Ds, k0, base = p
    v = chi * D * (T/tau + 1)
    cross = F(0)
    if conditional and D:
        cross = min((chi*D + tau*eta)*square/2,
                    min(B*tau, exposure)*min(B*v, b*v+eta*FS, eta*exposure))
    vq = Q * Ds * (T/tau + 1)
    service = min(B*vq, b*vq+q*FS, q*exposure) if sensitive else F(0)
    return base + k0*min(exposure, B*tau) + chi*tau*square/2 + cross + service


class FormulaChecks(unittest.TestCase):
    def test_rarity_bound_and_attainment(self):
        for B, b, FS, T in [(F(3), F(1), F(5), F(7)),
                             (F(1), F(0), F(0), F(7)),
                             (F(2), F(2), F(9), F(7)),
                             (F(3), F(1), F(90), F(7))]:
            exposure, square = rarity(B, b, FS, T)
            L = min(T, FS/(B-b)) if B > b else T
            self.assertEqual(square, B*B*L + b*b*(T-L))
            self.assertLessEqual(B*L+b*(T-L), exposure)
        B, b = F(7, 5), F(1, 3)
        for x in [F(0), b/2, b, (b+B)/2, B]:
            s = max(F(0), x-b)
            self.assertLessEqual(x*x, b*b+(B+b)*s)

    def test_full_word_coefficient(self):
        for n, W in [(39, 1935832), (39, 2), (7, 3)]:
            chi = F(n-1, n*W)
            self.assertEqual(chi*(W*n)**2/2, W*comb(n, 2))

    def test_piecewise_pair_and_pending_integrals(self):
        # Two words, offset latch times; horizon not a whole number of cycles.
        T, tau, D, eta = F(27), F(10), F(2), F(1, 4)
        seg = [(F(0), F(4), F(1, 10)), (F(4), F(9), F(3, 10)),
               (F(9), T, F(1, 10))]
        B, b, FS = F(3, 10), F(1, 10), F(1)
        exposure, square = rarity(B, b, FS, T)
        pair, cross, actual_volume = F(0), F(0), F(0)
        pending = []
        for phase in [F(0), F(5)]:
            reads = [phase + j*tau for j in range(3) if phase+j*tau < T]
            bounds = sorted(set([F(0), T] + reads))
            pair += sum((eta*integral(seg, u, v)**2/2
                         for u, v in zip(bounds, bounds[1:])), F(0))
            previous = F(0)
            for read in reads:
                end = min(T, read+D)
                cross += eta*integral(seg, previous, read)*integral(seg, read, end)
                actual_volume += eta*(end-read)
                pending.append((read, end))
                previous = read
        pending.sort()
        self.assertTrue(all(v <= x for (u, v), (x, y) in zip(pending, pending[1:])))
        chi = 2*eta
        self.assertLessEqual(pair, chi*tau*square/2)
        self.assertLessEqual(cross, (chi*D+tau*eta)*square/2)
        volume = chi*D*(T/tau+1)
        self.assertLessEqual(actual_volume, volume)
        self.assertLessEqual(cross, min(B*tau, exposure)*
                             min(B*volume, b*volume+eta*FS, eta*exposure))

    def test_42_branches_equal_direct_certificate(self):
        for D, Ds, k0 in [(F(2), F(1), F(1, 3)), (F(0), F(0), F(0))]:
            exposure, square = rarity(F(3, 10), F(1, 10), F(1), F(27))
            p = (F(27), F(3, 10), F(1, 10), F(1), exposure, square,
                 F(1, 2), F(1, 4), F(1, 2), F(1), D, Ds, k0, F(1, 1000))
            for conditional, sensitive in product([False, True], repeat=2):
                ts = triples(p, conditional, sensitive)
                self.assertLessEqual(len(ts), 42)
                for tau in [F(1, 2), F(3), F(10), F(27), F(100)]:
                    algebra = min(a*tau+b+e/tau for a, b, e in ts)
                    self.assertEqual(algebra, direct_bound(p, tau, conditional, sensitive))

    def test_mask_maximum_independent_overlap(self):
        for a, b, h in [(F(5), F(2), F(1)), (F(5), F(2), F(13)),
                         (F(7, 3), F(2, 3), F(19, 3)), (F(4), F(4), F(9))]:
            # Extrema occur where a moving endpoint crosses an interval edge.
            phases = {F(0), b % a, (-h) % a, (b-h) % a}
            actual = max(mask_integral(b, a, h, s) for s in phases)
            self.assertEqual(actual, mask_bound(b, a, h))

    def test_fifo_service_curve(self):
        a, b = F(7), F(3)
        R = 1-b/a
        for t in [F(j, 3) for j in range(100)]:
            self.assertGreaterEqual(t-mask_bound(b, a, t), max(F(0), R*(t-b)))
        sigma, u = F(2), F(1, 5)
        delay = b+sigma/R
        for v in [F(0), F(1), F(11), F(100)]:
            self.assertLessEqual(sigma+u*v, R*(v+delay-b))

    def test_balanced_ticks_word_period_and_masks(self):
        for W, M, c in [(3, 11, 2), (7, 32, 3), (2, 9, 4)]:
            starts = [(j*M)//W for j in range(5*W)]
            a = F(M, W)
            for j in range(4*W):
                self.assertEqual(starts[j+W]-starts[j], M)
                self.assertGreaterEqual(starts[j+1]-starts[j], c)
                self.assertGreaterEqual(starts[j], j*a-1)
                self.assertLessEqual(starts[j]+c, j*a+c)
            self.assertLessEqual(starts[W-1]+c, M)
            for H in [F(1, 2), F(M), F(5*M, 2)]:
                busy = sum((max(F(0), min(F(s+c), H)-s) for s in starts), F(0))
                self.assertLessEqual(busy, c*(H/a+2))

    def test_rounding_must_recheck_both_ends(self):
        f = lambda tau: tau+1/tau
        self.assertEqual(f(F(1)), 2)
        self.assertGreater(f(F(1, 2)), 2)
        # A quadratic interval with two rational roots; no clamping to table min.
        table = [F(1, 2), F(1), F(2), F(3), F(4)]
        direct = [t for t in table if t+F(2)/t <= 3]
        interval = [t for t in table if 1 <= t <= 2]
        self.assertEqual(direct, interval)
        self.assertEqual([t for t in [F(3), F(4)] if 1 <= t <= 2], [])

    def test_cell_bound_for_clean_and_dirty_start(self):
        for n in [3, 7, 39]:
            for initial in [0, 1]:
                hits = 0
                for i, j in product(range(n), repeat=2):
                    middle = initial ^ (1 << i)
                    final = middle ^ (1 << j)
                    hits += middle.bit_count() > 1 or final.bit_count() > 1
                self.assertGreaterEqual(F(hits, n*n), F(n-1, n))

    def test_uniform_number_of_cells(self):
        L, c, tmin, W = F(17), F(1), F(5), 3
        for tau, ell in product([F(5), F(7), F(13)], [F(1, 2), F(1), F(2)]):
            total = 0
            for phase in [F(0), F(1, 2), F(9, 4)]:
                windows = sorted((max(F(0), phase+j*tau), min(L, phase+j*tau+c))
                                 for j in range(-1, 6)
                                 if phase+j*tau < L and phase+j*tau+c > 0)
                left = F(0)
                for u, v in windows:
                    total += floor((u-left)/ell)
                    left = v
                total += floor((L-left)/ell)
            J = floor(L/tmin)+2
            bound = max(0, ceil(W*L/ell-W*J*(c/ell+2)))
            self.assertGreaterEqual(total, bound)

    def test_r0b_units_and_preregistered_ranges(self):
        Ws = [2**18, 2**19, 2**20, 1935832, 2**21, 2**22]
        Rs = [16*10**6, 64*10**6, 256*10**6]
        taxes = [F(1, 1000), F(1, 400), F(1, 100)]
        periods = [F(39*W, R)/tax for W, R, tax in product(Ws, Rs, taxes)]
        self.assertEqual(min(periods), F('3.9936'))
        self.assertEqual(max(periods), F('10223.616'))
        self.assertEqual(F(39*1935832, Rs[0]), F('4.7185905'))
        critical = [F(1, 100)*tax*R/(39*comb(39, 2)*W**2)
                    for W, R, tax in product(Ws, Rs, taxes)]
        self.assertEqual(max(critical)/min(critical), 40960)
        cmax, hmin = F(39, Rs[0]), F(1, 1000)
        self.assertEqual(F(1, 100)+cmax/hmin, F('0.0124375'))
        self.assertEqual(F(2, 100)+2*cmax/hmin, F('0.024875'))
        self.assertLess(F('0.024875'), F(5, 100))
        self.assertGreater(cmax, F(1, 10**6))


if __name__ == '__main__':
    unittest.main(verbosity=2)

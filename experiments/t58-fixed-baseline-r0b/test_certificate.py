"""Small independent oracles; no mission simulation or adaptive comparison."""
import itertools
import unittest
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction as F
from certificate import (Risk, Resource, admissible_interval, branches, components,
    exp_neg, sqrt_bounds, fixed_period, resources, resource_ok, mask_bound,
    class_lower, direct_lower, preparation, conditional_cost, select_conditional,
    floor, ceil, merge_intervals, integer_interval)


def risk(**kw):
    values = dict(T=F(27), B=F(3, 10), b=F(1, 10), FS=F(1),
                  q=F(1, 2), Q=F(1), chi=F(1, 2), eta=F(1, 4))
    values.update(kw)
    return Risk(**values)


def resource(**kw):
    values = dict(W=2, c=F(1, 100), H=F(27), h=F(1), tax=F(1, 2),
                  peak=F(1, 2), delay=F(1), sigma=F(1, 10), u=F(1, 5),
                  g=F(1, 10), tick=F(1, 100))
    values.update(kw)
    return Resource(**values)


class ImplementationChecks(unittest.TestCase):
    def test_exp_independent_decimal(self):
        with localcontext() as ctx:
            ctx.prec = 140
            for x in map(F, ["0", "0.00000000000000001", "0.1", "1", "2", "79", "181"]):
                lo, hi = exp_neg(x)
                reference = (-Decimal(x.numerator)/Decimal(x.denominator)).exp()
                self.assertLessEqual(Decimal(lo.numerator)/Decimal(lo.denominator), reference)
                self.assertGreaterEqual(Decimal(hi.numerator)/Decimal(hi.denominator), reference)

    def test_sqrt_independent_squared_enclosure(self):
        for x in [F(0), F(2), F(4, 9), F(10**50+1, 10**49), F(1, 10**100)]:
            lo, hi = sqrt_bounds(x)
            self.assertLessEqual(lo*lo, x)
            self.assertGreaterEqual(hi*hi, x)
        self.assertEqual(sqrt_bounds(F(4, 9)), (F(2, 3), F(2, 3)))

    def test_all_degenerate_quadratics(self):
        cases = [((0, 0, 0), 0, (F(0), None)),
                 ((0, 1, 0), 0, None), ((0, 0, 1), 0, None),
                 ((0, 0, 2), 1, (F(2), None)),
                 ((1, 0, 0), 0, None), ((1, 0, 1), 2, (F(1), F(1))),
                 ((1, 0, 2), 3, (F(1), F(2))), ((1, 3, 0), 2, None),
                 ((1, 0, 1), 1, None)]
        for triple, eps, expected in cases:
            self.assertEqual(admissible_interval(tuple(map(F, triple)), F(eps)), expected)

    def test_inner_intervals_against_rational_polynomial(self):
        for a, b, e in itertools.product([F(0), F(1, 7), F(1)], repeat=3):
            iv = admissible_interval((a, b, e), F(3, 2))
            if iv:
                lo, hi = iv
                points = [t for t in [lo, hi, F(1), F(3)] if t is not None and t > 0
                          and t >= lo and (hi is None or t <= hi)]
                for t in points:
                    self.assertLessEqual(a*t*t+(b-F(3, 2))*t+e, 0)

    def test_both_rounding_directions_and_absent_tick(self):
        iv = admissible_interval((F(1), F(0), F(1)), F(2))
        self.assertEqual(iv, (F(1), F(1)))
        for t in [F(1, 2), F(3, 2)]:
            self.assertGreater(t+1/t, 2)
        self.assertGreater(ceil(iv[0]/F(3, 4)), floor(iv[1]/F(3, 4)))
        self.assertEqual(merge_intervals([(F(1), F(2)), (F(3), None), (F(2), F(3))]),
                         [(F(1), None)])

    def test_feasible_tick_arbitrarily_close_to_irrational_root(self):
        triple = (F(1, 4), F(0), F(1, 40))
        epsilon = F(11, 40)+F(1, 2**500)
        inner = admissible_interval(triple, epsilon)
        self.assertLess(inner[1], 1)  # A mere 180-bit inner radical loses tick 1.
        self.assertEqual(integer_interval(triple, epsilon, F(1), 1, 10), (1, 1))
        for a, b, e in itertools.product([F(0), F(1, 7), F(1)], repeat=3):
            triple = (a, b, e)
            expected = [m for m in range(1, 41) if a*F(m, 5)+b+e/F(m, 5) <= F(3, 2)]
            result = integer_interval(triple, F(3, 2), F(1, 5), 1, 40)
            self.assertEqual(result, (expected[0], expected[-1]) if expected else None)

    def test_original_and_expansion_including_clock_box(self):
        for mode, D, Ds in itertools.product(["U", "C"], [F(0), F(1, 100)],
                                            [F(0), F(1, 200)]):
            p = risk(mode=mode, D=D, Ds=Ds, K0=1, d=F(1, 10000))
            for low, high in [(F(1), F(1)), (F(99, 100), F(101, 100))]:
                ts = branches(p, low, high)
                self.assertLessEqual(len(ts), 42)
                for t in [F(1, 10), F(1), F(30)]:
                    self.assertEqual(min(a*t+b+e/t for a, b, e in ts),
                                     components(p, t*low, t*high)["total"])

    def test_entire_integer_domain_against_exhaustive_oracle(self):
        for mode, Ds, clock in itertools.product(["U", "C"], [F(0), F(1, 1000)],
                                                [F(0), F(1, 100)]):
            p = risk(mode=mode, D=F(1, 1000), Ds=Ds)
            r = resource(clock_error=clock)
            eps = F(2, 5)
            admissible = []
            for M in range(1, 501):
                v = resources(r, M)
                if (p.D < v["tau_lo"] and resource_ok(v) and
                    components(p, v["tau_lo"], v["tau_hi"])["total"] <= eps):
                    admissible.append(M)
            result = fixed_period(p, r, eps, 1, 500)
            self.assertEqual(result["selected_tick"], max(admissible) if admissible else None)
            expanded = {m for lo, hi in result["certified_tick_intervals"] for m in range(lo, hi+1)}
            self.assertEqual(expanded, set(admissible))

    def test_zero_radiation_and_initial_failure_no_clamp(self):
        p = risk(B=F(0), b=F(0), FS=F(0))
        r = resource()
        self.assertEqual(fixed_period(p, r, F(1, 10), 1, 1000)["selected_tick"], 1000)
        self.assertIsNone(fixed_period(replace(p, rho0=F(1, 5)), r, F(1, 10), 1, 1000)["selected_tick"])
        self.assertIsNone(fixed_period(p, r, F(1, 10), 1, 1)["selected_tick"])

    def test_clock_enclosure_not_nominal_claim(self):
        p = risk(mode="C", D=F(1, 1000), Ds=F(1, 1000))
        r = resource(clock_error=F(1, 20))
        answer = fixed_period(p, r, F(2, 5), 1, 500)
        M = answer["selected_tick"]
        self.assertIsNotNone(M)
        for stretch in [F(95+j, 100) for j in range(11)]:
            self.assertLessEqual(components(p, M*r.tick*stretch)["total"], F(2, 5))
        self.assertLessEqual(components(p, answer["resource"]["tau_lo"],
                                      answer["resource"]["tau_hi"])["total"], F(2, 5))

    def test_mask_peak_finite_window_independent_geometry(self):
        for a, b, h in [(F(5), F(2), F(13)), (F(7, 3), F(2, 3), F(4)),
                        (F(5), F(2), F(1)), (F(5), F(5), F(8))]:
            phases = {F(0), b % a, (-h) % a, (b-h) % a}
            actual = max(sum((max(F(0), min(j*a+b, s+h)-max(j*a, s))
                              for j in range(-2, ceil((s+h)/a)+2)), F(0)) for s in phases)
            self.assertEqual(mask_bound(b, a, h), actual)
        for W, M, c in [(3, 11, F(2)), (5, 31, F(4))]:
            starts = [F(j*M//W) for j in range(10*W)]
            for H in [F(1, 2), F(M), F(3*M+1, 2)]:
                actual = sum((max(F(0), min(s+c, H)-s) for s in starts), F(0))
                self.assertLessEqual(actual, c*(H*W/M+2))
                self.assertGreaterEqual(actual, c*max(F(0), H*W/M-2))
            for j in range(W):
                self.assertEqual(starts[j+W]-starts[j], M)
            self.assertLessEqual(starts[W-1]+c, M)

    def test_fifo_empty_overload_and_delay_not_necessity(self):
        empty = resources(resource(sigma=F(0), g=F(0), u=F(0)), 100)
        self.assertEqual(empty["delay_upper"], 0)
        overload = resources(resource(u=F(99, 100)), 100)
        self.assertIsNone(overload["delay_upper"])
        self.assertFalse(overload["mandatory_U_block_exclusion"])

    def test_lower_cells_enumerated_across_all_test_phases(self):
        W, L, c, H, tax = 3, F(17), F(1), F(100), F(1, 2)
        lb = class_lower(W, 39, F(1), L, c, c, H, tax, F(1),
                         witness_admissible=True, deterministic_window_contract=True)
        for tau in [lb["tau_min"], F(10), F(20)]:
            for phase in [F(0), F(1, 2), F(9, 4)]:
                windows = sorted((max(F(0), phase+j*tau), min(L, phase+j*tau+c))
                                 for j in range(-1, 20)
                                 if phase+j*tau < L and phase+j*tau+c > 0)
                left, count = F(0), 0
                for u, v in windows:
                    count += floor(u-left)
                    left = v
                count += floor(L-left)
                self.assertGreaterEqual(W*count, lb["N"])
        self.assertFalse(class_lower(W, 39, F(1), L, c, c, H, tax,
                                     witness_admissible=False, deterministic_window_contract=True)["applicable"])

    def test_preparation_and_direct_lower_contract(self):
        p = preparation(F(1), F(1, 100), 100, 1, F(0), F(1, 100), F(0))
        self.assertEqual(p["Q"], 4)
        self.assertEqual(p["K0"], 4)
        self.assertEqual(p["rho0"], F(3, 200))
        self.assertIsNone(direct_lower(F(1, 10), F(1), structural_mark_contract=False))
        self.assertGreater(direct_lower(F(1, 10), F(1), structural_mark_contract=True), 0)

    def test_conditional_cost_includes_bad_histories_and_finite_search(self):
        p = risk(B=F(1, 100), b=F(1, 100), FS=F(0), mode="C")
        r = resource()
        args = dict(read=F(1, 200), write=F(1, 200), m=1, b_nom=p.b,
                    chi_gross=p.chi, eta_gross=p.eta)
        result = select_conditional(p, r, F(1, 10), [20, 50, 100], **args)
        self.assertIsNotNone(result)
        self.assertGreater(result["cost"]["bad_probability_upper"], 0)
        self.assertGreaterEqual(result["cost"]["writes_upper"], p.B*p.T)
        explicit = [conditional_cost(p, r, M, **args)["actual_upper"] for M in [50, 100]]
        self.assertLessEqual(result["cost"]["actual_upper"], min(explicit))

    def test_invalid_inputs_rejected(self):
        for p in [risk(B=F(-1)), risk(mode="bad"), risk(D=F(-1)), risk(eta=F(1))]:
            with self.assertRaises(ValueError):
                p.validate()
        with self.assertRaises(ValueError):
            fixed_period(risk(D=F(1)), resource(), F(1, 10), 1, 10)
        with self.assertRaises(ValueError):
            resource(sigma=F(0), g=F(1)).validate()
        with self.assertRaises(ValueError):
            risk(B=0.3).validate()


if __name__ == "__main__":
    unittest.main(verbosity=2)

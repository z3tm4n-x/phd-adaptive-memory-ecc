"""Small mechanisms and proof-boundary checks, not radiation simulations."""
import unittest
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from bounds import plateau, moderate_lower, tail_lower, price_floor, ratio_or_status, status


class NecessaryTests(unittest.TestCase):
    def w(self,**kw):return plateau(F(1000),F(4),F(1),F(300),**kw)
    def test_uncapped_plateau(self):self.assertEqual(self.w()['L'],100)
    def test_mixed_term_not_missing(self):self.assertEqual(self.w()['S2_excess'],1500)
    def test_full_background_not_double_counted(self):self.assertEqual(self.w()['S2'],2500)
    def test_S2_restricts_witness(self):self.assertEqual(self.w(S2_cap=F(1750))['L'],50)
    def test_fluence_restricts_witness(self):self.assertEqual(self.w(F_cap=F(1150))['L'],50)
    def test_excess_restricts_witness(self):self.assertEqual(self.w(excess_cap=F(150))['L'],10)
    def test_reject_bbar_not_class(self):self.assertFalse(self.w(S2_cap=F(500))['admissible'])
    def test_zero_background_can_survive_cap(self):
        self.assertTrue(plateau(F(1000),F(4),F(0),F(300),S2_cap=F(500))['admissible'])
    def test_free_initial_is_required(self):self.assertFalse(self.w(initial_peak_allowed=False)['admissible'])
    def test_no_fluence_no_plateau(self):self.assertFalse(plateau(F(100),F(4),F(1),F(0))['admissible'])
    def test_constant_case_no_division(self):self.assertEqual(plateau(F(100),F(1),F(1),F(0))['L'],100)
    def test_negative_cap_rejected(self):
        with self.assertRaises(ValueError):self.w(S2_cap=F(-1))
    def test_constant_cap_rejected(self):self.assertFalse(plateau(F(100),F(1),F(1),F(0),F_cap=F(99))['admissible'])
    def test_arbitrary_phase_edge(self):
        # Accepted counterexample: 8 blocks of length 2 in [0,350].
        self.assertLess(16,F(8*2*350,200)-4)
        self.assertGreaterEqual(16,F(8*2*350,200)-2*8*2)
    def test_read_not_reserved_write_in_floor(self):
        self.assertLess(price_floor(100,F(1),F(2),F(10),F(1000)),price_floor(100,F(2),F(2),F(10),F(1000)))
    def test_component_edge(self):
        self.assertEqual(price_floor(100,F(1),F(2),F(10),F(1000),3),F('8.8'))
    def test_zero_denominator(self):self.assertEqual(ratio_or_status(F(0),F(0))['status'],'undefined_0_over_0')
    def test_infinite_ratio(self):self.assertEqual(ratio_or_status(F(1),F(0))['status'],'infinity')
    def test_unknown_is_not_zero(self):self.assertEqual(ratio_or_status(None,F(1))['status'],'missing')
    def test_unknown_not_impossible(self):self.assertEqual(status(),'unknown')
    def test_constant_exclusion_not_adaptive_success(self):self.assertEqual(status(fixed_excluded=True),'unknown')
    def test_adaptation_necessary_requires_lower(self):self.assertEqual(status(adaptive_ok=True),'adaptive_sufficient_necessity_unknown')
    def test_necessary_and_sufficient(self):self.assertEqual(status(adaptive_ok=True,fixed_excluded=True),'adaptation_needed_and_sufficient')
    def test_period_exclusion_conflict(self):
        with self.assertRaises(ValueError):status(adaptive_ok=True,period_excluded=True)
    def test_price_boundary_is_closed(self):self.assertEqual(status(constant_ok=F(1)<=F(1)),'constant_sufficient')
    def test_lower_domain_failure_is_not_zero_certificate(self):
        self.assertIsNone(moderate_lower(10,39,F(4),F(5),F(1),F(2),F(3),F(0)))
    def test_tail_domain_failure(self):self.assertIsNone(tail_lower(10,39,F(4),F(5),F(3),F(2),F(0)))
    def test_independent_probability_arithmetic(self):
        # Independent high precision evaluates the unrelaxed expression.
        # Exact rational decisions use only the proven relaxations in bounds.py.
        with localcontext() as ctx:
            ctx.prec=80
            W,n,B,L,c,P0,P1=100,39,F(1),F(1000),F('0.001'),F('.2'),F(1)
            low=moderate_lower(W,n,B,L,c,P0,P1,F(0))
            dec=lambda x:D(x.numerator)/D(x.denominator)
            beta=F(n-1,2*n*W)
            z=beta*B*B*(L-2*P1)*P0*(1-c/P0)**2
            exact=1-(-(dec(z)*(-dec(B*P1/W)).exp())).exp()
            self.assertLessEqual(dec(low),exact)
    def test_upper_ratios_are_not_ratio_upper(self):
        # True bg=1,total=10; bounds bg<=100,total<=100 give ratio 1, not >=10.
        self.assertLess(F(100,100),F(10,1))
    def test_float_input_rejected(self):
        with self.assertRaises(ValueError):plateau(1000,4,1,300,S2_cap=1750.0)
    def test_integer_inputs_stay_exact(self):
        self.assertIsInstance(plateau(1000,4,1,301)['L'],F)
        self.assertIsInstance(ratio_or_status(1,3)['value'],F)
    def test_negative_failure_quota_rejected(self):
        with self.assertRaises(ValueError):tail_lower(100,39,1,1000,1,10,F(-1))


if __name__=='__main__':unittest.main()

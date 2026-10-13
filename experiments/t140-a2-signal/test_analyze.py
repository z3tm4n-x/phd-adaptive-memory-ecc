"""Addressed checks, not a Monte-Carlo campaign."""
from fractions import Fraction as F
import unittest
import analyze as a


class T140Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = a.analyze()
        cls.cert = a.module('t140_test_t58','experiments/t58-fixed-baseline-r0b/certificate.py')
        cls.t57 = a.module('t140_test_t57','theory/t57_uniform_budget.py')
        cls.p = cls.t57.model(1935832,256000000)

    def test_preserved_preflight(self):
        self.assertTrue(self.r['preflight_byte_identical'])
        self.assertEqual(len(self.r['source_blobs']),8)

    def test_fixed_witness_and_resources(self):
        w = self.r['fixed']['witness']
        self.assertEqual(w['selected_tick'],273275955)
        self.assertLessEqual(w['upper_components']['total'],F('.01'))
        self.assertTrue(self.cert.resource_ok(w['resource']))

    def test_all_fixed_periods_lower_coverage(self):
        f = self.r['fixed']
        self.assertLessEqual(f['lower_at_previous_tick'],F('.01'))
        self.assertGreater(f['lower_at_P0'],F('.01'))
        self.assertGreater(f['lower_tail'],F('.01'))
        self.assertLess(f['lower_P0_s'],f['lower_split_P1_s'])
        self.assertLess(f['optimal_fixed_price_lower'],f['optimal_fixed_price_upper'])

    def test_two_disjoint_segments_strengthen_peak_lower(self):
        p = self.p
        f = self.r['fixed']
        bounds = a.module('t140_test_t126','experiments/t126-regime-map/bounds.py')
        peak = bounds.moderate_lower(p.W,39,p.B,f['plateau_L_s'],p.c,
                                    f['lower_P0_s'],f['lower_split_P1_s'],F(0))
        self.assertGreater(f['lower_at_P0'],peak)

    def test_witness_exposure_and_growth(self):
        p = self.p
        L = self.r['fixed']['plateau_L_s']
        self.assertEqual((p.B-p.b)*L,p.FS)
        self.assertEqual(p.B**2*L+p.b**2*(p.T-L),p.S2)
        self.assertTrue(0 < L < p.T)  # only downward jump, any one-sided growth

    def test_layer_against_accepted_tradeoff(self):
        p = self.p
        row = self.r['layers']['T57_alpha_0.001']
        accepted = self.t57.price_tradeoff(p,F('.25'),self.r['target_adaptive_price'])
        self.assertFalse(accepted['possible'])
        self.assertEqual(accepted['theta_max'],row['u_upper']*p.T/p.gamma)

    def test_optimistic_resource_information_barrier(self):
        for row in self.r['layers'].values():
            self.assertGreater(row['lifetime_mean_price_lower'],self.r['target_adaptive_price'])
            self.assertLess(row['gain_ceiling_with_presented_fixed_upper'],5)
        self.assertLess(self.r['budgets']['necessary_reserve_ceiling_for_layer_5x_s'],
                        self.r['T57_min_resource_period_s'])
        self.assertGreater(self.r['budgets']['implied_reserve_bus_density'],F('.25'))

    def test_risk_reservation_makes_floor_stricter(self):
        rows = self.r['layers']
        self.assertGreater(rows['T57_alpha_0.001']['lifetime_mean_price_lower'],
                           rows['T57_even_free_information']['lifetime_mean_price_lower'])

    def test_clipped_pair_optimum_kkt(self):
        p = self.p
        r = self.r['relaxation']
        L=p.FS/(p.B-p.b); d=L/p.T; k=F(38,78*p.W)
        A=k*p.b*p.b*(p.T-L); S=k*p.B*p.B*L; x=r['Pmin_s']
        self.assertLess(r['P_peak_free_s'],x)
        self.assertGreater((1-d)*A*S/(p.eps-S*x)**2-d/x**2,0)
        self.assertEqual(A*r['Pquiet_s']+S*x,p.eps)
        self.assertLess(r['gain'],5)
        self.assertGreater(r['unbounded_resource_gain'],5)

    def test_floor_sum_against_exhaustive_small(self):
        for n in range(20):
            for m in range(1,10):
                for k in range(20):
                    self.assertEqual(a.floor_sum(n,m,k,3),sum((k*i+3)//m for i in range(n)))

    def test_phase_exposure_against_direct_cells(self):
        W,M,tick,c=7,47,F(1,10),F(1,5)
        P=M*tick
        for time_index in range(160):
            time=F(time_index,10)
            cut=time-c
            direct=F(0)
            for w in range(W):
                phase=(w*M//W)*tick
                for j in range(5):
                    latch=phase+j*P
                    if latch<=cut:
                        start=F(0) if j==0 else phase+(j-1)*P+c
                        direct+=(latch-start)/W
            self.assertEqual(a.visible_exposure(time,W,M,tick,c),direct)

    def test_delivery_is_not_free(self):
        W,M,tick,c=7,47,F(1,10),F(1,5)
        for t in [F(1),F(5),F(10)]:
            self.assertEqual(a.visible_exposure(t+F(3,10),W,M,tick,c,F(3,10)),
                             a.visible_exposure(t,W,M,tick,c))

    def test_unobserved_service_hits_removed(self):
        W,M,tick,c=7,47,F(1,10),F(1,5)
        # Delay zero and take a sufficiently large time; nonzero U window
        # loses exposure compared with an instantaneous-fence oracle.
        self.assertLess(a.visible_exposure(F(10),W,M,tick,c),
                        a.visible_exposure(F(10),W,M,tick,F(0)))

    def test_mission_tail_is_not_single_95_percent(self):
        o=self.r['observation']
        self.assertLess(o['union_example_alpha_per_decision'],F(1,10**10))
        for row in o['calendars'].values():
            self.assertGreater(row['q_for_union_over_N_decisions']['time_upper_s'],
                               row['q95']['time_upper_s'])

    def test_finite_causal_candidate_and_budget(self):
        c=self.r['candidate']
        self.assertTrue(c['finite_numerical_acceptance'])
        self.assertTrue(c['conditional_price_valid'])
        self.assertTrue(c['resource']['ok'])
        self.assertEqual(c['risk_upper']+c['risk_remainder'],F('.01'))
        self.assertEqual(c['statistical_union_upper'],
                         c['epochs']*self.cert.exp_neg(F(c['H']))[1])
        self.assertGreater(c['extra_control_bus_per_1ms_s'],0)
        self.assertGreater(c['finite_numerical_certificate']['margin'],0)
        self.assertLess(self.r['inputs']['T_s']/c['resource']['gap']+2,2**48)
        self.assertIsNone(self.r['budgets']['max_extra_nonnegative_cost_for_5x'])

    def test_steady_background_not_no_events_for_mission(self):
        self.assertGreater(self.r['observation']['expected_background_parents'],500000)
        self.assertIsNone(self.r['inputs']['qualified_rho'])
        self.assertIsNone(self.r['inputs']['qualified_K'])


if __name__ == '__main__':
    unittest.main()

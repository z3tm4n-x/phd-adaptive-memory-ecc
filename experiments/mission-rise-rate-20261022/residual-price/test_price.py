"""Directed contract/counter tests; no stochastic/controller simulation."""
from fractions import Fraction as F
from unittest.mock import patch
import unittest

import run


class ResidualPriceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = run.context()
        cls.r = run.evaluate()

    def test_no_new_risk_call(self):
        with patch.object(run.informational, 'compute', side_effect=AssertionError('new Q')):
            with patch.object(run.cmp, 'risk', side_effect=AssertionError('new Q')):
                self.assertEqual(run.evaluate(), self.r)

    def test_remove_exactly_one_startup_before_cap(self):
        old = run.account(self.c, include_long_cold_start=True)
        new = run.account(self.c)
        self.assertEqual(old['refined_uncapped_read_upper'] - new['refined_uncapped_read_upper'],
                         self.c['recover_one'])
        for key in old['terms_read_count_upper']:
            if key != 'initial_long_FAST':
                self.assertEqual(old['terms_read_count_upper'][key], new['terms_read_count_upper'][key])
        self.assertEqual(old['reads_upper'], new['reads_upper'])
        self.assertEqual(old['full_cost_rates']['timer_events'], new['full_cost_rates']['timer_events'])

    def test_quotas_unchanged_and_lower_is_not_quota(self):
        q = self.r['unchanged']['quotas']
        self.assertEqual(q['recoveries_upper'], 1000)
        self.assertEqual(q['ordinary_loss_episodes_upper'], 1001)
        self.assertEqual(F(q['ordinary_outage_fraction']), F(1, 10000))
        self.assertEqual(F(q['ordinary_false_expected_per_s']), F(1, 10**6))
        self.assertTrue(all(x == 0 for x in self.r['mandatory_lower']['optional_additional_lower'].values()))
        for key in ('recovery', 'loss_duration', 'false', 'weak_E_repeat'):
            self.assertGreater(self.c['terms'][key], 0)

    def test_calendar_only_not_admission(self):
        cal = self.c['cal']
        self.assertGreater(cal['zero_union_slack'], 0)
        self.assertGreaterEqual(cal['recovery']['lower'], cal['h_upper'] + cal['tau'])
        self.assertGreaterEqual(cal['Pl'], F(14400))
        self.assertIsNone(self.r['diagnostic_calendar']['Q'])
        self.assertFalse(self.r['diagnostic_calendar']['implementation_approved'])

    def test_parent_normalization_and_read_terms(self):
        moments = run.cmp.per_bit_moment_caps(self.c['cfg'])
        self.assertEqual(self.c['parents'], self.c['W'] * 39 * moments['M1'])
        self.assertEqual(self.c['terms']['recovery'], 1000 * self.c['recover_one'])
        self.assertEqual(self.c['terms']['false'], self.c['S'](self.c['L']) * F(1, 10**6) * self.c['T'])

    def test_cap_and_monotonicity_of_unknown_parameters(self):
        p0 = run.account(self.c)
        p1 = run.account(self.c, F(1, 1000))
        p2 = run.account(self.c, F(1, 1000), F(1))
        self.assertLessEqual(p0['core_upper'], p1['core_upper'])
        self.assertLessEqual(p1['core_upper'], p2['core_upper'])
        for row in (p0, p1, p2):
            self.assertLessEqual(row['reads_upper'], row['hard_read_upper'])
            self.assertLessEqual(row['repairs_upper'], row['reads_upper'])
            self.assertLessEqual(row['core_upper'], row['all_history_core_upper'])
        with self.assertRaises(ValueError):
            run.account(self.c, F(2))
        with self.assertRaises(ValueError):
            run.account(self.c, veto=p0['veto_domain_per_s'][1]+1)

    def test_application_copies_initialization_and_observation_remain(self):
        p = run.account(self.c); baseline = self.c['app']['full_cost_rates']
        for key in ('application_reads', 'application_writes', 'initialization', 'app_dispatch', 'encodes'):
            self.assertEqual(p['full_cost_rates'][key], F(baseline[key]))
        for key in ('cuts', 'captures', 'decisions', 'timer_events'):
            self.assertGreater(p['full_cost_rates'][key], 0)
        self.assertGreater(p['energy_coefficients_per_second']['transport_requests'], 0)
        self.assertEqual(p['transport_plus_loss_state_bytes'], 131136)

    def test_necessary_gate_open_is_not_sufficient_price(self):
        self.assertTrue(self.r['mandatory_lower']['fivefold_not_excluded'])
        self.assertGreater(self.r['optimistic_zero_pbad_v_slice']['core_upper'],
                           self.r['price_contract']['fivefold_witness_target'])
        self.assertFalse(self.r['optimistic_zero_pbad_v_slice']['new_Q_certificate'])

    def test_single_band_budget_is_for_upper_expression_only(self):
        b = self.r['price_contract']; S = self.c['S']
        length = b['single_additive_band_budget_s']
        self.assertLessEqual(S(length), b['extra_read_count_budget'])
        cmin = self.c['cfg']['calendar']['c_ticks'] * self.c['s']['xminus']
        self.assertGreater(S(length + 2*cmin/run.NS), b['extra_read_count_budget'])
        self.assertGreater(self.c['S'](self.c['cal']['recovery']['upper']), b['extra_read_count_budget'])

    def test_witness_off_and_no_campaign(self):
        self.assertTrue(self.r['competitors']['fixed44']['sufficient'])
        for name in ('OFF39','OFF44'):
            self.assertFalse(self.r['competitors'][name]['sufficient'])
            self.assertEqual(self.r['competitors'][name]['Q_upper'], 1)
        self.assertEqual(set(self.r['computations'].values()), {0})


if __name__ == '__main__':
    unittest.main()

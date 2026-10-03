"""Regression and contract separation, not flight qualification or RTL tests."""
from fractions import Fraction as F
import json
import unittest

import run


class T90Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = run.calculate()

    def test_exact_working_rows_not_interior(self):
        a, b = self.data['baselines']
        self.assertTrue(all(x['all_published_fields_equal'] for x in [a, b]))
        self.assertEqual((a['result']['g'], a['result']['ka'], a['result']['Dstar']),
                         (140, 367, F('0.0002802445')))
        self.assertEqual((b['result']['g'], b['result']['ka'], b['result']['Dstar']),
                         (131, 3, F('0.0000545365')))

    def test_2p5_not_a_one_percent_certificate(self):
        a, b = [x['result'] for x in self.data['baselines']]
        self.assertLess(a['objective'], F('.01'))
        self.assertGreater(b['base_tax'], F('.01'))
        self.assertFalse(b['full_goal_pass'])

    def test_calendar_window_at_actual_g(self):
        a, b = self.data['baselines']
        self.assertGreater(a['timing']['window']['hF_ticks'], b['timing']['window']['hF_ticks'])
        self.assertEqual(a['timing']['window']['hF_ticks'], a['result']['lease_ticks'])

    def test_margin_and_resources(self):
        for row in self.data['baselines']:
            m, r, t = row['timing']['window'], row['result'], row['timing']
            self.assertGreaterEqual(m['hF_min'], F('1.1')*m['hF_required'])
            self.assertGreaterEqual(t['program_delay_margin_slack_s'], 0)
            self.assertLessEqual(r['peak_upper'], F('.8'))
            self.assertEqual(t['joint_U_required_upper_s'], F(99999,1100000000000))
            self.assertIsNone(t['physical_joint_U_WCET_s'])

    def test_addressed_cases_only(self):
        self.assertEqual(len(self.data['diagnostics']), 4)
        for d in self.data['diagnostics']:
            baseline = next(x['result'] for x in self.data['baselines'] if x['result']['shield']==d['shield'])
            for key in ('Dstar','g','ka','vc'):
                self.assertEqual(d[key], baseline[key])

    def test_main_long_windows_uninformative_not_zero_price(self):
        for d in self.data['diagnostics']:
            if d['shield'] == '3':
                self.assertEqual(d['result']['status'], 'LOW_uninformative')
                self.assertEqual(d['result']['mass_lower'], 0)
                self.assertLess(d['result']['k'], 0)
                self.assertIsNone(d['certified_risk_upper'])
                self.assertIsNone(d['full_price_upper'])
                self.assertFalse(d['full_goal_pass'])

    def test_long_windows_2p5_not_general_impossibility(self):
        for d in self.data['diagnostics']:
            if d['shield'] == '2.5':
                self.assertEqual(d['result']['status'], 'certified_conditional')
                self.assertGreater(d['result']['mass_lower'], 0)
                self.assertGreater(d['full_price_upper'], F('.01'))

    def test_physical_unknowns_never_filled_with_diagnostic(self):
        profiles=json.loads((run.HERE/'monitor_profiles.json').read_text())['profiles']
        old=json.loads((run.ROOT/'experiments/t82-realistic-timing/monitor_profiles.json').read_text())['profiles']
        self.assertEqual({p['id'] for p in profiles}, {p['id'] for p in old})
        self.assertEqual(len(profiles), 2)
        for p in profiles:
            self.assertFalse(p['physical_qualification'])
            self.assertTrue(all(v is None for v in p['physical_contract'].values()))
            for f in p['facts'].values():
                self.assertEqual(f['status'],'documented')
                self.assertTrue(f['source'])
                self.assertIn('unit',f)

    def test_no_saturation_conversion(self):
        profiles=json.loads((run.HERE/'monitor_profiles.json').read_text())['profiles']
        for p in profiles:
            self.assertIsNone(p['physical_contract']['saturation_hard_count_rate_per_s'])
            self.assertIsNone(p['physical_contract']['counter_bits'])

    def test_handoff_does_not_start_95_or_certify_ERR(self):
        h=self.data['handoff']
        self.assertIsNone(h['confirmed_real_monitor'])
        self.assertIsNone(h['physical_ERR_token_lower'])
        self.assertFalse(h['formulas_changed'])
        self.assertEqual(len(h['author_options']), 2)


if __name__ == '__main__':
    unittest.main()

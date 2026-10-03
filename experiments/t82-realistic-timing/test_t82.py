import copy
from fractions import Fraction as F
import unittest

from timing import (inputs, min_ticks, retime, tick_bounds, service_upper, margin_rows,
                    resources, minimum_resource_g, calculate, bounds, old_channel_diagnostics,
                    err_only_fallback, evaluate_old)
from independent import check


class TimingChecks(unittest.TestCase):
    def test_clock_rounding_and_bad_neighbor(self):
        cfg = inputs()[0]['input']
        tm, _ = tick_bounds(cfg)
        for margin, expected in [(F('.05'), 95), (F('.10'), 100)]:
            ticks = min_ticks(F('90e-9'), margin, tm)
            self.assertEqual(ticks, expected)
            self.assertGreaterEqual(ticks*tm, (1+margin)*F('90e-9'))
            self.assertLess((ticks-1)*tm, (1+margin)*F('90e-9'))
        self.assertLess(90*tm, F('90e-9'))

    def test_external_not_90_and_not_double_clocked(self):
        cfg = inputs()[0]['input']
        tm, _ = tick_bounds(cfg)
        for margin in [F('.05'), F('.10')]:
            upper = service_upper('external39_resource_projection')
            ticks = min_ticks(upper, margin, tm)
            self.assertIn(ticks, [253, 265])
            self.assertLess((ticks-1)*tm, (1+margin)*upper)
            self.assertGreaterEqual(ticks*tm, (1+margin)*upper)

    def test_all_old_JSON_rows_preserved(self):
        from confirm_t73_sync import read_new
        expected = {(r['set'], r['shield_g_cm2']): r for r in read_new()['verified_results']}
        for variant in inputs():
            for env in variant['input']['environments']:
                v = calculate(variant['input'], env)
                row = expected[variant['set'], env['shield_g_cm2']]
                for key in ['risk_upper', 'quiet_mission_upper', 'quiet_returns_upper', 'peak_upper', 'app_delay_upper_s']:
                    self.assertEqual(bounds(v[key])[1], row[key])

    def test_margins_and_all_scientific_inputs_unchanged(self):
        for variant in inputs():
            cfg = variant['input']
            untouched = copy.deepcopy(cfg)
            for architecture in ['internal38_nominal_projection', 'external39_resource_projection']:
                for margin in [F('.05'), F('.10')]:
                    changed = retime(cfg, margin, architecture, True, True)
                    for block in ['scenario', 'environments', 'environment_contract', 'mark_contract', 'whole_mission_quotas']:
                        self.assertEqual(changed[block], cfg[block])
                    self.assertEqual(cfg, untouched)
                    self.assertTrue(all(row['pass_margin'] for row in margin_rows(changed, margin, architecture)))
                    self.assertFalse(any(row['physical_qualification'] for row in margin_rows(changed, margin, architecture)))

    def test_resource_first_good_and_previous_bad(self):
        for variant in inputs():
            for margin in [F('.05'), F('.10')]:
                for architecture in ['internal38_nominal_projection', 'external39_resource_projection']:
                    cfg = retime(variant['input'], margin, architecture, True, True)
                    g = cfg['service']['g_ticks']
                    self.assertTrue(resources(cfg)['ok'])
                    previous = resources(cfg, g-1)
                    self.assertFalse(previous['ok'] and (1+margin)*previous['delay']<=F('3e-6'))
                    self.assertEqual(g, minimum_resource_g(cfg, margin))

    def test_independent_decimal_and_strong_fixed_neighbor(self):
        for variant in inputs():
            for margin in [F('.05'), F('.10')]:
                cfg = retime(variant['input'], margin, 'internal38_nominal_projection', True, True)
                for env in cfg['environments']:
                    v = calculate(cfg, env)
                    self.assertEqual(check(cfg, env, v)['metrics_checked'], 7)
                    self.assertTrue(v['E3_arbitrary_phase_J0_valid'])
                    self.assertGreater(v['E3_risk_lower'], F('.0035'))
                    self.assertGreater(v['fixed_risk_next_quantum'], F('.001'))

    def test_no_calibration_from_area_or_electronics(self):
        profiles, hypotheses = old_channel_diagnostics()
        self.assertTrue(all(r['a_M'] is None for r in profiles))
        self.assertTrue(all(not r['necessary_timing_pass'] for r in profiles))
        self.assertTrue(all(r['qualified_a_M'] is None for r in hypotheses))

    def test_gate_delivery_ERR_not_free(self):
        cfg = inputs()[0]['input']
        before = {r['bound']: r for r in margin_rows(cfg, F('.05'), 'internal38_nominal_projection')}
        for key in ['U', 'delivery_compute', 'gate_with_application_guard', 'ERR_delivery']:
            self.assertFalse(before[key]['pass_margin'])
        changed = retime(cfg, F('.10'), 'internal38_nominal_projection', True)
        self.assertGreater(F(changed['own_ERR']['max_delivery_s']), F(cfg['own_ERR']['max_delivery_s']))
        self.assertGreater(changed['service']['decision_lead_ticks'], cfg['service']['decision_lead_ticks'])

    def test_ERR_fallback_and_next_bad_quantum(self):
        rows = err_only_fallback()
        self.assertEqual(len(rows), 16)
        for row in rows:
            self.assertLessEqual(row['risk_upper'], F('.001'))
            self.assertGreater(row['risk_next_g'], F('.001'))
            self.assertGreater(row['quiet_upper'], F('.01'))
            self.assertTrue(row['quotas_and_control_cost_retained'])
            if row['resource_pass']:
                self.assertIsNotNone(row['best_certified_tax_in_this_always_S_family'])

    def test_no_external_risk_transfer_or_unstable_delay_bound(self):
        rows, *_ = evaluate_old()
        for row in rows:
            if row['architecture'].startswith('external'):
                self.assertIsNone(row['risk_upper'])
                self.assertIsNone(row['quiet_mission_upper'])
                self.assertFalse(row['conditional_scalar_pass'])
            if 'FIFO' in row['failures']:
                self.assertIsNone(row['app_delay_upper_s'])
        selected = [r for r in rows if r['set']=='T73_published' and r['margin']=='0.10' and
                    r['stage']=='retimed_all_deadlines_g' and r['architecture'].startswith('internal')]
        self.assertEqual([r['g_ticks'] for r in selected], [131, 131])
        self.assertEqual([r['conditional_scalar_pass'] for r in selected], [False, True])


if __name__ == '__main__':
    unittest.main()

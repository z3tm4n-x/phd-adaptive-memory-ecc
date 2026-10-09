"""Addressed mathematical/interface regressions; not a composed RTL test."""
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('t135_align64_test', HERE/'align64.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AlignmentTests(unittest.TestCase):
    def test_pinned_engineer_arithmetic_including_invalidate(self):
        self.assertEqual(len(a.source_checks()), 7)
        cert = a.generation_certificate()
        self.assertEqual(cert['max_edges_upper'], 78894788947889481)
        self.assertLess(cert['max_edges_upper'], 2**57)
        self.assertTrue(cert['saturation_unreachable'])
        self.assertEqual(cert['extra_saturation_unavailability_s'], 0)

    def test_horizon_and_initial_state_are_real_restrictions(self):
        self.assertFalse(a.generation_certificate(bits=32)['saturation_unreachable'])
        self.assertFalse(a.generation_certificate(T=F(10**12))['saturation_unreachable'])
        self.assertFalse(a.generation_certificate(initial=2**64-2)['saturation_unreachable'])
        with self.assertRaises(ValueError):
            a.generation_certificate(initial=-1)

    def test_full_width_is_needed_even_without_saturation(self):
        old, current = 7, 2**32+7
        self.assertLess(current, a.generation_certificate()['max_edges_upper'])
        self.assertNotEqual(old, current)
        self.assertEqual(old & (2**32-1), current & (2**32-1))
        # Clock bound does not make a truncated stale tag safe.

    def test_added_source_stages_fit_but_are_not_WCET(self):
        t = a.timing_ledger()
        self.assertEqual(t['inbound_s'], F('274.002720e-9'))
        self.assertEqual(t['outbound_s'], F('217.002160e-9'))
        self.assertEqual(t['inbound_unallocated_s'], F('45.997280e-9'))
        self.assertEqual(t['outbound_unallocated_s'], F('102.997840e-9'))
        self.assertEqual(t['decomposition_response_upper_s'], F('2.614174992e-6'))
        self.assertIsNone(t['integrated_inbound_WCET_s'])
        self.assertIsNone(t['integrated_outbound_WCET_s'])

    def test_10us_recovery_counts_and_paid_rounding(self):
        s = dict(a.b.prefetch_service(), ERR_or_loss_to_rule_s=F('10e-6'))
        c = a.b.calendar(a.b.environment(), s)
        self.assertEqual((c['w_count'], c['h_count'], c['recovery_count']),
                         (4500045002, 9000090002, 9015504896))
        self.assertEqual(c['tau'], F('.30829479331708'))
        self.assertGreaterEqual(c['recovery_hold_lower'], c['h']+c['tau'])
        self.assertGreater(c['recovery_rounding_extra'], 0)
        self.assertEqual(c['timer_counter_bits'], 34)
        stale = a.b.calendar(a.b.environment(), a.b.prefetch_service())
        self.assertLess(stale['recovery_hold_lower'], c['h']+c['tau'])

    def test_report_removes_only_saturation_price(self):
        out = json.loads((HERE/'report-r3.json').read_text())
        row = out['recommended_250_64']
        old = json.loads((HERE/'report-r2.json').read_text())['rows']['recommended_250']
        self.assertEqual(row['risk_upper'], old['risk_upper'])
        self.assertEqual(row['resources'], old['resources'])
        self.assertEqual(row['calendar'], old['calendar'])
        self.assertEqual(row['price_bad_probability'], row['risk_upper'])
        self.assertEqual(F(row['full_bus_mission']), F(old['full_bus_mission_without_saturation']))
        self.assertEqual(F(row['full_bus_quiet']), F(old['full_bus_quiet_without_saturation']))
        self.assertGreater(F(row['price']['additional_mission_price']), 0)
        self.assertTrue(row['mathematical_admission'])
        self.assertFalse(row['implemented_and_timed'])
        self.assertTrue(all(v is None for v in out['actual_integrated_bounds'].values()))


if __name__ == '__main__':
    unittest.main()

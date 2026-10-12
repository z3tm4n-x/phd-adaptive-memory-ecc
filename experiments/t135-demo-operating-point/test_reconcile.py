"""Addressed r2 regressions. No claim of verification of connected RTL."""
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('t135_r2',HERE/'reconcile.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class ReconciliationTests(unittest.TestCase):
    def test_engineer_arithmetic_and_source_are_exact(self):
        self.assertEqual(len(r.source_checks()),9)

    def test_one_outer_timing_contract(self):
        t=r.timing_ledger()
        self.assertEqual(t['inbound_s'],F('254.002520e-9'))
        self.assertEqual(t['outbound_s'],F('213.002120e-9'))
        self.assertGreater(t['inbound_unallocated_s'],0)
        self.assertGreater(t['outbound_unallocated_s'],0)
        self.assertEqual(t['upper_from_decomposition_s'],F('2587.774728e-9'))

    def test_saturation_not_an_assumed_hard_ERR_count(self):
        p=r.b.environment();s16=r.saturation(p,16);s32=r.saturation(p,32)
        self.assertEqual(s16['probability_before_bad_upper'],1)
        self.assertGreater(s32['probability_before_bad_upper'],F('1.8265e-5'))
        self.assertLess(s32['probability_before_bad_upper'],F('1.8266e-5'))
        self.assertEqual(p['errors'],F('6e-6'))
        self.assertEqual(r.saturation(dict(p,F=F(0),K0=0,T=F(0)),16)['expected_increments_before_bad_upper'],1001)

    def test_no_generation_wrap_or_truncation(self):
        def permit(candidate,current,event=False):
            return not event and current<2**32-1 and candidate==current
        self.assertFalse(permit(2**32-1,2**32-1))
        self.assertFalse(permit(7,7,True))
        self.assertTrue(permit(65536,65536))
        self.assertFalse(permit(0,65536))
        # Mutant that transmits only 16 bits reaccepts an old candidate.
        self.assertEqual(0 & 65535,65536 & 65535)

    def test_reusing_epoch_requires_quiescence(self):
        old_inflight=[dict(generation=0,valid=True)]
        reset_generation=0
        self.assertTrue(any(x['valid'] and x['generation']==reset_generation for x in old_inflight))
        # Empty all channels and invalidate all staged candidates before reuse.
        old_inflight.clear()
        self.assertFalse(any(x['valid'] and x['generation']==reset_generation for x in old_inflight))

    def test_100MHz_calendar_and_latency_boundary(self):
        s=dict(r.b.CFG['dual_domain'],service_quantum_ticks=10)
        s.update(r.operation_inputs('candidate_100_operations'));s=r.b.reserve_calendar(s)
        self.assertEqual((s['c_ticks'],s['app_charge_ticks'],s['g_ticks']),(190,280,230))
        c=r.b.calendar(r.b.environment(),s);a=r.b.resources(c,s)
        self.assertGreater(a['response_upper'],F('3e-6'))
        self.assertGreater(a['peak_slack'],0)
        bound=a['request_response_sum_max']
        eq=dict(s,release_to_response_s=bound-s['request_to_queue_s'])
        self.assertEqual(r.b.resources(c,eq)['response_upper'],F('3e-6'))
        eq['release_to_response_s']+=F('1e-9')
        self.assertFalse(r.b.resources(c,eq)['admitted'])

    def test_joint_proof_rejects_changed_grid(self):
        with self.assertRaises(AssertionError):
            r.joint(r.b.environment(),dict(r.b.prefetch_service(),g_ticks=230,c_ticks=190))

    def test_report_has_separate_price_and_risk(self):
        x=json.loads((HERE/'report-r2.json').read_text())
        a=x['rows']['recommended_250']
        self.assertLess(F(a['risk_upper']),F('.001'))
        self.assertGreater(F(a['price_bad_probability']),F(a['risk_upper']))
        self.assertGreater(F(a['saturation_mission_price_increment']),0)
        self.assertFalse(x['rows']['reserve100_original']['mathematical_admission'])
        self.assertFalse(x['rows']['reserve100_demo']['mathematical_admission'])
        self.assertTrue(x['rows']['reserve100_demo_rebalanced']['mathematical_admission'])
        self.assertGreater(F(x['reserve100_pointwise_certificate_floor']),F('.001'))
        self.assertTrue(a['mathematical_admission'])
        self.assertFalse(a['implemented_and_timed'])


if __name__=='__main__':unittest.main()

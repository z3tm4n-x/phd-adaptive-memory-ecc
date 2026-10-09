"""Addressed contract/boundary regressions; no new RTL tests or campaign."""
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('t135_calc',HERE/'calculate.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


class ContractTests(unittest.TestCase):
    def test_joint_environment_and_frozen_candidate(self):
        p=c.environment();d=c.environment(True)
        self.assertEqual(d['b']**2*d['T']+(d['B']+d['b'])*d['FS'],d['S2exact'])
        self.assertEqual(d['D'],p['D']);self.assertEqual(d['errors'],p['errors'])
        q=c.frozen_substitution(d)['risk_upper']
        self.assertTrue(F('.00064109224')<q<F('.00064109226'))

    def test_S2_alone_does_not_imply_smaller_FS_or_candidate(self):
        p=c.environment();d=dict(p,S2exact=c.environment(True)['S2exact'])
        a=c.frozen_substitution(d)['risk_upper']
        old=json.loads((c.ROOT/'experiments/t114-two-stage-err/report.json').read_text())['rows'][26]
        self.assertEqual(a,F(old['risk_upper']))

    def test_countdown_partial_first_tick_is_paid(self):
        s=c.prefetch_service()
        for target in (F(90),F(180),F('180.3082861')):
            t=c.timer(target,s);q=s['timer_quantum_ticks']
            self.assertGreaterEqual(t['lower'],target)
            self.assertLess((t['count']-2)*q*c.TM-c.J,target)
            self.assertLess(t['count'],2**34)
            self.assertGreater(t['upper'],t['lower'])

    def test_CDC_sum_boundary_and_overrun(self):
        p=c.environment();s=c.prefetch_service();cal=c.calendar(p,s)
        maximum=c.resources(cal,s)['request_response_sum_max']
        exact=dict(s,release_to_response_s=maximum-s['request_to_queue_s'])
        self.assertEqual(c.resources(cal,exact)['response_upper'],F('3e-6'))
        late=dict(exact,release_to_response_s=exact['release_to_response_s']+F('1e-9'))
        self.assertFalse(c.resources(cal,late)['admitted'])

    def test_slow_path_cannot_be_hidden_after_original_freeze(self):
        p=c.environment();s=c.prefetch_service();cal=c.calendar(p,s)
        bad=dict(s,decision_transport_s=F('1e-6'))
        self.assertLess(c.resources(cal,bad)['gate_slack'],0)
        wide=c.parse_service(c.CFG['dual_domain'])
        self.assertGreater(c.resources(c.calendar(p,wide),wide)['gate_slack'],0)

    def test_extra_CDC_cannot_be_added_to_E(self):
        p=c.environment();s=c.prefetch_service();cal=c.calendar(p,s)
        bad=dict(s,E_s=s['E_s']+F('1e-9'))
        self.assertLess(c.resources(cal,bad)['E_margin_slack'],0)

    def test_missing_times_are_not_zero_or_clock_scaling(self):
        s=dict(c.CFG['dual_domain'],R_s=None)
        with self.assertRaises(ValueError):c.parse_service(s)
        with self.assertRaises(ValueError):c.parse_service({'service_quantum_ticks':10})

    def test_incomplete_observed_write_rejected(self):
        s=dict(c.CFG['dual_domain'],observed_write32_s=c.CFG['dual_domain']['E_s'])
        with self.assertRaises(ValueError):c.parse_service(s)

    def test_conditional_reserve_calendar_rounding(self):
        # Algebraic sentinel only: exact old durations on a 10 ns service grid.
        # It is NOT a proposed/measured 100 MHz implementation.
        s=dict(c.CFG['dual_domain'],service_quantum_ticks=10)
        r=c.reserve_calendar(s);cal=c.calendar(c.environment(),r)
        self.assertEqual(r['c_ticks'],170);self.assertEqual(r['app_charge_ticks'],240)
        self.assertEqual(r['g_ticks'],210)
        self.assertGreaterEqual(c.resources(cal,r)['placement_slack'],0)
        self.assertGreaterEqual(c.resources(cal,r)['E_margin_slack'],0)

    def test_full_FAST_cost_is_available_without_price_availability(self):
        p=c.environment();s=c.prefetch_service();cal=c.calendar(p,s)
        allerr=s['E_s']/(s['g_ticks']*c.TM)
        peak=c.resources(cal,s)['whole_bus_peak']
        self.assertGreater(peak,allerr)
        self.assertLess(peak,F('.8'))
        self.assertGreater(allerr,F('.75'))

    def test_slow_recovery_rounding_is_paid_once_in_price(self):
        p=c.environment();s=c.prefetch_service();cal=c.calendar(p,s)
        extra=cal['recovery_rounding_extra']
        self.assertGreater(extra,F('6e-6'));self.assertLess(extra,F('6.3e-6'))
        self.assertEqual(cal['recovery_hold_upper'],cal['h_upper']+cal['tau']+extra)
        self.assertGreaterEqual(cal['recovery_hold_lower'],cal['h']+cal['tau'])
        r=c.pay_recovery_rounding(dict(mission_upper_intercept=F(0),quiet_upper_intercept=F(0)),p,cal,s)
        expected=s['E_s']/(cal['g']*c.TM)*1001*extra/p['T']
        self.assertEqual(r['additional_mission_price'],expected)
        self.assertEqual(r['additional_quiet_price'],expected/F('.9'))
        self.assertGreater(expected,0)


if __name__=='__main__':unittest.main()

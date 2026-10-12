"""Addressed r4 arithmetic and mathematical counterexamples, not RTL proof."""
from fractions import Fraction as F
import importlib.util
import itertools
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('t135_integrated_tests',HERE/'integrated_check.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


class IntegratedContractTests(unittest.TestCase):
    def test_engineer_bounds_repeated_read_only(self):
        data,pins=a.source_checks()
        self.assertEqual(len(pins),10)
        self.assertEqual(data['generation']['mission_fast_edges_upper'],78894788947889481)

    def test_endpoint_placement_includes_app_prepare_cut(self):
        data,_=a.source_checks()
        s=dict(a.b.prefetch_service(),ERR_or_loss_to_rule_s=F('10e-6'))
        t=a.timing(data,s)
        self.assertEqual(t['inbound_for_frame_wait_ns'],F('177.001760'))
        self.assertGreater(t['inbound_for_frame_wait_remaining_ns'],0)
        self.assertGreater(t['outbound_remaining_ns'],0)
        self.assertGreater(t['candidate_remaining_ns'],0)

    def test_history_bounds_account_for_bunched_loss(self):
        data,_=a.source_checks();h=data['history']
        self.assertEqual(h['full_flag_occupancy_upper'],275)
        self.assertEqual(h['loss_transitions_mission_max'],2002)
        self.assertGreater(h['processed_history_ns'],5000)
        self.assertLess(h['last_history_to_fresh_applicable_including_loss_CDC_ns'],10000)

    def test_ghost_cache_invariant_and_missing_invalidation_counterexample(self):
        # Exhaust the local abstract transition cases; the text gives induction
        # for arbitrary width/lines. This test does NOT replace engineer RTL/PDR.
        for G,valid,install,event in itertools.product(range(3),(False,True),range(3),(False,True)):
            ghost=G if valid else 0
            after_G=G+int(event)
            after_valid=valid or install==G
            after_ghost=G if install==G else ghost
            if event:after_valid=False
            self.assertTrue(not after_valid or after_ghost==after_G)
        # Explicit counterexample when the invalidate transition is removed.
        cached_low,cached_ghost,new_generation=True,7,8
        self.assertFalse(not cached_low or cached_ghost==new_generation)

    def test_same_risk_and_explicit_recovery_price(self):
        new=json.loads((HERE/'report-r4.json').read_text())['rows']['selected_r3_original']
        old=json.loads((HERE/'report-r3.json').read_text())['recommended_250_64']
        self.assertEqual(new['risk_upper'],old['risk_upper'])
        self.assertEqual(new['calendar'],old['calendar'])
        self.assertEqual(new['resources'],old['resources'])
        for scope in ('quiet','mission'):
            delta=F(new['recovery_transition_price'][scope])
            self.assertGreater(delta,0)
            self.assertLess(delta,F('3e-11'))
            self.assertEqual(F(new['full_bus_'+scope]),F(old['full_bus_'+scope])+delta)

    def test_certificate_floor_is_not_physical_lower_risk(self):
        out=json.loads((HERE/'report-r4.json').read_text())
        fl=out['certificate_floor']
        self.assertLess(F(fl['g192_placement_slack_s']),0)
        self.assertLess(F(fl['relative_slack_ceiling']),F('.04'))
        self.assertIn('not physical',fl['scope'])
        for name,r in out['rows'].items():
            if name.endswith('original'):
                self.assertGreaterEqual(F(r['risk_upper']),F(fl['value']))

    def test_declared_alias_map_is_bijective_not_physical_evidence(self):
        W=524288
        for w in (0,1,173,W-1):
            for alias in (0,1):
                address=2*w+alias
                self.assertEqual(divmod(address,2),(w,alias))
                self.assertLess(address,2*W)
        out=json.loads((HERE/'report-r4.json').read_text())['conditional_address_map']
        self.assertIsNone(out['actual_chip_mapping'])
        self.assertFalse(out['D_or_ERR_requalified'])

    def test_demo_is_existing_strict_subset_not_new_main(self):
        out=json.loads((HERE/'report-r4.json').read_text())
        d=out['demo_exposure']
        self.assertEqual(F(d['original_peak_equivalent_s']),115776)
        self.assertLess(F(d['demo_peak_equivalent_s']),58000)
        self.assertIsNone(d['physical_support'])
        self.assertFalse(d['author_approved'])
        self.assertLess(F(out['rows']['existing_demo_250_50']['risk_upper']),F('.000636'))


if __name__=='__main__':unittest.main()

"""Directed checks of resource boundaries, not a repeat of old risk series."""
from fractions import Fraction as F
from math import gcd
import unittest

import resource_preflight as r


class ResourceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs, cls.cfg = r.load()

    def test_real_slot_phases_and_full_permutation_at_each_volume(self):
        cal = self.cfg['calendar']
        for b in self.inputs['mandatory_and_control_useful_bytes']:
            W = b // 4
            self.assertEqual(gcd(3, W), 1)
            for j in (0, 1, 7, 8, W-1, W, 3*W+7):
                self.assertEqual(r.slot(j+W, cal)-r.slot(j, cal), W*196)
            self.assertEqual(r.slot(W-1, cal), W*196-420)
            self.assertEqual(r.slot(8, cal)-r.slot(7, cal), 420)

    def test_count_upper_covers_literal_edges_with_clock_and_phase(self):
        # Independent small literal enumeration; no probability/model input.
        cfg = r.configuration(self.cfg, 4*32)
        J = F(cfg['service']['operation_endpoint_span_ns'])
        for scale in (F('0.99999'), F('1.00001')):
            for offset in (-J, F(0), J, F(417)):
                for duration_ns in (1, 164, 1568, 6001, 12544, 50177):
                    cfg['mission_s'] = F(duration_ns, r.NS)
                    literal = sum(0 <= scale*r.slot(j,cfg['calendar'])+offset < duration_ns
                                  for j in range(512))
                    self.assertLessEqual(literal, r.cmp.read_bounds(cfg,1)['upper'])

    def test_necessary_vs_sufficient_application_and_reserved_slots(self):
        _, original = r.load()
        rows = [r.preflight(self.cfg, b) for b in self.inputs['mandatory_and_control_useful_bytes']]
        self.assertEqual(self.cfg, original)  # volume change cannot modify source config
        for row in rows:
            a, z, c = row['application'], row['resource'], row['calendar']
            self.assertEqual(a['completed_reads_lower'], a['offered_reads']-1)
            nominal = F(a['offered_reads']*68, self.cfg['mission_s']*r.NS)
            self.assertLess(a['serial_mission_lower'], nominal)
            self.assertLess(nominal, a['serial_mission_upper'])
            self.assertGreater(z['available_serial_upper_for_necessary_exclusion'],
                               z['sufficient_serial_average_remainder_after_app_upper'])
            self.assertEqual(z['available_serial_upper_for_necessary_exclusion']+a['serial_mission_lower'], F(4,5))
            self.assertFalse(c['app_slots_reallocated'])
            self.assertTrue(row['initialization']['before_t0'])
            self.assertTrue(row['initialization']['not_subtracted_from_in_mission_resource'])
            self.assertIsNone(row['fixed_class_excluded'])
        self.assertEqual(len({x['resource']['peak_including_full_reserved_management_slot'] for x in rows}),1)
        self.assertEqual(rows[-1]['calendar']['nominal_minimum_full_pass_cycle_ns'],
                         8*rows[0]['calendar']['nominal_minimum_full_pass_cycle_ns'])


if __name__ == '__main__':
    unittest.main()

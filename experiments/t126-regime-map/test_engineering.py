import copy
from fractions import Fraction as F
import json
import unittest

import bounds
import checker
import engineering as e


class EngineeringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=e.build()
        cls.report=e.serial(cls.raw)

    def test_independent_all_rows(self):
        checker.check_all(self.report)

    def test_36_full_range(self):
        rows=[x for x in self.raw['rows'] if x['family']=='R0B_grid']
        self.assertEqual(len(rows),36)
        self.assertTrue(all(x['full_tick_range']==[1,2**64-1] for x in rows))

    def test_per_bit_scaling(self):
        rows=[x for x in self.raw['rows'] if x['family']=='R0B_grid']
        for key in ['B','b','FS']:
            self.assertEqual(len({x[key]/(x['n']*x['W']) for x in rows}),1)

    def test_resource_minimum_not_busy(self):
        for r in self.raw['rows']:
            if r['family']!='R0B_grid':continue
            c=F(r['n'],r['R_eff_bit_s'])
            self.assertGreater(r['P_min'],r['W']*c)
            self.assertTrue(r['resource_at_boundary']['peak_ok'])

    def test_phi_lower_rejects_initial_and_empty_FS(self):
        for kw in [{'start':False},{'Scap':F(500)},{'Fcap':F(900)}]:
            self.assertIsNone(checker.plateau_reference(F(1000),F(4),F(1),F(300),**kw))
        self.assertIsNone(checker.plateau_reference(F(1000),F(4),F(1),F(0)))

    def test_independent_caps_and_constant_limit(self):
        for fc,sc,ec in [(None,None,None),(F(1150),None,None),(None,F(1750),None),(None,None,F(150))]:
            ref=checker.plateau_reference(F(1000),F(4),F(1),F(300),fc,sc,ec)
            got=bounds.plateau(1000,4,1,300,F_cap=fc,S2_cap=sc,excess_cap=ec)
            self.assertEqual(ref,got['L'])
        self.assertEqual(checker.plateau_reference(F(1000),F(1),F(1),F(0)),1000)

    def test_sentinel_mixed_term(self):
        r=copy.deepcopy(self.report)
        row=next(x for x in r['rows'] if x['family']=='CY_new_input')
        row['S2_mixed']='0'
        with self.assertRaises(AssertionError):checker.check_all(r)

    def test_sentinel_unknown_not_zero(self):
        r=copy.deepcopy(self.report)
        next(x for x in r['rows'] if x['family']=='CY_new_input')['Dstar']='0'
        with self.assertRaises(AssertionError):checker.check_all(r)

    def test_sentinel_upper_failure_not_impossibility(self):
        r=copy.deepcopy(self.report)
        next(x for x in r['rows'] if x['family']=='R0B_grid')['status']='period_class_excluded'
        with self.assertRaises(AssertionError):checker.check_all(r)

    def test_sentinel_wrong_phase_edge(self):
        r=copy.deepcopy(self.report)
        r['necessary_checks'][0]['constant_price_lower']=str(F(r['necessary_checks'][0]['constant_price_lower'])+F('1e-9'))
        with self.assertRaises(AssertionError):checker.check_all(r)

    def test_sentinel_input_hash(self):
        with self.assertRaises(ValueError):e.verify_blob(b'altered source',next(iter(e.PINS['t127_git_blobs'].values())))

    def test_sentinel_quiet_not_mission(self):
        r=copy.deepcopy(self.report)
        row=next(x for x in r['rows'] if x['family']=='T114_control' and x['constant_quiet_export'])
        row['constant_quiet_upper']=row['constant_mission_upper']
        with self.assertRaises(AssertionError):checker.check_all(r)

    def test_new_four_shields_one_example(self):
        rows=[x for x in self.raw['rows'] if x['family']=='CY_new_input']
        self.assertEqual(len(rows),36)
        self.assertEqual(len({r['shield_g_cm2'] for r in rows}),4)
        self.assertEqual(len({r['example_group'] for r in rows}),1)

    def test_clock_and_write_full_calendar(self):
        p=e.t114.old.environment(e.t114.old.HANDOFF['rows'][0])
        profile=dict(e.t114.CFG['profiles'][1]); growth=e.t114.CFG['growth_classes'][0]
        profile['g_ticks']=192
        old=e.t114.resource(e.t114.calendar(p,profile,1,growth))
        self.assertLess(old['placement_slack'],0)
        profile['g_ticks']=196
        cal=e.t114.calendar(p,profile,1,growth);new=e.t114.resource(cal)
        self.assertGreater(new['placement_slack'],0)
        self.assertGreater(cal['Ps'],p['W']*e.t114.T['E'])
        self.assertEqual(cal['app'],F('217.002160e-9'))

    def test_finite_edges(self):
        # Independent direct occupancy of two partial blocks in [0,H].
        W,c,P,H=3,F(2),F(11),F(17)
        phase=[F(0),F(11,3),F(22,3)]
        busy=sum((max(F(0),min(H,t+c)-max(F(0),t))
                  for ph in phase for k in range(-1,3) for t in [ph+k*P]),F(0))
        self.assertGreaterEqual(busy/H,max(F(0),W*c/P-2*W*c/H))
        self.assertLessEqual(busy/H,W*c/P+2*W*c/H)


if __name__=='__main__':unittest.main()

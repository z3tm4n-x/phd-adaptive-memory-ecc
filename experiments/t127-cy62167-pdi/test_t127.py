import math
import unittest
import calculate as c
import checker


class QualificationTests(unittest.TestCase):
    def test_no_double_count(self):
        self.assertEqual(c.sum_components(1,2),3)
        with self.assertRaisesRegex(ValueError,'already contains HEP'):
            c.sum_components(1,2,extra_hep=.2)

    def test_unknown_not_zero_sentinel(self):
        checker.validate_unknown_upper(None,None)
        with self.assertRaisesRegex(ValueError,'Unknown Dstar'):
            checker.validate_unknown_upper(.0007,None)

    def test_mixed_term_and_normalization(self):
        exposure,bg,solar,mixed,total=c.conditional_square(.0001,.2)
        self.assertEqual(c.BITS,524288*38)
        self.assertEqual(exposure,115776*.2)
        self.assertAlmostEqual(mixed,2*.0001*exposure)
        self.assertGreater(total,bg+solar)

    def test_guard_wrong_mixed_direction(self):
        _,bg,solar,mixed,total=c.conditional_square(.01,.2)
        self.assertFalse(math.isclose(total,bg+solar-mixed,rel_tol=1e-12))

    def test_mapping_energy_not_double_BEOL(self):
        t=c.transport.RangeTable()
        incident=float(t.inverse(3+t.range(1.)))
        self.assertAlmostEqual(float(t.residual(incident,3)),1.,places=9)
        self.assertAlmostEqual(float(c.transport.sigma([1.])[0]),1.27e-9,delta=1e-22)

    def test_resource_rejects_raw_Wc(self):
        cal,r=c.service_case()
        self.assertGreater(r['P_min_s'],524288*164e-9)
        self.assertEqual(r['g_ticks'],196)
        self.assertFalse(next(x for x in r['candidates'] if x['g_ticks']==192)['passes_declared_calendar_resource_test'])
        self.assertLessEqual(r['joint_delay_upper_s'],3e-6)
        self.assertLessEqual(r['application_at_rate_limit_peak'],.8)

    def test_missing_D_leaves_upper_unknown(self):
        cal,_=c.service_case()
        out=c.fixed_arithmetic(.00015,.245,6940,28366,cal['Ps'],cal['Ps_min'])
        self.assertIsNone(out['Q_conditional_upper'])
        self.assertGreater(out['initial_term'],0)
        self.assertGreater(out['aperture_cross'],0)

    def test_one_example_grid(self):
        self.assertEqual(c.CFG['shield_g_cm2'],[2.5,3.,3.5,4.])
        self.assertEqual(c.CFG['example_group'],'CY62167_full38_shield_curve')
        self.assertTrue(all(v is None for v in c.CFG['full38_physical_Dstar_by_shield'].values()))

    def test_empirical_population_not_normative(self):
        p,_=c.population()
        self.assertEqual(p['strict_GOST_fluence_filtered_count'],131)
        self.assertFalse(p['population_identity'])
        self.assertIsNone(p['revised_nbar'])

    def test_reject_4pi_fluence_mutation(self):
        g=c.gost_rows()
        row=next(r for r in g if r['shield_g_cm2']==3. and r['response']=='pdi')
        scalar=checker.independent_gost_fold(3.,'fluence')
        self.assertLess(abs(row['N_solar_protons']/scalar-1),.001)
        self.assertGreater(abs(4*math.pi*row['N_solar_protons']/scalar-1),.001)


if __name__=='__main__':
    unittest.main()

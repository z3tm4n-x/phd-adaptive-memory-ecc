"""Directed checks for epsilon transfer, budgets, counts and comparison direction."""
import unittest,json
from fractions import Fraction as F
from model import load,setup,NS,count_reads,risk_base,exposure,poisson_K,excursion,HERE,Series
import run

class SliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=run.calculate(); _,i,cfg,cases=load();cls.c=setup(i,cfg);cls.cases=cases
    def test_only_epsilon_changes(self):
        self.assertEqual([F(x['fixed']['epsilon']) for _,x in self.cases],[F('.1'),F('.01'),F('.001'),F('.0001')])
        self.assertFalse(self.result['direction_A_closed'])
    def test_fixed_full_budget_and_next_integer(self):
        c=self.c
        for r in self.result['rows']:
            f=r['fixed']; eps=r['epsilon'];k=f['k']
            self.assertLessEqual(f['Q_upper'],eps)
            self.assertGreater(risk_base(c,c['fast'],k+1)+c['delta0'],eps)
            self.assertEqual(f['budget']['alpha'],0);self.assertEqual(f['budget']['deltaC'],0)
    def test_nonlinear_point_one_and_OFF(self):
        r=self.result['rows'][0];lo=r['lower_bounds'];H=F(lo['H_exact_enclosure']['lower'])
        self.assertGreater(H,F('.105'))
        self.assertGreater(H-lo['linear_H_not_used'],F('.005'))
        for r in self.result['rows']: self.assertTrue(r['lower_bounds']['OFF_excluded'])
    def test_three_mandatory_adaptive_points_and_budget(self):
        c=self.c
        for row in self.result['rows'][:3]:
            a=row['adaptive'];b=a['budget'];N=a['N']
            self.assertLessEqual(a['Q_upper'],row['epsilon'])
            self.assertEqual(N*a['alpha'],b['alpha_total'])
            self.assertEqual(N*a['zeta'],b['zeta_total'])
            self.assertEqual(N*a['beta'],b['extension_total'])
            self.assertLessEqual(a['rare_bill'],a['beta'])
            self.assertLessEqual(a['residue_tail'],a['zeta'])
            self.assertEqual(a['k_rare']%a['k_base'],0)
            self.assertLess(a['learning_and_reserved_epochs_upper_s'],c['T'])
            self.assertIsNone(a['admission_law']);self.assertIsNone(a['control_CPU_energy_WCET'])
            self.assertTrue(a['finite_budget_never_refilled'])
    def test_exposure_exact_direct_sum_same_candidate(self):
        c=self.c
        for row in self.result['rows'][:3]:
            a=row['adaptive'];ex=a['group'];u=c['R']/2
            direct=ex['w']*((ex['M']-ex['q'])*c['b']+sum(max(F(0),u-c['g']*(ex['span']+k*ex['a0'])) for k in range(ex['q']+1,ex['M']+1)))
            self.assertEqual(direct,ex['mu'])
            self.assertLess(a['C_max'],F(a['score_lower']))
            self.assertGreaterEqual(a['C_max']+1,F(a['score_lower']))
    def test_count_edges_without_float_rounding(self):
        c=dict(self.c,W=16);cycle=16*c['cal']['g_ticks'];k=3
        starts=[n*k*cycle+j//8*c['cal']['frame_ticks']+j%8*c['cal']['c_ticks'] for n in range(3) for j in range(16)]
        for s in starts:
            for dx in (F(-1,2),0,F(1,2)):
                self.assertEqual(count_reads(s+dx,c,cycle,k),sum(t<s+dx for t in starts))
    def test_comparisons_use_correct_bounds_and_remain_separate(self):
        for row in self.result['rows'][:3]:
            a=row['adaptive'];f=row['fixed'];lo=row['lower_bounds']
            for cls in ('constant','schedule'):
                x=row['comparisons'][cls]
                self.assertEqual(x['saving_ceiling_for_this_family_vs_optimum_using_feasible_member'],1-a['mandatory_expected_bus_lower']/f['bus_upper'])
                self.assertEqual(x['guaranteed_saving_from_sufficient_A_upper_and_class_lower'],1-a['hard_bus_upper']/lo[cls+'_bus_lower'])
                self.assertFalse(x['proved_optimum'])
    def test_optional_uncertified_not_impossible(self):
        a=self.result['rows'][3]['adaptive']
        self.assertEqual(a['status'],'NOT_CERTIFIED_BY_THIS_FAMILY')
        self.assertNotIn('impossible',a['reason'].lower())
    def test_shared_app_not_zero_or_double_charged(self):
        c=self.result['shared_app_init'];self.assertEqual(c['application_reads'],315569688607)
        self.assertTrue(c['ECC_included_once']);self.assertGreater(c['init_bus_upper_fraction'],0)
        self.assertIsNone(self.result['observation_cost']['extra_veto_expected'])
    def test_prepaid_series_invalid_late_and_restore_no_refund(self):
        a=self.result['rows'][0]['adaptive']; series=Series(a)
        r1=series.step(0,valid=False)
        r2=series.step(0)
        r3=series.step(0,timely=False)
        r4=series.step(a['C_max']+1)
        self.assertEqual([r['admit'] for r in (r1,r2,r3,r4)],[False,True,False,False])
        self.assertEqual(r4['alpha_spent'],4*a['alpha'])
        self.assertEqual(series.saved_passes,a['multiplier']-1)
        length=a['group']['M']*a['k_base']+a['k_rare']
        self.assertEqual(r4['epoch_end_block'],1+4*length)
        self.assertFalse(r4['clean_reset'])
        for _ in range(a['N']-4): series.step(0,valid=False)
        with self.assertRaises(ValueError): series.step(0)
    def test_retained_losses_allow_zero_success_for_selected_family(self):
        for row in self.result['rows'][:3]:
            x=row['adaptive']['all_attempts_invalid_loss_witness']
            self.assertTrue(x['possible']);self.assertLessEqual(x['episodes'],1001)
            self.assertLessEqual(x['restores'],1000);self.assertLess(x['outage_seconds'],F('31557.6'))

if __name__=='__main__': unittest.main()

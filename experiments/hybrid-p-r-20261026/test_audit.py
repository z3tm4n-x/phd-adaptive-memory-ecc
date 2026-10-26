from fractions import Fraction as F
import math
import unittest
import audit as a


class TargetedChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=a.calculate()
        cls.inp,cls.cfg=a.load()

    def test_one_full_pass_and_real_application_slots(self):
        cal=self.cfg['calendar']; W=self.cfg['words']; r=self.result['service']
        self.assertEqual(len({(3*j)%W for j in range(W)}),W)
        self.assertTrue(all(a.start_ticks(j,cal)%cal['frame_ticks']<cal['application_grant_phase_ticks'] for j in range(W)))
        self.assertGreater(r['control_E_slack_ns'],0)
        self.assertGreater(r['drain_after_last_release_lower_ns'],r['source_to_fresh_upper_ns'])
        self.assertEqual(r['proposed_block_ticks']%cal['frame_ticks'],0)

    def test_late_parent_breaks_literal_auxiliary_without_second_hit(self):
        r=self.result['interface_witness']
        self.assertEqual(r['parents'],1)
        self.assertEqual(r['maximum_error_weight'],1)
        self.assertFalse(r['physical_A'])
        self.assertFalse(r['T36_defined_second_hit_break'])
        self.assertEqual([x['real_pass_C'] for x in r['history']],[1,1])
        self.assertEqual([x['literal_T36_aux_C'] for x in r['history']],[1,0])
        self.assertEqual([x['residual_real_errors'] for x in r['history']],[1,0])

    def test_exposure_piecewise_matches_integral_at_boundaries(self):
        for P in (F(0),F(1),F(3)):
            for t in (P,P+1,P+7):
                for g in (F(0),F(1,3),F(2)):
                    for v in (F(0),g*P,g*t,g*P+F(1,7),F(20)):
                        reference=v*(t-P) if not g else (max(F(0),v-g*P)**2-max(F(0),v-g*t)**2)/(2*g)
                        self.assertEqual(a.mu(v,t,P,g),reference)
        with self.assertRaises(ValueError): a.mu(F(1),F(1),F(2),F(1))

    def test_quantile_has_independent_tail_witness(self):
        g=self.result['t36_gate']; M=g['residual_poisson_mean']; z=g['residue_zeta_per_step']
        self.assertEqual(g['K_star'],4)
        # Falling-factorial Markov bound for P[N>=5], independent of CDF sum.
        self.assertLessEqual(M**5/math.factorial(5),z)
        # P[N=4] alone already excludes Q=3; lower exponential bound exp(-M)>=1-M.
        self.assertGreater((1-M)*M**4/math.factorial(4),z)
        self.assertEqual(a.poisson_quantile(F(0),z)['Q'],0)

    def test_known_and_unknown_mass_share_one_old_cap(self):
        e=self.result['environment']; p=self.inp['proposed_environment']['p']
        self.assertGreater(e['known_amplitude'],0)
        self.assertGreater(e['residual_R'],0)
        self.assertGreater(e['residual_g'],0)
        self.assertEqual(e['array_background']+e['known_amplitude']+e['residual_R'],e['array_peak'])
        self.assertEqual(e['known_extra_mass']+e['residual_F_r'],e['array_solar_mass'])
        witness=e['translated_r_witness']
        self.assertEqual(e['residual_R']*(witness['rise_s']/2+witness['plateau_s']),e['residual_F_r'])
        self.assertGreater(witness['latest_onset_s'],0)
        self.assertTrue(p['known_exactly_to_both'])

    def test_reserve_obstruction_does_not_depend_on_chosen_residue_tail(self):
        g=self.result['t36_gate']; eps=F(self.inp['fixed']['epsilon'])
        self.assertGreater(g['any_period_pair_floor'],eps/2)
        self.assertGreater(g['V_pair_term'],eps/2)
        self.assertGreater(g['V_residual_term'],0)
        self.assertEqual(g['V_total'],g['V_pair_term']+g['V_residual_term'])
        self.assertFalse(g['reserve_passes'])
        self.assertFalse(g['optimistic_K0_reserve_passes'])

    def test_no_inadmissible_zero_history_is_promoted_to_pilot(self):
        g=self.result['t36_gate']
        self.assertIsNone(g['reachable_informative_history'])
        self.assertIsNone(g['admissible_relaxation'])
        self.assertTrue(all(not r['zero_count_can_lower_B'] for r in g['actions']))
        self.assertTrue(all('NOT_EVALUATED' in r['actual_admission'] for r in g['actions']))

    def test_full_horizon_shared_budget_and_nonzero_unknown_price(self):
        g=self.result['t36_gate']; cost=self.result['horizon_cost']; fixed=self.inp['fixed']
        self.assertEqual(cost['horizon_s'],315576000)
        self.assertEqual(g['e0'],F(fixed['lifetime_other_budget'])+F(self.inp['diagnostic']['alpha_star'])+F(self.inp['diagnostic']['zeta_star']))
        self.assertEqual(g['gamma']+g['delta'],F(fixed['epsilon']))
        self.assertGreater(g['N_full_mission'],10**9)
        self.assertTrue(cost['continued_after_hidden_A'])
        self.assertTrue(cost['full_started_terminal_pass_paid'])
        self.assertEqual(cost['initial_encodes'],fixed['words'])
        self.assertEqual(cost['application_write_count'],0)
        self.assertGreater(cost['common_ECC_nominal'],0)
        self.assertGreater(cost['initial_core_upper'],0)
        self.assertEqual(cost['unknown_costs'],self.inp['unknown_costs'])
        self.assertTrue(all(value is None for value in cost['unknown_costs'].values()))
        self.assertGreater(cost['rates_per_s']['logical_counter_increments_hard'],0)
        self.assertIsNone(cost['physical_or_hybrid_Q'])
        self.assertFalse(self.result['old_Q_recomputed'])

    def test_last_pass_ceil_is_sufficient_without_resetting_time(self):
        cost=self.result['horizon_cost']; P=self.result['service']['proposed_P_lower_s']
        n=cost['full_passes_upper']; T=cost['horizon_s']
        self.assertGreaterEqual(n*P,T)
        self.assertLess((n-1)*P,T)
        self.assertEqual(cost['reads_upper'],n*self.inp['fixed']['words'])


if __name__=='__main__': unittest.main()

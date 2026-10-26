"""Directed verification of the new pilot, not a replay of old campaigns."""
from fractions import Fraction as F
import os
import unittest
from sources import load,bindings
import run,pilot,cost,risk

class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.export=os.environ.get('PILOT_HISTORICAL_ROOT')
        _,cls.inp,cls.cfg,cls.hist=load(cls.export)
        cls.result=run.calculate(cls.export)
        cls.cases={c['name']:c for c in cls.result['branches']}

    def test_four_registered_branches(self):
        self.assertEqual([self.cases[n]['branch'] for n in pilot.CASES],list(pilot.CASES))
        self.assertEqual([self.cases[n]['next_period_blocks'] for n in pilot.CASES],[12000,2,2,2])
        for c in self.cases.values():
            self.assertEqual(c['attempted_used_pass_counts'],119989)
            self.assertEqual(c['uncounted_tail'],11)
            self.assertEqual(c['scheduled_queries'],1)
            self.assertEqual(c['queries_after_restore'],0)
            self.assertEqual(c['alpha_reserved'],F('1e-4'))

    def test_registered_cutoff_not_exponential_rejection(self):
        c=pilot.run_case('admit',self.inp,self.cfg,self.hist,count_override=3)
        self.assertTrue(c['admit'])
        self.assertFalse(self.cases['count_reject']['admit'])
        score=self.result['risk']['exact']['log_test_lower_C3']
        self.assertGreater(score-1,F('9.22'))  # C=4 still passes this numerical score

    def test_loss_and_restore_sticky_until_single_query(self):
        c=self.cases['invalid']
        self.assertTrue(c['invalid'])
        self.assertEqual(c['checkpoints'][-1]['processed_G'],1)
        self.assertTrue(c['checkpoints'][-1]['invalid'])
        self.assertTrue(c['no_state_phase_or_risk_reset'])
        self.assertEqual(c['statistical_comparisons'],0)
        self.assertEqual(c['certified_used_pass_counts'],0)

    def test_tail_extra_E_allowed_but_tail_loss_invalid(self):
        extra=pilot.run_case('admit',self.inp,self.cfg,self.hist,guard_action=risk.USED+1)
        loss=pilot.run_case('admit',self.inp,self.cfg,self.hist,loss_action=risk.USED+1)
        self.assertTrue(extra['admit'])
        self.assertEqual(extra['fixture_counts']['extra_guard_reads'],1)
        self.assertTrue(loss['invalid'])
        self.assertFalse(loss['admit'])

    def test_used_extra_E_invalidates_group(self):
        c=pilot.run_case('admit',self.inp,self.cfg,self.hist,guard_action=1)
        self.assertTrue(c['invalid'])
        self.assertIn('extra E outside mandatory scan',c['reasons'])

    def test_service_failure_is_not_safe_invalid(self):
        c=pilot.run_case('admit',self.inp,self.cfg,self.hist,pending=True,incomplete=True)
        self.assertFalse(c['certificate_applicable'])
        self.assertEqual(c['branch'],'service_contract_violation')
        self.assertFalse(c['admit'])

    def test_empty_wire_requires_external_prefix(self):
        _,_,close=bindings(self.hist)
        args=dict(W=self.inp['fixed']['words'],calendar=self.cfg['calendar'],service=self.cfg['service'],
            scan_start=0,previous_decision=0,decision_tick=25701088,entry_G=0,
            current_G=None,processed_G=0,prefix_certificate=False)
        self.assertTrue(close([],**args)['invalid'])
        self.assertTrue(close([],**dict(args,current_G=1,prefix_certificate=True))['invalid'])
        self.assertEqual(close([],**dict(args,current_G=0,prefix_certificate=True))['C'],0)

    def test_late_cannot_cancel_base_or_retry(self):
        c=self.cases['late']; block=self.result['risk']['timing']['block_ticks']
        self.assertGreater(c['ready_tick'],c['deadline_tick']+block)
        self.assertFalse(c['admit'])
        self.assertEqual(c['queries_after_extension'],0)

    def test_residual_is_not_reset_and_same_parent_can_repeat(self):
        w=self.result['weak_E_witness']
        self.assertEqual((w['parent_count'],w['repair_transactions']),(1,2))
        self.assertEqual((w['residual_at_query'],w['residual_after_next_E']),(1,0))
        self.assertLess(w['first_release_tick'],w['query_tick'])
        self.assertLess(w['query_tick'],w['next_main_visit_tick'])

    def test_calendar_edges_against_direct_enumeration(self):
        cal=self.cfg['calendar']; W=16; block=W*cal['g_ticks']+7*cal['frame_ticks']
        starts=[2*n*block+j//8*cal['frame_ticks']+j%8*cal['c_ticks'] for n in range(4) for j in range(W)]
        for start in starts:
            for eps in (F(-1,2),F(0),F(1,2)):
                t=start+eps
                self.assertEqual(cost.scheduled_reads_before(t,W,cal,block),sum(x<t for x in starts))

    def test_extension_saves_exact_scans_and_keeps_terminal_phase(self):
        c=self.result['cost']['calendar']; W=self.inp['fixed']['words']; cal=self.cfg['calendar']
        block=self.result['risk']['timing']['block_ticks']; end=(2*risk.M+risk.RARE+1)*block
        for t in (end,end+2*block,F(self.inp['fixed']['mission_s'])*10**9):
            diff=cost.read_count_fast(t,W,cal,block)-cost.read_count_fast(t,W,cal,block,True)
            self.assertEqual(diff,5999*W)
        self.assertEqual(c['saved_main_reads_if_admitted'],786300928)
        paths=self.result['cost']['branch_paths']
        self.assertEqual(paths[1]['main_reads_nominal']-paths[0]['main_reads_nominal'],786300928)
        for p in paths:
            self.assertEqual(p['startup_reads']+p['learning_reads']+p['remaining_reads'],p['main_reads_nominal'])

    def test_cost_counts_whole_T_after_hidden_A(self):
        c=self.result['cost']; cal=self.cfg['calendar']; W=self.inp['fixed']['words']
        block=self.result['risk']['timing']['block_ticks']; T=F(self.inp['fixed']['mission_s'])*10**9
        A=F(1,10)*10**9
        before=cost.read_count_fast(A,W,cal,block)
        total=cost.read_count_fast(T,W,cal,block)
        self.assertGreater(total-before,1000*before)
        self.assertEqual(total,c['calendar']['nominal_base_started_reads'])
        self.assertTrue(c['expected_upper']['no_stop_after_A'])
        self.assertLessEqual(c['calendar']['physical_base_started_reads_lower'],total)
        self.assertGreaterEqual(c['calendar']['physical_base_started_reads_upper'],total)

    def test_full_cost_not_just_saved_reads(self):
        c=self.result['cost']; coeff=c['expected_upper']['coefficients']
        self.assertEqual(coeff['repair_upper_before_min_if_deltaC_requirement'],
            2*coeff['Fparent']+coeff['U_joint_if_deltaC_requirement']*coeff['Nhard'])
        self.assertIn('delta_exec*Nhard',c['expected_upper']['read_formula'])
        self.assertIsNone(c['resource_vector']['CPU_ns_per_operation'])
        self.assertIsNone(c['resource_vector']['energy_J_per_operation'])
        self.assertIsNone(c['expected_upper']['variables']['delta_C'])
        self.assertFalse(c['full_mean_gain_claimed'])
        for p in c['branch_paths']:
            self.assertGreater(p['path_nominal_full_core_s'],p['path_nominal_protection_core_s'])

    def test_shared_risk_and_runtime_obligations(self):
        r=self.result['risk']; q=r['exact']['Q_upper_if_example_requirement_met']
        self.assertLess(q,F('.001'))
        self.assertTrue(r['conditional_Q_not_branch_conditioned'])
        self.assertFalse(r['budgets']['hardware_probability_established'])
        self.assertEqual(r['timing']['group_prepare_window_s'],F('.085432'))
        self.assertEqual(r['timing']['fresh_tail_final_gate_budget_lower_ns'],F('1270.8848'))
        self.assertTrue(r['reachability']['allowed_outage_can_cover_whole_training'])
        self.assertIsNone(r['reachability']['universal_admission_probability_lower'])

if __name__=='__main__': unittest.main()

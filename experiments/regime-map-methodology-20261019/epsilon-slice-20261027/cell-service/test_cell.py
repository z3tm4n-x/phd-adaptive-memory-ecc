"""Directed interface/count/price checks, not hardware or channel simulation."""
import unittest
from fractions import Fraction as F
from cell_model import CellSelector,BLOCK,K,W,T,fence,ends,slot,load,calculate

class CellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,cls.src,cls.ref,cls.inp,cls.cfg=load();cls.result=calculate()

    def test_same_settings_and_Q_for_all_epsilon(self):
        self.assertEqual([r['epsilon'] for r in self.result['rows']],['1/10','1/100','1/1000','1/10000'])
        for new,old in zip(self.result['rows'],self.src['rows']):
            if 'adaptive' in new:
                a=new['adaptive'];b=old['adaptive']
                for k in ('k_base','k_rare'):self.assertEqual(a[k],b[k])
                self.assertEqual(a['Q_upper_at_design'],b['Q_upper_at_deltaC_design'])
                self.assertEqual(a['budgets']['deltaC_design_cap'],'1/20000')
        self.assertNotIn('adaptive',self.result['rows'][-1])

    def test_fixed_fences_and_all_scan_starts_fit_old_slots(self):
        cal=self.cfg['calendar'];frame=cal['frame_ticks']
        for row in self.result['rows'][:-1]:
            a=row['adaptive']
            for k in (a['k_base'],a['k_rare']):
                en=ends(k);self.assertEqual((en[0],en[-1]),(2,K))
                self.assertTrue(all(t2-t1>=2 for t1,t2 in zip((0,)+en,en)))
                for j in (0,6,a['N_cells']-1):
                    for end in en:
                        scan=fence(j)+(end-1)*BLOCK
                        self.assertEqual(scan%frame,0)
                        self.assertLess(scan+slot(W-1,cal)+125,fence(j)+end*BLOCK)
                for cut in (0,1,2,K-1,K):
                    self.assertLessEqual(sum(e<=cut for e in en),a['base_passes_per_cell'])

    def test_all_words_once_and_app_slots_reserved(self):
        cal=self.cfg['calendar']
        self.assertEqual(len({3*j%W for j in range(W)}),W)
        # Eight phase inequalities prove all identical frames, no T-long trace.
        for phase in range(8):
            self.assertLessEqual(slot(phase,cal)+125,cal['application_grant_phase_ticks'])
        tm=self.result['timing']
        self.assertGreater(tm['control_slot_slack_ns'],0)
        self.assertGreater(tm['peak_extra_bus_core_fraction_limit'],0)

    def test_clock_endpoint_extrema_and_final_deadline(self):
        tm=self.result['timing'];s=self.cfg['service'];cal=self.cfg['calendar']
        self.assertEqual(tm['final_gate_install_after_fresh_lower_ns'],F('1270.8848'))
        for xi in map(F,('.99999','1','1.00001')):
            for jitter in (F('-.5'),F('.5')):
                self.assertGreater(BLOCK*xi+jitter,0)
                release=slot(W-1,cal)*xi+124*xi+jitter
                self.assertGreaterEqual(BLOCK*xi-F('.5')-release-10000,tm['final_gate_install_after_fresh_lower_ns'])

    def test_arbitrary_bad_C_can_only_choose_one_calendar(self):
        for row in self.result['rows'][:-1]:
            a=row['adaptive'];sel=CellSelector(a['k_base'],a['k_rare'])
            values=[None,-1,10**100,'0',0,4,5,0,4,False,0,0]
            for j,C in enumerate(values):
                plan=sel.begin(j,C=C,valid=True,ready_tick=fence(j),prefix=True,healthy=True)
                self.assertIn(plan,sel.plans.values());self.assertLessEqual(len(plan),a['base_passes_per_cell'])
                self.assertEqual(sel.late_result(j,C=0,valid=True),plan)
            self.assertEqual(sel.scheduled_extra_E,0)
            with self.assertRaises(ValueError):sel.begin(0)

    def test_invalid_late_prefix_and_restore_keep_epoch(self):
        sel=CellSelector(403,719)
        for j in range(6):sel.begin(j)
        self.assertEqual(sel.begin(6,C=0,valid=True,ready_tick=fence(6)+1,prefix=True,healthy=True),ends(403))
        sel.observe_invalid(6,('GAP','ERR','RESTORE'));sel.restore()
        for j in range(7,13):
            self.assertEqual(sel.begin(j,C=0,valid=True,ready_tick=fence(j),prefix=True,healthy=True),ends(403))
        self.assertEqual(sel.begin(13,C=0,valid=True,ready_tick=fence(13),prefix=True,healthy=True),ends(719))
        self.assertEqual(sel.begin(14,C=0,valid=True,ready_tick=fence(14),prefix=False,healthy=True),ends(403))
        with self.assertRaises(ValueError):sel.begin(15,pending=True)

    def test_double_install_is_not_a_count_error(self):
        self.assertEqual(len(ends(403)),61)
        self.assertEqual(len(set(ends(403))|set(ends(719))),94)
        sel=CellSelector(403,719);sel.begin(0)
        with self.assertRaises(ValueError):sel.begin(0,C=0,valid=True,ready_tick=fence(0),prefix=True,healthy=True)

    def test_loss_after_choice_cannot_move_current_passes(self):
        sel=CellSelector(403,719)
        for j in range(6):sel.begin(j)
        plan=sel.begin(6,C=0,valid=True,ready_tick=fence(6),prefix=True,healthy=True)
        self.assertEqual(plan,ends(719))
        sel.observe_invalid(6,('GAP','ERR','RESTORE'));sel.restore()
        self.assertEqual(sel.late_result(6,C=10**100,valid=False),plan)
        self.assertEqual(sel.begin(7,C=0,valid=True,ready_tick=fence(7),prefix=True,healthy=True),ends(403))
        self.assertEqual(sel.scheduled_extra_E,0)

    def test_C3_escape_and_separate_comparisons(self):
        for row in self.result['rows'][:-1]:
            a=row['adaptive'];dc=F(a['budgets']['deltaC_design_cap'])
            for x in ('bus','core'):
                c=a['coordinates'][x]
                self.assertEqual(c['V']+dc*c['escape_coefficient'],c['U0']+dc*c['C_h'])
                self.assertEqual(set(c['comparison']),{'constant','schedule'})
                self.assertEqual(c['comparison']['schedule']['allowance_20']>0,row['epsilon']=='1/100')
                self.assertLess(c['comparison']['schedule']['allowance_30'],0)

    def test_missing_prefix_and_raw_channel_not_zero(self):
        for row in self.result['rows'][:-1]:
            a=row['adaptive'];h=a['handling'];inv=a['additional_invalid']
            self.assertEqual(inv['all_missing_prefix_means_z'],1)
            self.assertGreater(h['raw0'],1500)
            self.assertGreater(h['rates_good_or_explicitly_bad_capped']['cut_ready'],250000)
            self.assertGreater(h['extra_raw_v_domain'][1],250000000)
            self.assertTrue(a['policy_extra_E']['legacy_OUR_wrapper_unchanged_would_not_establish_zero'])
        a=self.result['rows'][1]['adaptive']['coordinates']['bus']
        self.assertGreater(a['V']+a['A_z'],F('0.8')*a['comparison']['schedule']['class_necessary_read_lower'])

    def test_global_horizon_and_common_payload_not_free(self):
        self.assertEqual(self.result['shared_application']['reads'],315569688607)
        self.assertEqual(self.result['shared_application']['useful_writes'],0)
        for row in self.result['rows'][:-1]:
            a=row['adaptive'];self.assertEqual(a['M_b'],W*(1+a['N_cells']*a['base_passes_per_cell']))
            self.assertTrue(a['handling']['pass_closes_bound_includes_B_C_and_A'])
        self.assertFalse(self.result['acceptance_or_hardware_gain_claimed'])

if __name__=='__main__':unittest.main()

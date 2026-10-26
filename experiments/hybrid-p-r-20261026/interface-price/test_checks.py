from decimal import Decimal, localcontext
from fractions import Fraction as F
import os
import unittest
from common import NS,ceil,load,wire_functions
import interface as ic
import price as pc

class TargetedChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.i,cls.cfg,cls.hist=load(os.environ.get('HYBRID_HISTORY_ROOT'))
        cls.p=pc.calculate(cls.i,cls.cfg,cls.m)
        cls.v=ic.calculate(cls.i,cls.cfg,cls.hist)
        enc,dec=wire_functions(cls.hist['adapter.py'])
        cls.enc,cls.dec=staticmethod(enc),staticmethod(dec)

    def binding(self,records,**kwargs):
        args=dict(W=self.i['fixed']['words'],calendar=self.cfg['calendar'],service=self.cfg['service'],
                  scan_start=0,previous_decision=0,entry_G=0,current_G=len(records),
                  processed_G=len(records),prefix_certificate=True)
        args.update(kwargs)
        args.setdefault('decision_tick',args['scan_start']+self.v['timing']['block_ticks'])
        return ic.close_counter(records,**args)

    def record(self,t,g,word=0,causes=('ERR',),**extra):
        return self.dec(self.enc(dict(t=t,g=g,word=word,origin='control',causes=list(causes),**extra)))

    def test_price_root_independent_100_digit_closed_form(self):
        p=self.p;env=self.i['proposed_environment'];r=env['residual']
        W=self.i['fixed']['words'];b=F(env['background']);B=F(env['total_peak'])
        R=F(r['cap_R']);g=F(r['growth_g']);Fr=F(r['mass_F_r'])
        L=Fr/R-R/(2*g);d=F(p['service']['fixed_aperture_upper_ns'])/NS
        eps=F(self.i['fixed']['epsilon']);delta=F(self.m['delta_exec'])
        with localcontext() as ctx:
            ctx.prec=100
            D=lambda x:Decimal(x.numerator)/Decimal(x.denominator)
            k=D(F(38,78)*((b+R)/W)**2)*(-D(B*L/W)).exp()
            H=-(1-D(eps+delta)).ln()
            y=H/(k*W)
            # Stable algebraic root via z=sqrt(x+1); no author bisection.
            z=2*D(L+d)/((y+4*D(d)*D(L+d)).sqrt()+y.sqrt())
            x=z*z-1
            self.assertLessEqual(Decimal(p['inversion']['x_star']['lower']),x)
            self.assertGreaterEqual(Decimal(p['inversion']['x_star']['upper']),x)
            n=W*x*D(F(self.i['fixed']['mission_s'])-R/g-L)/D(L+d)
            self.assertLessEqual(p['inversion']['necessary_integer_visits_lower'],int(n)+1)

    def test_direction_of_root_target_and_rounding(self):
        p=self.p;L=p['witness']['plateau_s'];d=F(p['service']['fixed_aperture_upper_ns'])/NS
        target=p['inversion']['target']
        lo=F(p['inversion']['x_star']['lower']);hi=F(p['inversion']['x_star']['upper'])
        self.assertGreaterEqual(pc.f(lo,L,d),F(target['upper']))
        self.assertLessEqual(pc.f(hi,L,d),F(target['lower']))
        self.assertEqual(pc.root_bracket(L*L,L,d),(0,0))
        self.assertEqual(pc.root_bracket(F(4),F(10),F(0)),(24,24))
        with self.assertRaises(ValueError): pc.root_bracket(F(0),L,d)

    def test_service_bus_and_core_are_distinct_lower_coordinates(self):
        s=self.p['service'];xm=s['clock_lower'];J=s['J_ns']
        self.assertEqual(s['R_bus_lower_ns'],48*xm-J)
        self.assertEqual(s['R_core_lower_ns'],68*xm-J)
        self.assertEqual(s['fixed_aperture_upper_ns'],124*s['clock_upper']+3*J)
        self.assertGreater(s['R_core_lower_ns'],s['R_bus_lower_ns'])
        self.assertGreater(s['nominal_anchor_spacing_lower_ns'],s['future_boundary_strip_ns'])

    def test_future_envelope_and_pending_are_separate_edge_obligations(self):
        s=self.p['service'];J=s['J_ns'];T=F(1000)
        # One nominal aperture touches T; its physical visit starts after T.
        anchor=T+J/2;actual_start=anchor+J
        self.assertLess(anchor-J,T);self.assertGreater(actual_start,T)
        # An unrelated one-visit calendar has a genuinely unfinished operation.
        start=T-F(34);finish=start+68
        self.assertLess(start,T);self.assertGreater(finish,T)
        self.assertEqual(s['terminal_edge_deductions'],2)
        self.assertEqual(self.p['geometric_good_execution']['completed_reads_lower'],
                         self.p['inversion']['necessary_integer_visits_lower']-2)

    def test_execution_failure_may_be_correlated_and_costless(self):
        p=self.p;d=p['expected_price']['delta_exec'];n=p['geometric_good_execution']['completed_reads_lower']
        # Extremal good/bad cost table; no cost is assumed on bad histories.
        expectation=(1-d)*n+d*0
        self.assertEqual(expectation,p['expected_price']['completed_reads_lower'])
        self.assertLess(expectation,n)
        self.assertEqual(p['expected_price']['factor'],1-F(self.i['fixed']['lifetime_other_budget']))
        self.assertFalse(p['expected_price']['counter_error_budget_charged'])

    def test_lower_price_uses_whole_horizon_and_separate_common_work(self):
        p=self.p;T=F(self.i['fixed']['mission_s']);e=p['expected_price'];s=p['service']
        self.assertEqual(e['protection_read_bus_fraction_lower'],
                         e['completed_reads_lower']*s['R_bus_lower_ns']/(NS*T))
        self.assertGreater(p['common_price']['good_application_bus_fraction_lower'],0)
        self.assertGreater(p['common_price']['good_initial_core_fraction_lower'],0)
        self.assertIsNone(p['unpriced']['controller_CPU_ns_per_action'])
        self.assertIsNone(p['unpriced']['energy_J_per_action'])
        self.assertTrue(p['no_gain_claim'])
        self.assertTrue(p['inversion']['OFF_excluded_by_necessary_count'])

    def test_complete_count_and_empty_prefix_need_source_binding(self):
        self.assertEqual(self.v['witnesses']['complete_two_ERR']['C'],2)
        self.assertEqual(self.v['witnesses']['healthy_closed_empty']['C'],0)
        pair=self.v['witnesses']['identical_wire_empty_vs_dropped_tail']
        self.assertEqual(pair['wire_records_both'],[])
        self.assertEqual(pair['true_C'],[0,1])
        self.assertTrue(pair['with_existing_generation_gate']['invalid'])
        self.assertTrue(pair['without_prefix_binding']['invalid'])

    def test_loss_restore_cannot_restore_missing_count(self):
        r=self.record(68,1,causes=('GAP','ERR','RESTORE'),covers=[1,1])
        self.assertNotIn('word',r)
        out=self.binding([r],source_healthy=True)
        self.assertIsNone(out['C'])
        self.assertTrue(any('GAP' in s for s in out['reasons']))
        # A later RESTORE does not repair an earlier absent record either.
        out=self.binding([self.record(68,2,causes=('RESTORE',))],current_G=2,processed_G=2)
        self.assertTrue(out['invalid'])

    def test_duplicate_record_is_not_second_ERR_and_stale_is_invalid(self):
        r=self.record(68,1)
        self.assertTrue(self.binding([r,r],current_G=1,processed_G=1)['invalid'])
        r2=self.record(68,2)  # different G cannot relabel the same transaction
        self.assertTrue(self.binding([r,r2])['invalid'])
        self.assertTrue(self.binding([r],entry_G=1,current_G=1,processed_G=1)['invalid'])

    def test_same_word_on_later_pass_is_a_distinct_transaction(self):
        B=self.v['timing']['block_ticks']
        one=self.binding([self.record(68,1)])
        two=self.binding([self.record(B+68,2)],scan_start=B,previous_decision=B,
                         entry_G=1,current_G=2,processed_G=2)
        self.assertEqual((one['C'],two['C']),(1,1))

    def test_phase_boundary_word_mapping_and_wrong_epoch(self):
        cal=self.cfg['calendar'];W=self.i['fixed']['words']
        for j in (0,1,7,8,W-1):
            r=self.record(ic.slot_start(j,cal)+68,1,(3*j)%W)
            self.assertEqual(self.binding([r])['C'],1)
        self.assertTrue(self.binding([self.record(232,1,0)])['invalid'])
        self.assertTrue(self.binding([self.record(68,1)],epoch_known=False)['invalid'])
        v=self.v['timing']
        self.assertLess(v['timestamp_aperture_ticks'],v['minimum_control_start_gap_ticks'])

    def test_cut_equality_is_in_next_packet(self):
        cut=self.cfg['observation']['cut_ns'];ready=self.cfg['observation']['batch_ready_ns']
        delivered=lambda arrival:(arrival//cut+1)*cut+ready
        self.assertEqual(delivered(cut-4),7900)
        self.assertEqual(delivered(cut),11900)
        self.assertEqual(delivered(cut+4),11900)
        self.assertGreater(delivered(cut),delivered(cut-4))

    def test_records_after_decision_or_reversed_source_time_are_invalid(self):
        end=self.v['timing']['block_ticks']
        self.assertTrue(self.binding([self.record(end+4,1,causes=('RESTORE',))])['invalid'])
        r=[self.record(232,1,3),self.record(68,2,0)]
        self.assertTrue(self.binding(r)['invalid'])

    def test_invalid_reasons_do_not_authorize_missing_service(self):
        r=[self.record(68,1)]
        for reason in ('guard_outside_scan','pending','unknown_at_entry'):
            self.assertTrue(self.binding(r,**{reason:True})['invalid'])
        for reason in ('main_pass_complete','decision_computation_ready','source_healthy'):
            out=self.binding(r,**{reason:False})
            self.assertIsNone(out['C']);self.assertTrue(out['no_action_authorized'])
        self.assertFalse(self.binding(r,pending=True)['full_service_boundary'])

    def test_physical_counts_drain_and_k1_deadline(self):
        v=self.v;tim=v['timing'];n=v['counts']['full_decisions_upper'];T=F(self.i['fixed']['mission_s'])
        self.assertLessEqual(n*tim['P_lower_s'],T)
        self.assertGreater((n+1)*tim['P_lower_s'],T)
        self.assertGreater(n,v['counts']['old_nominal_floor_for_comparison_only'])
        self.assertEqual(tim['post_fresh_finalize_invert_install_budget_lower_ns'],
                         tim['drain_after_last_release_lower_ns']-tim['source_to_fresh_upper_ns'])
        self.assertGreater(tim['post_fresh_finalize_invert_install_budget_lower_ns'],0)
        self.assertEqual(tim['nominal_k1_free_time_after_decision_ns'],0)
        self.assertGreater(tim['source_epoch_max_drift_from_nominal_s'],3000)

    def test_state_and_timestamp_capacity_are_not_free(self):
        s=self.v['state'];c=self.v['counts']
        self.assertEqual(s['counter_bits'],18);self.assertEqual(s['pass_id_bits'],34)
        self.assertLess(c['source_G_upper'],2**64);self.assertLess(c['source_ticks_upper'],2**60)
        self.assertEqual(s['persistent_counter_bytes'],64)
        self.assertEqual(s['total_retained_plus_example_counter_bytes'],131200)
        self.assertFalse(s['reuse_of_existing_64_loss_bytes'])
        self.assertIsNone(s['solver_workspace_bytes'])

if __name__=='__main__':unittest.main()

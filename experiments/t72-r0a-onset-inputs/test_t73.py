import copy
from fractions import Fraction as F
import unittest
from verify_t73 import load,variants,calculate,t58
from t73_calendar import Calendar,add_time,MAX_TIME,geometry_enumeration
from t73_resources import check_peak,check_fifo,check_price_strips


class DirectedChecks(unittest.TestCase):
    def test_phi_certificates(self):
        for _,c,_ in variants():
            m=c['monitor']
            lower=1-t58.exp_neg(F(m['z']))[1]
            self.assertLessEqual(F(m['phi_rational_lower']),lower)
    def test_both_sources_and_explicit_failure_repair(self):
        results={name:[calculate(c,e) for e in c['environments']] for name,c,_ in variants()}
        self.assertTrue(all(r['all_scalar_tests_pass'] for r in results['T73_published']))
        self.assertFalse(results['T72_budgets_explicit_T73_extension'][0]['all_scalar_tests_pass'])
        self.assertGreater(results['T72_budgets_explicit_T73_extension'][0]['known_T72_subtotal_if_two_missing_quotas_excluded'],F('.001'))
        self.assertFalse(results['T72_explicit_same_method_revision'][0]['passes_also_24h_and_returns'])
        self.assertTrue(all(r['passes_also_24h_and_returns'] for r in results['T72_revision_shorter_return_hold']))
        for rows in results.values():
            for r in rows:
                self.assertLessEqual(r['fixed_risk_upper'],F('.001'))
                self.assertGreater(r['fixed_risk_next_quantum'],F('.001'))
                self.assertTrue(r['fixed_resource_ok'])
                self.assertTrue(r['E3_J0_valid'])
                self.assertTrue(r['E3_arbitrary_phase_J0_valid'])
                self.assertGreater(r['E3_risk_lower'],F('.0035'))
                self.assertLess(r['unsigned64_time_max'],1<<64)
        self.assertGreater(results['T73_published'][0]['nominal_90ns_U_clock_margin_s'],0)
        self.assertLess(results['T72_revision_shorter_return_hold'][0]['nominal_90ns_U_clock_margin_s'],0)

    def test_quota_zero_and_pq_clipping(self):
        c=load(); c['whole_mission_quotas']['alpha_M']='0'
        r=calculate(c,c['environments'][0]);self.assertLess(r['alpha_margin'],0)
        c=load();c['whole_mission_quotas']['delta_E']='2'
        r=calculate(c,c['environments'][0]);self.assertEqual(r['p_q'],1)
        # No multiplication by J of the global quota.
        c=load();base=calculate(c,c['environments'][0]);c['whole_mission_quotas']['delta_E']='0.000002'
        r=calculate(c,c['environments'][0]);self.assertEqual(r['p_q']-base['p_q'],F('.000001'))

    def test_delivery_boundary(self):
        c=load();r=calculate(c,c['environments'][0])
        xp=F(c['service']['constant_clock_scale_max']);dt=F(c['service']['tick_nominal_s'])
        safe_ticks=t58.floor(r['d_safe_lower_s']/(xp*dt))
        c['monitor']['delivery_computation_deadline_after_window_ticks']=str(safe_ticks)
        self.assertGreaterEqual(calculate(c,c['environments'][0])['time_margin_s'],0)
        c['monitor']['delivery_computation_deadline_after_window_ticks']=str(safe_ticks+1)
        self.assertLess(calculate(c,c['environments'][0])['time_margin_s'],0)


class CalendarChecks(unittest.TestCase):
    def cal(self):return Calendar(8,3,2,3,2,1,5,100)

    def test_all_good_counts_have_finite_acceptance(self):
        c=load();q=calculate(c,c['environments'][0])['LOW_margin']>0
        for count in range(c['monitor']['k']+1):
            a=self.cal();self.assertTrue(a.message(0,at=10,lease_end=80,count=count,k=18500,qualified=q))
        a=self.cal();self.assertFalse(a.message(0,at=10,lease_end=80,count=18501,k=18500,qualified=q))

    def test_bad_messages_and_no_budget_reset(self):
        for flag in ['late','overflow','numeric_failure']:
            a=self.cal();self.assertFalse(a.message(0,at=10,lease_end=80,count=0,k=10,qualified=True,**{flag:True}))
            self.assertIsNone(a.covered)
            self.assertEqual(a.window_number,1)
        a=self.cal()
        for j in range(3):a.message(j,at=10+j,lease_end=80,count=0,k=10,qualified=True,valid=False)
        self.assertEqual(a.window_number,3)
        with self.assertRaises(ValueError):a.message(0,at=20,lease_end=80,count=0,k=10,qualified=True)

    def test_leases_break_extend_and_irrevocable_block(self):
        a=self.cal();a.message(0,at=0,lease_end=80,count=0,k=10,qualified=True)
        j=10;before=a.decide(j);self.assertFalse(before)
        a.err(a.start(j)+1) # flag arrives inside the already promised block slot
        self.assertEqual(a.decide(j),before)
        a.message(1,at=70,lease_end=90,count=0,k=10,qualified=True)
        self.assertEqual(a.covered,(0,90))
        a.message(2,at=91,lease_end=100,count=0,k=10,qualified=True)
        self.assertEqual(a.covered,(91,100))
        self.assertTrue(a.decide(31))

    def test_first_dirty_words_and_partial_last_cell(self):
        for ka in [3,5]:
            a=Calendar(8,ka,2,3,2,1,5,49)
            first={}
            for j in range(8):
                self.assertTrue(a.decide(j));first[a.word(j)]=a.end(j)
            self.assertEqual(len(first),8);self.assertLessEqual(max(first.values()),a.ps)
            self.assertFalse(a.decide(100))

    def test_timer_overflow_is_explicit(self):
        with self.assertRaises(OverflowError):add_time(MAX_TIME,1)
        a=self.cal();a.alarm(MAX_TIME-1);self.assertEqual(a.hold_until,MAX_TIME)
        a=self.cal();a.window_number=MAX_TIME
        self.assertFalse(a.message(MAX_TIME,at=10,lease_end=80,count=0,k=10,qualified=True))
        self.assertEqual(a.window_number,MAX_TIME)
        for count in [MAX_TIME+1,1.5,float('nan'),float('inf')]:
            a=self.cal();self.assertFalse(a.message(0,at=10,lease_end=80,count=count,k=10,qualified=True))

    def test_exhaustive_pair_geometry(self):
        r=geometry_enumeration();self.assertEqual(r['geometry_cases'],1024)


class ResourceChecks(unittest.TestCase):
    def test_mask_all_phases(self):self.assertEqual(check_peak(),2400)
    def test_nonzero_monitor_FIFO_and_transitions(self):self.assertEqual(check_fifo()['cases'],66)
    def test_price_strips_with_adjacent_bad_windows(self):self.assertTrue(check_price_strips()['all_extra_slots_covered'])
    def test_arbitrary_phase_finite_horizon_edge(self):
        # Deterministic U, disjoint blocks, same period per word. Not the
        # uniformly paired E2 calendar: its 2c edge cannot be reused here.
        W,c,tau,T=8,2,200,350
        actual=sum(max(0,min(T,s+c)-max(0,s)) for p in range(180,196,2) for s in [p-tau,p,p+tau])
        self.assertEqual(actual,16)
        self.assertLess(actual,F(W*c*T,tau)-2*c)
        self.assertGreaterEqual(actual,F(W*c*T,tau)-2*W*c)


if __name__=='__main__':unittest.main()

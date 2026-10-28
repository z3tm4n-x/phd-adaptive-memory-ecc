"""Directed tests of new calendar/bound/account transitions, not old campaigns."""
from fractions import Fraction as F
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import first_point as fp


class FirstPointTests(unittest.TestCase):
    def test_registered_menu_and_single_residual_budget(self):
        p=fp.Point()
        candidates=p.candidates()
        self.assertEqual({tuple(r['pair']) for r in candidates['rows']},{(1,1),(1,2),(3,3)})
        self.assertEqual(candidates['selected']['N0'],[3,3])
        self.assertTrue(all(pair==[3,3] for pair in candidates['selected'].values()))
        for r in candidates['rows']:
            h,l=r['pair']
            if h==l:
                self.assertIs(r['prices']['M'],r['prices']['N0'])
                self.assertEqual(r['risks']['M']['upper'],r['risks']['F']['upper'])
                self.assertEqual(r['risks']['M']['terms']['exceptions'],p.delta0)
            else:
                risk=r['risks']['M']
                terms=[(p.P(h)+p.dE)*(2*p.pmax+p.R),(p.P(l)+p.dE)*(2*p.b+p.R)]
                self.assertEqual(risk['terms']['residual'],p.K*p.Fr*max(terms))
                self.assertLess(risk['terms']['residual'],p.K*p.Fr*sum(terms))
                self.assertLessEqual(risk['upper'],r['risks']['Nplus_box']['upper'])
        for row in candidates['generation']:
            k=row['largest_kH'];m=row['ratio'];f=row['formula']
            if k:
                self.assertLessEqual(p.risk(k,k*m,f)['upper'],p.eps)
                self.assertGreater(p.risk(k+1,(k+1)*m,f)['upper'],p.eps)
            else:
                self.assertGreater(p.risk(1,m,f)['upper'],p.eps)

    def test_directed_threshold_and_registered_n0_bounds(self):
        p=fp.Point(); t=p.fixed_threshold()
        lo,hi=t['last_not_excluded'],t['excluded_from']
        self.assertEqual(hi['P0_s']-lo['P0_s'],F(1,10**9))
        self.assertGreater(hi['Q_lower'],p.eps)
        self.assertTrue(all(x['Q_lower_expression_enclosure_upper']<p.eps for x in lo['witnesses']))
        self.assertEqual(hi['Q_lower'],max(x['Q_lower'] for x in hi['witnesses']))
        self.assertFalse(hi['class_excluded_by_resource'])
        for pair in ((3,3),(1,2)):
            q=p.n0_lower(*pair)
            self.assertGreater(q['Q_lower'],0)
            self.assertLess(q['Q_lower'],q['Q_upper'])
            self.assertLessEqual(q['Q_upper'],p.eps)
            self.assertEqual(q['status'],'certified')

    def test_full_cost_keeps_exceptions_repairs_app_and_tail(self):
        p=fp.Point(); U=p.risk(3,3,'F')['upper']; c=p.price(3,3,U,False)
        self.assertEqual(c['reads_upper'],p.W*(p.T/p.P(3,False)+2)+p.delta0*p.Nmax)
        self.assertEqual(c['repairs_upper'],2*p.Fparents+U*p.Nmax)
        for name in ('bus','serial'):
            x=c['coordinates'][name]
            self.assertEqual(x['protection_upper_s'],x['checks_upper_s']+x['repairs_upper_s'])
            self.assertEqual(x['all_known_upper_s'],x['protection_upper_s']+x['app_s']['upper']+x['init_s']['upper'])
            self.assertGreater(x['app_s']['lower'],0)
            self.assertGreater(x['init_s']['lower'],0)
        self.assertFalse(c['control_included'])
        guarded=p.price(1,2,p.risk(1,2,'M')['upper'],True)
        unguarded=p.price(1,2,p.risk(1,2,'N0_actual')['upper'],False)
        self.assertGreater(guarded['read_terms_upper']['startup_tail'],unguarded['read_terms_upper']['startup_tail'])
        self.assertGreater(guarded['read_terms_upper']['bad_execution'],0)
        self.assertGreater(guarded['repairs_upper'],2*p.Fparents)
        self.assertGreaterEqual(guarded['hold']['lower_s'],p.P(1)+p.dE)
        # Full-price upper difference is deliberately not an exact guard cost.
        self.assertNotEqual(guarded['coordinates']['serial']['protection_upper_s']-unguarded['coordinates']['serial']['protection_upper_s'],
                            guarded['coordinates']['serial']['checks_upper_s']-unguarded['coordinates']['serial']['checks_upper_s'])

    def test_arithmetic_prefix_against_literal_slot_schedule(self):
        p=fp.Point(); p.W=32
        starts=[F(1568*(j//8)+164*(j%8))*p.xp/fp.NS for j in range(600)]
        for k in (1,2,3,7):
            for index in range(1,580,11):
                for d in (-F(1,10**15),F(0),F(1,10**15)):
                    t=starts[index]+d
                    literal=sum(s<t and (j//p.W)%k==0 for j,s in enumerate(starts))
                    self.assertEqual(p.support_prefix(t,k),literal)

    def test_control_budget_is_joint_and_not_zero_assumed(self):
        p=fp.Point();lower=p.fixed_threshold()['excluded_from']
        fixed=p.price(3,3,p.risk(3,3,'F')['upper'],False)
        window=p.price(1,2,p.risk(1,2,'M')['upper'],True)
        mg=p.management(window,lower,fixed)
        self.assertTrue(all(n>0 for n in mg['calendar_action_counts_upper'].values()))
        B=mg['conditional_burst_work_upper_s']; tau=mg['conditional_local_processing_budget_s']
        latency=(fp.ceil(B/mg['guaranteed_progress_s'])+20)*mg['frame_upper_s']+tau
        self.assertLessEqual(latency,p.delay)
        u=mg['window_action_mean_sufficient_for_any_composition']
        for name,weight in (('check',1),('command',3),('timer',5),('extra_bundle',1)):
            # Entire joint mean spent on any one operation still fits the burst.
            self.assertLessEqual(weight*u/mg['rates_upper_per_s'][name],B)
        self.assertIsNone(mg['CPU']);self.assertIsNone(mg['energy'])
        self.assertLess(mg['gain_conditions']['serial']['additional_rule_budget_for_strict_gain_per_s'],0)
        f=p.management(fixed,lower,fixed)
        self.assertTrue(all(n==0 for n in f['calendar_action_counts_upper'].values()))
        self.assertGreater(f['local_slot_selector_checks_upper'],0)

    def test_complete_guard_calendar_against_literal_poll_and_freeze(self):
        # Dimensionally scaled toy executor makes literal enumeration bounded.
        # It tests selection, phases, startup, loss/restore, tail and endpoint
        # equality; it is not a new physical/radiation cell.
        with patch.object(fp,'NS',1000):
            p=fp.Point(); p.W=8; p.T=F(50); p.N=2
            p.left=F(10);p.width=F(2);p.cycle=F(20)
            loss=(15*p.xp,17*p.xp)
            for pair in ((1,2),(2,4)):
                for lost in (None,loss):
                    sets=[]
                    for guarded in (False,True):
                        hold=p.hold(pair[0],guarded)
                        H=hold['upper_s']; actual=hold['ticks']*p.xp/fp.NS
                        C=H+p.hp+p.delay+p.freeze+2*p.et
                        chosen=set(); j=0
                        while True:
                            t=F(1568*(j//8)+164*(j%8))*p.xp/fp.NS
                            if t>=p.T:break
                            u=t-320*p.xp/fp.NS
                            poll=max(0,u//p.xp)*p.xp
                            fast=u<actual or t>=p.T-C
                            for win in range(p.N):
                                a=p.left+win*p.cycle;b=a+p.width
                                fast |= (poll-p.et<=b+H and poll+p.hp+p.delay+p.freeze+H+p.et>=a)
                            if lost:
                                fast |= lost[0]<=u<lost[1]+actual
                            phase=j//p.W
                            if phase%pair[1]==0 or fast and phase%pair[0]==0:
                                chosen.add(j)
                            j+=1
                        self.assertEqual(p.exact_reads(*pair,guarded,lost),len(chosen))
                        sets.append(chosen)
                    self.assertTrue(sets[0]<=sets[1])


if __name__=='__main__':
    unittest.main()

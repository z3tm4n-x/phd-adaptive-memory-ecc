from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import unittest

import t80_joint as j
import t80_engine as old
from t80_joint_policy import DirectState


def dec(x):
    q=F(x);return D(q.numerator)/D(q.denominator)


class Joint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v=j.source_check()
        cls.p=old.context(cls.v[0],'.10','internal38',1)
        cls.p['mode']='combined'

    def test_pinned_four_budgets_unchanged(self):
        self.assertEqual([F(v['input']['mark_contract']['D_star_full38_direct_exposure_upper'])
                          for v in self.v],[F('5e-5')]+[F('1e-4')]*3)
        self.assertIsNone(j.CONFIG['physical_D_upper'])
        self.assertIsNone(j.CONFIG['physical_ERR_lower'])
        self.assertIsNone(j.CONFIG['physical_joint_WCET_s'])

    def test_majorant_at_edges_both_sides_of_jump(self):
        p=self.p
        for ka in (1,3,101,4095):
            for vc in (2*p['b'],F('.001'),p['B']/2):
                r=j.pair_bound(p,ka,vc)
                for x in (F(0),p['b'],vc-F('1e-20'),vc,vc+F('1e-20'),p['B']):
                    lhs=p['Ps']*x*x*(1+(ka if x<=vc else 0))
                    self.assertLessEqual(lhs,r['u']+r['v']*max(F(0),x-p['b']))
                self.assertLessEqual(r['Q'],r['old_pair'])
                self.assertLessEqual(r['Q'],r['mandatory_pair'])

    def test_degenerate_fallback_and_flat_switch(self):
        p=self.p
        for vc in (p['b'],p['B']):
            self.assertEqual(j.pair_bound(p,7,vc)['v_branch'],'not_applicable')
        ka=101;vf=j.flat_v(p,ka)
        r=j.pair_bound(p,ka,vf)
        self.assertEqual(r['v_low'],r['v_peak'])
        self.assertEqual(j.pair_bound(p,ka,vf-F('1e-12'))['v_branch'],'peak')
        self.assertEqual(j.pair_bound(p,ka,vf+F('1e-12'))['v_branch'],'low')
        q=dict(p,B=F(10),b=F(1))
        # ka=81/19 is a mathematical boundary, not an allowed calendar.
        self.assertEqual(j.flat_v(q,F(81,19)),1)
        q['B']=q['b']
        self.assertIsNone(j.pair_bound(q,3,q['b'])['v'])

    def test_B3_nonzero_H_and_long_window_saturation(self):
        p=self.p
        for w in (1,60,300):
            m=j.window(p,F(10**6),F(w),F(1),F(2),'total_load',2)
            r=j.conflict_B3(p,m)
            self.assertTrue(r['B3_applies']);self.assertGreater(m['H'],0)
            self.assertLessEqual(r['a_mass'],r['mu_upper'])
            self.assertGreater(r['pM_B3_lower'],F('.999999'))
            th=j.safe_threshold(m['mR'],m['aM'],m['H'])
            exponent=th['z']*th['k']-j.phi(th['z'])[0]*m['mu']
            self.assertLessEqual(exponent,-m['H'])
            _,dm=j.strips(p,m,F(300),'reset-slow')
            self.assertGreater(m['J']*dm/p['T']*r['pM_B3_lower'],1)

    def test_cadence_J_H_quotas_ring_and_unknown(self):
        p=self.p;prev=0
        for div in (2,8,32):
            m=j.window(p,F(10**6),F(1),F(1),F(2),'total_load',div)
            self.assertGreater(m['J'],prev);prev=m['J']
            self.assertEqual(m['h0']+m['Delta_m'],m['wm'])
            self.assertEqual(m['ring_counters'],div+1)
            self.assertLessEqual(m['J']*F(3,8)**m['H'],F(p['q']['alpha_M']))
            q=j.cadence_context(p,div)
            self.assertEqual(q['q'],p['q']);self.assertEqual(q['g'],131)
            self.assertEqual(q['CX'],p['CX']*F(div,2))
            self.assertFalse(j.cadence_context(p,div,available=False)['cadence_pass'])

    def test_fast_integral_zero_age_and_outside_cone(self):
        x=F('.0003');w=F(1)
        lo,hi=j.fast_exposure(x,F(0),w,w)
        exact=x*w-F('.000048')*w*w/2
        self.assertLessEqual(lo,exact);self.assertGreaterEqual(hi,exact)
        lo,_=j.fast_exposure(x,F(0),w,F(100))
        self.assertEqual(lo,0)
        with self.assertRaises(ValueError):j.fast_exposure(x,F(0),w,F('.5'))

    def test_fast_exponential_integral_decimal90_and_Darboux(self):
        x,b,w,h=F('.003'),F('.00015'),F(1),F(3)
        lo,hi=j.fast_exposure(x,b,w,h)
        with localcontext() as ctx:
            ctx.prec=90
            exact=dec(x)/D('.048')*((-D('.048')*dec(h-w)).exp()-(-D('.048')*dec(h)).exp())-dec(b*w)
            self.assertLessEqual(dec(lo),exact);self.assertGreaterEqual(dec(hi),exact)
            N=256;dt=dec(w)/N
            lower=dt*sum(max(D(0),dec(x)*(-D('.048')*(dec(h-w)+i*dt)).exp()-dec(b)) for i in range(1,N+1))
            upper=dt*sum(max(D(0),dec(x)*(-D('.048')*(dec(h-w)+i*dt)).exp()-dec(b)) for i in range(N))
            self.assertLessEqual(lower,dec(lo));self.assertGreaterEqual(upper,dec(hi))
            self.assertLessEqual(upper-lower,dec(x)*dt)

    def test_B6_zero_and_k_at_or_above_m(self):
        self.assertEqual(j.analytic_safe_value(F(100),0).lo,D(100))
        self.assertEqual(j.analytic_safe_value(F(100),100).hi,0)
        self.assertEqual(j.analytic_safe_value(F(100),101).hi,0)
        with localcontext() as ctx:
            ctx.prec=90;exact=D(100)-20+D(20)*D('.2').ln()
            iv=j.analytic_safe_value(F(100),20)
            self.assertLessEqual(iv.lo,exact);self.assertGreaterEqual(iv.hi,exact)

    def test_exact_tail_and_quantile(self):
        with localcontext() as ctx:
            ctx.prec=90
            for mu,k in ((F(0),0),(F(2),0),(F(8),3),(F(8),20)):
                iv=j.poisson_tail_exact(mu,k)
                term=(-dec(mu)).exp();total=term
                for r in range(1,k+1):term*=dec(mu)/r;total+=term
                exact=1-total
                self.assertLessEqual(iv.lo,exact+D('1e-85'))
                self.assertGreaterEqual(iv.hi,exact-D('1e-85'))
                self.assertGreaterEqual(dec(j.poisson_chernoff(mu,k)),exact-D('1e-85'))
        k=j.k_price_exact(F(8),F('.001'))
        self.assertLessEqual(F(j.poisson_tail_exact(F(8),k).hi),F('.001'))
        self.assertGreater(F(j.poisson_tail_exact(F(8),k-1).lo),F('.001'))

    def test_B7_negative_zero_positive_contrast_and_rounding(self):
        p=self.p;m=j.window(p,F(10**6),F(1),F(1),F(2),'total_load',2)
        m['b_nom']=p['b']
        self.assertEqual(j.requirement_B7(m,F(0),F('.001'),F('.1'),F('.1'))['status'],'nonpositive_contrast')
        zero=dict(m,b_nom=F(0))
        self.assertEqual(j.requirement_B7(zero,F(0),F('.001'),F('.1'),F('.1'))['contrast_upper'],0)
        r=j.requirement_B7(m,F('.002'),F('.001'),F('.1'),F('.1'))
        self.assertEqual(r['status'],'sufficient')
        a=F(j.t58.ceil(r['a_suff_upper']))
        mu=m['wp']*(a*p['b']+F('.001'))
        numerator=j.I(mu)*(j.I('.1').exp()-j.I(1))+(j.I(1000)).ln()
        k=j.t58.ceil(F((numerator/j.I('.1')).hi))
        self.assertLessEqual(j.poisson_chernoff(mu,k),F('.001'))
        self.assertGreaterEqual(a*j.phi(F('.1'))[0]*F('.002')-F('.1')*k,m['H'])

    def test_return_edges_multiple_intervals_not_multiple_quotas(self):
        p=self.p;TQ=p['T']*F(9,10)
        for kq in (1,1000):
            a,b=j.price_edges(p,TQ,kq)
            self.assertEqual(a,2*p['cp']*kq/TQ)
            self.assertEqual(b,p['sigmaX']*kq/TQ)
        self.assertEqual(j.price_edges(p),j.price_edges(p,p['T'],1))
        with self.assertRaises(ValueError):j.price_edges(p,F(0),1)

    def test_reset_pruning_and_bounded_subwindow_counts(self):
        p=self.p;m=j.window(p,F(10**6),F(1),F(1),F(2),'total_load',2)
        r=j.best_reset(p,m,F('1e-6'),F(300))
        self.assertEqual(r['status'],'certified_conditional')
        self.assertEqual(r['quiet_upper'],p['cp']/p['gm']+sum(j.price_edges(p))+p['CX'])
        weak=j.window(p,F(1000),F(1),F(1),F(2),'total_load',2)
        self.assertEqual(j.best_reset(p,weak,F('1e-6'),F(300))['status'],'LOW_uninformative')
        for k in (0,1,17,1000):
            for counts in ([0]*8,[1]*8,[k,0,0],[k+1,0,0],[2**80,1,2]):
                self.assertEqual(sum(counts)<=k,sum(min(x,k+1) for x in counts)<=k)

    def test_direct_above_ve_reset_rejects_and_initial_strip(self):
        p=self.p;m=j.window(p,F(10**6),F(1),F(1),F(2),'total_load',2)
        vc=j.flat_v(p,101)
        self.assertGreater(vc,F('.001'))
        row=j.evaluate(p,m,101,vc,'direct-fast',F(300))
        self.assertEqual(row['status'],'certified_conditional')
        self.assertEqual(j.evaluate(p,m,101,vc,'reset-slow',F(300),F('.5'),F('1e-6'))['status'],'reset_vc_outside')
        _,direct=j.strips(p,m,F(300),'direct-fast')
        _,reset=j.strips(p,m,F(300),'reset-slow')
        self.assertGreaterEqual(reset-direct,300)
        self.assertGreater(row['quiet_start_component'],0)
        self.assertGreaterEqual(m['hF_slack'],0)

    def test_piecewise_ka_candidates_against_all_odd(self):
        p=self.p;m=j.window(p,F(10**6),F(1),F(1),F(2),'total_load',8)
        for vc in (F('.0004'),F('.001'),F('.003')):
            cap=min(4095,j.max_ka(p,vc))
            de,dm=j.strips(p,m,F(0),'direct-fast')
            for pm in (F(0),F('1e-8'),F(1)):
                cost=lambda k:j.price(p,m,k,j.pair_bound(p,k,vc)['risk_upper'],de,dm,pm)['objective']
                ks=j.ka_candidates(p,m,vc,cap,de)
                self.assertEqual(min(cost(k) for k in ks),min(cost(k) for k in range(1,cap+1,2)))
                if cap<4095:self.assertGreater(j.pair_bound(p,cap+2,vc)['risk_upper'],p['eps'])

    def test_early_known_pass_both_shields_with_margin(self):
        for si in (0,1):
            p=old.context(self.v[0],'.10','internal38',si);p['mode']='combined'
            p=j.cadence_context(p,2)
            m=j.window(p,F(10**6),F(1),F(1),F(2),'total_load',2)
            r=j.best_direct(p,m)
            self.assertTrue(r['full_goal_pass']);self.assertLessEqual(r['risk_upper'],p['eps'])
            self.assertTrue(p['cadence_pass']);self.assertEqual(p['g'],131)
            self.assertLessEqual(p['resource']['peak'],F('.8'))
            self.assertLessEqual(F('1.1')*p['resource']['delay'],F('3e-6'))


class DirectPolicy(unittest.TestCase):
    def state(self):
        return DirectState(w=10,stride=5,h0=5,d=1,DQ=300,lease=30,k=4,hE=2,hM=2)

    def test_delivered_LOW_continuity_past_edge_and_initial_short(self):
        s=self.state()
        self.assertTrue(s.execute(1,0,2,2,3,100))
        s.message(0,0,11)
        self.assertIsNone(s.Q);self.assertEqual(s.LOW,(11,30))
        self.assertTrue(s.execute(2,11,12,2,3,100))
        s.message(1,0,16);self.assertEqual(s.LOW,(11,35))
        self.assertFalse(s.execute(4,16,18,2,3,100))
        before=s.LOW;s.err(17);self.assertEqual(s.LOW,before)
        s.message(2,0,22);self.assertIsNone(s.LOW) # late: deadline21
        s.message(3,0,26);self.assertEqual(s.LOW,(26,45))

    def test_no_retroactive_use_or_unbudgeted_OR(self):
        s=self.state()
        with self.assertRaises(ValueError):s.message(0,0,10)
        self.assertEqual(s.LOW_kind,'direct-fast')
        s.message(0,0,11)
        self.assertTrue(s.execute(1,11,11,2,3,100))
        s.message(1,0,16)
        self.assertTrue(s.execute(1,20,20,2,3,100)) # existing promise is fixed


if __name__=='__main__':unittest.main()

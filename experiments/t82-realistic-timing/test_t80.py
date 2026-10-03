from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import unittest

from t80_engine import (CONFIG, FAMILY, source_check, context, short_gate, retrospective,
                        monitor_window, threshold, lease, monitor_candidate, choose_monitor,
                        odd_candidates, phi, t58)
from t80_err import I, integral_A, exposure, majorant, cell_upper, err_price
from t80_policy import MonitorState, ERRState


class Numerical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.variants = source_check()
        cls.p = context(cls.variants[0], '.10', 'internal38', 1)

    def test_sources_four_budgets_and_unknowns(self):
        self.assertEqual(len(self.variants), 4)
        self.assertIsNone(CONFIG['service_projection']['internal_joint_WCET_s'])
        self.assertIsNone(CONFIG['singleton_ERR']['physical_a_E'])
        self.assertEqual([F(v['input']['mark_contract']['D_star_full38_direct_exposure_upper'])
                          for v in self.variants], [F('.00005')]+[F('.0001')]*3)

    def test_short_risk_first_with_beta0_and_external(self):
        for v in self.variants:
            for m in CONFIG['margins']:
                for si in range(2):
                    p = context(v, m, 'external39', si)
                    for mode in ('combined','monitor-only','ERR-only'):
                        self.assertFalse(short_gate(p, mode)['short_pass'])
        p = context(self.variants[1], '.10', 'internal38', 0)
        self.assertFalse(short_gate(p, 'combined')['short_pass'])
        self.assertGreater(short_gate(self.p,'ERR-only')['short_pairs_upper'],
                           short_gate(self.p,'combined')['short_pairs_upper'])

    def test_fast_retrospective_saturation_and_zero(self):
        b, q = self.p['b'], 2*self.p['b']
        self.assertEqual(retrospective(b,b,F(100)),0)
        self.assertEqual(retrospective(q,b,F(30)),retrospective(q,b,F(150)))
        self.assertEqual(retrospective(q,b,F(30)), (q-b)**2/(2*F('.048')*F('.001')))
        # Independent monotone Darboux enclosure on a rational time grid.
        h, N, slope = F(3), 1024, F('.000048')
        dt = h/N
        lo = dt*sum(max(F(0),q-b-slope*i*dt) for i in range(1,N+1))
        hi = dt*sum(max(F(0),q-b-slope*i*dt) for i in range(N))
        exact = retrospective(q,b,h)
        self.assertLessEqual(lo,exact); self.assertLessEqual(exact,hi)
        self.assertLessEqual(hi-lo,(q-b)*dt)

    def test_k_next_integer_and_mission_H(self):
        m = monitor_window(self.p,F(10**6),F(60),F(1),F(2),'total_load')
        th = threshold(m,F(1))
        self.assertGreaterEqual(th['k'],0)
        self.assertGreaterEqual(th['LOW_slack'],0)
        self.assertLess(th['next_k_slack_upper'],0)
        alpha=F(self.p['q']['alpha_M'])
        self.assertLessEqual(m['J']*F(3,8)**m['H'],alpha)
        self.assertGreater(m['J']*F(3,8)**(m['H']-1),alpha)
        self.assertEqual(th['pM_upper'],1)
        weak=threshold(monitor_window(self.p,F(1000),F(300),F(1),F(2),'total_load'),F(1))
        self.assertLess(weak['k'],0)

    def test_low_deadline_margin_and_next_lease_quantum(self):
        m=monitor_window(self.p,F(10**6),F(300),F(60),F('1.5'),'total_load')
        bad=lease(self.p,m,F('.048'),F('.5'))
        self.assertLess(bad['lease_slack_s'],0)
        good=lease(self.p,m,F('.000001'),F('.015625'))
        self.assertGreater(good['lease_slack_s'],0)
        exact=(good['vc']-m['qR'])/(F('.001')*F('.000001'))
        self.assertLessEqual(good['lease_ticks']*self.p['tp'],exact)
        self.assertGreater((good['lease_ticks']+1)*self.p['tp'],exact)
        zero=lease(self.p,m,F(0),F('.015625'),finite_zero_growth_lease=F(10000))
        self.assertGreater(zero['lease_slack_s'],0)

    def test_odd_optimizer_against_full_integer_scan(self):
        for n in (1,4,99,4095):
            for a in (F(0),F('.2'),F('1.2')):
                for b in (F(0),F('.000003'),F('.01'),F(3)):
                    f=lambda k:F(1,k)+min(F(1),a+b*k)
                    self.assertEqual(min(map(f,odd_candidates(n,b))),min(f(k) for k in range(1,n+1,2)))

    def test_selected_monitor_independent_decimal90(self):
        p=self.p
        r=choose_monitor(p,F(10**6),F(60),F(1),F(2),F('.000001'),F(300),'total_load','combined')
        self.assertEqual(r['status'],'certified_conditional')
        with localcontext() as c:
            c.prec=90
            dec=lambda x:D(x.numerator)/D(x.denominator) if isinstance(x,F) else D(x)
            beta=D(37)/(D(76)*D(p['W']))
            V=min(dec(r['vc'])**2*dec(p['T']),dec(p['b'])**2*dec(p['T'])+(dec(r['vc'])+dec(p['b']))*dec(p['FS']))
            risk=D('.000006')+D('.00005')+dec(p['B'])*dec(p['Ps'])/dec(p['W'])+beta*dec(p['Ps'])*(dec(p['S2'])+r['ka']*V)
            self.assertLess(abs(risk-dec(r['risk_upper'])),D('1e-80'))
            # Saturated (8): independent cost including post-failure hard mode.
            cf=dec(p['cp'])/dec(p['gm'])
            quiet=cf/D(r['ka'])+cf+(2*dec(p['cp'])+dec(p['sigmaX']))/dec(p['T'])+dec(p['CX'])
            self.assertLess(abs(quiet-dec(r['quiet_upper'])),D('1e-80'))
        self.assertGreater(r['next_odd_risk'],p['eps'])

    def test_integral_exp_branch_and_saturation(self):
        for x,t in ((F('.04'),F(1)),(F('.04'),F(80)),(F('.3'),F(1000))):
            v=integral_A(x,t)
            with localcontext() as c:
                c.prec=90
                xd,td=D(x.numerator)/D(x.denominator),D(t.numerator)/D(t.denominator)
                rho,l=D('.048'),D('.001')
                te=(xd/l).ln()/rho
                v1=min(td,te);v2=min(max(D(0),td-te),1/rho)
                exact=xd/rho*(1-(-rho*v1).exp())+l*(v2-rho*v2*v2/2)
                self.assertLessEqual(v.lo,exact);self.assertGreaterEqual(v.hi,exact)
        self.assertEqual(integral_A(F('.001'),F(1000),F(0)).lo,D(1))
        saturated=exposure(F('.3'),F(200),F(10000))
        self.assertLess(saturated.hi,D('1e-43'))

    def test_E1_interval_majorant_and_no_information(self):
        p=self.p;a=F(p['W']-1,p['W'])
        r=majorant(p['B'],p['b'],p['T'],p['FS'],p['S2'],a,F(1),F(121))
        self.assertGreaterEqual(r['minimum_E1_slack'],0)
        # Independent 90-digit point checks supplement interval E1 over ALL cells.
        for i in range(1,501):
            x=p['B']*i/500
            expo=exposure(x,F(1),F(121))
            with localcontext() as c:
                c.prec=90
                dec=lambda q:D(q.numerator)/D(q.denominator)
                psi=dec(x)**2*(-dec(a)*expo.lo).exp()
                self.assertLessEqual(psi,dec(r['u']+r['v']*max(F(0),x-p['b'])))
        self.assertGreaterEqual(cell_upper(F('.01'),F('.02'),F(0),F(1),F(2)),F('.02')**2)
        self.assertEqual(exposure(F('.001'),F(1),F(1)).lo,0)

    def test_separate_price_strips_and_modes(self):
        p=self.p
        args=(p,F(10**6),F(60),F(1),F(2),F('.000001'),F(300),'total_load')
        both=choose_monitor(*args,'combined');mon=choose_monitor(*args,'monitor-only')
        self.assertLess(both['DE'],F('1.001'))
        self.assertGreater(both['DM'],300)
        self.assertEqual(mon['DE'],0)
        self.assertEqual(mon['quiet_ERR_component'],0)
        self.assertEqual(short_gate(p,'combined')['quota_upper']-short_gate(p,'monitor-only')['quota_upper'],F('.000001'))


class StateTransitions(unittest.TestCase):
    def state(self):
        return MonitorState(w=10,stride=5,h0=5,d=1,DQ=15,lease=30,k=4,hE=2,hM=2)

    def test_initial_peak_short_dip_and_actual_quiet_reset(self):
        s=self.state()
        self.assertTrue(s.execute(1,0,2,2,3,100))
        s.message(0,0,11);s.message(1,0,16)
        self.assertIsNone(s.LOW)  # quiet dip shorter than DQ
        s.message(2,10,21)  # rapid rebound: clears Q
        self.assertIsNone(s.Q)
        for j in (3,4,5):s.message(j,0,j*5+11)
        self.assertEqual(s.Q,(20,35));self.assertEqual(s.LOW,(35,65))

    def test_ERR_preserves_LOW_but_monitor_loss_clears(self):
        s=self.state()
        for j in range(4):s.message(j,0,j*5+11)
        q,low=s.Q,s.LOW
        s.err(26)
        self.assertEqual((s.Q,s.LOW),(q,low))
        self.assertEqual(s.holdE,28)
        s.message(4,0,32)  # deadline31, late even with a small value
        self.assertIsNone(s.LOW)

    def test_count_edges_bad_numbers_gap_and_deadline(self):
        for value,accepted in ((3,True),(4,True),(5,False),(-1,False),(float('nan'),False),(2**64,False)):
            s=self.state();self.assertEqual(s.message(0,value,11),accepted)
        s=self.state()
        with self.assertRaises(ValueError):s.message(0,0,10)
        s.message(0,0,11);s.message(3,0,26)
        self.assertEqual(s.Q,(20,25))

    def test_ERR_finite_exit_flags_losses_and_pending(self):
        with self.assertRaises(ValueError):ERRState(10,10)
        s=ERRState(11,10)
        self.assertTrue(s.execute(1,0,3))
        self.assertFalse(s.execute(2,11,3))
        self.assertTrue(s.execute(3,11,3))
        s.flag_or_loss(12)
        self.assertTrue(s.execute(4,12,3))
        self.assertTrue(s.execute(4,100,3))  # already promised; not revoked
        self.assertFalse(s.execute(5,100,3))

    def test_two_sided_LOW_and_mandatory_slot(self):
        s=self.state();s.LOW=(20,40)
        self.assertTrue(s.execute(1,20,21,2,3,100))  # missing past half
        self.assertFalse(s.execute(2,23,25,2,3,100))
        self.assertTrue(s.execute(3,23,25,2,3,100))
        self.assertTrue(s.execute(4,39,39,2,3,100))  # missing future half


if __name__=='__main__':unittest.main()

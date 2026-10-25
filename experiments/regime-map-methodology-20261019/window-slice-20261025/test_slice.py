from fractions import Fraction as F
import unittest
from model import Slice,NS,ceil
from calendar_math import q_ns,prefix_indices,pass_prefix,count,critical_indices,mode_at,Selector,nominal_bands
from table import down


class SliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.s=Slice()

    def test_batch_geometry_permutation_and_nested_support(self):
        W=self.s.W
        self.assertEqual(len({3*j%W for j in range(W)}),W)
        for j in range(16):
            self.assertEqual(q_ns(j+W)-q_ns(j),W*196)
            for k in (20,1780):self.assertEqual(q_ns(j+k*W)-q_ns(j),k*W*196)
        self.assertEqual(1780%20,0)
        self.assertEqual([q_ns(j+1)-q_ns(j) for j in range(8)],[164]*7+[420])

    def test_prefix_AP_against_short_direct_enumeration(self):
        W=16;starts=[q_ns(j) for j in range(30000)]
        for left,right in [(0,1),(0,1568),(163,164),(164,165),(1148,1568),
                           (1,50000),(5039,101121),(4000000,5100000)]:
            for k in (1,20,1780):
                direct=sum(left<=t<right and (j//W)%k==0 for j,t in enumerate(starts))
                self.assertEqual(count(k,W,F(left,NS),F(right,NS)),direct)
        for j in (0,7,8,15,16,28500):
            self.assertEqual(prefix_indices(F(q_ns(j))),j)
            self.assertEqual(prefix_indices(F(q_ns(j))+F(1,10)),j+1)

    def test_accepted_point_and_affine_transfer(self):
        s=self.s
        for key in ('Q_upper','pure_bus_upper','reads_upper','repairs_upper'):
            self.assertEqual(s.upper(30)[key],s.a[key])
        for eta in (F(0),F(1,3),F(1200)):
            row=s.upper(eta)
            self.assertEqual(row['pure_bus_upper'],s.bus0+eta*s.slope)
            self.assertEqual(row['Q_upper'],s.U)
            self.assertLess(row['reads_upper'],s.hard)
        self.assertLess(F(s.accepted['witness']['rise_s']['hi'])+430,600)

    def test_ready_at_freeze_and_stale_commands(self):
        q=F(q_ns(self.s.W*20),NS);phi=q-F(320,NS)
        selector=Selector();selector.command(0,phi-2,False)
        selector.expire(selector.generation,phi-1)
        self.assertFalse(selector.fast())
        selector.command(2,phi,True)
        self.assertTrue(selector.fast()) # equality is applied before freeze
        self.assertFalse(selector.command(1,phi,False))
        self.assertTrue(selector.fast())

    def test_return_generation_cannot_erase_new_loss(self):
        self.assertGreaterEqual(self.s.hold_lower,self.s.H)
        self.assertLess(self.s.hold_count,2**34)
        self.assertLessEqual(self.s.hplus+2*self.s.delay+self.s.hold_upper+self.s.freeze,2*self.s.C)
        c=Selector();c.command(0,F(0),False);old=c.generation
        c.command(1,F(1,2),False,healthy=False)
        c.expire(old,F(2));self.assertTrue(c.fast())
        c.command(2,F(3),False);generation=c.generation
        c.expire(generation,F(399,100));self.assertTrue(c.fast())
        c.expire(generation,F(4));self.assertFalse(c.fast())
        c.command(3,F(5),True)
        c.expire(generation,F(6));self.assertTrue(c.fast())

    def test_false_alarm_uses_paid_band_and_recovery(self):
        s=self.s;i=100
        for edge in (F(i),F(i)+s.delay,F(i+1)+s.delay,F(i+2)+2*s.delay):
            for j in critical_indices(s,edge):
                q=F(q_ns(j),NS)
                if mode_at(s,j,30,0,false_poll=i) and not mode_at(s,j,30,0):
                    self.assertGreaterEqual(q,F(i))
                    self.assertLessEqual(q,F(i)+2*s.C)

    def test_same_information_schedule_equals_healthy_online_rule(self):
        s=self.s
        for eta in (F(0),F(30),F(30999,1000),F(1200)):
            bands=nominal_bands(s,eta)
            for a,b in bands[:2]+bands[-2:]:
                r=0 if a<10000 else s.m['windows']-1
                for t in (a,b):
                    for j in critical_indices(s,t):
                        q=F(q_ns(j),NS)
                        if 0<=q<s.T:
                            # Only the nearest one or two bands can intersect this short probe.
                            compiled=any(lo<=q<hi for lo,hi in bands[:2]+bands[-2:])
                            self.assertEqual(mode_at(s,j,eta,r),compiled)

    def test_terminal_started_operation_is_not_truncated_into_a_repair(self):
        s=self.s;j=s.W*20+7;q=F(q_ns(j),NS)
        end=q+s.E/2
        self.assertEqual(count(20,s.W,q,end),1)
        self.assertGreater(q+s.E,end)
        self.assertEqual(count(20,s.W,q,max(q,end-s.E)),0)

    def test_joint_service_is_more_than_mean_price(self):
        s=self.s;g=s.geometry();m=s.management()
        self.assertGreater(g['gap_after_app_s'],0);self.assertGreater(g['gap_before_next_control_s'],0)
        self.assertLess(g['total_peak_upper'],F(4,5))
        self.assertGreater(g['total_peak_upper'],F(64,100))
        for x in m['examples']:
            self.assertGreater(x['available_local_processing_s'],m['local_processing_budget_for_map_s'])
        # Spending a large positive-gain mean allowance on one poll does NOT meet d.
        b=s.upper(30)['u_limits']['1']/m['rates_upper_per_s']['check']
        self.assertGreater(b/g['management_chunk_budget_s']*g['frame_upper_s'],s.delay)

    def test_budget_display_is_conservative(self):
        for eta in (0,30,120,600,1200):
            for u in self.s.upper(eta)['u_limits'].values():
                shown=F(down(u*10**6))
                self.assertLessEqual(shown,u*10**6)
                self.assertLess(u*10**6-shown,F(1,100))

    def test_service_counts_unusable_end_of_slot(self):
        geom=self.s.geometry();cap=geom['management_chunk_budget_s']
        atomic=geom['management_atomic_limit_s'];progress=geom['guaranteed_management_progress_s']
        self.assertEqual(progress,cap-atomic)
        for atoms in ([atomic]*100,[F(16,NS),F(24,NS),F(1,NS)]*100):
            frames=1;used=F(0)
            for work in atoms:
                self.assertLessEqual(work,atomic)
                if used+work>cap:frames+=1;used=F(0)
                used+=work
            self.assertLessEqual(frames,ceil(sum(atoms,F(0))/progress)+1)
        # Two maximal atomics cannot fit, despite their 64 nominal ns sum.
        self.assertGreater(2*atomic,cap)
        self.assertLess(ceil(100*atomic/cap),100)


if __name__=='__main__':unittest.main()

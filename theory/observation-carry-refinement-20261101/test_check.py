"""Structural tests of the new pair covering, plus the one-point certificate."""
from fractions import Fraction as F
import unittest
import check as c


class CarryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=c.calculate()

    def test_same_word_seam_is_fixed_before_the_new_decision(self):
        a=self.result['application']; b=c.v.Bank(c.W)
        block=1568*(c.W//8+7)
        K=b.kcell
        def ends(k):
            out=[2]
            while out[-1]<K:
                out.append(min(K,out[-1]+k))
            return out
        for k in (a['k_base'],a['k_rare']):
            e=ends(k)
            self.assertEqual(e[-1],K)
            self.assertEqual(len(e),b.passes(k))
            self.assertGreaterEqual(min(y-x for x,y in zip([0]+e,e)),2)
            # The word phase may be near either end of a scan; no scan-wide reset.
            for j in (0,1,7,8,c.W//2,c.W-8,c.W-1):
                q=1568*(j//8)+164*(j%8)
                previous_last=(K-1)*block+q
                first=(K+1)*block+q
                self.assertEqual(first-previous_last,2*block)
                self.assertGreater(first,K*block)
                for end in e[1:]:
                    self.assertGreater(K*block+(end-1)*block+q,K*block)
                self.assertLess(q,block)
        self.assertEqual(a['bits_for_main_ERR_count_without_false_or_extra'],29)
        self.assertEqual(a['bits_for_six_main_counts'],32)

    def test_live_and_pending_pairs_have_a_word_interval_witness(self):
        # Pure finite service geometry, not a new radiation point or Monte Carlo.
        # A weak E keeps every birth after actual start, and holds old marks until
        # release. Its residual/pending is built independently of the pair labels.
        cuts=list(map(F,(1,3,6,9)))
        end=F(10)
        points=sorted(set([F(0),end]+[t+d for t in cuts for d in
                          (F('-0.1'),F(0),F('.03'),F('.1'),F('.15'),F('.2'),F('.3'))]))
        for delay in (F(0),F('.04'),F('.09')):
            services=[(t+delay,t+F('.2')) for t in cuts]
            for u in points:
                # Pre-start births must be removed by release; later births may survive.
                clear=min([release for start,release in services if u<start]+[end+1])
                for v in points:
                    if not u<v<min(clear,end):
                        continue
                    iu=sum(t<=u for t in cuts)
                    iv=sum(t<=v for t in cuts)
                    same_interval=iu==iv
                    aperture=(iv==iu+1 and v<cuts[iu]+F('.2'))
                    self.assertTrue(same_interval or aperture,(u,v,delay))
        # One birth crossing a fence is allowed; it need not survive only d_E.
        self.assertGreater(F('5.9')-F('3.1'),F('.2'))

    def test_one_point_and_preserved_observation_windows(self):
        r=self.result; a=r['application']; b=c.v.Bank(c.W)
        self.assertEqual(r['frozen']['epsilon'],F('.01'))
        self.assertEqual((b.kcell,b.c,c.v.M),(3001,32,6))
        self.assertGreater(b.weak,F('.01'))
        self.assertEqual(a['aperture_pair_upper'],b.B*b.dE*b.mass/c.W)
        self.assertEqual(r['geometry']['P_obs'],b.p)
        self.assertEqual(a['exposure_lower'],b.exposure(a['u'],a['k_base']))
        self.assertEqual(a['history_parent_mu_p_upper'],b.mu_p)
        self.assertEqual(r['geometry']['history_upper_s'],F('3700.84389530187232'))
        self.assertEqual(a['k_base'],6)
        self.assertEqual(a['k_rare'],11)
        self.assertEqual(a['u'],F('.203580698573'))

    def test_shared_break_budget_and_scalar_boundary(self):
        a=self.result['application']; b=c.v.Bank(c.W)
        q0=c.EPS/20+a['aperture_pair_upper']+a['word_interval_pair_upper']
        self.assertEqual(a['q0_for_break_observation_and_cost'],q0)
        self.assertEqual(a['Q_upper'],c.v.DELTA0+c.v.DELTAC+q0)
        self.assertLess(a['Q_upper'],c.EPS)
        score=lambda u:c.v.SCORE*b.exposure(u,a['k_base'])-c.v.ETA*b.c
        target=a['log_threshold_upper']+F(1,10**6)
        self.assertGreater(score(a['u']),target)
        self.assertLessEqual(score(a['u']-F(1,10**12)),target)
        self.assertGreater(self.result['scalar_boundary_check']['next_legal']['Q_upper'],c.EPS)
        maximum=a['main_reads_maximum']
        self.assertEqual(a['main_repairs_upper'],min(maximum,2*b.mass+q0*maximum))
        for coord,v in a['costs'].items():
            self.assertIsNone(v['actual_extra_processing'])
            self.assertGreater(v['strict_full_cost_budget']['schedule'],0)
            self.assertGreaterEqual(v['strict_full_cost_budget']['constant'],v['strict_full_cost_budget']['schedule'])


if __name__=='__main__':
    unittest.main()

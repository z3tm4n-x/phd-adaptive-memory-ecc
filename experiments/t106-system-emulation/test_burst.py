"""Addressed checks of the declared normalized input, not physics validation."""
import gzip
import json
import math
import unittest
from burst_inputs import HERE, BG, SOLAR, BOUND, growth_bound


class BurstInputTests(unittest.TestCase):
    def test_slope_below_and_above_ell(self):
        self.assertAlmostEqual(growth_bound([.0001,.0007]),.01)
        self.assertAlmostEqual(growth_bound([.001,.004]),.05)
        self.assertEqual(growth_bound([.004,.001]),0)

    def test_independent_profile_accounting(self):
        with gzip.open(HERE/'outputs/t67-profile.json.gz','rt') as f:original=json.load(f)['records']
        with gzip.open(HERE/'outputs/burst-rate.json.gz','rt') as f:rate=json.load(f)
        r=rate['rate_per_array_s'];peak=max(x[1] for x in original)
        self.assertEqual(len(r),6066)
        self.assertEqual(rate['utc_start'],original[0][0])
        for i,x in enumerate(original):self.assertAlmostEqual(r[i],BG+SOLAR*x[1]/peak,places=16)
        self.assertEqual(r[-1],r[-2]);self.assertAlmostEqual(max(r),BOUND,places=16)
        audit=json.loads((HERE/'outputs/burst-input.json').read_text())
        # Midpoint integral is exact for an affine function. Simpson is exact
        # for its square, independent of the production closed expressions.
        n=sum(60*(a+b)/2 for a,b in zip(r,r[1:]))
        s2=sum(10*(a*a+4*((a+b)/2)**2+b*b) for a,b in zip(r,r[1:]))
        self.assertTrue(math.isclose(n,audit['expected_parents'],rel_tol=1e-13))
        self.assertTrue(math.isclose(s2,audit['integral_rate_squared_per_s'],rel_tol=1e-13))
        h=lambda x:x/.001 if x<=.001 else 1+math.log(x/.001)
        bound=0
        for a,b in zip(r,r[1:]):
            # Dense transformed finite differences are an independent lower
            # diagnostic; exact segment bound is tested analytically above.
            for k in range(10):
                x=a+(b-a)*k/10;y=a+(b-a)*(k+1)/10
                bound=max(bound,(h(y)-h(x))/6)
        self.assertLessEqual(bound,audit['max_H_l_relative_growth_per_s']+1e-13)
        self.assertLess(audit['max_H_l_relative_growth_per_s'],.048)

    def test_stream_full38_and_time(self):
        with gzip.open(HERE/'outputs/burst-stimulus.json.gz','rt') as f:s=json.load(f)
        events=s['injections']
        self.assertEqual(s['horizon_ns'],6065*60*10**9)
        self.assertEqual(s['applications'],[])
        self.assertTrue(all(0<=e['word']<524288 and 0<=e['bit']<38 and e['at_ns']%4==2 for e in events))
        self.assertTrue(all(a['at_ns']<=b['at_ns'] for a,b in zip(events,events[1:])))
        self.assertEqual([e['parent'] for e in events],list(range(1,len(events)+1)))
        self.assertEqual({e['bit'] for e in events},set(range(38)))
        # This is a distribution sanity check, not an empirical NHPP proof.
        counts=[sum(e['bit']==b for e in events) for b in range(38)]
        mean=len(events)/38
        self.assertLess(sum((x-mean)**2/mean for x in counts),100)


if __name__=='__main__':unittest.main()

import math
import unittest
import numpy as np
from counts import Integral, available, weight_one
from onsets import inspect
from risk_inputs import grow, ticks, check, input_rows, HERE, fixed_necessity
import json
from controller import BurstController, word_phases, scalar_envelope_check


class CountChecks(unittest.TestCase):
    def test_lattice_against_independent_explicit_words(self):
        f = Integral([0., .1, 2., .03, 1.], 3.)
        for a in [.05, 2., 10., 60.]:
            for phase in [0., .5, .999999]:
                for elapsed in [0., .1, 3., 8., 14.9]:
                    for delay in [0., .2, 20.]:
                        w = 17
                        visit = phase*a+np.arange(w)*a/w
                        last = visit + np.floor((elapsed-delay-visit)/a)*a
                        expected = float(np.mean(f(last))) if elapsed >= delay else 0.
                        got = available(f, elapsed, a, phase, delay, w)
                        self.assertAlmostEqual(expected, got['visited_tokens_expected'], places=11)
                        self.assertLessEqual(got['phase_free_visited_lower'], got['visited_tokens_expected']+1e-12)
                        self.assertLessEqual(got['visited_tokens_expected'], got['phase_free_visited_upper']+1e-12)

    def test_exact_xor_and_deficit(self):
        for n in [2, 32, 38, 39]:
            for mu in [0., 1e-8, .01, .5, 3.]:
                p1 = weight_one(mu, n)
                self.assertGreaterEqual(p1+1e-15, max(0., mu-mu*mu))
                self.assertLessEqual(p1, mu+1e-15)
        # Enumerate number of flips for n=2 via odd total = weight one.
        self.assertAlmostEqual(weight_one(.4, 2), (1-math.exp(-.8))/2)

    def test_missing_not_zero(self):
        with self.assertRaises(ValueError): Integral([1., float('nan')], 60)

    def test_packed_phases(self):
        f = Integral([1.,.1,2.,.03,1.],3.)
        for t in [0.,.02,3.,6.,6.02,9.,14.9]:
            for phase in [0.,.5,.999999]:
                w,a,span=19,6.,.05
                v=phase*a+np.arange(w)*span/w
                last=v+np.floor((t-v)/a)*a
                expected=float(np.mean(f(last)))
                actual=available(f,t,a,phase,0.,w,span)['visited_tokens_expected']
                self.assertAlmostEqual(actual,expected,places=10)


class SegmentChecks(unittest.TestCase):
    def call(self, x, valid=None, sig=None, peak=100):
        n = len(x)
        return inspect(np.arange(n)*60, np.asarray(x), np.ones(n, bool) if valid is None else valid,
                       np.zeros(n) if sig is None else sig, 60, .1, 180, [.5], 0, n*60, peak)

    def test_quiet_repeat_postpeak(self):
        r, _ = self.call([.01,.01,.01,.2,.6,.3,.7,.05,.7], peak=370)
        self.assertEqual([a['segment_type'] for a in r], ['primary_entry','repeat_pre_peak','post_peak_growth'])
        self.assertEqual([a['quiet_root_index'] for a in r], [3,3,3])

    def test_gap_breaks_history(self):
        r, _ = self.call([.01,.01,.01,.2,.6], valid=[1,1,0,1,1])
        self.assertIsNone(r[0]['quiet_root_index'])
        r, _ = self.call([.01,.01,.01,.2,.6], sig=[0,0,0,1,1])
        self.assertIsNone(r[0]['quiet_root_index'])

    def test_not_reached_and_left_censor(self):
        r,s = self.call([.6,.7])
        self.assertEqual(r[0]['status'], 'left_censored_target')
        self.assertIsNone(r[0]['quiet_root_index'])
        r,s = self.call([.01,.01])
        self.assertEqual(s[0]['status'], 'not_reached')


class RiskChecks(unittest.TestCase):
    def test_rounding_and_growth(self):
        self.assertEqual(ticks(.066545847861,1e-8,False),6654584)
        self.assertEqual(ticks(90e-9,1e-8,True),9)
        self.assertEqual(ticks(90.001e-9,1e-8,True),10)
        self.assertAlmostEqual(grow(.0001,.001,.048,2.1,.35),.0002008)
        self.assertEqual(grow(.0001,.001,.048,1e6,.35),.35)
        self.assertEqual(grow(0.,.001,0.,30.,.35),0.)

    def test_hidden_failure_cost_and_explicit_method_change(self):
        config=json.loads((HERE/'config.json').read_text())
        c,g=config['conditional_r0a'],config['method_parameter_grid']
        for r in input_rows(config):
            old=check(c,g,r,6.,.05,.0001,2.,10.)
            new=check(c,g,r,6.,.05,.0001,2.,5.)
            self.assertFalse(old['conditional_quiet_pass'])
            self.assertTrue(new['conditional_algebra_pass'])
            self.assertGreater(new['total_risk_upper_conditional'],new['pair_risk_upper_conditional'])
            self.assertLess(new['calendar_pass_s'],.05)
            slow={**c,'read_s':.000000120256,'write_s':.000000120256}
            bad=check(slow,g,r,6.,.05,.0001,2.,5.)
            self.assertFalse(bad['resources_and_nested_grid'])
            self.assertFalse(bad['conditional_quiet_pass'])

    def test_constant_necessity_is_separate_from_sufficient_test(self):
        config=json.loads((HERE/'config.json').read_text())
        for r in input_rows(config):
            z=fixed_necessity(config['conditional_r0a'],r)
            self.assertTrue(z['excludes_constant_1pct_on_conditional_class'])
            self.assertGreater(z['first_exceedance_probability_lower'],.001)


class ControllerChecks(unittest.TestCase):
    def test_ERR_adds_without_postponing_reference_and_missing_fails_safe(self):
        a=BurstController(600,5,500)
        b=BurstController(600,5,500)
        for k in range(1800):
            kw=dict(alarm=k==200,missing=k==1000,quiet_history_ticks=k if k<200 else max(0,k-1000))
            ref=a.step(k,**kw)
            got=b.step(k,err=k in [105,405,1205],**kw)
            self.assertEqual(ref['reference_pass'],got['reference_pass'])
            self.assertFalse(ref['reference_pass'] and not got['actual_pass'])
            if k==1000:self.assertTrue(got['monitor_high'])

    def test_phases_full_W_resource_and_application_gap(self):
        p=word_phases(2**19,9,10,5)
        self.assertLessEqual(p[-1]+9,5000000)
        self.assertTrue(all(v-u>=9 for u,v in zip(p,p[1:])))
        self.assertTrue(all(p[k]-p[k-1]-9==5 for k in range(10,len(p),10)))

    def test_piecewise_integral_independent(self):
        # Three word phases and a deliberately long interval at low rate.
        times=list(range(13)); rates=[.1]*6+[1.]*6
        fences=[[3,6,7,8,9,10,11],[2,5,6,7,8,9,10,11],[1,4,6,7,8,9,10,11]]
        out=scalar_envelope_check(times,rates,fences,3,1,.1)
        self.assertTrue(out['all_long_intervals_below_cap'])
        i2=sum(x*x for x in rates)
        low_i2=sum(x*x for x in rates if x<=.1)
        self.assertLessEqual(out['sum_exposure_squares'],3*(i2+2*low_i2)+1e-12)
        rates[4]=2.
        bad=scalar_envelope_check(times,rates,fences,3,1,.1)
        self.assertFalse(bad['all_long_intervals_below_cap'])


if __name__ == '__main__': unittest.main()

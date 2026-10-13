import math
import unittest
import numpy as np
from scipy.stats import poisson
from moments import gram_moments,assemble,pack,q90,overflow_bound,shape_transfer,rolling_moments


class MomentTests(unittest.TestCase):
    def test_rolling_odd_and_even_endpoints(self):
        y=np.array([1.,5.,2.,4.,3.,9.,1.])
        for width in (1,2,3,4,7):
            n,s,p=rolling_moments(y,width,2.)
            windows=[y[i:i+width] for i in range(len(y)-width+1)]
            np.testing.assert_array_equal(n,[2*w.sum() for w in windows])
            np.testing.assert_array_equal(s,[2*(w*w).sum() for w in windows])
            np.testing.assert_array_equal(p,[w.max() for w in windows])

    def test_full_square_has_all_six_cross_terms(self):
        x=np.array([[1.,2.,4.],[3.,1.,2.]])
        n,g=gram_moments(x,2.)
        a=assemble(.5,4.,n,g)
        self.assertEqual(a['S2'],2*((.5+7)**2+(.5+6)**2))
        self.assertGreater(a['solar_cross'],0)
        self.assertEqual(a['mixed_S2'],2*.5*n.sum())

    def test_nonoverlap_packing_matches_literal_history(self):
        counts=np.array([[1,2]])
        r=pack(counts,np.array([1.,2.]),np.array([2.,6.]),np.array([4.,18.]),
               np.array([2.,3.]),dict(mean=1.,mean_square=1.,peak=1.),.5,8.)
        literal=np.array([2.,3.,3.,3.,3.,1.,1.,1.])+.5
        self.assertEqual(r['F'][0],sum(literal))
        self.assertEqual(r['S2'][0],sum(literal**2))

    def test_zero_events_retains_offmask_and_background(self):
        r=pack(np.array([[0]]),np.array([2.]),np.array([3.]),np.array([5.]),
               np.array([2.]),dict(mean=1.,mean_square=1.,peak=1.),2.,10.)
        self.assertEqual(r['F'][0],30.)
        self.assertEqual(r['S2'][0],90.)

    def test_overflow_is_counted_not_conditioned_away(self):
        counts=np.array([[0],[0],[0],[0],[1],[1],[1],[1],[2],[2]])
        r=pack(counts,np.array([6.]),np.array([6.]),np.array([6.]),np.array([1.]),
               dict(mean=0.,mean_square=0.,peak=0.),0.,10.)
        self.assertEqual(len(r['S2']),10)
        self.assertEqual(r['overflow'].sum(),2)
        self.assertTrue(math.isinf(q90(r['S2'])[0]))
        self.assertTrue(np.isfinite(q90(r['S2'][~r['overflow']])[0]))

    def test_exact_capacity_fits(self):
        r=pack(np.array([[2]]),np.array([5.]),np.array([5.]),np.array([5.]),np.array([1.]),
               dict(mean=0.,mean_square=0.,peak=100.),0.,10.)
        self.assertFalse(r['overflow'][0])
        self.assertEqual(r['S2'][0],10.)
        self.assertEqual(r['peak'][0],1.)

    def test_poisson_overflow_bound_encloses_exact_tail(self):
        b=overflow_bound(100.56812028745298,775800.,315576000.)
        self.assertEqual(b['event_count_necessary'],407)
        self.assertLessEqual(poisson.sf(406,100.56812028745298),b['probability_upper'])
        self.assertLess(b['log_probability_upper'],-260)

    def test_shape_transfer_preserves_background_cross(self):
        a=shape_transfer(2.,10.,100.,.5,100.)
        self.assertEqual(a,400+400+500)
        self.assertEqual(shape_transfer(2.,10.,100.,1.,100.)-a,500)

    def test_infeasible_shape_rejected(self):
        with self.assertRaises(ValueError):shape_transfer(0.,1.,100.,.1,100.)

    def test_rate_scale_does_not_change_ideal_potential(self):
        x=np.array([[.1],[4.],[.2]])
        n,g=gram_moments(x,1.)
        a=assemble(.3,3.,n,g);b=assemble(.9,3.,3*n,9*g)
        self.assertAlmostEqual(3*a['S2']/a['F']**2,3*b['S2']/b['F']**2)

    def test_ion_trace_is_frozen_under_low_energy_removal(self):
        # The isotope proxy remains r*(L+H); it is not recalibrated from H alone.
        from radiation import scenario
        parts={'H_low':2.,'H_high':1.,'LET_exclusive':3.}
        x=np.array([[2.,1.]])
        full,w,_,_=scenario(parts,parts,x,1.,1.,1.,1.)
        no,w0,_,_=scenario(parts,parts,x,1.,0.,1.,1.)
        np.testing.assert_array_equal(full[2],no[2])
        self.assertEqual(float((x@w)[0])-float((x@w0)[0]),2.)

    def test_marginal_quantile_product_is_not_joint(self):
        # One shared observation supplies both factors. Anti-alignment matters.
        peak=np.arange(1.,11.);fluence=peak[::-1]
        self.assertNotEqual(q90(peak*fluence)[0],q90(peak)[0]*q90(fluence)[0])

    def test_subbin_variance_leaves_first_moment(self):
        coarse=np.array([[2.]])
        refined=np.array([[0.],[4.]])
        n,g=gram_moments(coarse,2.);nr,gr=gram_moments(refined,1.)
        np.testing.assert_array_equal(n,nr)
        self.assertEqual(gr[0,0]-g[0,0],8.)


if __name__=='__main__':unittest.main()

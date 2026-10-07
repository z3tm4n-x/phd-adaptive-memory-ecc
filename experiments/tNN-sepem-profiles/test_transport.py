import unittest
import numpy as np
from scipy.integrate import quad
from transport import RangeTable, sigma, quadrature, Response, ENERGY, BITS, ANGULAR


class TransportTests(unittest.TestCase):
    def test_range_roundtrip_and_stopping(self):
        t=RangeTable()
        e=np.geomspace(.002,9000,500)
        np.testing.assert_allclose(t.inverse(t.range(e)),e,rtol=3e-14)
        self.assertEqual(float(t.residual(5.,3.)),0.)
        self.assertTrue(45 < t.inverse(3.) < 60)

    def test_pdi_not_lost(self):
        self.assertAlmostEqual(float(sigma(1)),1.27e-9,delta=1e-20)
        self.assertEqual(float(sigma(1,"no_pdi")),0.)
        self.assertGreater(float(sigma(1)),1000*float(sigma(184.)))

    def test_particle_conservation_independent_change_of_variable(self):
        t=RangeTable()
        # Flat incident spectrum; independent residual-range partitions give
        # exactly dEin, not a renormalized density of transmitted particles.
        a,b=40.,120.
        threshold=float(t.inverse(3.))
        expected=b-max(a,threshold)
        residual=t.residual(np.linspace(max(a,threshold),b,20001),3.)
        back=t.inverse(t.range(np.maximum(residual,.001))+3.)
        # The first residual is stopped; finite PSTAR lower endpoint retained.
        measured=np.sum(np.diff(back))
        self.assertAlmostEqual(measured,expected,delta=.001)
        self.assertLess(expected,b-a)

    def test_constant_cross_section_known_spectrum(self):
        # Independent analytic integral through a monotone range transform.
        t=RangeTable()
        lo=float(t.inverse(3.))
        analytic=1/lo-1/10000
        cuts=np.unique(np.r_[lo,t.energy[t.energy>lo],10000.])
        z,w=np.polynomial.legendre.leggauss(12)
        total=0.
        for a,b in zip(cuts[:-1],cuts[1:]):
            e=(a+b)/2+(b-a)/2*z
            total+=np.sum((b-a)/2*w/e**2)
        self.assertAlmostEqual(total,analytic,delta=1e-12)

    def test_narrow_pdi_independent_adaptive_integral(self):
        t=RangeTable()
        e,w,_,_=quadrature(t,3.,order=12)
        measured=np.sum(w*e**-3)
        # quad on separately inverted sigma/range boundaries; independent
        # integration and no moment lookup, but shared source tables disclosed.
        from transport import SIGMA_E
        breaks=np.unique(np.r_[float(t.inverse(3.)),t.inverse(3+t.range(SIGMA_E)),
                               t.energy,10000.])
        breaks=breaks[(breaks>=5)&(breaks<=10000)]
        independent=sum(quad(lambda x: float(sigma(t.residual(x,3.)))*x**-3,
                             a,b,epsabs=1e-23,epsrel=1e-7,limit=150)[0]
                        for a,b in zip(breaks[:-1],breaks[1:]))
        self.assertAlmostEqual(measured/independent,1.,delta=2e-5)

    def test_envelope_and_bohr(self):
        e=np.geomspace(.002,1000,10000)
        self.assertTrue(np.all(sigma(e,"step_envelope") >= sigma(e)*(1-1e-13)))
        t=RangeTable()
        sd=t.bohr_range_sd(3.)
        self.assertGreater(sd,0.)
        self.assertLess(sd,.2)

    def test_sigma_units_and_bits(self):
        self.assertEqual(BITS,19922944)
        self.assertAlmostEqual(ANGULAR,4*np.pi)


if __name__ == "__main__":
    unittest.main()

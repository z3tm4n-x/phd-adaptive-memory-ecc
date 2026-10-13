import math
import unittest
import numpy as np
from chain import (Spectrum,fold,proton_sigma,envelope,timeseries_moments,
                   unknown_residual_increment,probability_release,validate_components,BITS,T)
from calculate import legacy_row


class ChainTests(unittest.TestCase):
    def spectrum(self,angular='omni',product='flux',boundary='after_Al_before_BEOL'):
        return Spectrum(np.array([1.,3.]),np.array([2.,2.]),'E_MeV',product,angular,boundary,'H','analytic')

    def test_constant_fold_units(self):
        self.assertAlmostEqual(fold(self.spectrum(),lambda x:np.ones_like(x)*1e-10),4e-10*BITS,places=13)

    def test_solid_angle_once(self):
        sig=lambda x:np.ones_like(x)
        self.assertAlmostEqual(fold(self.spectrum('per_sr'),sig)/fold(self.spectrum(),sig),4*math.pi)

    def test_fluence_no_time_factor(self):
        sig=lambda x:np.ones_like(x)
        self.assertEqual(fold(self.spectrum(product='fluence'),sig),fold(self.spectrum(),sig))

    def test_word_normalization_once(self):
        sig=lambda x:np.ones_like(x)
        self.assertAlmostEqual(fold(self.spectrum(),sig)/fold(self.spectrum(),sig,check_ratio=0),38/32)

    def test_no_double_transport(self):
        with self.assertRaises(ValueError):
            fold(self.spectrum(),lambda e:e,rho=3)

    def test_no_implicit_transport(self):
        with self.assertRaises(ValueError):
            fold(self.spectrum(boundary='before_Al'),lambda e:e)

    def test_BEOL_boundary_rejected(self):
        with self.assertRaises(ValueError):
            self.spectrum(boundary='sensitive_volume')

    def test_partition(self):
        e=np.r_[np.geomspace(.1,1000,300),5.]
        np.testing.assert_allclose(proton_sigma(e),proton_sigma(e,'low')+proton_sigma(e,'high'),rtol=0,atol=0)

    def test_double_count_rejected(self):
        for names in [['H_full','H_high'],['H_low','H_low'],['LET_exclusive','He']]:
            with self.assertRaises(ValueError):validate_components(names)

    def test_square_full_sum(self):
        r=timeseries_moments(np.array([[1.,2.],[2.,1.]]),3.,background=.5)
        self.assertEqual(r['S2_s_inv'],6*3.5**2)
        self.assertEqual(r['gram_s_inv'][0][1],12.)

    def test_background_cross(self):
        e=envelope(2.,[3.],[15.],['H_full'],duration=10.)
        self.assertEqual(e['S2_upper_s_inv'],40+60+45)

    def test_envelope_achieved(self):
        e=envelope(.1,[2.,3.],[8.,12.],['H_low','H_high'],duration=10.)
        x=np.array([[2.,3.]]*4+[[0.,0.]]*6)
        self.assertAlmostEqual(e['S2_upper_s_inv'],timeseries_moments(x,1.,background=.1)['S2_s_inv'])

    def test_noncoincident_upper(self):
        x=np.array([[2.,0.],[0.,3.],[0.,0.]])
        m=timeseries_moments(x,1.)
        e=envelope(0,[2.,3.],m['N_components'],['H_low','H_high'],duration=3.)
        self.assertGreater(e['S2_upper_s_inv'],m['S2_s_inv'])

    def test_scaling_linear_and_square(self):
        x=np.array([[1.,2.],[0.,3.]])
        a=timeseries_moments(x,2.);b=timeseries_moments(x*38/32,2.)
        self.assertAlmostEqual(b['N']/a['N'],38/32)
        self.assertAlmostEqual(b['S2_s_inv']/a['S2_s_inv'],(38/32)**2)

    def test_subbin(self):
        # Same fluence: half-bin zero, half-bin double => S2 doubles.
        a=timeseries_moments(np.array([[2.]]),300.)
        b=timeseries_moments(np.array([[0.],[4.]]),150.)
        self.assertEqual(a['N'],b['N'])
        self.assertEqual(b['S2_s_inv'],2*a['S2_s_inv'])

    def test_unknown_not_zero(self):
        self.assertIsNone(probability_release(False,True,True,123.))
        self.assertIsNone(probability_release(True,False,True,123.))
        self.assertIsNone(probability_release(True,True,False,123.))
        self.assertEqual(unknown_residual_increment(100.,25.),125.)

    def test_invalid_nonfinite_negative(self):
        for value in [-1.,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):timeseries_moments(np.array([[value]]),300.)

    def test_impossible_moments(self):
        with self.assertRaises(ValueError):envelope(0,[1.],[2.],['H_full'],duration=1)
        with self.assertRaises(ValueError):envelope(0,[1.],[1.],['H_full'],duration=1,shape=[.1])

    def test_t127_regression(self):
        self.assertAlmostEqual(legacy_row(3.,'historical_HEP')['S2_upper_s_inv'],6939.003958627652,places=7)
        self.assertAlmostEqual(legacy_row(3.,'main_loglog')['S2_upper_s_inv'],41867.127059712766,places=7)


if __name__=='__main__':unittest.main()

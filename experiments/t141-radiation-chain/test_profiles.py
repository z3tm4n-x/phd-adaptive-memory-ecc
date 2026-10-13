import unittest
import numpy as np
from profiles import mission_values,statistics,BandResponse
from chain import T


class ProfileTests(unittest.TestCase):
    def test_common_spectrum_low_plus_high(self):
        response=BandResponse(order=12)
        v,flux=response.calculate(np.ones((1,11)))
        self.assertTrue(np.all(v>0));self.assertGreater(flux[0],0)
        self.assertEqual(v.shape,(1,4,2))

    def test_packed_history_exact_square(self):
        # Two non-overlapping events: 10s at2, 20s at3; off-time solar=1.
        events=np.array([[10,20,40,2],[20,60,180,3.]])
        counts=np.array([[1,1],[2,0]])
        off=dict(off_mean_s_inv=1.,off_mean_square_s_inv2=1.,off_peak_s_inv=1.)
        v=mission_values(counts,events,off,b=.5,c=2.)
        expected=10*4.5**2+20*6.5**2+(T-30)*2.5**2
        self.assertAlmostEqual(v['S2'][0],expected)
        self.assertAlmostEqual(v['N'][0],10*4.5+20*6.5+(T-30)*2.5)

    def test_no_overlap_without_room_rejected(self):
        with self.assertRaises(ValueError):
            mission_values(np.array([[2]]),np.array([[T,1.,1.,1.]]),
                dict(off_mean_s_inv=0.,off_mean_square_s_inv2=0.,off_peak_s_inv=0.),0.,1.)

    def test_mask_moments_partition(self):
        bands=np.array([[1.,2.],[1.,3.],[0.,2.],[1.,1.]])
        ev,off,solar=statistics(bands,[(1,3)],False)
        self.assertAlmostEqual(ev[:,1].sum()+off['off_N'],solar.sum()*300)
        self.assertAlmostEqual(ev[:,2].sum()+off['off_S2_s_inv'],solar@solar*300)
        self.assertAlmostEqual(ev[0,2],ev[0,6]+ev[0,7]+ev[0,8])


if __name__=='__main__':unittest.main()

import unittest
from pathlib import Path
import numpy as np
from cosrad_rate_reconstruction import *
P=Path(__file__).resolve().parent
class TestTargets(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.g=load_phase_a(P/'cosrad_input_cross_sections.csv')
 def test_direct_nodes(self):
  f=direct_point_model(self.g['W_00_01']); self.assertAlmostEqual(float(f(np.array([33]))[0]),0.0,15); self.assertAlmostEqual(float(f(np.array([42]))[0]),1.0689966441151094e-4,15); self.assertAlmostEqual(float(f(np.array([57]))[0]),3.342767046184631e-4,15)
 def test_zero_mapping_point(self): self.assertEqual(float(direct_point_model(self.g['W_01_02'])(np.array([57.]))[0]),0.0)
 def test_accumulation_nodes(self):
  g=self.g['W_00_01']; f=accumulation_structured_model(g); self.assertTrue(np.allclose(f(g.LET_MeV_cm2_mg.to_numpy(float)),g.sigma_accumulation_point_cm2.to_numpy(float),rtol=2e-15,atol=1e-14))
 def test_data_only_and_proton_contract(self): self.assertEqual(N_BITS,2**24); self.assertEqual(PROTON_GEOMETRIC_FACTOR,0.5); self.assertEqual(PROTON_BIT_SIGMA_CM2,8e-14)
if __name__=='__main__':unittest.main()

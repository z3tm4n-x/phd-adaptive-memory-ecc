import unittest
from pathlib import Path
import pandas as pd,numpy as np
P=Path(__file__).resolve().parent
class TestBoundary(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.d=pd.read_csv(P/'shielding_boundary_summary.csv');cls.sep=pd.read_csv(P/'sep_peak_rates.csv')
 def test_acs_boundary(self):
  q=self.d[(self.d.mapping_id=='W_00_01')&(self.d.estimate_type=='ARTICLE_CONFIDENCE_STYLE')&(self.d.rate_reconstruction_route=='SPECTRAL_EXTERNAL_CONVOLUTION')].iloc[0];self.assertEqual(q.fD_equals_1_grid_low,2.0);self.assertEqual(q.fD_equals_1_grid_high,2.25);self.assertGreater(q.fD_equals_1_interp,2.0);self.assertLess(q.fD_equals_1_interp,2.25)
 def test_point_boundary_below_grid(self):
  q=self.d[(self.d.mapping_id=='W_00_01')&(self.d.estimate_type=='POINT')&(self.d.rate_reconstruction_route=='SPECTRAL_EXTERNAL_CONVOLUTION')].iloc[0];self.assertEqual(q.boundary_status,'BELOW_GRID');self.assertEqual(q.first_positive_period_shield,1.5)
 def test_sep_is_peak_only(self): self.assertTrue(self.sep.status.str.contains('NO-MISSION-INTEGRATION-WITHOUT-DURATION').all())
if __name__=='__main__':unittest.main()

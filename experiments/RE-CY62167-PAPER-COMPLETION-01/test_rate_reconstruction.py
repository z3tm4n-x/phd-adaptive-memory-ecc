import os,unittest
from pathlib import Path
import numpy as np,pandas as pd
from cosrad_parser import load_package
from cosrad_rate_reconstruction import *
P=Path(__file__).resolve().parent
class TestRates(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.pkg=load_package(Path(os.environ['CY62167_COSRAD_RESULTS'])); cls.g=load_phase_a(P/'cosrad_input_cross_sections.csv'); cls.rows=pd.DataFrame(spectral_rows(cls.pkg,cls.g,'GCR'))
 def test_nonnegative(self): self.assertTrue((self.rows['nu_direct_total_s-1']>=0).all()); self.assertTrue((self.rows['nu_accumulation_total_bit_s-1']>=0).all())
 def test_mapping_heavy_ion_equality(self):
  a=self.rows[(self.rows.mapping_id=='W_00_01')&(self.rows.estimate_type=='POINT')]['nu_direct_HI_s-1'].to_numpy();b=self.rows[(self.rows.mapping_id=='W_00_11')&(self.rows.estimate_type=='POINT')]['nu_direct_HI_s-1'].to_numpy();self.assertTrue(np.allclose(a,b,rtol=0,atol=1e-25))
 def test_legacy_anchor_rates(self):
  q=self.rows[(self.rows.mapping_id=='W_00_01')&(self.rows.estimate_type=='ARTICLE_CONFIDENCE_STYLE')];
  got={float(r.shield_g_cm2):r for _,r in q.iterrows()}; self.assertAlmostEqual(got[2.5]['nu_direct_total_s-1'],2.7972157e-12,rel_tol:=None) if False else self.assertLess(abs(got[2.5]['nu_direct_total_s-1']/2.797e-12-1),0.001)
 def test_proton_is_separate_model(self):
  q=self.rows[(self.rows.mapping_id=='W_00_01')&(self.rows.estimate_type=='POINT')&(np.isclose(self.rows.shield_g_cm2,2.5))].iloc[0]; self.assertGreater(q['nu_accumulation_proton_bit_s-1'],0); self.assertLess(q['nu_accumulation_proton_bit_s-1']/q['nu_accumulation_total_bit_s-1'],0.05)
if __name__=='__main__':unittest.main()

import os,tempfile,unittest,zipfile
from pathlib import Path
import numpy as np
from cosrad_parser import load_package,SHIELDS,THRESHOLDS
class TestParser(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.path=Path(os.environ['CY62167_COSRAD_RESULTS']); cls.pkg=load_package(cls.path)
 def test_spectra_columns(self):
  for n in ['gl_x.txt','gp_x.txt','sl_x.txt','sp_x.txt']:
   s=self.pkg.spectra[n]; self.assertEqual(s.values.shape[1],9); self.assertTrue(np.allclose(s.shields,SHIELDS))
 def test_response_columns_and_sigma(self):
  for r in self.pkg.responses.values(): self.assertTrue(np.allclose(r.shields,SHIELDS)); self.assertEqual(r.bit,1.0); self.assertEqual(r.sigma_m_cm2,1.0); self.assertTrue(np.allclose(r.proton_rate+r.ion_rate,r.sum_rate,rtol=0.02,atol=1e-20))
 def test_gcr_sep_are_distinct(self):
  g=self.pkg.spectra['gl_x.txt']; s=self.pkg.spectra['sl_x.txt']; self.assertNotEqual(g.values.shape,s.values.shape); self.assertNotEqual(float(g.values.sum()),float(s.values.sum()))
 def test_file_order_independence(self):
  with tempfile.TemporaryDirectory() as td:
   q=Path(td)/'rev.zip'
   with zipfile.ZipFile(self.path) as zin, zipfile.ZipFile(q,'w') as zout:
    for i in reversed([i for i in zin.infolist() if not i.is_dir()]): zout.writestr(i.filename,zin.read(i.filename))
   b=load_package(q,verify_sha=False)
   self.assertTrue(np.array_equal(b.spectra['gl_x.txt'].x,self.pkg.spectra['gl_x.txt'].x)); self.assertTrue(np.array_equal(b.responses[('GCR',33.0)].ion_rate,self.pkg.responses[('GCR',33.0)].ion_rate))
if __name__=='__main__':unittest.main()

import os,unittest
from pathlib import Path
from cosrad_parser import load_package
from cosrad_operator import let_unit_invariance,kernel_g
class TestUnits(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.pkg=load_package(Path(os.environ['CY62167_COSRAD_RESULTS']))
 def test_jacobian_invariance_gcr(self):
  s=self.pkg.spectra['gl_x.txt']; vals=[let_unit_invariance(s.x,s.values[:,j],lambda L:kernel_g(L,33))[2] for j in range(9)]; self.assertLess(max(vals),1e-12)
 def test_jacobian_invariance_sep(self):
  s=self.pkg.spectra['sl_x.txt']; vals=[let_unit_invariance(s.x,s.values[:,j],lambda L:kernel_g(L,10))[2] for j in range(9)]; self.assertLess(max(vals),1e-12)
if __name__=='__main__':unittest.main()

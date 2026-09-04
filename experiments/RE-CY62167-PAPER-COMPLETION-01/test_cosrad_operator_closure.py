import os,unittest
from pathlib import Path
from cosrad_parser import load_package
from cosrad_operator import operator_closure
class TestClosure(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.rows=operator_closure(load_package(Path(os.environ['CY62167_COSRAD_RESULTS'])))
 def test_all_cases_present(self): self.assertEqual(len(self.rows),216)
 def test_not_closed(self): self.assertTrue(any(r['closure_status']=='SPECTRAL_OPERATOR_NOT_CLOSED' for r in self.rows)); self.assertGreater(max(r['absolute_relative_difference'] for r in self.rows if r['environment']=='GCR'),0.9)
 def test_sep_not_closed(self): self.assertGreaterEqual(max(r['absolute_relative_difference'] for r in self.rows if r['environment']=='SEP'),0.99)
if __name__=='__main__':unittest.main()

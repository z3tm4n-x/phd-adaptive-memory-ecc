import json,os,unittest
from pathlib import Path
from cosrad_parser import load_package,scenario_manifest,COSRAD_SHA256,SHIELDS,THRESHOLDS
P=Path(__file__).resolve().parent
class TestManifest(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.pkg=load_package(Path(os.environ['CY62167_COSRAD_RESULTS'])); cls.m=scenario_manifest(cls.pkg)
 def test_fingerprint_and_members(self): self.assertEqual(self.pkg.sha256,COSRAD_SHA256); self.assertEqual(len(self.pkg.members),38)
 def test_scenario(self): self.assertEqual(self.m['scenario']['apogee_km'],36000); self.assertEqual(self.m['scenario']['GCR_solar_cycle_number'],'even'); self.assertEqual(self.m['scenario']['SEP_probability'],0.1)
 def test_grids(self): self.assertEqual(self.m['shielding_grid_g_cm2'],list(SHIELDS)); self.assertEqual(self.m['unit_response_thresholds_MeV_cm2_mg'],list(THRESHOLDS))
 def test_rounding_015(self):
  x=[r for r in self.m['threshold_printing_audit'] if r['PI_declared_L0']==0.15]; self.assertEqual(len(x),2); self.assertTrue(all(r['COSRAD_printed_L0']==0.2 and r['status']=='OUTPUT_FORMAT_ROUNDING' for r in x))
if __name__=='__main__':unittest.main()

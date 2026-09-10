import os,unittest
from pathlib import Path
import pandas as pd,numpy as np
from cosrad_parser import load_package
from cosrad_rate_reconstruction import load_phase_a
from cosrad_event_mixture import event_weights
P=Path(__file__).resolve().parent
class TestWeights(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.rows=pd.DataFrame(event_weights(load_package(Path(os.environ['CY62167_COSRAD_RESULTS'])),load_phase_a(P/'cosrad_input_cross_sections.csv'),'GCR'))
 def test_conservation(self):
  for _,g in self.rows.groupby(['shield_g_cm2','mapping_id']):
   self.assertAlmostEqual(g.lambda_registered_event_s_1.sum() if False else g['lambda_registered_event_s-1'].sum(),g['event_rate_total_s-1'].iloc[0],places=12)
   self.assertTrue(np.allclose(g['lambda_direct_registered_s-1']+g['lambda_residual_event_s-1'],g['lambda_registered_event_s-1'],rtol=1e-12,atol=1e-20))
 def test_reference_blocker_label(self): self.assertTrue(self.rows.status.str.contains('TAU_MAX_REFERENCE_BLOCKED_BY_COSRAD_OPERATOR_SEMANTICS').all())
if __name__=='__main__':unittest.main()

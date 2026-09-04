import unittest
from pathlib import Path
import numpy as np,pandas as pd
from run_phase_b import BETA,T,QDOP,R1U,R2U
P=Path(__file__).resolve().parent
class TestGeo(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.b=pd.read_csv(P/'geo_bound_results.csv'); cls.r=pd.read_csv(P/'resource_results.csv'); cls.ref=pd.read_csv(P/'geo_reference_results.csv'); cls.leg=pd.read_csv(P/'legacy_article_regression.csv')
 def test_beta(self): self.assertEqual(BETA,31/(2*2**24))
 def test_acs_transition_and_tau(self):
  q=self.b[(self.b.mapping_id=='W_00_01')&(self.b.estimate_type=='ARTICLE_CONFIDENCE_STYLE')&(self.b.rate_reconstruction_route=='SPECTRAL_EXTERNAL_CONVOLUTION')]; a=q[np.isclose(q.shield_g_cm2,2.0)].iloc[0];b=q[np.isclose(q.shield_g_cm2,2.5)].iloc[0];c=q[np.isclose(q.shield_g_cm2,3.0)].iloc[0];self.assertEqual(a.bound_status,'DIRECT-BOUND-EXHAUSTED');self.assertLess(abs(b.tau_max_U_s-20.5),0.1);self.assertLess(abs(c.tau_max_U_s-45.7),0.1)
 def test_reference_blocked(self): self.assertTrue((self.ref.reference_status=='TAU_MAX_REFERENCE_BLOCKED_BY_COSRAD_OPERATOR_SEMANTICS').all()); self.assertTrue((self.ref.reference_comparison_status=='REFERENCE-NOT-AVAILABLE').all())
 def test_architecture_and_old_resource(self): self.assertEqual(R1U,0.04718592);self.assertEqual(R2U,0.18874368); self.assertTrue((self.r.architecture_status=='ARCHITECTURALLY-FEASIBLE').all()); x=self.leg[self.leg.quantity=='R2U_interface_percent_at_tau_20s'].iloc[0]; self.assertAlmostEqual(float(x.phase_B_value),0.9437184,12)
if __name__=='__main__':unittest.main()

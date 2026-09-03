import math, unittest
from tau_bound import BETA, q_upper, tau_max_upper, direct_budget_fraction, direct_log_sensitivity
class TestTauBound(unittest.TestCase):
    def test_beta(self): self.assertEqual(BETA,31/(2*2**24))
    def test_monotone_tau(self):
        vals=[q_upper(3.156e8,t,1e-13,2e-5) for t in (1,2,10,100)]
        self.assertTrue(all(b>a for a,b in zip(vals,vals[1:])))
    def test_direct_exhausted(self):
        tau,status=tau_max_upper(1e-3/3.156e8,1e-5)
        self.assertIsNone(tau); self.assertEqual(status,'DIRECT-BOUND-EXHAUSTED')
    def test_sensitivity_no_special_half_threshold(self):
        s,status=direct_log_sensitivity(0.5)
        self.assertEqual(s,-1.0); self.assertEqual(status,'DEFINED')
if __name__=='__main__': unittest.main()

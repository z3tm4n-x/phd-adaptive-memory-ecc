import unittest
from resource_model import N_READ_R1,N_READ_R2,tau_min_arch,old_article_interface_fraction,resource_at_period,TIMING_AUDIT
class TestResourceModel(unittest.TestCase):
    def test_read_ratio(self): self.assertEqual(N_READ_R2/N_READ_R1,4)
    def test_tau_min(self):
        self.assertAlmostEqual(tau_min_arch('R1','U')[0],0.04718592,places=12)
        self.assertAlmostEqual(tau_min_arch('R2','U')[0],0.18874368,places=12)
        self.assertAlmostEqual(tau_min_arch('R1','E')[0],0.02359296,places=12)
        self.assertAlmostEqual(tau_min_arch('R2','E')[0],0.09437184,places=12)
    def test_old_percentages(self):
        self.assertAlmostEqual(old_article_interface_fraction(20)*100,0.9437184,places=10)
        self.assertAlmostEqual(old_article_interface_fraction(45)*100,0.4194304,places=10)
    def test_architecture_status(self):
        self.assertEqual(resource_at_period(0.1,'R2','U')['architecture_status'],'ARCHITECTURALLY-INFEASIBLE-FOR-DECLARED-SCAN')
        self.assertEqual(resource_at_period(1,'R2','U')['architecture_status'],'ARCHITECTURALLY-FEASIBLE')
    def test_timing_traceability(self):
        names={r['parameter'] for r in TIMING_AUDIT}
        self.assertTrue({'tRC','tWC','tAW','tPWE','tSD','read_write_transition_gap'} <= names)
if __name__=='__main__': unittest.main()

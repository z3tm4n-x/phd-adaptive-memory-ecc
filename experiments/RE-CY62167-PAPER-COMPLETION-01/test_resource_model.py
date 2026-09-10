import unittest
from resource_model import N_READ_R1,N_READ_R2,tau_min_arch,old_article_interface_fraction,resource_at_period,resource_semantics,TIMING_AUDIT
class TestResourceModel(unittest.TestCase):
    def test_read_ratio(self): self.assertEqual(N_READ_R2/N_READ_R1,4)
    def test_frozen_numeric_floors(self):
        self.assertAlmostEqual(tau_min_arch('R1','U')[0],0.04718592,places=12)
        self.assertAlmostEqual(tau_min_arch('R2','U')[0],0.18874368,places=12)
        self.assertAlmostEqual(tau_min_arch('R1','E')[0],0.02359296,places=12)
        self.assertAlmostEqual(tau_min_arch('R2','E')[0],0.09437184,places=12)
    def test_old_percentages_unchanged(self):
        self.assertAlmostEqual(old_article_interface_fraction(20)*100,0.9437184,places=10)
        self.assertAlmostEqual(old_article_interface_fraction(45)*100,0.4194304,places=10)
    def test_unconditional_full_pass_status(self):
        self.assertEqual(resource_at_period(0.1,'R2','U')['architecture_status'],'ARCHITECTURALLY-INFEASIBLE-FOR-DECLARED-SCAN')
        self.assertEqual(resource_at_period(1,'R2','U')['architecture_status'],'ARCHITECTURALLY-FEASIBLE')
    def test_err_read_only_is_not_exact_total(self):
        r=resource_at_period(1,'R2','E')
        self.assertEqual(r['resource_value_semantics'],'READ-ONLY-LOWER-BOUND')
        self.assertEqual(r['interface_value_semantics'],'READ-ONLY-LOWER-BOUND')
        self.assertEqual(r['write_cost_status'],'UNKNOWN-EXPECTED-WRITE-COST')
        self.assertEqual(r['expected_total_cost_status'],'UNKNOWN-WITHOUT-ERR-WRITE-MODEL')
        self.assertEqual(r['architecture_status'],'NECESSARY-READ-TIME-FEASIBLE')
        self.assertTrue(r['sufficient_full_pass_feasible'])
        self.assertAlmostEqual(r['worst_case_full_pass_bound_s'],0.18874368,places=12)
    def test_timing_traceability(self):
        names={r['parameter'] for r in TIMING_AUDIT}; self.assertTrue({'tRC','tWC','tAW','tPWE','tSD','read_write_transition_gap'} <= names)
if __name__=='__main__': unittest.main()

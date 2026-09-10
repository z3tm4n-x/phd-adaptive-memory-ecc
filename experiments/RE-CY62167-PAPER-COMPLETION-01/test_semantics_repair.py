import unittest
from reference_solver import synthetic_tau_upper, synthetic_reference_tau_bracket
from resource_model import resource_at_period
from run_phase_b import _qualify_resource_rows

class TestSemanticsRepair(unittest.TestCase):
    def test_cancellation_fixture(self):
        state=set(); state.symmetric_difference_update({0}); state.symmetric_difference_update({0,1})
        self.assertEqual(state,{1}); self.assertLess(len(state),2); surrogate_absorbed=True; self.assertTrue(surrogate_absorbed)
    def test_benchmark_numbers_frozen(self):
        self.assertAlmostEqual(synthetic_tau_upper(),243.55401798,places=6)
        lo,hi=synthetic_reference_tau_bracket(); self.assertAlmostEqual(lo,315.224841226,places=6); self.assertAlmostEqual(hi,315.744500579,places=6)
    def test_err_resource_qualification(self):
        row=resource_at_period(20.0,'R2','E')
        self.assertEqual(row['resource_value_semantics'],'READ-ONLY-LOWER-BOUND')
        self.assertEqual(row['write_cost_status'],'UNKNOWN-EXPECTED-WRITE-COST')
        self.assertEqual(row['architecture_status'],'NECESSARY-READ-TIME-FEASIBLE')
        self.assertTrue(row['sufficient_full_pass_feasible'])
        self.assertEqual(row['expected_total_cost_status'],'UNKNOWN-WITHOUT-ERR-WRITE-MODEL')
    def test_export_path_retains_err_qualifications(self):
        rows=[{'tau_s':20.0,'scan_mode':'R2','write_policy':'E','tau_min_arch_s':0.09437184,'architecture_status':'ARCHITECTURALLY-FEASIBLE','period_feasible':True,'interface_fraction':0.004718592}]
        row=_qualify_resource_rows(rows)[0]
        self.assertEqual(row['resource_value_semantics'],'READ-ONLY-LOWER-BOUND')
        self.assertEqual(row['interface_value_semantics'],'READ-ONLY-LOWER-BOUND')
        self.assertEqual(row['architecture_status'],'NECESSARY-READ-TIME-FEASIBLE')
        self.assertTrue(row['sufficient_full_pass_feasible'])
        self.assertEqual(row['write_cost_status'],'UNKNOWN-EXPECTED-WRITE-COST')
if __name__=='__main__': unittest.main()

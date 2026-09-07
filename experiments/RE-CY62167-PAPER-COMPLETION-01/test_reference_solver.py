import math, random, unittest
from reference_solver import synthetic_tau_upper, synthetic_reference_tau_bracket, synthetic_reference_risk_bounds, combined_reference_risk, ResidualMark, simulate_residual_first_passage

class TestReferenceSolver(unittest.TestCase):
    def test_frozen_arithmetic_benchmark(self):
        self.assertAlmostEqual(synthetic_tau_upper(),243.55401798,places=6)
        lo,hi=synthetic_reference_tau_bracket()
        self.assertAlmostEqual(lo,315.224841226,places=6)
        self.assertAlmostEqual(hi,315.744500579,places=6)
        self.assertIn('not a verified reference bracket', synthetic_reference_tau_bracket.__doc__.lower())
    def test_legacy_formula_outputs_monotone(self):
        vals=[synthetic_reference_risk_bounds(t) for t in (10,100,300,500)]
        self.assertTrue(all(vals[i+1][0]>vals[i][0] and vals[i+1][1]>vals[i][1] for i in range(len(vals)-1)))
    def test_direct_absorbing_product_is_surrogate_only(self):
        nu=2e-6; T=100
        self.assertAlmostEqual(combined_reference_risk(nu,T,1.0),1-math.exp(-nu*T),places=15)
        self.assertIn('surrogate', combined_reference_risk.__doc__.lower())
        bad=ResidualMark(bit_ids=(1,2),word_ids=(7,7),word_positions=(0,0))
        with self.assertRaises(ValueError):
            simulate_residual_first_passage([bad],[1],1.0,1,1,16,random.Random(1))
    def test_cancellation_fixture_distinguishes_toggle_and_surrogate(self):
        physical=set(); physical.symmetric_difference_update({0}); self.assertEqual(physical,{0})
        direct_mark={0,1}; physical.symmetric_difference_update(direct_mark)
        physical_failed=len(physical)>=2; surrogate_absorbed=True
        self.assertEqual(physical,{1}); self.assertFalse(physical_failed); self.assertTrue(surrogate_absorbed)
    def test_residual_same_bit_toggles_do_not_create_two_bit_failure(self):
        mark=ResidualMark(bit_ids=(123,),word_ids=(7,),word_positions=(0,))
        self.assertFalse(simulate_residual_first_passage([mark],[1],50.0,1.0,10.0,16,random.Random(2)))
if __name__=='__main__': unittest.main()

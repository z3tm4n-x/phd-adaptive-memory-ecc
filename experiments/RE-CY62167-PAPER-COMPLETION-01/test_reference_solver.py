import math, random, unittest
from reference_solver import synthetic_tau_upper, synthetic_reference_tau_bracket, synthetic_reference_risk_bounds, combined_reference_risk, ResidualMark, simulate_residual_first_passage
class TestReferenceSolver(unittest.TestCase):
    def test_benchmark(self):
        self.assertAlmostEqual(synthetic_tau_upper(),243.55401798,places=6)
        lo,hi=synthetic_reference_tau_bracket()
        self.assertTrue(315.225-0.001 <= lo <= 315.745)
        self.assertTrue(315.225 <= hi <= 315.745+0.001)
    def test_reference_monotone(self):
        vals=[synthetic_reference_risk_bounds(t) for t in (10,100,300,500)]
        self.assertTrue(all(vals[i+1][0]>vals[i][0] and vals[i+1][1]>vals[i][1] for i in range(len(vals)-1)))
    def test_direct_absorbing_combination(self):
        nu=2e-6; T=100
        self.assertAlmostEqual(combined_reference_risk(nu,T,1.0),1-math.exp(-nu*T),places=15)
        # A direct event is not presented as a toggle mark to the residual kernel.
        bad=ResidualMark(bit_ids=(1,2),word_ids=(7,7),word_positions=(0,0))
        with self.assertRaises(ValueError):
            simulate_residual_first_passage([bad],[1],1.0,1,1,16,random.Random(1))
    def test_residual_same_bit_toggles_do_not_create_two_bit_failure(self):
        mark=ResidualMark(bit_ids=(123,),word_ids=(7,),word_positions=(0,))
        self.assertFalse(simulate_residual_first_passage([mark],[1],50.0,1.0,10.0,16,random.Random(2)))
if __name__=='__main__': unittest.main()

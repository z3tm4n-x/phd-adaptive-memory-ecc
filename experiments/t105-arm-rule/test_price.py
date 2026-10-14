import unittest
from check_price import duration,peak
class AccountingTests(unittest.TestCase):
    def test_partial_endpoints(self):
        self.assertEqual(duration([(0,10),(20,30)],5,25),10)
        self.assertNotEqual(duration([(0,10),(20,30)],5,25),20) # whole-operation mutant
    def test_continuous_sliding_not_only_bins(self):
        intervals=[(8,12)]
        self.assertAlmostEqual(peak(intervals,0,20,5),.8)
        self.assertGreater(peak(intervals,0,20,5),max(duration(intervals,x,x+5)/5 for x in (0,5,10,15)))
    def test_piecewise_against_exhaustion(self):
        intervals=[(2,7),(10,11),(13,18),(23,27),(30,34)]
        self.assertEqual(peak(intervals,0,35,9),max(duration(intervals,x/2,x/2+9)/9 for x in range(53)))
if __name__=='__main__':unittest.main()

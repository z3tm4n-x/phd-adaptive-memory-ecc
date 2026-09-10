import unittest
from mapping_family import gaussian_binomial_21_2_direct, gaussian_binomial
class TestFullLinearFamily(unittest.TestCase):
    def test_independent_counts(self):
        self.assertEqual(gaussian_binomial_21_2_direct(),733006703275)
        self.assertEqual(gaussian_binomial(21,2),733006703275)
    def test_strict_nesting_cardinality(self):
        self.assertLess(55,210); self.assertLess(210,gaussian_binomial(21,2))
if __name__=='__main__': unittest.main()

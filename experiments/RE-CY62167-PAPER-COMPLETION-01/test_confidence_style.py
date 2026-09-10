import unittest
from confidence_style import article_direct_upper95_baseline, GENERALIZATION_STATUS, NORMATIVE_STATUS
class TestConfidenceStyle(unittest.TestCase):
    def test_baseline_formula(self):
        v,s=article_direct_upper95_baseline(0.0003342767046184631,3)
        self.assertAlmostEqual(v,0.0010904848941775637,places=15)
        self.assertIn('ARTICLE-CONFIDENCE-STYLE',s)
    def test_no_uncontrolled_generalization(self):
        v,s=article_direct_upper95_baseline(1e-4,1)
        self.assertIsNone(v); self.assertEqual(s,GENERALIZATION_STATUS)
    def test_normative_status(self):
        self.assertIn('NOT ESTABLISHED',NORMATIVE_STATUS)
if __name__=='__main__': unittest.main()

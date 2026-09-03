import unittest
from collections import Counter
from mapping_family import build_mapping_family, baseline_word_equals_floor_div4

class TestMappingFamily(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.rows=build_mapping_family()
    def test_210_and_55(self):
        self.assertEqual(len(self.rows),210)
        self.assertEqual(sum(r['retained'] for r in self.rows),55)
    def test_spacing_distribution(self):
        self.assertEqual(Counter(r['minimum_spacing'] for r in self.rows),Counter({1:74,2:31,4:27,8:23,16:55}))
    def test_metric_filter_not_ambiguous(self):
        a={r['mapping_id'] for r in self.rows if r['minimum_spacing_L1']>=16}
        b={r['mapping_id'] for r in self.rows if r['minimum_spacing_L2']>=16}
        c={r['mapping_id'] for r in self.rows if r['minimum_spacing_Linf']>=16}
        self.assertEqual(a,b); self.assertEqual(b,c); self.assertEqual(len(a),55)
    def test_baseline(self):
        r=next(r for r in self.rows if r['mapping_id']=='W_00_01')
        self.assertTrue(r['retained']); self.assertTrue(r['baseline_mapping'])
        self.assertTrue(baseline_word_equals_floor_div4())
if __name__=='__main__': unittest.main()

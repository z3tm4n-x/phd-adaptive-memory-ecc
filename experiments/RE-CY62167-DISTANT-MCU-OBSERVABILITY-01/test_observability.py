import unittest
from types import SimpleNamespace
import observability as o

class ObsTests(unittest.TestCase):
    def cell(self,x,y): return SimpleNamespace(x=x,y=y)
    def test_w16_exact_relation(self):
        self.assertTrue(o.exact16(0,16)); self.assertTrue(o.exact16(16,0))
        self.assertFalse(o.exact16(0,15)); self.assertFalse(o.exact16(16,1))
    def test_w16_multiple_relation(self):
        self.assertTrue(o.multiple16(0,32)); self.assertTrue(o.multiple16(48,0))
        self.assertFalse(o.multiple16(16,1)); self.assertFalse(o.multiple16(0,3))
    def test_recursive_square3_bridge_can_span_16(self):
        cs=[self.cell(x,0) for x in (0,3,6,9,12,15,16)]
        self.assertTrue(o.square3_connected(cs))
        self.assertGreaterEqual(max(max(dx,dy) for dx,dy in o.pairs(cs)),16)
    def test_isolated_id16_pair_not_square3_connected(self):
        self.assertFalse(o.square3_connected([self.cell(0,0),self.cell(16,0)]))
    def test_uniform_relation_probabilities(self):
        self.assertGreater(o.relation_probability_exact16(),0)
        self.assertGreater(o.relation_probability_multiple16(),o.relation_probability_exact16())
        self.assertLess(o.relation_probability_multiple16(),1)

if __name__=='__main__': unittest.main()

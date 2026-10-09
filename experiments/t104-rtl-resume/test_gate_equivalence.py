import unittest
from gate_check import INPUTS, STATE, harness, pack, vectors, proof_copy


class GateEquivalenceTests(unittest.TestCase):
    def test_complete_widths(self):
        self.assertEqual(sum(w for _, w in INPUTS), 455)
        self.assertEqual(sum(w for _, w in STATE), 520)
        self.assertEqual(len(set(n for n, _ in STATE)), len(STATE))

    def test_no_assumed_relation(self):
        source = harness()
        self.assertNotIn('assume(', source)
        self.assertEqual(source.count('assert('), 2)
        self.assertIn('gold_state==dut_state', source)

    def test_bounds_and_reproducible_vectors(self):
        with self.assertRaises(ValueError):
            pack(STATE, {'err_count': 1 << 64})
        first, count = vectors()
        self.assertEqual(vectors(), (first, count))
        self.assertEqual(count, 6384)

    def test_instrumentation_fail_closed(self):
        with self.assertRaises(ValueError):
            proof_copy('module something; endmodule')


if __name__ == '__main__':
    unittest.main()

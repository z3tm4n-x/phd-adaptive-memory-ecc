"""Independent discrete best-case server attacks optimistic raw ABI."""
import unittest
from fractions import Fraction
from budget import calculate, raw_tail_lower

class BudgetTest(unittest.TestCase):
    def test_explicit_record_server(self):
        # Earliest completion of each padded record. All reads pipeline, no
        # address/CPU overhead; opening a record can complete first beat now.
        free=-20
        for index in range(2000):
            first=max(index*20,free+20)
            free=first+4*20
        self.assertEqual(free-39980,160000)
        self.assertLessEqual(raw_tail_lower(),free-39980)

    def test_bound_direction(self):
        self.assertEqual(raw_tail_lower(),122500)
        self.assertGreater(raw_tail_lower(),10000)
        # Sentinel: changing necessary bandwidth lower into a 10us pass is
        # rejected, not fixed with an invented CPU speed.
        self.assertFalse(raw_tail_lower()<=10000)

    def test_unknown_not_zero(self):
        r=calculate()
        for key in ('CPU_wcet_ns','PSPL_upper_ns','CPU_load_percent','modified_top_STA'):
            self.assertIsNone(r[key])
        self.assertEqual(Fraction(r['available_for_history_CPU_PSPL_ns']),Fraction('5489.95492'))

    def test_packing_strengthens_optimism(self):
        self.assertEqual(raw_tail_lower(record_bits=160),160000)
        self.assertLess(raw_tail_lower(record_bits=130),raw_tail_lower(record_bits=160))

if __name__=='__main__':unittest.main()

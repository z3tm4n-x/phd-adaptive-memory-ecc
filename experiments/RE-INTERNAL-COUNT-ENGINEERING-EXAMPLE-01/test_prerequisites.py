import unittest
from fractions import Fraction
from itertools import product
from prerequisite_checks import (CHECK, DATA, decode, encode, exhaustive_results,
                                  normalization, physical_trace, set_oracle,
                                  window_guard)


class Prerequisites(unittest.TestCase):
    def test_full_word_exhaustive(self):
        result = exhaustive_results()
        self.assertEqual(result['single_error_checks'], 36 * 39)
        self.assertEqual(result['double_error_checks'], 36 * 741)

    def test_parity_count_mutation_is_rejected(self):
        # Deliberate data-only mutation: ignores all seven parity corrections.
        mismatches = []
        for position in range(1, 40):
            correct_count = decode(encode(0) ^ (1 << (position - 1)))[1]
            mutant = correct_count if position in DATA else 0
            if mutant != correct_count:
                mismatches.append(position)
        self.assertEqual(mismatches, list(CHECK))

    def test_units_and_normalization(self):
        result = normalization(8, Fraction(1, 1000))
        self.assertEqual(result['information_bits'], 256)
        self.assertEqual(result['protected_bits'], 312)
        self.assertEqual(result['array_arrivals_per_second'], Fraction(39, 125))
        self.assertEqual(result['coding_overhead'], Fraction(7, 32))
        self.assertNotEqual(result['array_arrivals_per_second'], 32 * 8 * Fraction(1, 1000))
        # Expected different-bit pair counts, not a ratio of true failure risks.
        self.assertEqual(Fraction(39 * 38, 32 * 31), Fraction(741, 496))

    def test_check_boundary_order(self):
        events = [(2, 39), (3, 3)]
        self.assertEqual(physical_trace(events, [2], 1, 4),
                         set_oracle(events, [2], 1, 4))
        self.assertEqual(physical_trace(events, [2], 1, 4)[-1][-1], 3)

    def test_direct_executor_against_independent_set_oracle(self):
        # All pairs, all39 positions; parity/data and same-bit cancellation.
        for a, b in product(range(1, 40), repeat=2):
            for times in [(1, 2), (1, 4), (1, 5), (4, 5)]:
                events = list(zip(times, (a, b)))
                self.assertEqual(physical_trace(events, [3, 7], 1, 9),
                                 set_oracle(events, [3, 7], 1, 9))

    def test_delayed_write_counterexample(self):
        events = [(1, 3), (3, 39)]
        ideal = physical_trace(events, [2], 0, 4)
        delayed = physical_trace(events, [2], 2, 4)
        self.assertIsNone(ideal[-1][-1])
        self.assertEqual(delayed[-1][-1], 3)
        self.assertEqual(delayed[-1][2], 0)  # Write does not erase first passage.

    def test_initial_state_and_terminal_pending_write(self):
        self.assertEqual(physical_trace([], [2], 0, 3, initial=5)[-1][-1], 0)
        result = physical_trace([(1, 39)], [2], 2, 3)
        self.assertEqual(result[-1][3], 0)
        self.assertEqual(result[-1][2], 1 << 38)

    def test_guard_exact(self):
        # Artificial rational inputs for a unit test, not engineering parameters.
        self.assertEqual(window_guard(Fraction(2), 4, [Fraction(1, 10)] * 8),
                         Fraction(2, 5))
        self.assertEqual(window_guard(100, 4, [1]), 1)
        with self.assertRaises(ValueError):
            window_guard(1, 0, [1])


if __name__ == '__main__':
    unittest.main()

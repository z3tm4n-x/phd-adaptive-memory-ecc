"""Small exhaustive regression oracles; the all-history argument is in the note."""
import itertools
import unittest
from fractions import Fraction as F
from windows import Contract, app_accounting


def mode_at(freeze, checks, delays, danger, lookahead, lost=()):
    """Perfect tube is the earliest permitted LOW; loss only adds FAST.

    Sequence numbers reject late older commands. No simulated error stream.
    This oracle deliberately omits extra FAST holds (a conservative reduction).
    """
    received = []
    for i, (check, delay) in enumerate(zip(checks, delays)):
        forced = any(check <= b and check + lookahead >= a for a, b in danger)
        mode = 'FAST' if forced or i in lost else 'LOW'
        if check + delay <= freeze:
            received.append((i, mode))
    return max(received)[1] if received else 'FAST'


class WindowTests(unittest.TestCase):
    def test_fractional_boundaries_overlap_and_counts_against_scan(self):
        for W, k, f, T in itertools.product((2, 4), (1, 3, 5),
                                           (F(0), F(3, 2), F(13, 2)),
                                           (F(19), F(77, 4))):
            c = Contract(W, k, T, 2, f, F(1, 4), F(3, 2), 2, 1)
            for danger in ([], [(F(0), F(1))], [(F(17, 2), F(41, 4))],
                           [(F(8), F(10)), (F(9), F(13))], [(T, T)]):
                # Direct time-domain predicate, independent of ceil/range merge.
                expected = [j for j in range(c.N) if j < W or j*c.g < f
                            or j % k == 0 or any(
                                a-c.H_fast <= j*c.g <= b+f for a, b in danger)]
                actual = [x['j'] for x in c.small_windows(danger)]
                self.assertEqual(actual, expected)
                self.assertEqual(c.count(danger), len(expected))
                for word in range(W):
                    self.assertEqual(c.count(danger, word=word),
                                     sum(j % W == word for j in expected))
                    self.assertEqual(c.count(danger, word=word, completed_only=True),
                                     sum(j % W == word and j*c.g+c.c <= T for j in expected))

    def test_command_histories_with_loss_and_deadline_extremes(self):
        c = Contract(2, 3, 12, 1, F(5, 4), 0, F(1, 2), 2, 1)
        danger = [(F(6), F(8))]
        checks = list(range(0, 13, 2))
        slots = [j for lo, hi in c.fast_ranges(danger) for j in range(lo, hi+1)]
        for delays in itertools.product((F(0), F(1, 2), F(1)), repeat=len(checks)):
            for lost in ((), (3,), tuple(range(len(checks)))):
                for j in slots:
                    phi = j*c.g-c.freeze
                    if phi >= 0:
                        self.assertEqual(mode_at(phi, checks, delays, danger,
                                                 c.lookahead, lost), 'FAST')

    def test_freeze_cannot_be_omitted_from_lookahead(self):
        c = Contract(2, 5, 12, 1, 2, 0, F(1, 2), 1, 1)
        danger = [(F(8), F(9))]
        j = 6
        self.assertTrue(any(lo <= j <= hi for lo, hi in c.fast_ranges(danger)))
        checks = list(range(13))
        delays = [F(1)] * len(checks)
        self.assertEqual(mode_at(j-c.freeze, checks, delays, danger, c.lookahead), 'FAST')
        self.assertEqual(mode_at(j-c.freeze, checks, delays, danger,
                                 c.lookahead-c.freeze), 'LOW')

    def test_late_old_low_does_not_overwrite_new_fast(self):
        # Old LOW issued at 0 arrives at 3; newer forced FAST arrives at 1.
        self.assertEqual(mode_at(3, [0, 1], [3, 0], [(4, 5)], 3), 'FAST')

    def test_preentry_all_words_and_start_inside_zone(self):
        for a in (F(11), F(45, 4), F(15)):
            c = Contract(4, 3, 30, 2, 1, F(1, 4), 1, 3, 2)
            danger = [(a, a+1)]
            before = [x for x in c.small_windows(danger)
                      if a-c.H_fast <= x['j']*c.g and x['right'] <= a]
            self.assertEqual({x['word'] for x in before}, set(range(4)))
        c = Contract(8, 3, 4, 1, 0, 0, F(1, 2), 1, 0)
        self.assertEqual([x['j'] for x in c.small_windows([(0, 2)])], list(range(4)))
        # T shorter than a pass: do not claim all eight words cleaned.
        self.assertEqual(c.count([(0, 2)], word=7), 0)

    def test_pending_cost_and_tail_do_not_invent_E_at_T(self):
        c = Contract(2, 3, F(17, 4), 1, 0, 0, F(1, 2), 1, 0)
        danger = [(F(4), F(17, 4))]
        self.assertEqual(c.count(danger), 5)
        self.assertEqual(c.count(danger, completed_only=True), 4)
        last = c.small_windows(danger)[-1]
        self.assertEqual((last['j'], last['right'], last['completed_by_T']),
                         (4, F(9, 2), False))

    def test_mission_compression_and_cost_direction(self):
        c = Contract(131072, 3, 315576000*10**9, 1000, 100, 100, 400, 1000, 500)
        self.assertLess(c.count([]), c.N)  # lost throughout: actual FAST can equal N
        self.assertEqual(c.count([]), (c.N-1)//3+1+131072-((131072-1)//3+1))
        with self.assertRaisesRegex(ValueError, 'compressed'):
            c.small_windows([])

    def test_application_exact_T_counts_and_prefix(self):
        candidate = dict(memory=dict(words=4), mission=dict(duration_s='41/2000000000'),
                         inherited_contract=dict(application=dict(epoch_ns=2,
                         address_multiplier=3,first_ns=0,read_offset_ns=0,write_offset_ns=1),
                         constraints=dict(application_deadline_ns=2)))
        out = app_accounting(candidate)
        self.assertEqual((out['reads_offered_before_T'], out['writes_offered_before_T']), (11, 10))
        self.assertEqual(out['period_ns'], 8)
        self.assertEqual(out['pending_write_words'], [3])
        self.assertEqual(out['operations']['write_beats'], 3*(10+4))
        self.assertIsNone(out['Q_upper'])

    def test_invalid_contracts_are_rejected(self):
        for W, k, e, end in ((4, 2, 0, 1), (4, 3, 1, 1), (4, 3, 0, 3)):
            with self.assertRaises(ValueError):
                Contract(W, k, 10, 2, 0, e, end, 1, 0)
        c = Contract(4, 3, 10, 2, 0, 0, 1, 1, 0)
        with self.assertRaises(ValueError):
            c.fast_ranges([(-1, 3)])


if __name__ == '__main__':
    unittest.main()

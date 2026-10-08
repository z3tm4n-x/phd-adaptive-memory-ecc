import unittest
from board_check import conditional_margins, pin_plan
from composition_check import CORE_CHECKS, PORT_CHECKS


class BoardComponentsTests(unittest.TestCase):
    def test_source_cannot_be_substituted(self):
        with self.assertRaises(ValueError):
            pin_plan(b'plausible but not verified')

    def test_conditional_margin_direction(self):
        margins = conditional_margins()
        self.assertTrue(all(v > 0 for v in margins.values()))
        self.assertLess(margins['write_pulse_slack_over_35ns'], 0.5)
        self.assertLess(margins['read_capture_slack_ns'], 3.5)

    def test_composition_has_no_environment_assumptions(self):
        self.assertNotIn('assume(', CORE_CHECKS+PORT_CHECKS)
        self.assertEqual(CORE_CHECKS.count('assert('), 8)
        self.assertEqual(PORT_CHECKS.count('assert('), 4)


if __name__ == '__main__':
    unittest.main()

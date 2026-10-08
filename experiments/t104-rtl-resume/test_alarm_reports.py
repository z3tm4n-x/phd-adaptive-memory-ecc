import unittest
from compare_alarm import setup_summary, skew_summary


class AlarmReportTests(unittest.TestCase):
    def test_skew_direction(self):
        report = 'Requirement: 2.000ns\nSlack (VIOLATED) : -0.071ns\nActual Bus Skew: 2.071ns\n'
        self.assertEqual(skew_summary(report)['worst_slack_ns'], -0.071)
        with self.assertRaises(ValueError):
            skew_summary(report.replace('-0.071', '0.071'))

    def test_skew_must_exist(self):
        with self.assertRaises(ValueError):
            skew_summary('No path')

    def test_setup_endpoint_coverage(self):
        text = 'start\tend\tgroup\tslack_ns\na\tb\tmem_clk\t-2.0\n'
        timing = dict(setup_failing_endpoints=1, WNS_ns=-2.0, TNS_ns=-2.0)
        self.assertEqual(setup_summary({'setup.tsv': text}, timing)[0]['failing_endpoints'], 1)
        for wrong in (text+'c\tb\tmem_clk\t-2.0\n', text.replace('-2.0', '2.0')):
            with self.assertRaises(ValueError):
                setup_summary({'setup.tsv': wrong}, timing)


if __name__ == '__main__':
    unittest.main()

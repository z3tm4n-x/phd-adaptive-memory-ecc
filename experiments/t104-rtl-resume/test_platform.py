import unittest
from platform_probe import parse_inventory
from platform_run import parse_timing


class PlatformInventoryTests(unittest.TestCase):
    LOG = ("T104_VERSION_BEGIN\nVivado v2025.2\nT104_VERSION_END\n"
           "T104_INSTALLED_PART_COUNT 429\n"
           "T104_PART_UNAVAILABLE xc7z020clg484-1\n"
           "T104_PART_UNAVAILABLE xc7z020clg484-2\n"
           "T104_PLATFORM_STATUS BLOCKED_DEVICE_SUPPORT\n")
    PARTS = ["xc7z020clg484-1", "xc7z020clg484-2"]

    def test_blocker_is_not_timing_failure(self):
        result = parse_inventory(self.LOG, 2, self.PARTS)
        self.assertEqual(result["status"], "BLOCKED_DEVICE_SUPPORT")
        self.assertIsNone(result["wns_ns"])
        self.assertFalse(result["STA_run"])

    def test_missing_or_duplicated_part_rejected(self):
        for parts in (self.PARTS[:1], self.PARTS+self.PARTS):
            with self.assertRaises(ValueError):
                parse_inventory(self.LOG, 2, parts)

    def test_truncated_output_or_exit_masking_rejected(self):
        for log, code in ((self.LOG, 0), ("", 2), (self.LOG+self.LOG, 2)):
            with self.assertRaises(ValueError):
                parse_inventory(log, code, self.PARTS)


class TimingReportTests(unittest.TestCase):
    ROW = ("WNS(ns) TNS(ns) TNS Failing Endpoints TNS Total Endpoints "
           "WHS(ns) THS(ns) THS Failing Endpoints THS Total Endpoints "
           "WPWS(ns) TPWS(ns) TPWS Failing Endpoints TPWS Total Endpoints\n"
           "---------- ---------- ----------\n"
           " -2.500 -400.000 80 4000 -0.100 -1.000 10 4000 1.500 0.000 0 1800\n")

    def test_keep_setup_and_hold_failures(self):
        result = parse_timing(self.ROW)
        self.assertEqual(result["WNS_ns"], -2.5)
        self.assertEqual(result["WHS_ns"], -0.1)
        self.assertEqual(result["setup_failing_endpoints"], 80)

    def test_no_missing_report_becomes_zero_slack(self):
        for text in ("", self.ROW[:100], self.ROW+self.ROW):
            with self.assertRaises(ValueError):
                parse_timing(text)

    def test_mutated_slack_direction_rejected(self):
        with self.assertRaises(ValueError):
            parse_timing(self.ROW.replace(" -2.500", " 2.500"))

    def test_total_negative_slack_cannot_be_positive(self):
        with self.assertRaises(ValueError):
            parse_timing(self.ROW.replace(" -400.000", " 400.000"))


if __name__ == "__main__":
    unittest.main()

import unittest
from platform_probe import parse_inventory


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


if __name__ == "__main__":
    unittest.main()

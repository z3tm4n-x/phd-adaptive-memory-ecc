import unittest
import json
from compare_sta import SERIES, PART, reports, paths, cdc_groups, detail_summary


class DetailExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = reports(SERIES/PART/"reports.zip")
        cls.detail = reports(SERIES/"detail.zip")
        cls.timing = json.loads((SERIES/PART/"summary.json").read_text())["timing"]

    def test_all_dynamic_gray_bits_and_hold_endpoints(self):
        result = detail_summary(self.detail, self.timing)
        self.assertEqual(result["gray_dynamic_endpoints"], 124)
        self.assertEqual(sum(r["failing_endpoints"] for r in result["hold"]), 937)
        self.assertEqual({r["source_class"] for r in result["hold"]}, {"port"})

    def test_unconstrained_gray_bit_is_rejected(self):
        bad = dict(self.detail)
        bad["gray.tsv"] = bad["gray.tsv"].replace("MaxDelay Path 4.000ns -datapath_only", "", 1)
        with self.assertRaises(ValueError):
            detail_summary(bad, self.timing)

    def test_hidden_hold_endpoint_is_rejected(self):
        bad = dict(self.detail)
        bad["hold.tsv"] = "\n".join(bad["hold.tsv"].splitlines()[:-1])+"\n"
        with self.assertRaises(ValueError):
            detail_summary(bad, self.timing)

    def test_gray_missing_bit_is_not_automatically_constant(self):
        bad = dict(self.detail)
        bad["selection.txt"] = bad["selection.txt"].replace("DRIVER_TYPES GND", "DRIVER_TYPES LUT6", 1)
        with self.assertRaises(ValueError):
            detail_summary(bad, self.timing)

    def test_slack_sign_not_changed_in_extraction(self):
        source = self.raw["memory_paths.rpt"]
        self.assertEqual(paths(source)[0]["slack_ns"], -5.706)
        with self.assertRaises(ValueError):
            paths(source.replace("-5.706ns", "5.706ns", 1))

    def test_cdc_count_cannot_be_silently_waived(self):
        groups = cdc_groups(self.raw["cdc.rpt"])
        self.assertEqual(sum(r["count"] for r in groups if r["id"] == "CDC-1"), 1042)
        with self.assertRaises(ValueError):
            cdc_groups(self.raw["cdc.rpt"].replace("Critical   1042", "Critical   1041", 1))


if __name__ == "__main__":
    unittest.main()

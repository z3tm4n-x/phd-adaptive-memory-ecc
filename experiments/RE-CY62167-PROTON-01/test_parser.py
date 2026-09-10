#!/usr/bin/env python3
from pathlib import Path
import tempfile
import unittest

from parse_zenodo_protons import parse_cluster_file, physical_records


class ParserTests(unittest.TestCase):
    def test_timestamped_and_service_sentinel(self):
        text = """cluster 0 with xmin 1 xmax 2 ymin 3 ymax 4
xadd 5 yadd 6 11:02:03
123 1 3
124 2 4
NUMBER OF EVENTS =2
cluster 1 with xmin 0 xmax 0 ymin 0 ymax 0
xadd 0 yadd 0 3:3:3
807416886 0 0
NUMBER OF EVENTS =1
"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.txt"
            p.write_text(text)
            r = parse_cluster_file(p)
        self.assertEqual(len(r), 2)
        self.assertEqual(r[0].k, 2)
        self.assertEqual(r[0].timestamp_raw, "11:02:03")
        self.assertEqual(r[0].cells[0].field0_raw, 123)
        self.assertTrue(r[1].is_strict_service_record)
        self.assertEqual(len(list(physical_records(r))), 1)

    def test_non_timestamped_zero_record_is_retained(self):
        text = """cluster 0 with xmin 0 xmax 0 ymin 0 ymax 0
xadd 0 yadd 0
0 0
NUMBER OF EVENTS =1
"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.txt"
            p.write_text(text)
            r = parse_cluster_file(p)
        self.assertTrue(r[0].is_ambiguous_zero_record)
        self.assertFalse(r[0].is_strict_service_record)
        self.assertEqual(len(list(physical_records(r))), 1)

    def test_cluster_id_reset_opens_new_segment(self):
        text = """cluster 0 with xmin 0 xmax 0 ymin 0 ymax 0
xadd 0 yadd 0
1 1
NUMBER OF EVENTS =1
cluster 1 with xmin 0 xmax 0 ymin 0 ymax 0
xadd 0 yadd 0
2 2
NUMBER OF EVENTS =1
cluster 0 with xmin 0 xmax 0 ymin 0 ymax 0
xadd 0 yadd 0
3 3
NUMBER OF EVENTS =1
"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.txt"
            p.write_text(text)
            r = parse_cluster_file(p)
        self.assertEqual([x.segment_id for x in r], [1, 1, 2])

    def test_declared_count_mismatch_fails(self):
        text = """cluster 0 with xmin 0 xmax 0 ymin 0 ymax 0
xadd 0 yadd 0
1 1
NUMBER OF EVENTS =2
"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.txt"
            p.write_text(text)
            with self.assertRaises(ValueError):
                parse_cluster_file(p)


if __name__ == "__main__":
    unittest.main()

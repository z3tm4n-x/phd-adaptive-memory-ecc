"""Boundary and missing-data cases for the T197 scientific transformations."""
from datetime import datetime, timedelta
import json
import unittest

import reproduce as r


BASE=datetime(2006,12,1)


def record(seconds,value,line):
    time=BASE+timedelta(seconds=seconds)
    return {"line":line,"time":time,"raw_time":time.isoformat(),
            "raw_value":str(value),"value":value}


class ObservationSemantics(unittest.TestCase):
    def test_crossing_boundary_is_not_placed_at_a_fictitious_instant(self):
        records=[record(3590,7,1),record(3654,10,2)]
        hours=r.bin_data(records,[],r.counter_intervals(records,96),
                         [BASE+timedelta(hours=h) for h in range(3)])
        self.assertEqual([x["edac_increment_lower"] for x in hours],[0,0])
        self.assertEqual([x["edac_increment_upper"] for x in hours],[3,3])
        self.assertEqual(sum(x["edac_increment_at_right_endpoint"] for x in hours),3)
        self.assertTrue(all(x["joint_live_exposure_s"] is None for x in hours))

    def test_exact_hour_boundary_uses_right_closed_convention(self):
        records=[record(3536,7,1),record(3600,8,2),record(3664,10,3)]
        hours=r.bin_data(records,[record(3600,0,1)],r.counter_intervals(records,96),
                         [BASE+timedelta(hours=h) for h in range(3)])
        self.assertEqual([x["edac_increment_lower"] for x in hours],[1,2])
        self.assertEqual([x["edac_increment_upper"] for x in hours],[1,2])
        self.assertEqual([x["ima_valid_rows"] for x in hours],[1,0])
        self.assertIsNone(hours[1]["ima_median_cnts"])
        self.assertEqual(hours[0]["ima_median_cnts"],0)

    def test_missing_counter_value_breaks_both_adjacent_differences(self):
        records=[record(0,10,1),record(64,None,2),record(128,13,3),record(192,14,4)]
        edges=r.counter_intervals(records,96)
        self.assertEqual([e["delta"] for e in edges],[None,None,1])
        self.assertEqual([e["status"] for e in edges],["missing_value","missing_value","valid"])

    def test_reset_duplicate_and_gap_are_not_repaired(self):
        records=[record(0,65535,1),record(64,2,2),record(64,2,3),
                 record(64,3,4),record(256,7,5)]
        edges=r.counter_intervals(records,96)
        self.assertEqual([e["status"] for e in edges],
                         ["decrease_reset_or_rollover_unknown","duplicate_same_value",
                          "duplicate_conflicting_value","observation_gap"])
        self.assertEqual(edges[-1]["delta"],4)
        self.assertEqual(edges[0]["delta"],-65533)
        hours=r.bin_data(records,[],edges,[BASE,BASE+timedelta(hours=1)])
        self.assertEqual(hours[0]["edac_increment_upper"],0)

    def test_backward_clock_is_not_hidden_by_sorting(self):
        with self.assertRaisesRegex(ValueError,"Backward timestamp"):
            r.counter_intervals([record(64,1,1),record(0,2,2)],96)

    def test_fill_is_not_a_valid_zero_or_a_negative_label(self):
        metadata={"status":{"code":1200},"parameters":[{"name":"Time","units":"UTC"},
            {"name":"vex_ima_bg","units":"cnts","fill":"-1e31"},
            {"name":"vex_ima_totct","units":"cnts","fill":"-1e31"}]}
        raw=("#"+json.dumps(metadata)+"\n2006-12-01T00:00:00.000Z,0,0\n"
             "2006-12-01T00:03:12.000Z,-1e31,5\n").encode()
        rows=r.parse_ima(raw)
        self.assertEqual([x["value"] for x in rows],[0,None])
        cells=r.bin_data([],rows,[],[BASE,BASE+timedelta(hours=1)])
        self.assertEqual(cells[0]["ima_valid_rows"],1)
        self.assertEqual(cells[0]["ima_fill_rows"],1)
        self.assertEqual(cells[0]["negative_reference"],"UNKNOWN")

    def test_ima_gap_separates_blocks_and_never_invents_exposure(self):
        rows=[record(0,1,1),record(192,2,2),record(86400,3,3)]
        blocks,gaps=r.ima_blocks(rows,288)
        self.assertEqual([b["rows"] for b in blocks],[2,1])
        self.assertEqual(gaps[0]["seconds"],86208)
        self.assertTrue(all(b["live_exposure_s"] is None for b in blocks))

    def test_integer_counter_and_original_naive_time_are_preserved(self):
        raw=b"# DATE TIME,NDMW0D0A - DMS\n2006-12-01 00:00:46.121,76.0\n"
        parsed=r.parse_edac(raw)
        self.assertEqual(parsed[0]["value"],76)
        self.assertEqual(parsed[0]["raw_time"],"2006-12-01 00:00:46.121")
        self.assertIsNone(parsed[0]["time"].tzinfo)
        with self.assertRaisesRegex(ValueError,"Non-integral"):
            r.parse_edac(raw.replace(b"76.0",b"76.5"))


if __name__=="__main__": unittest.main()

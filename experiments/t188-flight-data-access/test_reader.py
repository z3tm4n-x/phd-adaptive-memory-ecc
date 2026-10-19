"""Semantic safety checks, using the frozen source fragments and adversarial cases."""
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

import reproduce as r


class ReaderSafety(unittest.TestCase):
    def test_sparse_platform_channel_is_not_zero(self):
        path = next((r.HERE/"audit/samples").glob("SOL_*2021_first10.txt"))
        _, _, names, times, values = r.parse_grains(path.read_bytes())
        i = names.index("NCDT07B0")
        self.assertTrue(all(row[i] is None for row in values))
        self.assertTrue(all(t.tzinfo is None for t in times))

    def test_his_repeats_and_memory_families_are_retained(self):
        path = next((r.HERE/"audit/samples").glob("SOHIS*_first10.txt"))
        stats, sample = r.audit_his(path.read_bytes())
        self.assertEqual(stats["rows"], 10)
        self.assertEqual(stats["unique_exact_lines"], 5)
        self.assertEqual(stats["exact_duplicate_extra_lines"], 5)
        self.assertEqual(len(stats["raw_families"]), 3)
        self.assertEqual(sample.splitlines()[0], sample.splitlines()[1])
        self.assertNotIn("physical_event_count", stats)

    def test_reset_across_missing_row_remains_visible(self):
        raw = ("# Number of samples:\n3\n# DATE TIME\tcounter\n"
               "2006-12-01 00:00:00\t65535\n"
               "2006-12-01 00:01:04\t \n"
               "2006-12-01 00:02:08\t2\n").encode()
        stats, _ = r.audit_grains(raw)
        col = stats["columns"]["counter"]
        self.assertEqual(col["missing"], 1)
        self.assertEqual(col["decreases_between_successive_observed_values"][0]["intervening_missing_rows"], 1)
        self.assertEqual(col["last"], 2)

    def test_hapi_fill_is_separate_from_valid_zero(self):
        path=r.HERE/"audit/samples/vex-ima-bg-20061201-20061220_first10.txt"
        header=path.read_text(encoding="utf-8").splitlines()[0]
        raw=(header+"\n2006-12-01T00:00:00.000Z,0,0\n2006-12-01T00:03:12.000Z,-1e31,2\n").encode()
        stats,_=r.audit_hapi(raw)
        self.assertEqual(stats["columns"]["vex_ima_bg"]["fill_rows"],1)
        self.assertEqual(stats["columns"]["vex_ima_totct"]["fill_rows"],0)
        self.assertTrue(stats["first"].endswith("+00:00"))

    def test_bad_row_is_not_silently_skipped(self):
        raw=b"# Number of samples:\n1\n# DATE TIME,a,b\n2006-12-01 00:00:00,1\n"
        with self.assertRaises(ValueError):r.parse_grains(raw)

    def test_changed_input_is_rejected_before_result(self):
        temp_base=(r.HERE.parents[1]/".cache"/"t188"/"tests").resolve()
        temp_base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_base) as td:
            self.assertTrue(Path(td).resolve().is_relative_to(temp_base))
            cache=Path(td)/"cache";cache.mkdir()
            (cache/"EDAC.zip").write_bytes(b"not the pinned archive")
            out=Path(td)/"out"
            run=subprocess.run([sys.executable,"-X","utf8",str(r.HERE/"reproduce.py"),"--cache",str(cache),"--out",str(out)],capture_output=True,text=True,encoding="utf-8")
            self.assertNotEqual(run.returncode,0)
            self.assertIn("Cached input hash mismatch",run.stderr)
            self.assertFalse((out/"inventory.json").exists())


if __name__=="__main__":unittest.main()

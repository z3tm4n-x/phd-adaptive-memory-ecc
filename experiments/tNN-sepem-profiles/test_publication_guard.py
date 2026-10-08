"""Narrow Git guard for licensed SEPEM raw inputs; no raw files are created."""

import fnmatch
import json
from pathlib import Path
import subprocess
import unittest


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]
RELATIVE_PACKAGE = PACKAGE.relative_to(ROOT).as_posix()
RAW_PATTERNS = (
    "SEPEM_RDS_v2-00*.zip",
    "SEPEM_H_reference.txt",
    "SEPEM_He_reference.txt",
    "SEPEM_H_GOES*.txt",
    "SEPEM_He_GOES*.txt",
    "SEPEM_H_SMS*.txt",
    "SEPEM_He_SMS*.txt",
)


def git_ignored(paths):
    # --no-index tests ignore rules even for already tracked positive controls.
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-z", "--stdin"],
        cwd=ROOT,
        input=("\0".join(paths) + "\0").encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return set(result.stdout.decode("utf-8").split("\0")) - {""}


class PublicationGuardTests(unittest.TestCase):
    def test_every_archived_raw_series_is_ignored_at_every_tested_depth(self):
        audit = json.loads((PACKAGE / "outputs/input_audit.json").read_text("utf-8"))
        raw_names = [item["name"] for item in audit["files"]
                     if item["name"].startswith(("SEPEM_H_", "SEPEM_He_"))]
        self.assertEqual(len(raw_names), 16)
        raw_names += ["SEPEM_RDS_v2-00.zip", "SEPEM_RDS_v2-00 (1).zip"]
        paths = [prefix + name for prefix in ("", RELATIVE_PACKAGE + "/",
                 "data/external/sepem_rds_v2/") for name in raw_names]
        self.assertEqual(git_ignored(paths), set(paths))

    def test_derived_outputs_sources_and_unrelated_archives_remain_visible(self):
        paths = [RELATIVE_PACKAGE + "/" + name for name in (
            "REPORT.md", "DATA_PASSPORT.md", "transport.py", "config.json",
            "outputs/events.csv", "outputs/input_audit.json",
            "outputs/largest-event-profiles.png", "inputs/nist_pstar_al.csv",
        )] + ["unrelated.zip", "SEPEM_derived_summary.csv", "notes.txt"]
        self.assertEqual(git_ignored(paths), set())

    def test_no_raw_names_are_in_the_index(self):
        result = subprocess.run(
            ["git", "ls-files", "--cached", "-z"], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
        paths = result.stdout.decode("utf-8").split("\0")
        raw = [path for path in paths if any(
            fnmatch.fnmatchcase(Path(path).name, pattern)
            for pattern in RAW_PATTERNS
        )]
        self.assertEqual(raw, [])


if __name__ == "__main__":
    unittest.main()

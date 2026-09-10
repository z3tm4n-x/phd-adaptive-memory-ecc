#!/usr/bin/env python3
from pathlib import Path
import hashlib
import math
import os
import unittest

from parse_zenodo_protons import parse_cluster_file, physical_records

N_BITS = 16_777_216
D = 3
S1_MD3 = 2 * D * (D + 1)

PROTON_FILES = [
    (0.9, "clust_p0.9MeV.txt"),
    (1.0, "clust_p1MeV.txt"),
    (1.1, "clust_p1.1MeV.txt"),
    (1.5, "clust_p1.5MeV.txt"),
    (2.5, "clust_p2.5MeV.txt"),
    (3.0, "clust_p3MeV.txt"),
    (4.0, "clust_p4MeV.txt"),
    (5.0, "clust_p5MeV.txt"),
    (29.0, "clust_p29MeV.txt"),
    (40.0, "clust_p40MeV.txt"),
    (80.0, "clust_p80MeV.txt"),
    (124.0, "clust_p124MeV.txt"),
    (164.0, "clust_p164MeV.txt"),
    (186.0, "clust_p186MeV.txt"),
]

ZENODO_MD5 = {
    "clust_p0.9MeV.txt": "10ab9973e182b8aa2d6647d3fb2d451a",
    "clust_p1MeV.txt": "a0dfb8e032b4102bd00815d800b9a770",
    "clust_p1.1MeV.txt": "68b78596d0903c014747c62c606eb851",
    "clust_p1.5MeV.txt": "fa049e8ef13a9c5e1e5d2c41353a6e4f",
    "clust_p2.5MeV.txt": "7cee7f8bc1497e3c79d11b2f304d2540",
    "clust_p3MeV.txt": "88f4ce176d5a6826f71f37ff32641c0e",
    "clust_p4MeV.txt": "713f0f33a961e143598021c88c5f2de0",
    "clust_p5MeV.txt": "2bcef85b1a963b2c4da61bf5c5544cce",
    "clust_p29MeV.txt": "be0a36e3ef587b3fa9fdcf0663aa404e",
    "clust_p40MeV.txt": "ff7fe1c5365f6ade8c81680423d68aa3",
    "clust_p80MeV.txt": "0ce14a24799e0523b8242d0d66d04c96",
    "clust_p124MeV.txt": "dbf5911333c50a5b6eb366c026208e7c",
    "clust_p164MeV.txt": "ec1a27f27a6b904557125d3219116a13",
    "clust_p186MeV.txt": "28614930fc22db2365e07b6a55850a17",
}


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def false2_pooled(n_sbu: int, s1: int) -> float:
    return (n_sbu * (n_sbu - 1) / 2) * s1 / N_BITS


class DatasetInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = os.environ.get("CY62167_ZENODO_DIR")
        if not raw:
            raise unittest.SkipTest("set CY62167_ZENODO_DIR for raw-data tests")
        cls.raw_dir = Path(raw)

    def test_all_requested_files_hash_and_declared_counts(self):
        for _, name in PROTON_FILES:
            path = self.raw_dir / name
            self.assertTrue(path.exists(), name)
            self.assertEqual(md5(path), ZENODO_MD5[name], name)
            # parse_cluster_file raises on every NUMBER OF EVENTS mismatch.
            records = parse_cluster_file(path)
            self.assertGreater(len(records), 0, name)

    def test_two_cell_raw_signature_is_square3_not_literal_md3(self):
        total_two = 0
        literal_md3_violations = 0
        square3_violations = 0
        for _, name in PROTON_FILES:
            recs = list(physical_records(parse_cluster_file(self.raw_dir / name)))
            for r in recs:
                if r.k != 2:
                    continue
                total_two += 1
                a, b = [(c.x, c.y) for c in r.cells]
                dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
                literal_md3_violations += int(dx + dy > 3)
                square3_violations += int(max(dx, dy) > 3)
        self.assertGreater(total_two, 0)
        self.assertGreater(literal_md3_violations, 0)
        self.assertEqual(square3_violations, 0)

    def test_service_sentinel_only_removed_under_strict_signature(self):
        strict = 0
        ambiguous = 0
        for _, name in PROTON_FILES:
            records = parse_cluster_file(self.raw_dir / name)
            strict += sum(r.is_strict_service_record for r in records)
            ambiguous += sum(r.is_ambiguous_zero_record for r in records)
            self.assertEqual(
                len(list(physical_records(records))),
                len(records) - sum(r.is_strict_service_record for r in records),
            )
        self.assertGreater(strict, 0)
        self.assertGreater(ambiguous, 0)

    def test_franco_rezaei_false_pair_sanity_check(self):
        # Rezaei 2020 reports ~0.71 expected false 2-bit events for the
        # 0xAA, 0.75-V static round with 1003 affected cells and D=3.
        predicted = false2_pooled(1003, S1_MD3)
        self.assertTrue(math.isclose(predicted, 0.718836, rel_tol=2e-3))
        self.assertAlmostEqual(predicted, 0.71, delta=0.02)


if __name__ == "__main__":
    unittest.main()

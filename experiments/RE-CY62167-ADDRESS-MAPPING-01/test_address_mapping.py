from __future__ import annotations
import json
import os
import random
import re
import tempfile
import unittest
from pathlib import Path
import address_mapping as am

def make_record(*, source: str, cluster: int, x: int, y: int, address: int) -> am.CellRecord:
    return am.CellRecord(source_file=source, segment_id=1, cluster_id=cluster, line_start=1, cell_index=0, timestamp_raw='00:00:00', xmin=x, xmax=x, ymin=y, ymax=y, xadd=x, yadd=y, number_of_events_declared=1, field_arity=3, field0_raw=address, x=x, y=y, raw_fields=(address, x, y), classification='PHYSICAL_ELIGIBLE', classification_reason='synthetic test fixture')

def full_rank_coordinate_points() -> list[tuple[int, int]]:
    return [(0, 0)] + [(1 << i, 0) for i in range(am.COORD_BITS)] + [(0, 1 << i) for i in range(am.COORD_BITS)]

class ParserAndClassificationTests(unittest.TestCase):

    def test_parser_integrity_and_supported_row_arities(self) -> None:
        three = 'cluster 0 with xmin 1 xmax 1 ymin 2 ymax 2\nxadd 1 yadd 2 01:02:03\n17 1 2\nNUMBER OF EVENTS = 1\n'
        records, stats = am.parse_cluster_text('three.txt', three)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].raw_fields, (17, 1, 2))
        self.assertEqual(records[0].classification, 'PHYSICAL_ELIGIBLE')
        self.assertEqual(stats.bounds_mismatch_count, 0)
        two = 'cluster 1 with xmin 3 xmax 3 ymin 4 ymax 4\nxadd 3 yadd 4\n3 4\nNUMBER OF EVENTS = 1\n'
        records, _ = am.parse_cluster_text('two.txt', two)
        self.assertEqual(records[0].raw_fields, (3, 4))
        self.assertEqual(records[0].classification, 'PHYSICAL_NO_ADDRESS')
        bad = three.replace('NUMBER OF EVENTS = 1', 'NUMBER OF EVENTS = 2')
        with self.assertRaisesRegex(ValueError, 'NUMBER OF EVENTS'):
            am.parse_cluster_text('bad.txt', bad)

    def test_service_and_ambiguous_classification_invariants(self) -> None:
        base = dict(cluster_id=0, timestamp_raw='03:03:03', xmin=0, xmax=0, ymin=0, ymax=0, xadd=0, yadd=0)
        out = (am.MAX_EXTERNAL_ADDRESS + 1, 0, 0)
        cls, _ = am.classify_cell(cells=[out], cell=out, **base)
        self.assertEqual(cls, 'STRICT_SERVICE')
        inside = (0, 0, 0)
        cls, _ = am.classify_cell(cells=[inside], cell=inside, **base)
        self.assertEqual(cls, 'AMBIGUOUS')
        ordinary = (0, 1, 0)
        cls, _ = am.classify_cell(cluster_id=0, timestamp_raw='03:03:03', xmin=1, xmax=1, ymin=0, ymax=0, xadd=1, yadd=0, cells=[ordinary], cell=ordinary)
        self.assertEqual(cls, 'PHYSICAL_ELIGIBLE')
        no_address_zero = (0, 0)
        cls, _ = am.classify_cell(cluster_id=0, timestamp_raw=None, xmin=0, xmax=0, ymin=0, ymax=0, xadd=0, yadd=0, cells=[no_address_zero], cell=no_address_zero)
        self.assertEqual(cls, 'AMBIGUOUS')

    def test_event_local_deduplication_and_conflict_detection(self) -> None:
        a = make_record(source='f', cluster=1, x=5, y=7, address=11)
        b = make_record(source='f', cluster=1, x=5, y=7, address=11)
        c = make_record(source='f', cluster=2, x=5, y=7, address=11)
        ded, conflicts, removed = am.deduplicate_event_local([a, b, c])
        self.assertEqual(len(ded), 2)
        self.assertEqual(removed, 1)
        self.assertEqual(conflicts, [])
        d = make_record(source='f', cluster=1, x=5, y=7, address=12)
        _, conflicts, _ = am.deduplicate_event_local([a, d])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['candidate_addresses'], [11, 12])

class ExactGF2Tests(unittest.TestCase):

    def test_exact_gf2_rank(self) -> None:
        rows = [1 << i for i in range(9)] + [1 << 0 ^ 1 << 8]
        self.assertEqual(am.gf2_rank(rows, 9), 9)
        self.assertEqual(am.gf2_rank(rows[:-2], 9), 8)

    def test_synthetic_known_affine_mapping_recovery(self) -> None:
        rng = random.Random(62167)
        expected = [rng.getrandbits(am.FEATURE_COUNT) for _ in range(am.ADDRESS_BITS)]
        records = []
        for n, (x, y) in enumerate(full_rank_coordinate_points()):
            address = am.predict_address(x, y, expected)
            records.append(make_record(source=am.TRAINING_SOURCE, cluster=n, x=x, y=y, address=address))
        recovered, rank = am.fit_affine_mapping(records)
        self.assertEqual(rank, am.FEATURE_COUNT)
        self.assertEqual(recovered, expected)

    def test_rank_deficient_synthetic_case_is_detected(self) -> None:
        coeffs = [1 << j % am.FEATURE_COUNT for j in range(am.ADDRESS_BITS)]
        records = []
        for n, (x, y) in enumerate(full_rank_coordinate_points()[:-1]):
            address = am.predict_address(x, y, coeffs)
            records.append(make_record(source=am.TRAINING_SOURCE, cluster=n, x=x, y=y, address=address))
        recovered, rank = am.fit_affine_mapping(records)
        self.assertLess(rank, am.FEATURE_COUNT)
        self.assertEqual(recovered, [])

    def test_exact_21_bit_address_reconstruction(self) -> None:
        coeffs = [1 << j % am.FEATURE_COUNT ^ 1 << (j + 7) % am.FEATURE_COUNT for j in range(am.ADDRESS_BITS)]
        for x, y in [(0, 0), (4095, 4095), (1365, 2730), (123, 3456)]:
            v = am.feature_mask(x, y)
            expected = sum((((v & c).bit_count() & 1) << j for j, c in enumerate(coeffs)))
            actual = am.predict_address(x, y, coeffs)
            self.assertEqual(actual, expected)
            self.assertGreaterEqual(actual, 0)
            self.assertLessEqual(actual, am.MAX_EXTERNAL_ADDRESS)

    def test_result_is_independent_of_input_order(self) -> None:
        rng = random.Random(7)
        coeffs = [rng.getrandbits(am.FEATURE_COUNT) for _ in range(am.ADDRESS_BITS)]
        records = []
        for n, (x, y) in enumerate(full_rank_coordinate_points()):
            records.append(make_record(source=am.TRAINING_SOURCE, cluster=n, x=x, y=y, address=am.predict_address(x, y, coeffs)))
        forward, rank1 = am.fit_affine_mapping(records)
        shuffled = records[:]
        rng.shuffle(shuffled)
        backward, rank2 = am.fit_affine_mapping(shuffled)
        self.assertEqual(rank1, am.FEATURE_COUNT)
        self.assertEqual(rank2, am.FEATURE_COUNT)
        self.assertEqual(forward, backward)
        self.assertEqual(forward, coeffs)

class ExportTests(unittest.TestCase):

    def test_exported_equations_equal_exported_coefficient_matrix(self) -> None:
        here = Path(__file__).resolve().parent
        coeff = json.loads((here / 'address_mapping_coefficients.json').read_text(encoding='utf-8'))
        features = coeff['feature_order']
        equations = (here / 'address_mapping_equations.md').read_text(encoding='utf-8').splitlines()
        parsed: dict[int, list[int]] = {}
        for line in equations:
            m = re.fullmatch('A(\\d+) = (.+)', line.strip())
            if not m:
                continue
            bit = int(m.group(1))
            rhs = m.group(2)
            terms = [] if rhs == '0' else rhs.split(' xor ')
            row = [int(name in terms) for name in features]
            self.assertEqual(len(terms), sum(row), f'unknown/duplicate term in {line}')
            parsed[bit] = row
        self.assertEqual(sorted(parsed), list(range(am.ADDRESS_BITS)))
        masks = []
        for j in range(am.ADDRESS_BITS):
            mask = sum((bit << i for i, bit in enumerate(parsed[j])))
            masks.append(mask)
        self.assertEqual(masks, coeff['coefficient_masks_lsb_feature_order'])

@unittest.skipUnless(os.environ.get('CY62167_ARCHIVE'), 'set CY62167_ARCHIVE for raw-data integration tests')
class FullArchiveIntegrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.archive = Path(os.environ['CY62167_ARCHIVE'])
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.result = am.run_analysis(cls.archive, cls.out)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_archive_parser_integrity_and_public_member_hashes(self) -> None:
        manifest = self.result['input_manifest']
        validation = self.result['validation']
        self.assertTrue(manifest['provided_archive']['archive_inspection_performed_before_member_payload_read'])
        self.assertTrue(manifest['all_members_match_public_zenodo_md5'])
        self.assertEqual(manifest['provided_archive']['member_count'], len(am.ZENODO_MD5))
        self.assertEqual(validation['parser']['bounds_mismatch_clusters'], 0)
        self.assertEqual(validation['parser']['coordinate_out_of_range_records'], 0)
        self.assertEqual(validation['event_local_address_conflicts'], [])

    def test_training_heldout_separation_guard_and_frozen_validation(self) -> None:
        sep = self.result['validation']['training_validation_separation']
        self.assertEqual(sep['fit_files'], [am.TRAINING_SOURCE])
        self.assertNotIn(am.TRAINING_SOURCE, sep['heldout_files'])
        self.assertFalse(sep['coefficient_selection_uses_heldout'])
        self.assertFalse(sep['feature_selection_uses_heldout'])
        self.assertEqual(self.result['validation']['training_mismatches'], 0)
        self.assertEqual(self.result['validation']['heldout_mismatches'], 0)

    def test_exported_outputs_reconstruct_addresses_directly(self) -> None:
        coeff = self.result['coefficients']['coefficient_masks_lsb_feature_order']
        _, infos = am.inspect_archive_before_member_read(self.archive)
        texts, _ = am.read_archive_members_and_hash(self.archive, infos)
        all_records = []
        for source in sorted(texts):
            rs, _ = am.parse_cluster_text(source, texts[source])
            all_records.extend(rs)
        primary = [r for r in all_records if r.classification == 'PHYSICAL_ELIGIBLE']
        deduped, conflicts, _ = am.deduplicate_event_local(primary)
        self.assertEqual(conflicts, [])
        for r in deduped:
            self.assertEqual(am.predict_address(r.x, r.y, coeff), r.field0_raw)
if __name__ == '__main__':
    unittest.main()

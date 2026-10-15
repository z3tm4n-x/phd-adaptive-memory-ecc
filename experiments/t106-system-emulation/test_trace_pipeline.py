"""Storage-only sentinels; independently computed original byte hash."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import burst_codec
import trace_codec
from trace_pipeline_v3 import AuditedRows, capture, transcode


class TracePipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.raw = self.root/'source.txt'; self.ct2 = self.root/'trace.ctz'
        self.ct3 = self.root/'trace.ct3'; self.receipt = self.root/'capture.json'
        self.data = ''.join(f'PIN {202376233820426000+i*4000} {i} 00000000 ff\n'
                            for i in range(trace_codec.BLOCK+3))+'END 363900000000000000\n'
        self.raw.write_bytes(self.data.encode('ascii'))

    def test_checkpoint_precedes_any_archive_readback(self):
        with patch.object(trace_codec, 'digest', side_effect=AssertionError('must not reread')):
            stats = capture(self.raw, self.ct2, self.receipt)
        self.assertEqual(stats['raw_sha256'], hashlib.sha256(self.raw.read_bytes()).hexdigest())
        self.assertEqual(stats['records'], self.data.count('\n'))
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt, dict(status='captured_not_yet_verified', **stats))
        self.assertEqual(''.join(trace_codec.lines(self.ct2)), self.data)

    def test_full_roundtrip_matches_existing_codecs(self):
        stats = capture(self.raw, self.ct2, self.receipt)
        old2 = self.root/'old.ctz'; old3 = self.root/'old.ct3'
        trace_codec.pack(self.raw, old2); burst_codec.pack(old2, old3)
        transcode(self.ct2, self.ct3, stats)
        self.assertEqual(self.ct2.read_bytes(), old2.read_bytes())
        self.assertEqual(self.ct3.read_bytes(), old3.read_bytes())
        audit = AuditedRows(); observed = list(audit(self.ct3)); audit.verify(stats)
        self.assertEqual(observed, [(i, row.split()) for i, row in enumerate(self.data.splitlines(), 1)])

    def test_bad_original_hash_rejected_before_publication(self):
        stats = capture(self.raw, self.ct2, self.receipt)
        with self.assertRaisesRegex(AssertionError, 'SHA mismatch'):
            transcode(self.ct2, self.ct3, dict(stats, raw_sha256='0'*64))
        self.assertFalse(self.ct3.exists()); self.assertTrue(self.receipt.exists())

    def test_record_count_and_incomplete_consumption_rejected(self):
        stats = capture(self.raw, self.ct2, self.receipt)
        transcode(self.ct2, self.ct3, stats)
        audit = AuditedRows(); reader = audit(self.ct3); next(reader)
        with self.assertRaisesRegex(AssertionError, 'complete trace'): audit.verify(stats)
        list(reader)
        with self.assertRaisesRegex(AssertionError, 'record-count'):
            audit.verify(dict(stats, records=stats['records']+1))

    def test_truncated_archive_rejected(self):
        stats = capture(self.raw, self.ct2, self.receipt)
        transcode(self.ct2, self.ct3, stats)
        damaged = self.root/'damaged.ct3'; damaged.write_bytes(self.ct3.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError, 'short CT3 block'): list(AuditedRows()(damaged))

    def test_wrong_decoded_field_rejected_by_original_hash(self):
        stats = capture(self.raw, self.ct2, self.receipt)
        transcode(self.ct2, self.ct3, stats)
        audit = AuditedRows()
        with patch.object(burst_codec, 'lines', return_value=iter(self.data.replace(' ff\n', ' fe\n', 1).splitlines(True))):
            list(audit(self.ct3))
        with self.assertRaisesRegex(AssertionError, 'SHA mismatch'): audit.verify(stats)

    def test_existing_archive_not_overwritten(self):
        stats = capture(self.raw, self.ct2, self.receipt)
        transcode(self.ct2, self.ct3, stats); before = self.ct3.read_bytes()
        with self.assertRaisesRegex(AssertionError, 'overwrite'): transcode(self.ct2, self.ct3, stats)
        self.assertEqual(before, self.ct3.read_bytes())


if __name__ == '__main__': unittest.main()

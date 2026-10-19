"""The recorder must reject real differences, not tuple/list representation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from report_guard import canonical, prepare, publish_or_compare


class ReportGuardTests(unittest.TestCase):
    def test_read_only_repair_replay_creates_no_scratch_directory(self):
        from verify_burst_repair import main
        with patch.object(Path, 'mkdir', side_effect=AssertionError('read-only replay created a directory')):
            main()

    def sample(self):
        return dict(scope='digital only', results=dict(count=2**63+1,
            mean=0.123456789012345, permissions=[(9, False, None)]),
            sha256={'a.trace.ct3': 'trace-digest', 'verify.py': 'old-code'})

    def test_container_only_change_is_equal(self):
        report = self.sample()
        self.assertEqual(prepare(report, canonical(report)), canonical(report))

    def test_provenance_refresh_is_auditable_and_idempotent(self):
        old = canonical(self.sample())
        new = copy.deepcopy(old)
        new['sha256']['verify.py'] = 'new-code'
        refreshed = prepare(new, old)
        self.assertEqual(refreshed['results'], old['results'])
        self.assertEqual(refreshed['verification_history'][0]['previous_sha256'], old['sha256'])
        self.assertEqual(prepare(new, refreshed), refreshed)

    def test_rejects_count_float_scope_or_trace_mutation(self):
        old = canonical(self.sample())
        mutations = [
            lambda d: d['results'].update(count=2**63),
            lambda d: d['results'].update(mean=0.123456789012346),
            lambda d: d['results'].update(permissions=[[9, 0, None]]),
            lambda d: d.update(scope='physical'),
            lambda d: d['sha256'].update({'a.trace.ct3': 'different'}),
            lambda d: d['sha256'].pop('a.trace.ct3'),
        ]
        for mutate in mutations:
            new = copy.deepcopy(old)
            mutate(new)
            with self.assertRaises(AssertionError):
                prepare(new, old)

    def test_rejection_leaves_saved_report_byte_identical(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'report.json'
            old = self.sample()
            publish_or_compare(path, old, record=True)
            before = path.read_bytes()
            changed = copy.deepcopy(old)
            changed['results']['count'] += 1
            with self.assertRaises(AssertionError):
                publish_or_compare(path, changed, record=True)
            self.assertEqual(path.read_bytes(), before)
            publish_or_compare(path, old)

    def test_read_only_cannot_silently_refresh_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'report.json'
            publish_or_compare(path, self.sample(), record=True)
            new = self.sample()
            new['sha256']['verify.py'] = 'new-code'
            before = path.read_bytes()
            with self.assertRaises(AssertionError):
                publish_or_compare(path, new)
            self.assertEqual(path.read_bytes(), before)

    def test_nonfinite_value_is_not_valid_result(self):
        for value in (float('nan'), float('inf'), -float('inf')):
            with self.assertRaises(ValueError):
                canonical({'value': value})


if __name__ == '__main__':
    unittest.main()

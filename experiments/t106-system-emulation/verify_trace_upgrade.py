"""V3 storage-only change: exact prior inputs/rows/results in real pilot runs."""
import argparse
import hashlib
import json
from pathlib import Path
from report_guard import encoded, publish_or_compare
from trace_pipeline_v3 import AuditedRows

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE/'outputs'


def main(record=False):
    files = [Path(__file__).resolve(), HERE/'POSTPROCESSING.md', HERE/'trace_pipeline_v3.py',
             HERE/'test_trace_pipeline.py', OUT/'failed-postprocessing-attempt.json']
    comparisons = {}
    for mode in ('adaptive', 'fixed'):
        paths = [OUT/f'{prefix}-pilot20-{mode}-skip{suffix}.json'
                 for prefix in ('burst2', 'burst3') for suffix in ('', '-checked')]
        old, old_check, new, new_check = [json.loads(p.read_text()) for p in paths]
        assert encoded(old['stimulus']) == encoded(new['stimulus'])
        assert old['input_sha256'] == new['input_sha256']
        assert old['trace_sha256'] == new['trace_sha256'], 'pilot raw trace changed'
        assert encoded(old_check['results']) == encoded(new_check['results']), 'pilot result changed'
        for p, h in new['source_sha256'].items():
            assert hashlib.sha256((REPO/p).read_bytes()).hexdigest() == h, p
        old_archive = OUT/f'burst2-pilot20-{mode}-skip.trace.ct3'
        new_archive = OUT/f'burst3-pilot20-{mode}-skip.trace.ct3'
        assert old_archive.read_bytes() == new_archive.read_bytes(), 'CT3 encoding changed'
        comparisons[mode] = dict(raw_trace_sha256=new['trace_sha256'],
            identical_inputs=True, identical_raw_trace=True, identical_results=True,
            identical_compact_archive=True, injections=len(new['stimulus']['injections']))
        files += paths+[old_archive, new_archive]
    old_path = OUT/'burst2-short-adaptive-skip.json'
    new_path = OUT/'burst3-short-adaptive-skip.json'
    old, new = [json.loads(p.read_text()) for p in (old_path, new_path)]
    assert old['stimulus'] == new['stimulus'] and old['input_sha256'] == new['input_sha256']
    assert old['trace_sha256'] == new['trace_sha256'], 'short trace changed'
    # Short CT2 is small and published; consume every row and check original hash.
    short = OUT/'burst3-short-adaptive-skip.trace.ctz'
    audit = AuditedRows(); list(audit(short)); audit.verify(new['trace_storage'])
    comparisons['short_adaptive'] = dict(identical_raw_trace=True, raw_trace_sha256=new['trace_sha256'])
    files += [old_path, new_path, short]
    report = dict(scope='storage repair only; real short and pilot20 executions, not full scenario2',
        comparisons=comparisons, sha256={p.relative_to(REPO).as_posix():
            hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    publish_or_compare(OUT/'trace-pipeline-equivalence.json', report, record)
    print('V3: short and both pilot20 raw traces match V2; CT3 bytes and scientific results match')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--record', action='store_true')
    main(p.parse_args().record)

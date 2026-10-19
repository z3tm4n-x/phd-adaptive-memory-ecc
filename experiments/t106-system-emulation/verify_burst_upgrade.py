"""Unchanged technical prefix: new stand against the original pinned evidence."""
import argparse
import hashlib
import json
from pathlib import Path
from report_guard import encoded, publish_or_compare

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE/'outputs'


def main(record=False):
    comparisons = {}
    files = [Path(__file__).resolve(), OUT/'failed-full-attempt.json']
    for mode in ('adaptive', 'fixed'):
        paths = [OUT/f'{prefix}-pilot20-{mode}-skip{suffix}.json'
                 for prefix in ('burst', 'burst2') for suffix in ('', '-checked')]
        old, old_check, new, new_check = [json.loads(p.read_text()) for p in paths]
        assert encoded(old['stimulus']) == encoded(new['stimulus'])
        assert old['input_sha256'] == new['input_sha256']
        assert old['trace_sha256'] == new['trace_sha256'], 'pilot raw trace changed'
        assert encoded(old_check['results']) == encoded(new_check['results']), 'pilot scientific result changed'
        for p, h in new['source_sha256'].items():
            assert hashlib.sha256((REPO/p).read_bytes()).hexdigest() == h, p
        comparisons[mode] = dict(raw_trace_sha256=new['trace_sha256'],
            identical_inputs=True, identical_raw_trace=True, identical_results=True,
            horizon_ns=new['stimulus']['horizon_ns'],
            injections=len(new['stimulus']['injections']))
        files += paths
    report = dict(scope='same original 20-event technical prefix; not full scenario2',
        comparisons=comparisons, sha256={p.relative_to(REPO).as_posix():
            hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    publish_or_compare(OUT/'burst-pilot-equivalence.json', report, record)
    print('Both original/new pilot20 streams, raw traces and scientific results are identical')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--record', action='store_true')
    main(p.parse_args().record)

"""Complete V3 capture -> CT3 integrity -> unchanged scientific checker.

The independent memory/rule/price checker is byte-identical to V2. Only its
generic row iterator is wrapped to hash the rows in the same complete pass.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch
from burst_run_inputs import HERE, build
import check_burst
from report_guard import publish_or_compare
from trace_pipeline_v3 import AuditedRows, transcode

REPO = HERE.parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''): h.update(chunk)
    return h.hexdigest()


def verify(mode, pilot_events=0, execute=False, record=False):
    case = 'pilot'+str(pilot_events) if pilot_events else 'burst'
    stem = f'burst3-{case}-{mode}-skip'
    output = HERE/'outputs'; meta_path = output/f'{stem}.json'
    trace = output/f'{stem}.trace.ct3'; destination = output/f'{stem}-checked.json'
    if execute:
        assert not meta_path.exists(), 'preserve existing execution; replay without --execute'
        cmd = [sys.executable, str(HERE/'run_burst_v3.py'), '--mode', mode]
        if pilot_events: cmd += ['--pilot-events', str(pilot_events)]
        subprocess.run(cmd, check=True)
    assert meta_path.exists(), 'capture metadata missing: '+stem
    meta = json.loads(meta_path.read_text())
    assert meta['stimulus'] == build('burst', pilot_events), 'frozen stream changed'
    for path, h in meta['source_sha256'].items():
        assert sha(REPO/path) == h, ('executed source drift', path)
    assert meta['trace_storage']['raw_sha256'] == meta['trace_sha256']
    if not trace.exists():
        assert record, 'first compact trace requires --record'
        print(stem, 'transcoding captured stream', flush=True)
        transcode(output/f'{stem}.trace.ctz', trace, meta['trace_storage'])
    started = time.monotonic(); audit = AuditedRows()
    print(stem, 'independent scientific replay with streaming integrity check', flush=True)
    with patch.object(check_burst, 'rows', audit):
        result = check_burst.check(trace, meta)
    audit.verify(meta['trace_storage'])
    print(stem, 'checked; seconds', round(time.monotonic()-started, 3), flush=True)
    assert result['injections'] == len(meta['stimulus']['injections'])
    assert result['application_completed'] == 0 and result['logical_data_words_changed'] == 0
    assert result['history_events'] == result['err_events']
    result['CPU'] = {k: meta[k] for k in
        ('ARM_instructions_including_boot', 'ARM_instructions_runtime', 'completed_driver_visits',
         'represented_full_services', 'represented_driver_visits', 'represented_MMIO_reads',
         'represented_MMIO_writes', 'represented_ISA_count', 'MMIO')}
    result['CPU']['actual_ARM_time_ns'] = None
    files = [meta_path, trace]+[HERE/f for f in
        ('check_burst.py', 'burst_codec.py', 'trace_codec.py', 'burst_price.py',
         'trace_pipeline_v3.py', 'verify_burst_v3.py', 'BURST_SCALE.md', 'BURST_REPAIR.md',
         'POSTPROCESSING.md', 'report_guard.py')]
    report = dict(scope='technical prefix ONLY' if pilot_events else 'complete frozen scenario2, digital model ONLY',
        original_frozen_input_commit='f68b335', runner_protocol='POSTPROCESSING.md',
        results=result, raw_trace_sha256=meta['trace_sha256'],
        sha256={p.relative_to(REPO).as_posix(): sha(p) for p in files},
        shared_dependencies=['birth-labelled Memory and ETransaction',
            'absolute raw rule Oracle', 'unchanged generic CT2/CT3 token coding and decoder',
            'row audit wrapper changes neither order nor fields; no model row reconstruction'],
        integrity=dict(original_records=meta['trace_storage']['records'],
            original_stream_hash_checked_during_scientific_replay=True, complete_EOF_checked=True),
        not_claimed=['hardware ARM time/WCET', 'mission Q(T)', 'physical response calibration', 'scientific acceptance'])
    report = publish_or_compare(destination, report, record)
    print(json.dumps({k: result[k] for k in
        ('horizon_ns', 'injections', 'err_events', 'mean_bus_fraction', 'peak_any_1ms_fraction',
         'completed_operations', 'unfinished_operations', 'first_exceedance_relative_ns')}), flush=True)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--execute', action='store_true')
    p.add_argument('--record', action='store_true'); p.add_argument('--pilot-events', type=int, default=0)
    p.add_argument('--mode', choices=['adaptive', 'fixed', 'both'], default='both'); a = p.parse_args()
    for mode in (['adaptive', 'fixed'] if a.mode == 'both' else [a.mode]):
        verify(mode, a.pilot_events, a.execute, a.record)

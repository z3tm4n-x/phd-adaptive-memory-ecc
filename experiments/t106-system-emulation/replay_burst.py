"""Read-only published-result verification with exact JSON containers.

This command never updates a report or its recorded provenance.
"""
import argparse
import hashlib
import json
from pathlib import Path
from burst_run_inputs import HERE,build
from burst_codec import digest
from check_burst import check
from report_guard import canonical,encoded

REPO=HERE.parents[1]


def verify(stem):
    report=json.loads((HERE/f'outputs/{stem}-checked.json').read_text())
    meta=json.loads((HERE/f'outputs/{stem}.json').read_text())
    for p,h in report['sha256'].items():
        assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,('source/archive drift',p)
    for p,h in meta['source_sha256'].items():
        assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,('executed source drift',p)
    if 'cold-envelope' in stem:
        from cold_envelope import build as cold_build
        expected=cold_build()
    else:
        expected=build(pilot_events=20 if 'pilot20' in stem else 0)
    assert meta['stimulus']==expected
    trace=HERE/f'outputs/{stem}.trace.ct3'
    assert digest(trace)==meta['trace_sha256']
    result=check(trace,meta)
    if 'CPU' in report['results']:
        result['CPU']={k:meta[k] for k in
            ('ARM_instructions_including_boot','ARM_instructions_runtime','completed_driver_visits',
             'represented_full_services','represented_driver_visits','represented_MMIO_reads',
             'represented_MMIO_writes','represented_ISA_count','MMIO')}
        result['CPU']['actual_ARM_time_ns']=None
    assert encoded(result)==encoded(report['results']),('independent replay changed',stem)
    print(stem,': read-only replay matched; injections',result['injections'],flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',choices=['pilot20','burst','cold-envelope'],default='pilot20')
    a=p.parse_args()
    prefix='burst2' if a.case=='burst' else 'burst'
    for mode in ('adaptive','fixed'):verify(f'{prefix}-{a.case}-{mode}-skip')

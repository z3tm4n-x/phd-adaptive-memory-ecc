"""New full-profile/prefix execution and independent trace verification.

No scientific summary is accepted merely because execution returned zero.
--record is explicit and source/stream/memory/price assertions precede it.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from burst_run_inputs import HERE,build
from burst_codec import pack,digest
from check_burst import check

REPO=HERE.parents[1]


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def verify(mode,pilot_events=0,execute=False,record=False):
    case='pilot'+str(pilot_events) if pilot_events else 'burst'
    stem=f'burst-{case}-{mode}-skip'
    output=HERE/'outputs';meta_path=output/f'{stem}.json'
    trace=output/f'{stem}.trace.ct3'
    destination=output/f'{stem}-checked.json'
    if execute:
        cmd=[sys.executable,str(HERE/'run_burst.py'),'--mode',mode]
        if pilot_events:cmd+=['--pilot-events',str(pilot_events)]
        subprocess.run(cmd,check=True)
    assert meta_path.exists(),'execution missing: '+stem
    meta=json.loads(meta_path.read_text())
    assert meta['stimulus']==build('burst',pilot_events),'frozen stream changed'
    for path,h in meta['source_sha256'].items():
        assert sha(REPO/path)==h,('runner source drift',path)
    if execute or not trace.exists():
        assert record,'first compact trace requires --record'
        stats=pack(output/f'{stem}.trace.ctz',trace)
        assert stats['raw_sha256']==meta['trace_sha256']
    assert digest(trace)==meta['trace_sha256'],'raw trace differs'
    started=time.monotonic();result=check(trace,meta)
    print(stem,'checked; seconds',round(time.monotonic()-started,3),flush=True)
    assert result['injections']==len(meta['stimulus']['injections'])
    assert result['application_completed']==0 and result['logical_data_words_changed']==0
    assert result['history_events']==result['err_events']
    result['CPU']={k:meta[k] for k in
        ('ARM_instructions_including_boot','ARM_instructions_runtime','completed_driver_visits',
         'represented_full_services','represented_driver_visits','represented_MMIO_reads',
         'represented_MMIO_writes','represented_ISA_count','MMIO')}
    result['CPU']['actual_ARM_time_ns']=None
    files=[meta_path,trace]+[HERE/f for f in
        ('check_burst.py','burst_codec.py','burst_price.py','verify_burst.py','BURST_SCALE.md')]
    report=dict(scope='technical prefix ONLY' if pilot_events else 'complete frozen scenario2, digital model ONLY',
        preregistered_runner_commit='f68b335',
        results=result,raw_trace_sha256=meta['trace_sha256'],
        sha256={p.relative_to(REPO).as_posix():sha(p) for p in files},
        shared_dependencies=['birth-labelled Memory and ETransaction',
            'absolute raw rule Oracle','generic column token coding; no model row reconstruction'],
        not_claimed=['hardware ARM time/WCET','mission Q(T)','physical response calibration','scientific acceptance'])
    if record:
        destination.write_text(json.dumps(report,indent=2)+'\n')
    else:assert report==json.loads(destination.read_text()),'replayed result changed'
    print(json.dumps({k:result[k] for k in
        ('horizon_ns','injections','err_events','mean_bus_fraction','peak_any_1ms_fraction',
         'completed_operations','unfinished_operations','first_exceedance_relative_ns')}),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true')
    p.add_argument('--record',action='store_true');p.add_argument('--pilot-events',type=int,default=0)
    p.add_argument('--mode',choices=['adaptive','fixed','both'],default='both');a=p.parse_args()
    for mode in (['adaptive','fixed'] if a.mode=='both' else [a.mode]):
        verify(mode,a.pilot_events,a.execute,a.record)

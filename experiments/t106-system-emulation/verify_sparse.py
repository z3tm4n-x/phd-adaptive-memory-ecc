"""Replay/fresh execution for scenario5 and nonempty acceleration witnesses."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from check_sparse import HERE, check
from trace_codec import pack, digest, compare
from sparse_inputs import build

REPO=HERE.parents[1]
RUNS=[('short','adaptive','literal'),('short','adaptive','skip'),
      ('lowprobe','adaptive','no-low'),('lowprobe','adaptive','skip'),
      ('memory','adaptive','skip'),('memory','fixed','skip')]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def verify(execute=False,record=False):
    dest=HERE/'outputs/sparse-summary.json'
    old=json.loads(dest.read_text()) if dest.exists() else None
    if not execute and not record:
        assert old,'explicit --record is required for the first reviewed results'
        for path,h in old['sha256'].items():assert sha(REPO/path)==h,path
    results={};files=[];metas={}
    for case,mode,variant in RUNS:
        stem=f'sparse-{case}-{mode}-{variant}'
        if execute:
            cmd=[sys.executable,str(HERE/'run_sparse.py'),'--case',case,'--mode',mode]
            if variant=='literal':cmd.append('--literal')
            if variant=='no-low':cmd.append('--no-low-jump')
            subprocess.run(cmd,check=True)
            pack(HERE/f'outputs/{stem}.trace.gz',HERE/f'outputs/{stem}.trace.ctz')
        j,p=HERE/f'outputs/{stem}.json',HERE/f'outputs/{stem}.trace.ctz'
        m=json.loads(j.read_text());metas[stem]=m
        assert m['stimulus']==build(case),'frozen input changed'
        for path,h in m['source_sha256'].items():assert sha(REPO/path)==h,path
        assert digest(p)==m['trace_sha256'],'lossless trace digest'
        if execute and old:
            assert sha(p)==old['sha256'][p.relative_to(REPO).as_posix()],('deterministic trace changed',stem)
        r=check(p,m)
        if variant=='skip' and case in ('short','lowprobe'):
            base='literal' if case=='short' else 'no-low'
            r['literal_equivalence']=compare(HERE/f'outputs/sparse-{case}-{mode}-{base}.trace.ctz',p)
        r['CPU']={k:m[k] for k in ('ARM_instructions_runtime','ARM_instructions_including_boot',
            'completed_driver_visits','represented_full_services','represented_driver_visits',
            'represented_MMIO_reads','represented_MMIO_writes','represented_ISA_count','MMIO')}
        r['CPU']['actual_ARM_time_ns']=None
        results[stem]=r;files.extend((j,p))
        print(stem,':',r['pin_edges_checked'],'literal E edges;',r['application_completed'],'responses;',
              r['completed_operations'],'completed/represented operations',flush=True)
    a,b=[metas[f'sparse-memory-{m}-skip'] for m in ('adaptive','fixed')]
    assert a['stimulus']==b['stimulus']
    for key in ('injections.txt','application.txt'):assert a['input_sha256'][key]==b['input_sha256'][key]
    # Compression and acceleration do not silently erase CPU/MMIO work.
    a,b=[metas[f'sparse-short-adaptive-{v}'] for v in ('literal','skip')]
    for key in ('runtime_read','runtime_write'):
        assert a['MMIO'][key]-b['MMIO'][key]==10*b['represented_full_services']
    assert a['completed_driver_visits']-b['completed_driver_visits']==2*b['represented_full_services']
    for mode in ('adaptive','fixed'):
        r=results[f'sparse-memory-{mode}-skip']
        assert r['first_exceedance_relative_ns']==180600000006
        assert r['application_completed']==40 and r['remaining_error_positions']==0
        assert r['never_written_words']==524283
        long=[x for x in r['read_results'] if x['word']==400000]
        assert len(long)==7 and all(x['data']=='12340000' for x in long)
        untouched=[x for x in r['read_results'] if x['word']==12345]
        assert len(untouched)==4 and all(x['data']=='a5a53039' for x in untouched)
    files += [HERE/f for f in ('SPARSE.md','sparse_inputs.py','run_sparse.py','tb_sparse.sv','sparse.tcl',
                              'check_sparse.py','trace_codec.py','test_sparse.py','verify_sparse.py')]
    result={'preregistered_commit':'9d340bb','scope':'scenario5; prior1/3/4 retained; scenario2 not executed',
        'results':results,'sha256':{p.relative_to(REPO).as_posix():sha(p) for p in files},
        'shared_dependencies':['birth-labelled Memory oracle','ETransaction/ServiceConfig/raw Oracle',
            'previous exact price integral','CP15/GIC harness','ABI/vendor XPM/Unicorn/XSim'],
        'not_claimed':['physical memory qualification','hardware ARM WCET','mission Q(T)','five-scenario completion']}
    result=json.loads(json.dumps(result))
    if execute or record:dest.write_text(json.dumps(result,indent=2)+'\n')
    else:assert result==old,'replayed result changed'
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--record',action='store_true')
    a=p.parse_args();verify(a.execute,a.record)

"""Portable replay or fresh full-top/ELF generation of the long clean cases."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from check_accel import HERE,check,compare_short

REPO=HERE.parents[1]
RUNS=[('short','adaptive','literal'),('short','adaptive','skip'),
      ('lowprobe','adaptive','no-low'),('lowprobe','adaptive','skip'),
      ('quiet','adaptive','skip'),('quiet','fixed','skip'),
      ('loss','adaptive','skip'),('loss','fixed','skip')]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def profile():
    meta=json.loads((HERE/'outputs/t67-profile.json').read_text())
    p=HERE/'outputs/t67-profile.json.gz';assert sha(p)==meta['profile_sha256']
    for path,digest in meta['source_sha256'].items():assert sha(REPO/path)==digest,path
    with gzip.open(p,'rt') as f:table=json.load(f)
    rows=table['records'];assert len(rows)==6065 and table['duration_s']==60
    assert all(b[0]-a[0]==60 for a,b in zip(rows,rows[1:]))
    assert all(isinstance(t,int) and v is not None and math.isfinite(v) and v>=0 and good for t,v,good in rows)
    assert max(r[1] for r in rows)==meta['peak_model_per_s']
    assert math.isclose(math.fsum(r[1]*60 for r in rows),meta['integral_valid_model_inversions'],rel_tol=2e-15)
    assert not meta['source_model']['is_R0A_full38_3g_calibration']
    return {k:meta[k] for k in ('bins','usable_bins','profile_sha256','R0A_normalization','source_model')}

def verify(execute=False,record=False):
    dest=HERE/'outputs/accel-summary.json'
    old=json.loads(dest.read_text()) if dest.exists() else None
    if not execute and not record:
        assert old,'run --record once after reviewing generated outputs'
        for path,digest in old['sha256'].items():assert sha(REPO/path)==digest,path
    if execute:
        for case,mode,variant in RUNS:
            cmd=[sys.executable,str(HERE/'run_accel.py'),'--case',case,'--mode',mode]
            if variant=='literal':cmd+=['--literal']
            if variant=='no-low':cmd+=['--no-low-jump']
            subprocess.run(cmd,check=True)
    results={};files=[]
    for case,mode,variant in RUNS:
        stem=f'accel-{case}-{mode}-{variant}'
        j,p=HERE/f'outputs/{stem}.json',HERE/f'outputs/{stem}.trace.gz'
        meta=json.loads(j.read_text())
        for path,digest in meta['source_sha256'].items():assert sha(REPO/path)==digest,('rerun after source change',path)
        with gzip.open(p,'rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==meta['trace_sha256']
        if old and execute:assert sha(p)==old['sha256'][p.relative_to(REPO).as_posix()],('deterministic trace changed',stem)
        result=check(p,meta)
        if variant=='skip' and case in ('short','lowprobe'):
            base='literal' if case=='short' else 'no-low'
            result['literal_equivalence']=compare_short(HERE/f'outputs/accel-{case}-{mode}-{base}.trace.gz',p)
        result['CPU']={k:meta[k] for k in ('ARM_instructions_runtime','completed_driver_visits','represented_full_services',
                      'represented_driver_visits','represented_MMIO_reads','represented_MMIO_writes','represented_ISA_count','MMIO')}
        result['CPU']['actual_ARM_time_ns']=None
        results[stem]=result;files.extend((j,p))
        print(stem,': checked',result['pin_edges_checked'],'E edges;',result['completed_operations'],'completed/represented operations',flush=True)
    # Pair identity is checked independently of filenames and resulting costs.
    for case in ('quiet','loss'):
        a=json.loads((HERE/f'outputs/accel-{case}-adaptive-skip.json').read_text())
        b=json.loads((HERE/f'outputs/accel-{case}-fixed-skip.json').read_text())
        assert a['stimulus']==b['stimulus']
    a=json.loads((HERE/'outputs/accel-short-adaptive-literal.json').read_text())
    b=json.loads((HERE/'outputs/accel-short-adaptive-skip.json').read_text())
    omitted=b['represented_full_services']
    for name in ('runtime_read','runtime_write'):
        assert a['MMIO'][name]-b['MMIO'][name]==10*omitted
    assert a['completed_driver_visits']-b['completed_driver_visits']==2*omitted
    result={'preregistered_commit':'0ebba34','scope':'scenarios1/3 plus prior4; 2/5 remain open',
      'results':results,'profile2_input':profile(),
      'shared_dependencies':['accepted ETransaction/ServiceConfig/raw Oracle','corrected startup CP15/GIC harness',
        'vendor XPM','ABI/constants','Unicorn/XSim'],
      'not_claimed':['hardware WCET','probability Q(T) over mission','five-scenario completion','new routed STA']}
    files += [HERE/p for p in ('run_accel.py','tb_accel.sv','accel.tcl','bridge.c','empty_rule.py','empty_time.py',
                              'check_accel.py','test_accel.py','verify_accel.py','ACCELERATION.md',
                              'outputs/t67-profile.json','outputs/t67-profile.json.gz')]
    result['sha256']={p.relative_to(REPO).as_posix():sha(p) for p in files}
    result=json.loads(json.dumps(result))  # normalize tuples to the published JSON schema
    if execute or record:dest.write_text(json.dumps(result,indent=2)+'\n')
    else:assert result==old,'replay result changed'
    print('Full clean-case replay PASS; scenario2 normalization/execution and scenario5 remain open')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--record',action='store_true')
    args=p.parse_args();verify(args.execute,args.record)

"""Edge oracle, ID join stress, actual XPM and mutation. No vendor stub in simulation."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
SPLIT=BASE/'split'
spec=importlib.util.spec_from_file_location('old_checks',SPLIT/'check.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--vendor',action='store_true')
    ap.add_argument('--vivado',default='/home/z3tm4n/bin/vivado-wsl')
    args=ap.parse_args()
    build=BASE/'.build'/('registered-check-'+str(time.time_ns()));build.mkdir(parents=True)
    sources=[p for p in HERE.iterdir() if p.suffix in ('.sv','.py','.tcl')]
    before={p.name:old.sha(p) for p in sources}
    results={}
    def run(cmd,name,timeout=180):
        code,log=old.run([str(x) for x in cmd],build,name,timeout=timeout)
        assert code==0,log[-6000:]
        return log
    def sim(name,top,files,expect):
        run(['iverilog','-g2012','-s',top,'-o',build/name,*files],name+'-compile')
        code,log=old.run(['vvp',str(build/name)],build,name)
        if expect: assert code==0 and 'PASS' in log,log
        else: assert code!=0 and 'mismatch' in log,log
        results[name]={'matched':expect,'log':log,'sha256':hashlib.sha256(log.encode()).hexdigest()}
    sim('equivalence','tb_equivalence',[HERE/'tb_equivalence.sv',HERE/'e_backend_registered.sv',BASE/'rtl/e_backend.sv'],True)
    mutant=(HERE/'e_backend_registered.sv').read_text().replace('step[35] && op==CONTROL','step[36] && op==CONTROL')
    (build/'mutant.sv').write_text(mutant)
    sim('release-mutant','tb_equivalence',[HERE/'tb_equivalence.sv',build/'mutant.sv',BASE/'rtl/e_backend.sv'],False)
    sim('generation','tb_generation',[HERE/'generation_guard.sv',HERE/'tb_generation.sv'],True)
    results['vendor']=[]
    if args.vendor:
        # Bench labels transactions by acceptance order only. IDs aren't inserted
        # into the fast DUT. Actual returned slow ID is checked against that order.
        tb=(SPLIT/'tb_lane.sv').read_text()
        changes={'wire [15:0] dq_out,gen;':'wire [15:0] dq_out; wire [63:0] gen;',
          'wire [120:0] granted;':'wire [56:0] granted; integer grant_count=0;',
          'active_id=granted[120:57];':'active_id=grant_count; grant_count=grant_count+1;',
          '$time,granted);':'$time,{active_id,granted});'}
        for src,dst in changes.items():
            assert tb.count(src)==1,src
            tb=tb.replace(src,dst)
        bench=build/'tb_lane.sv';bench.write_text(tb)
        for phase,stress in ((0,1),(1,1),(3,1),(0,0),(1,0),(3,0)):
            log=run([args.vivado,'-mode','batch','-nojournal','-nolog','-source',HERE/'xsim.tcl',
                     '-tclargs',phase,build/f'xsim-{phase}-{stress}',stress,bench],f'xsim-{phase}-{stress}',360)
            result=old.check_vendor_log(log)
            result.update(phase_ns=phase,stress=bool(stress))
            if not stress:
                assert result['max_accept_to_grant_ns_including_deliberate_out_of_contract_stall']<=160
                assert result['max_release_to_reply_ns']<=320+100
            results['vendor'].append(result)
    assert before=={p.name:old.sha(p) for p in sources},'sources changed during check'
    results.update(sources=before,build=str(build),shared_reference_sha256=old.sha(BASE/'reference.py'),
      shared_checker_sha256=old.sha(SPLIT/'check.py'),shared_vendor_bench_sha256=old.sha(SPLIT/'tb_lane.sv'))
    (HERE/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__': main()

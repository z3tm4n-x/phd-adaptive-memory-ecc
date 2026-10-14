"""Targeted vendor-XPM deadline runs. No ARM cycle model, no new STA."""
import argparse
import hashlib
import json
import os
import subprocess
import time
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check-published',action='store_true');args=ap.parse_args()
    if args.check_published:
        result=json.loads((HERE/'outputs/advance-rtl.json').read_text())
        with zipfile.ZipFile(HERE/'outputs/advance-evidence.zip') as z:
            for r in result['runs']:
                data=z.read(str(r['phase_ns'])+'/vivado.log')
                assert hashlib.sha256(data).hexdigest()==r['log_sha256']
                assert b'PASS ADVANCE' in data and b'Fatal:' not in data
        for p,h in result['source_sha256'].items():
            assert hashlib.sha256((HERE/p).read_bytes()).hexdigest()==h,p
        print('Published advance logs and all linked source hashes verified (no rerun).')
        return
    runs=[]
    for phase in (0,3,11):
        build=HERE/'.build'/('advance-'+str(phase));build.mkdir(parents=True,exist_ok=True)
        # Fresh project name leaves previous evidence recoverable; no delete.
        out=build/('xsim-'+str(time.time_ns()))
        cmd=[os.environ.get('VIVADO','/home/z3tm4n/bin/vivado-wsl'),'-mode','batch',
             '-nojournal','-nolog','-source',str(HERE/'advance_sim.tcl'),'-tclargs',str(out),str(phase)]
        before=time.monotonic()
        with (build/'vivado.log').open('w') as log:
            run=subprocess.run(cmd,cwd=build,stdout=log,stderr=subprocess.STDOUT,timeout=300)
        log=(build/'vivado.log').read_text()
        if run.returncode or 'PASS ADVANCE' not in log or 'Fatal:' in log:
            raise RuntimeError(log[-7000:])
        rows=[l for l in log.splitlines() if l.startswith(('ALLOW ','LOCAL_CONTROL ','PASS ADVANCE'))]
        runs.append({'phase_ns':phase,'elapsed_s':time.monotonic()-before,
                     'lines':rows,'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
        print(rows[-1],flush=True)
    files=['interval_link.sv','interval_guard.sv','tb_advance.sv','advance_sim.tcl',
           '../t104-rtl-resume/registered/handshake_channel.sv',
           '../t104-rtl-resume/physical/frame_engine.sv']
    result={'status':'PASS actual link/guard/calendar + vendor XPM, full-width time boundary tests',
            'runs':runs,'source_sha256':{p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in files},
            'limitations':['module-level idle-time jumps; not a mission trace',
                           'decision input tests separately composed with C/raw Oracle',
                           'no ARM/OCM/PS timing; not physical metastability proof'],
            'new_STA':False}
    (HERE/'outputs/advance-rtl.json').write_text(json.dumps(result,indent=2)+'\n')
    with zipfile.ZipFile(HERE/'outputs/advance-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
        for r in runs:
            p=HERE/'.build'/('advance-'+str(r['phase_ns']))/'vivado.log'
            entry=zipfile.ZipInfo(str(r['phase_ns'])+'/vivado.log',(2026,10,13,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED;z.writestr(entry,p.read_bytes())


if __name__=='__main__':main()

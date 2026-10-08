"""One read-only verification command, including pinned accepted controls.

Git objects for T127 are optional: the exact raw URL is a hash-checked fallback.
The optional master repository cache is external to the source checkout.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
MASTER='cf7ab706224f7872fdafcf34febda70e3f6c8dd1'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--master-repo',type=Path)
    ap.add_argument('--receipt',type=Path,help='optional execution receipt, never accepted scientific outputs')
    ap.add_argument('--skip-accepted',action='store_true',help='quick local development only, NOT complete reproduction')
    args=ap.parse_args();runs=[];start=time.perf_counter()
    def run(cmd):
        t=time.perf_counter();r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        entry=dict(command=cmd,seconds=time.perf_counter()-t,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
        runs.append(entry)
        print('Completed:', ' '.join(str(x) for x in cmd[-4:]),'exit',r.returncode,flush=True)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    py=[sys.executable,'-X','utf8','-B']
    if not args.skip_accepted:
        master=(args.master_repo or Path(os.environ.get('T126_MASTER_REPO',str(Path(tempfile.gettempdir())/'t126-master.git')))).resolve()
        if not master.exists():
            run(['git','init','--bare',str(master)])
        probe=subprocess.run(['git','-C',str(master),'cat-file','-e',MASTER+'^{commit}'],capture_output=True)
        if probe.returncode:
            run(['git','-C',str(master),'fetch','--depth','1','https://github.com/z3tm4n-x/chapter4-risk-limited-scrubber.git',MASTER])
        run(py+['experiments/t58-fixed-baseline-r0b/reproduce.py','--master-repo',str(master)])
        for path in ['t95-method-regime-map','t114-two-stage-err','t126-regime-map']:
            run(py+[f'experiments/{path}/verify.py'])
    run(py+['-m','unittest','discover','-s',str(HERE),'-p','test_*.py','-v'])
    run(py+[str(HERE/'engineering.py')])
    run(py+[str(HERE/'checker.py')])
    # Normal inherited ACL: Python 3.12 TemporaryDirectory's private Windows
    # ACL can deny the separately sandboxed compiler. Keep this small cache
    # outside Git; do not remove an existing user's cache on reproduction.
    cache=Path(tempfile.gettempdir())/'t126-compile-cache'
    cache.mkdir(exist_ok=True)
    run([sys.executable,'-X','utf8','-X','pycache_prefix='+str(cache),'-m','compileall','-q',str(HERE)])
    sources={}
    for path in sorted(HERE.glob('*.py')):
        sources[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'outputs').glob('*'))
             if p.name not in ['reproduction.json'] and p.is_file()}
    receipt=dict(task=126,complete_accepted_reproduction=not args.skip_accepted,
                 checkout_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                 python=sys.version,platform=platform.platform(),seconds=time.perf_counter()-start,
                 code_sha256=sources,output_sha256=outputs,runs=runs)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True,exist_ok=True)
        args.receipt.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(seconds=receipt['seconds'],complete=receipt['complete_accepted_reproduction'],commands=len(runs))))


if __name__=='__main__':main()

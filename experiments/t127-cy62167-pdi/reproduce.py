"""One-command bounded reproduction; raw files stay outside the checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--silso', type=Path)
    p.add_argument('--zenodo', type=Path)
    p.add_argument('--out',type=Path,default=HERE/'outputs')
    a=p.parse_args(); out=a.out.resolve(); out.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter(); runs=[]
    def run(args):
        r=subprocess.run([sys.executable,'-X','utf8','-B']+args,cwd=ROOT,text=True,encoding='utf-8',capture_output=True)
        runs.append(dict(args=args,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
        if r.returncode:
            (out/'checks.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
            raise RuntimeError(r.stderr)
    script=str(HERE/'calculate.py')
    optional=[]
    for key in ('silso','zenodo'):
        if getattr(a,key):optional+=['--'+key,str(getattr(a,key).resolve())]
    run([script,'--out',str(out)]+optional)
    run([str(HERE/'checker.py'),'--out',str(out)])
    run(['-m','unittest','discover','-s',str(HERE),'-v'])
    run(['-m','unittest','discover','-s','experiments/tNN-sepem-profiles','-v'])
    # compileall writes only pycache (ignored), never source files.
    run(['-m','compileall','-q',str(HERE)])
    # Keep the disposable repeat under the explicitly selected writable output
    # root; Windows short-name %TEMP% aliases may not inherit sandbox access.
    with tempfile.TemporaryDirectory(prefix='t127-check-',dir=out) as tmp:
        run([script,'--out',tmp]+optional)
        stable=['shield-conditional.csv','gost-proton-conditional.csv','service.json','population.json','inputs-126.json']
        for name in stable:
            if (out/name).read_bytes()!=(Path(tmp)/name).read_bytes():
                raise AssertionError('Non-reproducible output: '+name)
    result=dict(status='PASS_COMPUTATIONAL_ONLY',elapsed_seconds=time.perf_counter()-start,
                identical_second_run_files=stable,external_raw_rechecked=bool(a.zenodo),
                SILSO_monthly_reaggregation=bool(a.silso),runs=runs)
    (out/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    # Receipt deliberately excludes itself; avoids circular hashes/commit IDs.
    hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir()) if f.is_file() and f.name!='output_hashes.json'}
    (out/'output_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k!='runs'},indent=2))


if __name__=='__main__':main()

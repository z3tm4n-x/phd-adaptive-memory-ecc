"""One offline entry point; preserves accepted packages and raw files."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def run_package(args,out):
    profile=[sys.executable,str(HERE/'profiles.py'),'--raw',str(args.raw),'--cache',str(args.cache),'--out',str(out)]
    if args.reuse_cache:profile.append('--reuse-cache')
    subprocess.run(profile,check=True)
    for name in ('calculate.py','checker.py'):
        subprocess.run([sys.executable,str(HERE/name),'--out',str(out)],check=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--raw',type=Path,required=True)
    p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--out',type=Path,default=HERE/'outputs')
    p.add_argument('--reuse-cache',action='store_true')
    p.add_argument('--verify-again',action='store_true',help='repeat compact calculations in a new directory, using checked external cache')
    a=p.parse_args();run_package(a,a.out)
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_*.py','-v'],
                         capture_output=True,text=True,encoding='utf-8',errors='replace')
    if tests.returncode:
        print(tests.stdout+tests.stderr);raise SystemExit(tests.returncode)
    files={f.name:digest(f) for f in a.out.iterdir() if f.suffix in ('.json','.csv') and f.name!='validation.json'}
    same=None
    if a.verify_again:
        a.reuse_cache=True
        repeat_base=(HERE/'.cache').resolve()
        repeat_base.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='t141-repeat-',dir=repeat_base) as tmp:
            fresh=Path(tmp).resolve()
            if not fresh.is_relative_to(repeat_base):
                raise ValueError('Repeat directory escaped the verified workspace')
            run_package(a,fresh)
            new={f.name:digest(f) for f in fresh.iterdir() if f.suffix in ('.json','.csv')}
            same=files==new
            if not same:
                raise AssertionError('Nonreproducible outputs: '+str([k for k in files.keys()|new.keys() if files.get(k)!=new.get(k)]))
    record={'status':'PASS','tests_output':tests.stderr,'separate_process_output_hash_identity':same,
            'repeat_scope':'compact moments/statistics and independent fold; raw convolution reused only after hash verification',
            'output_sha256':files,
            'validation_code_sha256':{n:digest(HERE/n) for n in ('reproduce.py','checker.py','test_chain.py','test_profiles.py')},
            'independent_scientific_review':'not performed; numerical checker is not a review verdict'}
    (a.out/'validation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Tests PASS;',len(files),'artifacts;', 'repeated hashes identical' if same else 'single verified run')


if __name__=='__main__':main()

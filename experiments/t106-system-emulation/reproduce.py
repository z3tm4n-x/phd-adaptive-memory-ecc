"""One entry point: portable trace check, optionally repeat actual ISA/RTL."""
import argparse,hashlib,json,os,py_compile,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ARM=HERE.parent/'t105-arm-rule'
def bootstrap():
    manifest=json.loads((ARM/'outputs/analysis-tools.json').read_text())
    wheels=HERE/'.tools/wheels';wheels.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,'-m','pip','download','--no-deps','--dest',str(wheels),*manifest['packages']],check=True)
    files=[]
    for name,digest in manifest['wheels'].items():
        p=wheels/name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,('wheel changed',name)
        files.append(str(p))
    subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-index',
        '--target',str(HERE/'.tools/analysis'),*files],check=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--bootstrap',action='store_true')
    ap.add_argument('--execute-empty',action='store_true',help='Repeat literal RTL calendar and actual accepted ELF empty-transition checks')
    ap.add_argument('--execute-accel',action='store_true',help='Repeat full-top/ELF long clean cases and two acceleration witnesses')
    args=ap.parse_args()
    for p in HERE.glob('*.py'):py_compile.compile(str(p),doraise=True)
    subprocess.run([sys.executable,str(HERE/'provenance.py')],check=True)
    subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_*.py'],check=True)
    if args.bootstrap:bootstrap()
    if args.execute:subprocess.run([sys.executable,str(HERE/'run.py')],check=True)
    else:
        # Validate the pinned archive before independently replaying it.
        pinned=json.loads((HERE/'outputs/summary.json').read_text())['outputs_sha256']
        for name,digest in pinned.items():
            assert hashlib.sha256((HERE/'outputs'/name).read_bytes()).hexdigest()==digest,name
    subprocess.run([sys.executable,str(HERE/'check.py')],check=True)
    subprocess.run([sys.executable,str(HERE/'mutations.py')],check=True)
    if args.execute_empty:
        subprocess.run([sys.executable,str(HERE/'verify_empty_calendar.py'),'--execute'],check=True)
        subprocess.run([sys.executable,str(HERE/'verify_empty_rule.py'),'--execute-elf'],check=True)
    subprocess.run([sys.executable,str(HERE/'check_empty.py')],check=True)
    subprocess.run([sys.executable,str(HERE/'verify_accel.py')]+(['--execute'] if args.execute_accel else []),check=True)
    subprocess.run([sys.executable,str(HERE/'summary.py')],check=True)
    print('T106 scenarios1/3/4 + empty-transition components checked; scenarios2/5 NOT claimed complete')
if __name__=='__main__':main()

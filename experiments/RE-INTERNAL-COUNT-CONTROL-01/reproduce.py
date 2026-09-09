"""Rebuild deterministic checks and, optionally, the held-out experiment."""
from __future__ import annotations
import argparse,hashlib,json,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def manifest():
    import numpy,scipy,numba,mpmath
    files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(ROOT.rglob('*')) if p.is_file() and
           p.suffix in ['.py','.json','.csv','.md','.txt'] and
           'cache' not in p.parts and '__pycache__' not in p.parts and p.name!='manifest.json'}
    head=None
    try:head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,stderr=subprocess.DEVNULL,text=True).strip()
    except (FileNotFoundError,subprocess.CalledProcessError):pass
    data=dict(task='RE-INTERNAL-COUNT-CONTROL-01',base='a44355e38a5434fa69d7c343e456ddd944315d46',
              executing_repository_head=head,environment=dict(python=sys.version,numpy=numpy.__version__,scipy=scipy.__version__,numba=numba.__version__,mpmath=mpmath.__version__,platform=platform.platform()),
              note='Engineering execution record, not a Scientific Review or RES disposition.',sha256=files)
    (ROOT/'outputs'/'manifest.json').write_text(json.dumps(data,indent=2))
    return data

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');parser.add_argument('--retune',action='store_true');parser.add_argument('--manifest-only',action='store_true');args=parser.parse_args()
    if not args.manifest_only:
        import feasibility,core,exact_oracle,tests
        feasibility.run();core.main();exact_oracle.run();tests.run()
        if args.retune:
            import tune;tune.run()
        if args.full:
            import validate;validate.run()
    manifest()
if __name__=='__main__':main()

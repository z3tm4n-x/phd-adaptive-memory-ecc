"""Pinned, local-only ISA analysis dependencies; no system installation."""
import hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PACKAGES=('unicorn==2.1.4','capstone==5.0.6','pyelftools==0.33')

def activate():
    sys.path.insert(0,str(HERE/'.tools/analysis'))

def main():
    wheels=HERE/'.tools/wheels';wheels.mkdir(parents=True,exist_ok=True)
    manifest=HERE/'outputs/analysis-tools.json'
    if manifest.exists():
        data=json.loads(manifest.read_text())
    else:
        subprocess.run([sys.executable,'-m','pip','download','--no-deps','--dest',str(wheels),*PACKAGES],check=True)
        data={'purpose':'ISA execution, NOT cycle-accurate Cortex-A9','packages':list(PACKAGES),
          'wheels':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(wheels.glob('*.whl'))}}
    for name,digest in data['wheels'].items():
        p=wheels/name
        if not p.exists():
            subprocess.run([sys.executable,'-m','pip','download','--no-deps','--dest',str(wheels),*PACKAGES],check=True)
        if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise RuntimeError('wheel changed: '+name)
    subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-index',
        '--target',str(HERE/'.tools/analysis'),*[str(wheels/n) for n in data['wheels']]],check=True)
    manifest.write_text(json.dumps(data,indent=2)+'\n')
    activate()
    import unicorn,capstone,elftools
    print(unicorn.__version__,capstone.__version__,elftools.__version__)
if __name__=='__main__':main()

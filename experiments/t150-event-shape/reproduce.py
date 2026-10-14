"""Offline reproduction and a separately written scalar audit of saved moments."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE='a69fe3df97eac5a509f65446395891e71a8e9553'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def pin_sources():
    # No source is silently replaced by a fresh checksum. Match tracked Git
    # content against the accepted base before using any T141 derivative.
    paths=['experiments',':(exclude)experiments/t150-event-shape']
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--','experiments'],cwd=ROOT,text=True).splitlines()
    names=[n for n in names if not n.startswith('experiments/t150-event-shape/')]
    # git diff compares the current tracked index/worktree to the declared base.
    dirty=subprocess.check_output(['git','diff',BASE,'--name-only','--',*paths],cwd=ROOT,text=True)
    if dirty:raise ValueError('Accepted dependency changed: '+dirty)
    return len(names)


def run(a,out):
    subprocess.run([sys.executable,'-B',str(HERE/'radiation.py'),'--raw',str(a.raw),
        '--cache',str(a.cache),'--out',str(out)],check=True)
    subprocess.run([sys.executable,'-B',str(HERE/'controller.py'),'--out',str(out)],check=True)


def scalar_audit(cache,out):
    # Does not import T141/T150 calculation functions. Reconstruct a small real
    # event from the checked two-band cache with scalar fsum and the saved floor.
    x=np.load(cache/'bands.npy',mmap_mode='r')
    p=ROOT/'experiments/t141-radiation-chain/outputs'
    bg=list(csv.DictReader((p/'profile-background.csv').open(encoding='utf-8')))
    ev=list(csv.DictReader((out/'event-shapes.csv').open(encoding='utf-8')))
    checks=[]
    for i,rho in enumerate((2.5,3.,3.5,4.)):
        b=next(r for r in bg if float(r['shield_g_cm2'])==rho)
        floor=float(b['floor_s_inv']);ion=float(b['HI_to_H_assumed'])
        for case in ('full','no_low'):
            row=next(r for r in ev if float(r['shield_g_cm2'])==rho and r['response_case']==case and r['event']=='131')
            yy=[]
            for low,high in x[int(row['start_index']):int(row['stop_index']),i]:
                factor=max(0.,float(low+high)-floor)/float(low+high)
                L=float(low)*factor;H=float(high)*factor
                yy.append((L if case=='full' else 0.)+H+ion*(L+H))
            N=300*math.fsum(yy);S=300*math.fsum(v*v for v in yy)
            relative=abs(S-float(row['solar_S2_s_inv']))/S
            assert relative<2e-12 and math.isclose(N,float(row['solar_N']),rel_tol=2e-12)
            checks.append(dict(rho=rho,case=case,event=131,bins=len(yy),relative_S2_difference=relative))
    dec=list(csv.DictReader((out/'square-decomposition.csv').open(encoding='utf-8')))
    for r in dec:
        terms=('background_S2','mixed_S2','H_low_S2','H_high_S2','LET_S2',
               'twice_low_high','twice_low_LET','twice_high_LET')
        assert math.isclose(math.fsum(float(r[k]) for k in terms),float(r['S2']),rel_tol=2e-13)
    return checks


def main():
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True)
    p.add_argument('--cache',type=Path,required=True);p.add_argument('--out',type=Path,default=HERE/'outputs')
    p.add_argument('--verify-again',action='store_true');a=p.parse_args()
    pinned=pin_sources();run(a,a.out)
    tests=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(HERE),'-p','test_*.py','-v'],
        capture_output=True,text=True,encoding='utf-8',errors='replace')
    if tests.returncode:print(tests.stdout+tests.stderr);raise SystemExit(tests.returncode)
    independent=scalar_audit(a.cache,a.out)
    files={f.name:sha(f) for f in a.out.iterdir() if f.suffix in ('.json','.csv') and f.name!='validation.json'}
    same=None
    if a.verify_again:
        parent=(HERE/'.cache').resolve();parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='repeat-',dir=parent) as tmp:
            fresh=Path(tmp).resolve()
            if not fresh.is_relative_to(parent):raise ValueError('repeat path escaped workspace')
            run(a,fresh)
            same=files=={f.name:sha(f) for f in fresh.iterdir()}
            assert same,'separate-process outputs differ'
    report=dict(status='PASS',pinned_tracked_dependencies=pinned,tests_output=tests.stderr,
        separate_process_hash_identity=same,scalar_real_event_checks=independent,
        outputs_sha256=files,code_sha256={f.name:sha(f) for f in HERE.glob('*.py')},
        scope='calculation checks; no independent scientific review of T150 performed')
    (a.out/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'T150 PASS: {len(files)} outputs; repeated hashes identical={same}; eight scalar real-event checks')


if __name__=='__main__':main()

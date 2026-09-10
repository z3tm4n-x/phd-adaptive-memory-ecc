"""Reproduce certificates/tests, optionally pilot and full held-out experiment."""
from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def call(*args):subprocess.run([sys.executable,*args],cwd=ROOT,check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--full',action='store_true');p.add_argument('--retune',action='store_true');p.add_argument('--workers',type=int,default=4);a=p.parse_args()
    call('model.py');call('numeric_witness.py');call('feasibility.py');call('tests.py');call('diagnostics.py')
    if a.retune or (a.full and not (ROOT/'outputs'/'selected_analogue.json').exists()):
        call('experiment.py','pilot','--workers',str(a.workers))
    if a.full:call('experiment.py','full','--workers',str(a.workers))

if __name__=='__main__':main()

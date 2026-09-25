"""Run addressed regression/oracle checks, provenance, optional report capture.

Does not rerun or modify historical run_checks.py / checks.json.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy
import scipy
from audit import calculations

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent
REPO = PKG.parents[1]
BASE = '44b3d5992d7473fa6026de7b5eda26613e0623f8'
CANONICAL = [
    'docs/agents/00_GLOBAL_OPERATING_RULES.md',
    'docs/agents/07_RESEARCH_ENGINEER_LOCAL.md',
    'docs/agents/HANDOFF_CONTRACTS.md', 'README.md',
    'docs/current_status.md', 'docs/research_spec.md',
    'docs/decisions/DEC-004-dissertation-architecture-A.md',
    'docs/dissertation_concept.md', 'results/RES-003-internal-count-control.md',
    'docs/publication_plans/RES-003-PUBLICATION-HANDOFF.md',
    'docs/scientific_reviews/INTERNAL_COUNT_CONTROL_REVIEW_01.md',
    'experiments/RE-INTERNAL-COUNT-CONTROL-01/derivation.md',
    'experiments/RE-INTERNAL-COUNT-CONTROL-01/core.py',
    'experiments/RE-INTERNAL-COUNT-CONTROL-01/simulate.py',
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git(*args):
    return subprocess.check_output(['git','-c','core.longpaths=true',*args],cwd=REPO)


def preserved(path):
    old=git('show',BASE+':'+path)
    now=(REPO/path).read_bytes()
    base_blob=git('rev-parse',BASE+':'+path).decode().strip()
    head_blob=git('rev-parse','HEAD:'+path).decode().strip()
    return dict(path=path, base=BASE, base_sha256=sha(old), local_sha256=sha(now),
                byte_identical=old==now, git_blob=base_blob, head_git_blob=head_blob,
                canonical_blob_unchanged=base_blob==head_blob,
                equal_after_crlf_to_lf=old.replace(b'\r\n',b'\n')==now.replace(b'\r\n',b'\n'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--record',type=Path)
    parser.add_argument('--source-dir',type=Path)
    args=parser.parse_args()
    started=time.perf_counter()
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
    commands=[]
    for directory in (PKG,ROOT):
        for tail in (['-m','unittest','discover','-s',str(directory),'-p','test_*.py','-v'],
                     ['-m','compileall','-q','-b',str(directory)]):
            result=subprocess.run([sys.executable,*tail],env=env,capture_output=True,text=True,encoding='utf-8')
            commands.append(dict(argv=[sys.executable,*tail],exit_code=result.returncode,
                                 stdout=result.stdout,stderr=result.stderr))
    # Exact deterministic output identity in the pinned numerical environment.
    stored=json.loads((ROOT/'diagnostics.json').read_text(encoding='utf-8'))
    exact_reproduction=stored==calculations()
    prior_names=git('ls-tree','-r','--name-only',BASE,'--',PKG.relative_to(REPO).as_posix()).decode().splitlines()
    prior=[preserved(p) for p in prior_names]
    canonical=[preserved(p) for p in CANONICAL]
    unrelated=[]
    for p in git('diff',BASE,'--name-only').decode().splitlines():
        if not p.startswith(PKG.relative_to(REPO).as_posix()+'/continuation-01/'):
            unrelated.append(preserved(p))
    sources=[]
    if args.source_dir:
        for s in json.loads((ROOT/'sources.json').read_text(encoding='utf-8'))['sources']:
            if s['file'] and s['sha256']:
                f=args.source_dir/s['file']
                actual=sha(f.read_bytes())
                sources.append(dict(id=s['id'],file=str(f),sha256=actual,
                                    matched=actual==s['sha256'],pdf_header=f.read_bytes()[:5]==b'%PDF-'))
    result=dict(status='ADDRESSED_CHECKS_ONLY_NOT_COMPLETED_ENGINEERING_EXAMPLE',
        code_base=BASE,execution_head=git('rev-parse','HEAD').decode().strip(),
        base_is_ancestor=subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=REPO).returncode==0,
        python=platform.python_version(),numpy=numpy.__version__,scipy=scipy.__version__,
        platform=platform.platform(),commands=commands,
        deterministic_diagnostics_reproduced_exactly=exact_reproduction,
        prior_package=prior,canonical_sources=canonical,preexisting_status_entries=unrelated,
        downloaded_sources=sources,
        input_code_output_hashes={p.name:sha(p.read_bytes()) for p in sorted(ROOT.iterdir())
            if p.name in ['config.json','source_rows.json','sources.json','audit.py','independent_check.py','test_input.py','verify.py','diagnostics.json']},
        elapsed_s=time.perf_counter()-started,policy_trials=0)
    ok=(all(c['exit_code']==0 for c in commands) and exact_reproduction and result['base_is_ancestor']
        and all(p['canonical_blob_unchanged'] and p['equal_after_crlf_to_lf'] for p in prior+canonical)
        and all(p['byte_identical'] for p in unrelated)
        and all(p['matched'] and p['pdf_header'] for p in sources))
    result['addressed_checks_succeeded']=ok
    text=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if args.record:
        args.record.write_text(text,encoding='utf-8',newline='\n')
    print(json.dumps({k:result[k] for k in ['addressed_checks_succeeded','python','numpy','scipy','elapsed_s','policy_trials']}))
    if not ok:
        print(text)
        raise SystemExit(1)


if __name__=='__main__':
    main()

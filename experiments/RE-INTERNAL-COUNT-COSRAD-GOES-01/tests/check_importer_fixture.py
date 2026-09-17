#!/usr/bin/env python3
"""Offline fixture checks. BASE is replaced only in memory for a temporary repo.

No real GitHub checkout, credentials or push is used. Published source constants
are not modified. This tests guards, not an actual publication.
"""
from __future__ import annotations
from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import import_into_checkout as importer


def run() -> dict:
    checks = {}
    old_base = importer.BASE
    with tempfile.TemporaryDirectory(prefix='cosrad-import-fixture-') as folder:
        repo = Path(folder)
        def git(*args: str) -> str:
            return subprocess.run(['git','-C',str(repo),*args], check=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()
        git('init','-b','fixture-main')
        git('config','user.name','Package fixture test')
        git('config','user.email','fixture@example.invalid')
        git('remote','add','origin','https://github.com/'+importer.REPOSITORY+'.git')
        (repo/'README.md').write_text('offline fixture, not the research repository\n')
        git('add','README.md');git('commit','-m','fixture base')
        importer.BASE=git('rev-parse','HEAD')
        fixture_base=importer.BASE
        output=io.StringIO()
        def invoke(*args):
            with redirect_stdout(output), redirect_stderr(output):
                return importer.main([str(repo),*args])
        try:
            assert invoke()==0
            assert git('rev-parse','HEAD')==fixture_base
            assert git('symbolic-ref','--short','HEAD')=='fixture-main'
            assert not (repo/importer.PREFIX).exists()
            checks['dry_run_no_mutation']=True
            (repo/'dirty.tmp').write_text('sentinel')
            assert invoke()==2
            (repo/'dirty.tmp').unlink()
            checks['dirty_tree_rejected']=True
            assert invoke('--apply','--commit')==0
            assert git('rev-parse','HEAD^')==fixture_base
            assert git('symbolic-ref','--short','HEAD')==importer.BRANCH
            assert all(p.startswith(importer.PREFIX) for p in git('diff','--name-only',fixture_base,'HEAD').splitlines())
            assert git('rev-parse','fixture-main')==fixture_base
            checks['apply_commit_changes_task_only_keeps_original_branch']=True
            head=git('rev-parse','HEAD')
            assert invoke('--apply','--commit')==0 and git('rev-parse','HEAD')==head
            checks['identical_reimport_idempotent']=True
            target=repo/importer.PREFIX/'README.md'
            target.write_text('conflicting previous work\n')
            git('add',importer.PREFIX+'README.md');git('commit','-m','fixture conflict')
            assert invoke()==2
            checks['nonidentical_existing_file_rejected']=True
            (repo/'outside.txt').write_text('outside task\n')
            git('add','outside.txt');git('commit','-m','fixture outside')
            assert invoke()==2
            checks['outside_task_branch_change_rejected']=True
            return {'checks':checks,'passed':len(checks),
                    'real_base_or_repository_used':False,'network_used':False,
                    'push_executed':False,'source_BASE_modified':False,
                    'scope':'offline branch/copy/commit guards only; not GitHub publication'}
        finally:
            importer.BASE=old_base


if __name__=='__main__':
    print(json.dumps(run(),ensure_ascii=False,indent=2))

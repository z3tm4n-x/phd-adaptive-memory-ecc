#!/usr/bin/env python3
"""Safely import Package A into an existing authorized checkout; dry-run by default.

Example (from the extracted task directory):
 python -B src/import_into_checkout.py /path/to/repository
 python -B src/import_into_checkout.py /path/to/repository --apply --commit --push

No clone, reset, force-push, merge, main modification or PR action is performed.
Do not run concurrently with another process changing the checkout.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
from verify_package import ROOT, verify

BASE = '0715fd8e17b59a71d731110c53b87b900f8fa304'
BRANCH = 'research/internal-count-cosrad-goes-01'
PREFIX = 'experiments/RE-INTERNAL-COUNT-COSRAD-GOES-01/'
REPOSITORY = 'z3tm4n-x/phd-adaptive-memory-ecc'


def git(checkout: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(['git', '-C', str(checkout), *args],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace').strip()
                           or f'git {args[0]} failed ({result.returncode})')
    return result


def text(checkout: Path, *args: str) -> str:
    return git(checkout, *args).stdout.decode('utf-8').strip()


def clean(checkout: Path) -> None:
    if git(checkout, 'status', '--porcelain=v1', '--untracked-files=all').stdout:
        raise RuntimeError('Checkout is not clean; no changes were discarded')


def prepare(checkout: Path) -> tuple[list[str], bool, str]:
    files = verify(ROOT)
    top = Path(text(checkout, 'rev-parse', '--show-toplevel')).resolve()
    if top != checkout.resolve():
        raise RuntimeError('Pass the checkout root, not a nested directory')
    remote = text(checkout, 'remote', 'get-url', 'origin')
    pattern = rf'(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/){re.escape(REPOSITORY)}(?:\.git)?/?'
    if re.fullmatch(pattern, remote) is None:
        raise RuntimeError('origin does not identify the required GitHub repository')
    clean(checkout)
    if text(checkout, 'cat-file', '-t', BASE) != 'commit':
        raise RuntimeError('Exact base is not a locally available commit')
    exists = git(checkout, 'show-ref', '--verify', '--quiet',
                 f'refs/heads/{BRANCH}', check=False).returncode == 0
    target = BRANCH if exists else BASE
    if git(checkout, 'merge-base', '--is-ancestor', BASE, target, check=False).returncode:
        raise RuntimeError('Existing target branch is not descended from the exact base')
    changed = git(checkout, 'diff', '--name-only', '-z', BASE, target).stdout.split(b'\0')
    if any(name and not name.decode('utf-8').startswith(PREFIX) for name in changed):
        raise RuntimeError('Target branch contains changes outside the authorized task directory')
    for name in files:
        path = PREFIX + name
        existing = git(checkout, 'cat-file', 'blob', f'{target}:{path}', check=False)
        if existing.returncode == 0 and existing.stdout != (ROOT/name).read_bytes():
            raise RuntimeError(f'Nonidentical existing target file; refusing overwrite: {path}')
    return files, exists, target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    parser.add_argument('--apply', action='store_true', help='switch/create only the target branch and copy files')
    parser.add_argument('--commit', action='store_true', help='requires --apply; create a local commit')
    parser.add_argument('--push', action='store_true', help='requires --apply --commit; normal target-only push')
    args = parser.parse_args(argv)
    if args.commit and not args.apply or args.push and not (args.apply and args.commit):
        parser.error('--commit requires --apply; --push requires both --apply and --commit')
    checkout = args.checkout.expanduser().resolve()
    try:
        files, exists, target = prepare(checkout)
        print(f'Base: {BASE}\nBranch: {BRANCH}\nFiles: {len(files)}')
        if not args.apply:
            print('DRY_RUN_OK: no branch, file, commit or remote change was made')
            return 0
        clean(checkout)
        if exists:
            git(checkout, 'switch', BRANCH)
        else:
            git(checkout, 'switch', '-c', BRANCH, BASE)
        if text(checkout, 'symbolic-ref', '--short', 'HEAD') != BRANCH:
            raise RuntimeError('Refusing to copy onto another branch')
        for name in files:
            destination = checkout / PREFIX / name
            resolved = destination.resolve()
            if not resolved.is_relative_to((checkout/PREFIX).resolve()):
                raise RuntimeError(f'Escaping destination: {destination}')
            if destination.exists():
                if destination.is_symlink() or destination.read_bytes() != (ROOT/name).read_bytes():
                    raise RuntimeError(f'Unexpected working-tree collision: {destination}')
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/name, destination)
        if args.commit:
            outside = []
            tracked = git(checkout, 'diff', '--name-only', '-z', 'HEAD').stdout
            untracked = git(checkout, 'ls-files', '--others', '--exclude-standard', '-z').stdout
            for value in (tracked+untracked).split(b'\0'):
                if value and not value.decode('utf-8').startswith(PREFIX):
                    outside.append(value.decode('utf-8'))
            if outside:
                raise RuntimeError('Concurrent changes outside task: ' + ', '.join(outside))
            git(checkout, 'add', '--', PREFIX)
            pending = git(checkout, 'diff', '--cached', '--quiet', check=False).returncode
            if pending == 1:
                git(checkout, 'commit', '-m', 'exp: prepare RE-INTERNAL-COUNT-COSRAD-GOES-01 delivery A')
            elif pending != 0:
                raise RuntimeError('Cannot inspect staged changes')
            print('Local commit: ' + text(checkout, 'rev-parse', 'HEAD'))
        if args.push:
            if text(checkout, 'symbolic-ref', '--short', 'HEAD') != BRANCH:
                raise RuntimeError('Branch changed before push')
            result = git(checkout, 'push', 'origin', f'HEAD:refs/heads/{BRANCH}')
            print(result.stderr.decode(errors='replace').strip())
            print('Target branch published by a normal non-force push')
        elif args.commit:
            print('No push was requested')
        else:
            print('Copied without commit or push')
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        print(f'IMPORT STOPPED: {exc}', file=sys.stderr)
        print('No reset/rollback/force operation was attempted. Inspect the checkout before retrying.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

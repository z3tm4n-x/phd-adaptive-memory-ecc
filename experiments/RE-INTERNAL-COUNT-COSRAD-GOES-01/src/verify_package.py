#!/usr/bin/env python3
"""Verify the frozen delivery files, without network access or file mutation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'provenance/package_manifest.json'


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify(root: Path = ROOT) -> list[str]:
    root = root.resolve(strict=True)
    document = json.loads((root / MANIFEST).read_text(encoding='utf-8'))
    if document.get('schema_version') != 1:
        raise ValueError('Unsupported package-manifest schema')
    expected: set[str] = set()
    for record in document['files']:
        name = record['path']
        rel = PurePosixPath(name)
        if (rel.is_absolute() or '..' in rel.parts or '\\' in name
                or name != rel.as_posix() or name == MANIFEST or name in expected):
            raise ValueError(f'Unsafe or duplicated manifest path: {name}')
        expected.add(name)
        path = root.joinpath(*rel.parts)
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f'Missing, symlinked or escaping file: {name}')
        if path.stat().st_size != record['bytes'] or digest(path) != record['sha256']:
            raise ValueError(f'Integrity mismatch: {name}')
    actual: set[str] = set()
    for p in root.rglob('*'):
        if p.is_symlink():
            raise ValueError(f'Symlink in delivery: {p.relative_to(root)}')
        if p.is_file() and '__pycache__' not in p.parts:
            actual.add(p.relative_to(root).as_posix())
    extras = actual - expected - {MANIFEST}
    if extras:
        raise ValueError('Unmanifested files: ' + ', '.join(sorted(extras)))
    return sorted(expected | {MANIFEST})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        files = verify(args.root)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'VERIFICATION FAILED: {exc}', file=sys.stderr)
        return 2
    print(json.dumps({'verified_files': len(files)-1,
                      'manifest_self_hashed': False,
                      'status': 'INTEGRITY_OK_NOT_SCIENTIFIC_REVIEW'}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

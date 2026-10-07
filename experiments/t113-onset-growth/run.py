"""One command: pinned cache, directed tests, complete T113 tables, comparison."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np

from pipeline import HERE, T67, T72, analyze, serialize, sha, verify_inputs


def verified_cache(cache):
    """Use T72's parser/ledger; rebuilding is only needed when cache is absent.

    Verify all raw hashes even if a derived series exists. Accepted sources are
    never refreshed or edited. An unavailable or changed source is an error,
    with the existing table retained; it is not replaced by a zero trajectory.
    """
    sys.path.insert(0, str(T72))
    from prepare import prepare
    return prepare(cache)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache', type=Path, default=Path(os.environ.get('T113_CACHE', str(Path(tempfile.gettempdir()) / 't113-cache'))))
    p.add_argument('--write', action='store_true', help='Explicitly regenerate only T113 outputs')
    p.add_argument('--tests-only', action='store_true')
    args = p.parse_args()
    config = json.loads((HERE / 'config.json').read_text())
    verify_inputs(config)
    tests = unittest.defaultTestLoader.discover(str(HERE), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=1).run(tests)
    if not result.wasSuccessful():
        raise SystemExit(1)
    if args.tests_only:
        return
    manifest, series = verified_cache(args.cache)
    outputs = analyze(config, manifest, series)
    payloads = {name: serialize(name, value) for name, value in outputs.items()}
    reproduction = {
        'issue': 113, 'directed_tests': result.testsRun, 'all_passed': True,
        'source_sha256': config['source_sha256'],
        'source_series': {p.name: json.loads(p.read_text()) for p in sorted(series.glob('*.json'))},
        'output_sha256': {name: hashlib.sha256(value).hexdigest() for name, value in payloads.items()},
        'audit': outputs['handoff.json']['audit'],
        'config_sha256': sha(HERE / 'config.json'),
        'calculation_code_sha256': {name: sha(HERE / name) for name in ['onset_growth.py', 'pipeline.py', 'run.py', 'test_growth.py']},
        'python_requirement': '>=3.10', 'numpy_version': np.__version__,
    }
    payloads['reproduction.json'] = serialize('reproduction.json', reproduction)
    out = HERE / 'outputs'
    if args.write:
        out.mkdir(exist_ok=True)
        for name, value in payloads.items():
            (out / name).write_bytes(value)
        print('Wrote only T113 outputs', flush=True)
    else:
        mismatch = [name for name, value in payloads.items() if not (out / name).exists() or (out / name).read_bytes() != value]
        if mismatch:
            raise SystemExit('Reproduction differs (no files written): ' + ', '.join(mismatch))
        print('All T113 outputs byte-identical; no accepted/output file changed', flush=True)
    print(json.dumps({'tests': result.testsRun, 'windows': len(manifest['events']),
                      'raw_files': len(manifest['files']), **outputs['handoff.json']['audit']}, indent=2))


if __name__ == '__main__':
    main()

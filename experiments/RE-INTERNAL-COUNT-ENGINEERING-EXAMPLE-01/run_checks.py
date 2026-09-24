"""Reproduce addressed checks and provenance without any experiment or network."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
import unittest
from prerequisite_checks import exhaustive_results

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
BASE = '7b83f643efb37541547d7d93a65ba2f43acd43fd'
SOURCES = [
    'docs/agents/00_GLOBAL_OPERATING_RULES.md',
    'docs/agents/07_RESEARCH_ENGINEER_LOCAL.md',
    'docs/agents/HANDOFF_CONTRACTS.md',
    'README.md', 'docs/current_status.md', 'docs/research_spec.md',
    'docs/decisions/DEC-004-dissertation-architecture-A.md',
    'docs/dissertation_concept.md',
    'results/RES-003-internal-count-control.md',
    'docs/publication_plans/RES-003-PUBLICATION-HANDOFF.md',
    'docs/scientific_reviews/INTERNAL_COUNT_CONTROL_REVIEW_01.md',
    'experiments/RE-INTERNAL-COUNT-CONTROL-01/derivation.md',
    'experiments/RE-INTERNAL-COUNT-CONTROL-01/config.json',
    'experiments/RE-INTERNAL-COUNT-CONTROL-01/core.py',
    'experiments/RE-INTERNAL-COUNT-CONTROL-01/simulate.py',
]


def git(*args):
    return subprocess.check_output(['git', '-c', 'core.longpaths=true', *args], cwd=REPO)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.discover(str(ROOT), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    source_rows = []
    for path in SOURCES:
        canonical = git('show', BASE + ':' + path)
        local = (REPO / path).read_bytes()
        source_rows.append(dict(path=path, commit=BASE,
            git_blob=git('rev-parse', BASE + ':' + path).decode().strip(),
            canonical_sha256=sha(canonical), worktree_sha256=sha(local),
            canonical_bytes_equal=local == canonical,
            equal_after_crlf_to_lf=local.replace(b'\r\n', b'\n') == canonical.replace(b'\r\n', b'\n')))
    # Check every pre-existing file marked modified; never stage or rewrite it.
    modified = git('diff', '--name-only').decode().splitlines()
    prior = []
    own_prefix = ROOT.relative_to(REPO).as_posix() + '/'
    for path in modified:
        if path.startswith(own_prefix):
            continue
        canonical = git('show', BASE + ':' + path)
        local = (REPO / path).read_bytes()
        prior.append(dict(path=path, base_sha256=sha(canonical),
                          worktree_sha256=sha(local), byte_identical=canonical == local))
    payload = dict(task_id='RE-INTERNAL-COUNT-ENGINEERING-EXAMPLE-01',
        status='PREREQUISITE_CHECKS_ONLY_NOT_ENGINEERING_VALIDATION',
        python=platform.python_version(), platform=platform.platform(),
        tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        exhaustive=exhaustive_results(),
        complete_trace_comparisons=39 * 39 * 4,
        mutation_data_only_counter_rejected_positions=[1, 2, 4, 8, 16, 32, 39],
        elapsed_seconds=time.perf_counter()-start,
        sources=source_rows, preexisting_status_entries=prior,
        production_trials=0,
        script_hashes={p.name: sha(p.read_bytes()) for p in sorted(ROOT.glob('*.py'))})
    (ROOT / 'checks.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    if not result.wasSuccessful() or not all(x['equal_after_crlf_to_lf'] for x in source_rows):
        raise SystemExit(1)
    if not all(x['byte_identical'] for x in prior):
        raise SystemExit('Unrelated modified bytes require investigation; nothing overwritten.')


if __name__ == '__main__':
    main()

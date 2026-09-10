#!/usr/bin/env python3
"""Read-only delivery audit: hashes and saved NPZ summaries; no model execution.

Usage:
    python verify_unknown_d_delivery.py PATH_TO_ZIP_OR_EXTRACTED_ROOT --out AUDIT_DIR

Requires NumPy and SciPy for independent arithmetic of saved statistics. Does not
import any experiment module, generate random streams, rerun pilot selection, or
rewrite any source/record/table in the delivered experiment. Output must be
outside the experiment directory. The new manifest is dated at audit time and
is NOT a reconstructed historical execution manifest.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import zipfile

import numpy as np
from scipy.stats import beta as beta_distribution

ROOT_NAME = 'RE-INTERNAL-COUNT-UNKNOWN-D-01'
POLICIES = ['learning', 'frozen_uncertainty', 'Fixed', 'Precomputed',
            'PA_DOM_one_setting', 'known_D_RES003_diagnostic']


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_payload(path: Path):
    if path.is_file():
        content = path.read_bytes()
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            members = [m for m in archive.infolist() if not m.is_dir()]
            names = [m.filename for m in members]
            if len(names) != len(set(names)):
                raise ValueError('Duplicate ZIP members')
            payload = {}
            for name in names:
                p = PurePosixPath(name)
                if p.is_absolute() or '..' in p.parts or p.parts[0] != ROOT_NAME:
                    raise ValueError('Unexpected ZIP path: ' + name)
                payload[str(PurePosixPath(*p.parts[1:]))] = archive.read(name)
        return payload, {'name': path.name, 'size_bytes': len(content), 'sha256': digest(content)}
    if not path.is_dir():
        raise FileNotFoundError(path)
    payload = {}
    for p in sorted(path.rglob('*')):
        if p.is_symlink():
            raise ValueError('Symlink in audit source: ' + str(p))
        if p.is_file():
            payload[p.relative_to(path).as_posix()] = p.read_bytes()
    return payload, None


def audit(source: Path, out: Path):
    if source.is_dir() and (out == source or source in out.parents):
        raise ValueError('Output must be outside the audited experiment directory')
    payload, archive_id = load_payload(source)
    read_json = lambda name: json.loads(payload[name])
    read_csv = lambda name: list(csv.DictReader(io.StringIO(payload[name].decode('utf-8'))))
    timestamp = datetime.now(timezone.utc).isoformat()
    lock = read_json('outputs/validation_lock.json')
    execution = read_json('outputs/execution_record.json')
    pre = read_json('outputs/preexecution_source_lock.json')
    selected = read_json('outputs/selected_analogue.json')
    cfg = read_json('config.json')
    source_hashes = lock['source_sha256']
    errors = []
    for label, recorded in [('execution_record', execution['source_sha256']),
                            ('preexecution_source_lock', pre['sha256']),
                            ('selected_analogue', selected['source_sha256'])]:
        if recorded != source_hashes:
            errors.append(label + ': source hash dictionaries differ')
    for name, expected in source_hashes.items():
        if name not in payload or digest(payload[name]) != expected:
            errors.append('Source mismatch: ' + name)
    if digest(payload['outputs/selected_analogue.json']) != lock['pilot_selection_sha256']:
        errors.append('Pilot selection SHA-256 mismatch')
    root_sources = {n for n in payload if '/' not in n and Path(n).suffix in ('.py', '.json')}
    if root_sources != set(source_hashes):
        errors.append('Unexpected/missing root .py/.json files relative to source lock')

    archive_csv = {(int(r['dwell']), r['policy']): r for r in read_csv('outputs/comparison.csv')}
    archived_pairs = {(int(r['dwell']), r['comparison']): r for r in read_csv('outputs/paired_comparison.csv')}
    archived_family = {int(r['dwell']): r for r in read_csv('outputs/learning_effect_family.csv')}
    numeric_checks = 0
    exact_checks = 0
    max_scaled_error = 0.0

    def check_numbers(reference, computed, where):
        nonlocal numeric_checks, exact_checks, max_scaled_error
        for key, value in computed.items():
            if key not in reference:
                errors.append(where + ': missing CSV field ' + key)
                continue
            expected = float(reference[key])
            value = float(value)
            numeric_checks += 1
            exact_checks += int(value == expected)
            scaled = abs(value - expected) / max(1.0, abs(value), abs(expected))
            max_scaled_error = max(max_scaled_error, scaled)
            if not math.isfinite(value) or not math.isclose(value, expected, rel_tol=2e-12, abs_tol=2e-12):
                errors.append(f'{where}:{key}: actual={value!r}, CSV={expected!r}')

    rows, primary, raw_checks, pair_count = [], [], [], 0
    for rec in execution['records']:
        D = int(rec['dwell'])
        member = f'cache/heldout_{D}.npz'
        binary = payload[member]
        match = digest(binary) == rec['sha256']
        if not match:
            errors.append('Raw data SHA-256 mismatch: ' + member)
        with np.load(io.BytesIO(binary), allow_pickle=False) as npz:
            data = npz['data'].copy()
            seed = int(npz['seed'])
        n = int(rec['trials'])
        if data.shape != (n, len(POLICIES), 10) or seed != int(rec['seed']):
            raise ValueError('Unexpected NPZ shape or seed: ' + member)
        if not np.isfinite(data).all() or not np.isin(data[:, :, 0], [0.0, 1.0]).all():
            raise ValueError('Invalid data entries: ' + member)
        raw_checks.append({'path': member, 'sha256_matches_record': match,
                           'shape': list(data.shape), 'seed': seed, 'trials': n})
        means, failures = [], []
        for j, policy in enumerate(POLICIES):
            survived = data[:, j, 0] == 0
            f = int(np.count_nonzero(~survived))
            costs = data[survived, j, 1]
            mean = float(np.mean(costs))
            se = float(np.std(costs, ddof=1) / np.sqrt(len(costs)))
            lo = 0.0 if f == 0 else float(beta_distribution.ppf(.025, f, n-f+1))
            hi = 1.0 if f == n else float(beta_distribution.ppf(.975, f+1, n-f))
            upper = 1.0 if f == n else float(beta_distribution.ppf(1-.05/30, f+1, n-f))
            computed = {'trials': n, 'failures': f, 'F': f/n,
                        'F_CI95_low': lo, 'F_CI95_high': hi, 'F_family95_upper': upper,
                        'survivors': len(costs), 'passes_given_survival': mean,
                        'passes_CI95_low': mean-1.96*se, 'passes_CI95_high': mean+1.96*se,
                        'stop_passes_mean': float(np.mean(data[:, j, 1])),
                        'busy_given_survival': float(np.mean(data[survived, j, 2])),
                        'busy_stop_mean': float(np.mean(data[:, j, 2])),
                        'reads_stop_mean': float(np.mean(data[:, j, 3])),
                        'writes_stop_mean': float(np.mean(data[:, j, 4])),
                        'updates_given_survival': float(np.mean(data[survived, j, 6]))}
            check_numbers(archive_csv[(D, policy)], computed, f'comparison[{D},{policy}]')
            rows.append({'dwell': D, 'policy': policy, **computed})
            means.append(mean)
            failures.append(f)
        for j in range(1, len(POLICIES)):
            both = (data[:, 0, 0] == 0) & (data[:, j, 0] == 0)
            delta = data[both, j, 1] - data[both, 0, 1]
            mean = float(np.mean(delta)); se = float(np.std(delta, ddof=1)/np.sqrt(len(delta)))
            risk = data[:, 0, 0] - data[:, j, 0]
            rmean = float(np.mean(risk)); rse = float(np.std(risk, ddof=1)/np.sqrt(n))
            computed = {'common_survivors': int(np.count_nonzero(both)),
                        'saving_mean': mean, 'saving_CI95_low': mean-1.96*se,
                        'saving_CI95_high': mean+1.96*se,
                        'risk_difference_learning_minus_other': rmean,
                        'risk_diff_CI95_low': rmean-1.96*rse,
                        'risk_diff_CI95_high': rmean+1.96*rse,
                        'stop_pass_saving': float(np.mean(data[:, j, 1]-data[:, 0, 1]))}
            check_numbers(archived_pairs[(D, POLICIES[j])], computed, f'paired[{D},{j}]')
            pair_count += 1
        alpha = .05/15
        if data[:, :2, 1].max() > 3600:
            errors.append(f'Observed pass bound exceeded at D={D}')
        radii = [3600*math.sqrt(math.log(1/alpha)/(2*(n-f))) for f in failures[:2]]
        both = (data[:, 0, 0] == 0) & (data[:, 1, 0] == 0)
        delta = data[both, 1, 1]-data[both, 0, 1]
        joint_mean = float(np.mean(delta))
        family_values = {'individual_conditional_saving': means[1]-means[0],
                         'individual_family95_lower': means[1]-means[0]-sum(radii),
                         'common_survivor_saving': joint_mean,
                         'common_survivor_family95_lower': joint_mean-7200*math.sqrt(math.log(1/alpha)/(2*len(delta))),
                         'family_size': 15, 'alpha_each': alpha, 'passes_bound_per_method': 3600}
        check_numbers(archived_family[D], family_values, f'family[{D}]')
        primary.append({'dwell': D, 'trials': n,
                        'learning_failures': failures[0], 'frozen_failures': failures[1],
                        'F_learning': failures[0]/n, 'F_frozen': failures[1]/n,
                        'learning_passes_given_survival': means[0],
                        'frozen_passes_given_survival': means[1],
                        'saving_percent': 100*(means[1]-means[0])/means[1],
                        'individual_family95_lower': family_values['individual_family95_lower'],
                        'common_survivor_family95_lower': family_values['common_survivor_family95_lower']})

    tests = read_json('outputs/tests.json')['tests']
    oracle = read_json('outputs/small_physical_oracle.json')
    oracle_identity = {(float(r['D']), bool(r['learning'])): r for r in oracle}
    oracle_checks = []
    for t in tests:
        if 'F_exact' in t:
            r = oracle_identity[(float(t['D']), bool(t['learning']))]
            ok = t['F_exact'] == r['F_lower'] == r['F_upper']
            oracle_checks.append({'D': t['D'], 'learning': t['learning'], 'F_exact': t['F_exact'], 'same_as_oracle_file': ok})
            if not ok:
                errors.append('Saved small model outputs disagree')

    manifest_files = []
    for name, data in sorted(payload.items()):
        git_id = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        manifest_files.append({'path': name, 'size_bytes': len(data), 'sha256': digest(data), 'git_blob_sha1': git_id})
    manifest = {
        'schema_version': 1, 'task': ROOT_NAME,
        'artifact_type': 'POST_HOC_DELIVERY_INVENTORY_NOT_HISTORICAL_EXECUTION_MANIFEST',
        'generated_at_utc': timestamp,
        'base_commit_from_records': execution['base'],
        'input_archive': archive_id,
        'archive_prefix': ROOT_NAME+'/',
        'path_semantics': 'File paths relative to the root of the extracted experiment directory.',
        'file_count': len(manifest_files),
        'excluded_from_inventory': 'Only this newly created manifest and other audit outputs; no delivered file excluded.',
        'scope': 'Byte identities and saved-output arithmetic only. No scientific approval; no modelling or retuning.',
        'recorded_source_hashes_count': len(source_hashes),
        'historical_manifest_present': 'outputs/manifest.json' in payload,
        'files': manifest_files}
    summary = {
        'task': ROOT_NAME, 'generated_at_utc': timestamp,
        'audit_scope': 'Read-only hash audit and independent arithmetic from saved NPZ; no model imports/execution.',
        'input_archive': archive_id, 'file_count': len(payload),
        'recorded_sources_checked': len(source_hashes),
        'source_hash_dictionaries_compared': 4,
        'selected_analogue_sha256': digest(payload['outputs/selected_analogue.json']),
        'raw_data_checks': raw_checks,
        'comparison_rows_checked': len(rows), 'paired_rows_checked': pair_count,
        'family_rows_checked': len(primary),
        'numeric_fields_checked': numeric_checks,
        'numeric_fields_exact_float_equal': exact_checks,
        'max_scaled_absolute_error': max_scaled_error,
        'float_comparison_tolerance': {'rtol': 2e-12, 'atol': 2e-12},
        'integer_failure_counts': 'Recomputed directly from NPZ; required to match saved CSV.',
        'saved_test_records': len(tests),
        'saved_test_records_marked_passed': sum(bool(t.get('passed')) for t in tests),
        'tests_rerun_in_this_audit': False,
        'small_reference_saved_output_checks': oracle_checks,
        'primary_comparison': primary,
        'historical_manifest_present': 'outputs/manifest.json' in payload,
        'errors': errors,
        'status': 'CONSISTENT_SAVED_BYTES_AND_STATISTICS_NOT_SCIENTIFIC_REVIEW' if not errors else 'MISMATCHES_FOUND',
        'limits': ['Matching recorded hashes establishes internal consistency, not independent proof of historical execution or causal generation.',
                   'Guarantee labels, mathematical proofs, origin of the old claimed ZIP hash, model validity, and prior test execution are not authenticated by this audit.',
                   'New inventory is dated now and must not be backdated or represented as an original run manifest.']}
    out.mkdir(parents=True, exist_ok=True)
    (out/'delivery_manifest_2026-09-10.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    (out/'delivery_audit_2026-09-10.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    with (out/'recomputed_comparison.csv').open('w', encoding='utf-8', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with (out/'recomputed_primary_comparison.csv').open('w', encoding='utf-8', newline='') as f:
        writer=csv.DictWriter(f, fieldnames=list(primary[0])); writer.writeheader(); writer.writerows(primary)
    print(json.dumps({k: summary[k] for k in ('input_archive', 'file_count', 'recorded_sources_checked',
          'comparison_rows_checked', 'paired_rows_checked', 'family_rows_checked', 'numeric_fields_checked',
          'numeric_fields_exact_float_equal', 'max_scaled_absolute_error', 'saved_test_records',
          'saved_test_records_marked_passed', 'status', 'errors', 'primary_comparison')}, indent=2))
    return 1 if errors else 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args=parser.parse_args()
    raise SystemExit(audit(args.source.resolve(), args.out.resolve()))


if __name__=='__main__':
    main()

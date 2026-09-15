#!/usr/bin/env python3
"""Bounded input audit only. No rates, risk integrals, transport, or simulations."""
from __future__ import annotations

import argparse
import ast
import base64
import csv
import hashlib
import io
import json
import platform
import subprocess
import sys
import zipfile
import zlib
from fractions import Fraction
from pathlib import Path

BASE = '64a7a1f436b2abd6997d37d14e6ce571e3a480c8'
OLD = 'experiments/RE-CY62167-ECC-RISK-BRIDGE-01/'
EXPECTED = {
    OLD+'registered_direct_by_energy.csv': '643189d9c288b9fac353c1233a4c73dbc994c89c',
    OLD+'risk_bridge.py.zlib.b85': '959c210696bb7f5c112659129c3298d3bbecefbf',
    OLD+'upstream_interface.py.zlib.b85': '103a80d25709d09d7da9add19152c6144587411b',
    OLD+'input_manifest.json': '464c0667b946b6a88e54d8db7b9eedc245345d75',
    OLD+'full_output_manifest.json': 'ba08014e869fd82fe9b7a89017038c7d053d3824',
    OLD+'model_contract.json': 'cefda54f684268facd1e969cac2e9f23c451549e',
    'experiments/RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv': '5de108c6759bcf720073b3fbc6581389d46e63aa',
}
GOES_SHA = '7b5e2f62e8a3b235ae1956505742253bb7d7633dfaa4be6e0350e37e5d8ab581'
FULL_SHA = 'c10a68e721716c8c9b96bf99a9e2d1de0bd3b179ebcc747b3fd149ff0741ff83'
TRANSPORT_SHA = 'af35f22ed333150e5ac46df951989811efdef31ee8e9c517f121e5f0853c9cb6'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def blob(repo, path):
    return git(repo, 'show', BASE+':'+path)


def identity(data):
    return {
        'bytes': len(data),
        'sha256': hashlib.sha256(data).hexdigest(),
        'git_blob': hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--goes-archive', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    package = Path(__file__).resolve().parent
    inputs = {}
    for path, expected in EXPECTED.items():
        info = identity(blob(args.repo, path))
        if info['git_blob'] != expected:
            raise ValueError('frozen Git blob mismatch: '+path)
        inputs[path] = info
    reg = list(csv.DictReader(io.StringIO(blob(args.repo, OLD+'registered_direct_by_energy.csv').decode())))
    source = zlib.decompress(base64.b85decode(blob(args.repo, OLD+'upstream_interface.py.zlib.b85'))).decode()
    tree = ast.parse(source)
    assignments = [n for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'MULT_POINTS' for t in n.targets)]
    if len(assignments) != 1:
        raise ValueError('MULT_POINTS definition not unique')
    points = ast.literal_eval(assignments[0].value)
    by_energy = {str(float(e)): (ne, nb) for e, ne, nb, n1 in points}
    if len(reg) != 14 or len(by_energy) != 14:
        raise ValueError('wrong coefficient support')
    comparisons = []
    for row in reg:
        ne, nb = by_energy[str(float(row['energy_mev']))]
        nreg = int(row['N_registered_clusters'])
        nacc = int(row['accumulation_bits_W32seq'])
        if int(row['N_direct_W32seq']) != 0 or Fraction(row['p_registered_direct_W32seq']) != 0:
            raise ValueError('unexpected registered direct coefficient')
        if nacc != int(row['N_registered_bitflips']):
            raise ValueError('unexpected registered accumulation count')
        mreg, kbar = Fraction(nacc, nreg), Fraction(nb, ne)
        # IEEE-754 literal equality is checked separately from exact count ratios.
        stored_m = float(row['mean_accumulation_bits_per_registered_event'])
        if stored_m != nacc/nreg:
            raise ValueError('stored mean does not match registered counts')
        comparisons.append({
            'energy_mev': row['energy_mev'], 'registered_clusters': nreg,
            'registered_accumulation_bits': nacc, 'upstream_clusters': ne,
            'upstream_bits': nb, 'mreg_exact_counts': str(mreg),
            'kbar_exact_counts': str(kbar), 'weight_exact_counts': str(mreg/kbar),
            'exact_counts_equal': mreg == kbar,
            'frozen_float_coefficients_equal': stored_m == nb/ne,
        })
    unequal = [q['energy_mev'] for q in comparisons if not q['exact_counts_equal']]
    if set(map(float, unequal)) != {29., 40., 80., 124., 164., 186.}:
        raise ValueError('unexpected mismatch support')
    stub = identity(blob(args.repo, OLD+'direct_rate_5min.csv'))
    if stub['bytes'] != 512 or stub['sha256'] == FULL_SHA:
        raise ValueError('historical input availability changed; reassess before calculation')
    archive = args.goes_archive.read_bytes()
    if hashlib.sha256(archive).hexdigest() != GOES_SHA:
        raise ValueError('GOES archive identity mismatch')
    upstream_manifest = json.loads(blob(args.repo, 'experiments/RE-GOES19-PROTON-RATE-01/input_manifest.json'))
    expected_members = {x['name']: x['sha256'] for x in upstream_manifest['goes_archive']['files']}
    members = []
    timestamp_text = b'Time stamp at the start of the averaging period, in seconds since 2000-01-01 12:00:00 UTC'
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for date in ('20260119', '20260120'):
            matches = [n for n in z.namelist() if '_d'+date+'_' in n and n.endswith('.nc')]
            if len(matches) != 1:
                raise ValueError('daily member missing or ambiguous')
            name = matches[0]
            content = z.read(name)
            sha = hashlib.sha256(content).hexdigest()
            if sha != expected_members[Path(name).name]:
                raise ValueError('daily source SHA mismatch')
            if timestamp_text not in content or b'PT5M' not in content:
                raise ValueError('source timestamp/cadence metadata text absent')
            members.append({'name': name, 'sha256': sha, 'timestamp_attribute_text_found': True})
    stops = {}
    for script in ('extract_selected_rate.py', 'compute_bounds.py', 'independent_check.py'):
        p = subprocess.run([sys.executable, '-B', str(package/script)], capture_output=True, text=True)
        if p.returncode == 0 or 'DISABLED_UNQUALIFIED_DREG' not in p.stderr:
            raise ValueError('unsafe numerical entry point: '+script)
        stops[script] = {'returncode': p.returncode, 'stderr': p.stderr.strip()}
    report = {
        'task': 'RE-CY62167-COVERAGE-THRESHOLD-01', 'base_commit': BASE,
        'audit_code_commit': git(args.repo, 'rev-parse', 'HEAD').decode().strip(),
        'audit_scope': 'input identities, literal coefficient audit, protective stops only',
        'source_inputs': inputs, 'historical_direct_stub': stub,
        'historical_full_rate_sha256_required': FULL_SHA,
        'frozen_transport_sha256_required': TRANSPORT_SHA,
        'goes_archive': {'sha256': GOES_SHA, 'bytes': len(archive), 'selected_days': members},
        'temporal_contract': {'start_utc': '2026-01-19T04:00:00+00:00',
            'end_exclusive_utc': '2026-01-20T04:00:00+00:00', 'expected_bins': 288,
            'bin_s': 300, 'timestamp_semantics': 'start of averaging period',
            'time_arrays_checked': False, 'selected_rate_completeness_checked': False},
        'energy_coefficients': comparisons, 'unequal_energy_nodes': unequal,
        'upstream_identity': 'NOT_IDENTICAL_AS_ENERGY_TRANSFORMATION',
        'selected_integrated_equality': 'NOT_ESTABLISHED',
        'entry_point_stops': stops,
        'I1': None, 'I2': None, 'a_upper': None, 'b_upper': None,
        'delta_zero_coverage_limit_s': None, 'signed_slack': None,
        'numerical_execution': 'NOT_RUN', 'independent_integrals': 'NOT_RUN',
        'device_policy_status': 'NOT_ESTABLISHED',
        'environment': {'python': sys.version, 'platform': platform.platform()},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'input_audit': 'COMPLETED', 'unequal_energy_nodes': unequal,
                      'numerical_execution': 'NOT_RUN', 'output': str(args.out)}))


if __name__ == '__main__':
    main()

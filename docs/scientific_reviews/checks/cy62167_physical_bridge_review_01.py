#!/usr/bin/env python3
"""Bounded SR checks; no upstream driver, transport, raw parsing or output writes.

Usage: python3 -B docs/scientific_reviews/checks/cy62167_physical_bridge_review_01.py REPO
Reads frozen Git blobs; independently checks event traces and Poisson jump chains.
Small synthetic rates below are falsification fixtures, not replacement CY inputs.
"""
import csv
import hashlib
import importlib
import io
import itertools
import json
import platform
import subprocess
import sys
from collections import Counter
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 65
ROOT = Path(sys.argv[1]).resolve()
TARGET = '0c979c34d537c9f328858010a8df6cdeab598735'
PKG = 'experiments/RE-CY62167-PHYSICAL-BRIDGE-01/'


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def blob(path, ref=TARGET):
    return git('show', ref + ':' + path)


def provenance():
    m = json.loads(blob(PKG + 'MANIFEST.json'))
    checks = {}
    for name, identity in m['files'].items():
        b = blob(PKG + name)
        checks[name] = (len(b) == identity['size_bytes'] and
                        hashlib.sha256(b).hexdigest() == identity['sha256'])
    inputs = json.loads(blob(PKG + 'INPUTS.json'))
    source_checks = {}
    for x in inputs['controlled_inputs']:
        source_checks[x['path']] = git('rev-parse', x['ref'] + ':' + x['path']).decode().strip() == x['blob']
    contract = git('rev-parse', TARGET + ':' + PKG + 'CONTRACT.md').decode().strip()
    assert contract == m['preexecution_contract_git_blob']
    assert all(checks.values()) and all(source_checks.values())
    rows = list(csv.DictReader(io.StringIO(blob('experiments/RE-CY62167-ECC-RISK-BRIDGE-01/risk_curves.csv').decode())))
    selected = [r for r in rows if r['timestamp/window_start'] == '2026-01-19T04:00:00+00:00'
                and r['window_duration'] == '24h' and Decimal(r['shield_mm']) == 10
                and r['sigma_model'] == 'main_loglog' and r['direction_scenario'] == 'central_mean'
                and r['direct_scenario'] == 'DREG' and Decimal(r['tau_scrub_s']) == 1]
    assert len(selected) == 1
    r = selected[0]
    assert Decimal(r['F_total_upper']) == Decimal('0.0003098119451681036')
    assert Decimal(r['F_total_lower']) == Decimal('5.90925197663239e-10')
    maps = list(csv.DictReader(io.StringIO(blob('experiments/RE-CY62167-PAPER-COMPLETION-01/mapping_sweep_summary.csv').decode())))
    counts = Counter(x['N_direct_all_series'] for x in maps)
    assert len(maps) == 55 and counts == {'0': 45, '4': 9, '5': 1}
    assert [(x['mapping_id'], x['N_direct_proton']) for x in maps if int(x['N_direct_proton'])] == [('W_00_11', '1')]
    return {'manifest_files': checks, 'input_blobs': source_checks, 'contract_blob': contract,
            'slice': r, 'mapping_counts': counts,
            'delta_arithmetic_only': str(Decimal('.001') - Decimal(r['F_total_upper']))}


def structural():
    # Explicit bit tuples and componentwise flips, not RE's set/XOR helpers.
    totals = {}
    for n, t in [(6, 1), (7, 2), (8, 3)]:
        count = 0
        for state in itertools.product((0, 1), repeat=n):
            if sum(state) > t:
                continue
            for mark in itertools.product((0, 1), repeat=n):
                if sum(mark) < 2*t + 1:
                    continue
                after = tuple(1-b if hit else b for b, hit in zip(state, mark))
                assert sum(after) > t
                count += 1
        totals[f'n{n}_t{t}'] = count
    # First passage is sticky, even if a later toggle restores an endpoint.
    state = [0, 0, 0]; ever = False
    for mark in [(0, 1, 2), (0, 1, 2)]:
        for j in mark:
            state[j] = 1-state[j]
        ever |= sum(state) > 1
    assert ever and sum(state) == 0
    # A mixed data/parity failure requires neither D3 nor data-only failure.
    state = [0]*38
    state[0] = 1; state[32] = 1
    assert sum(state) == 2 and sum(state[:32]) == 1
    return {'generalized_cases': totals, 'failed_then_clean_endpoint': ever,
            'mixed_data_parity_without_D3_or_data_exceedance': True}


def execution_counterexamples():
    # read/commit are separate. A corrected read latches clean data.
    def execute(events, ideal):
        state = [0, 0]; write_pending = False; failed = False; trace = []
        for event in events:
            if isinstance(event, int):
                state[event] = 1-state[event]
            elif event == 'read':
                write_pending = sum(state) == 1
                if ideal == 'at_read':
                    state = [0, 0]
                    write_pending = False
            elif event == 'commit':
                if write_pending or ideal == 'at_completion':
                    state = [0, 0]
                write_pending = False
            failed |= sum(state) > 1
            trace.append({'event': event, 'state': list(state), 'ever_failed': failed})
        return failed, trace
    out = {}
    for label, events, ideal in [
        ('correcting_read_RMW', [0, 'read', 1, 'commit'], 'at_read'),
        ('clean_read_no_write', ['read', 0, 'commit', 1], 'at_completion'),
    ]:
        actual = execute(events, None); relaxation = execute(events, ideal)
        assert actual[0] and not relaxation[0]
        out[label] = {'conditional_write': actual[1], 'ideal_reset': relaxation[1]}
    return out


def survival_jump_chain(mu, n=32):
    # Condition on Poisson(n*mu) arrivals, update survival in 0/1 states.
    # No eigenformula, matrix exponential or RE helper is used.
    z = Decimal(n)*mu
    weight = (-z).exp(); p0 = Decimal(1); p1 = Decimal(0)
    survival = weight
    for k in range(1, 180):
        p0, p1 = p1/Decimal(n), p0
        weight *= z/Decimal(k)
        survival += weight*(p0+p1)
    return survival


def phase_check():
    for name in ['ecc_word_model.py', 'scrub_model.py']:
        relative = 'experiments/RE-CY62167-ECC-RISK-BRIDGE-01/' + name
        assert (ROOT / relative).read_bytes() == blob(relative)
    sys.path.insert(0, str(ROOT / 'experiments/RE-CY62167-ECC-RISK-BRIDGE-01'))
    ecc = importlib.import_module('ecc_word_model')
    scrub = importlib.import_module('scrub_model')
    import numpy as np
    import scipy
    # Production primitive checked against independent event-count recurrence.
    discrepancies = []
    for mu in ['0', '1e-8', '1e-5', '.0009', '.0011', '.01']:
        ref = Decimal(1)-survival_jump_chain(Decimal(mu))
        observed = ecc.clean_failure(float(mu))
        err = abs(Decimal(str(observed))-ref)
        assert err < Decimal('2e-11')
        discrepancies.append({'mu': mu, 'reference_F': str(ref), 'production_F': observed,
                              'absolute_error': str(err)})
    r = Decimal('0.00001'); T = 300; tau = 1
    full = survival_jump_chain(r) ** (T-1)
    def mean_risk(P):
        total = Decimal(0)
        for j in range(P):
            phi = (Decimal(j)+Decimal('.5'))/Decimal(P)
            total += 1-full*survival_jump_chain(r*phi)*survival_jump_chain(r*(1-phi))
        return total/Decimal(P)
    f16, f128 = mean_risk(16), mean_risk(128)
    production = float(scrub.cyclic_phase_aggregate_multi(np.array([float(r)]), [1], tau, 16)[1][1][0])
    assert abs(Decimal(str(production))-f16) < Decimal('1e-14')
    assert f128 > f16
    return {'numpy': np.__version__, 'scipy': scipy.__version__,
            'primitive_checks': discrepancies, 'stationary_fixture_T_s': T, 'tau_s': tau,
            'per_bit_rate_s': str(r), 'F_word_P16_independent': str(f16),
            'F_word_P128_independent': str(f128), 'F_word_P16_production': production,
            'P128_minus_P16': str(f128-f16),
            'interpretation': 'A concrete under-estimate of a finer phase average, not an error estimate for the frozen CY slice.'}


result = {'reviewed_sha': TARGET, 'python': sys.version, 'platform': platform.platform(),
          'provenance': provenance(), 'structural': structural(),
          'execution_counterexamples': execution_counterexamples(), 'phase_check': phase_check(),
          'scope': 'Fixture successes include expected falsifiers; not full-device acceptance.'}
print(json.dumps(result, indent=2, sort_keys=True))

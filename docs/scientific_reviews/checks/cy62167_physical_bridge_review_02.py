#!/usr/bin/env python3
"""Small independent re-review checks. No CY rate regeneration or main writes.

Usage: python3 -B THIS_SCRIPT REPO EXACT_REPAIR_COPY
The optional-input probes use deliberately invalid *synthetic* summaries in a
fresh temporary directory; they are not new or substituted scientific inputs.
"""
import itertools
import json
import subprocess
import sys
import tempfile
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 60
TARGET = 'c48ca29eb65fee96154d645819c4e533a1709037'
PREFIX = 'experiments/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01/'
REPO, COPY = map(lambda x: Path(x).resolve(), sys.argv[1:3])


def original(path):
    return subprocess.check_output(['git', '-C', str(REPO), 'show', TARGET + ':' + path])


def timeline(hits):
    """Physical latch/write and ideal-at-read evolve on the same bit toggles."""
    physical = [0, 0, 0]; ideal = [0, 0, 0]
    fp = fi = False
    pending = None
    distinct_rmw = False
    seen = [set(), set(), set()]
    trace = []
    events = [(t, 'hit', bit) for t, bit in hits]
    events += [(10, 'check', None), (12, 'write', None),
               (20, 'check', None), (22, 'write', None)]
    for time, kind, bit in sorted(events):
        if kind == 'hit':
            if pending is not None and bit != pending:
                distinct_rmw = True
            physical[bit] = 1-physical[bit]
            ideal[bit] = 1-ideal[bit]
            seen[time//10].add(bit)
        elif kind == 'check':
            assert pending is None
            pending = physical.index(1) if sum(physical) == 1 else None
            ideal = [0, 0, 0]
        elif pending is not None:
            physical = [0, 0, 0]  # committed clean image latched at singleton check
            pending = None
        fp |= sum(physical) > 1
        fi |= sum(ideal) > 1
        trace.append([time, kind, bit, list(physical), list(ideal), fp, fi])
    pair_event = any(len(bits) >= 2 for bits in seen)
    return {'physical_failure': fp, 'ideal_failure': fi, 'distinct_RMW_hit': distinct_rmw,
            'pair_arrival_event': pair_event, 'trace': trace}


def execution_checks():
    witness = timeline([(5, 0), (11, 0), (13, 0), (14, 1)])
    assert witness['physical_failure'] and not witness['ideal_failure']
    assert not witness['distinct_RMW_hit'] and witness['pair_arrival_event']
    count = 0; old_inclusion_violations = 0
    slots = [5, 11, 13, 14, 21, 23]
    for marks in itertools.product([-1, 0, 1, 2], repeat=len(slots)):
        r = timeline([(t, b) for t, b in zip(slots, marks) if b >= 0])
        assert not r['physical_failure'] or r['pair_arrival_event'] or r['distinct_RMW_hit']
        old_inclusion_violations += bool(r['physical_failure'] and not r['ideal_failure'] and not r['distinct_RMW_hit'])
        count += 1
    return {'same_bit_RMW_witness': witness, 'streams': count,
            'ideal_plus_distinct_RMW_inclusion_violations': old_inclusion_violations,
            'pair_event_plus_distinct_RMW_inclusion_violations': 0}


def poisson_safe(mu, n):
    # Independent event-count recurrence, not an eigenformula from RE.
    z = Decimal(n)*mu; weight = (-z).exp()
    p0, p1 = Decimal(1), Decimal(0); total = weight
    for k in range(1, 150):
        p0, p1 = p1/Decimal(n), p0
        weight *= z/Decimal(k)
        total += weight*(p0+p1)
    return total


def arithmetic_and_schedule():
    toggle_exact = 1-poisson_safe(Decimal('.01'), 3)**2
    p = 1-(-Decimal('.01')).exp()
    distinct_per_interval = 3*p*p-2*p*p*p
    pair_exact = 1-(1-distinct_per_interval)**2
    pair_upper = Decimal(3)*Decimal(2)*Decimal('.01')**2
    rmw_upper = Decimal('.004')
    rmw_exact = 1-(-rmw_upper).exp()
    assert toggle_exact < pair_exact <= pair_upper and rmw_exact <= rmw_upper
    recorded = json.loads(original(PREFIX+'outputs/synthetic_direction_check.json'))
    assert abs(pair_exact-Decimal(str(recorded['exact_pair_first_passage']))) < Decimal('1e-14')
    assert abs(rmw_exact-Decimal(str(recorded['exact_rmw_distinct_arrival']))) < Decimal('1e-14')
    # A pulse entirely within a read/write window refutes unqualified duty weighting.
    pulse_integral = Decimal(1)
    window_weighted = pulse_integral
    duty_weighted = Decimal('.1')*pulse_integral
    assert window_weighted > duty_weighted
    # Finite fixed phase schedule with tau=1, Delta=.07, 300-s aligned rate bins.
    # This is a mathematical fixture, not the frozen CY trace.
    phases = [Decimal(j+1)/10 for j in range(8)]
    delta = Decimal('.07'); total = Decimal(0)
    for phase in phases:
        for k in range(600):
            a = phase+k; b = min(a+delta, Decimal(600))
            total += max(Decimal(0), min(b, Decimal(300))-a)
            total += 2*max(Decimal(0), b-max(a, Decimal(300)))
    duty = len(phases)*delta*Decimal(900)
    assert total <= duty
    return {'synthetic_distinct_arrival_event_exact': str(pair_exact),
            'synthetic_toggle_first_passage_exact': str(toggle_exact), 'synthetic_pair_upper': str(pair_upper),
            'synthetic_RMW_exact': str(rmw_exact), 'synthetic_RMW_upper': str(rmw_upper),
            'pulse_all_check_integral': str(window_weighted), 'pulse_duty_integral': str(duty_weighted),
            'aligned_300s_bins_all_check_integral': str(total), 'aligned_duty_integral': str(duty)}


def untrusted_input_probe():
    for name in ['config.json', 'repair_checks.py', 'independent_check.py']:
        assert (COPY/name).read_bytes() == original(PREFIX+name)
    cfg = json.loads((COPY/'config.json').read_text())
    results = {}
    # Exercise existing optional CLI in an isolated dir, never rewrite RE outputs.
    with tempfile.TemporaryDirectory(prefix='sr-cy-r2-input-probe-') as tmp:
        d = Path(tmp)
        for label, i1, i2 in [('negative', -1, -1), ('unattested_zero', 0, 0)]:
            summary = {'integral_r': i1, 'integral_r2': i2,
                       'slice': cfg['slice'], 'source_identity': 'SYNTHETIC_UNTRUSTED_SR_PROBE'}
            path = d/(label+'.json'); path.write_text(json.dumps(summary))
            for driver in ['repair_checks.py', 'independent_check.py']:
                out = d/(label+'-'+driver+'.json')
                proc = subprocess.run([sys.executable, '-B', str(COPY/driver), '--config', str(COPY/'config.json'),
                                       '--rate-summary', str(path), '--out', str(out)], capture_output=True, text=True)
                assert proc.returncode == 0, proc.stderr
                result = json.loads(out.read_text())
                assert result['rate_qualification'] == 'QUALIFIED_BY_SUPPLIED_FROZEN_SUMMARY'
                results[label+'/'+driver] = result
    return results


out = {'reviewed_sha': TARGET, 'execution': execution_checks(),
       'arithmetic_and_schedule': arithmetic_and_schedule(), 'optional_interface_probes': untrusted_input_probe(),
       'scope': 'Expected counterexamples are not scientific inputs or positive physical certificates.'}
print(json.dumps(out, indent=2, sort_keys=True))

#!/usr/bin/env python3
"""Bounded SR-03 checks after the four RE commands in an isolated target copy.

Usage: python3 -B THIS_FILE REPO ISOLATED_REPAIR_PACKAGE
No rate data, random simulation, production writes or upstream execution.
The oracle reconstructs parity from arrival history and scheduled clean writes;
it does not use either RE executor to compute its expected states.
"""
import bisect
import hashlib
import importlib.util
import itertools
import json
from decimal import Decimal, getcontext
from fractions import Fraction as F
from pathlib import Path
import subprocess
import sys

TARGET = 'd3cd3e9385f62f047954ce3e54454eb5976ddcb8'
PREFIX = 'experiments/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-02/'
REPO, COPY = (Path(x).resolve() for x in sys.argv[1:3])
getcontext().prec = 60


def original(name):
    return subprocess.check_output(['git', '-C', str(REPO), 'show', TARGET+':'+PREFIX+name])


def load_module(name, file):
    assert (COPY/file).read_bytes() == original(file)
    spec = importlib.util.spec_from_file_location(name, COPY/file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


production = load_module('sr3_production_executor', 'executor_model.py')
bitmask = load_module('sr3_re_bitmask', 'independent_check.py')


def oracle(events, checks, delay, horizon, nbits):
    """Offline parity queries; derive commits by visiting checks only.

    All toy arrivals are in (0,H), off checks/commits. Delay is fixed and
    positive, completing before the next potential check. No pending start.
    """
    q = lambda x: F(str(x))
    hits = sorted((q(e['time']), e['bit']) for e in events)
    cs = sorted(q(c) for c in checks if 0 < q(c) < q(horizon))
    d, H = q(delay), q(horizon)
    assert d > 0 and len(set(t for t, _ in hits)) == len(hits)
    assert all(0 < t < H and t not in cs and 0 <= b < nbits for t,b in hits)

    def parity(start, end):
        return [b for b in range(nbits) if sum(start < t <= end and k == b for t,k in hits) % 2]

    writes = []  # (opening check, completion, observed original bit)
    records = []
    for index,c in enumerate(cs):
        last = max([F(0)] + [end for _,end,_ in writes if end <= c])
        state = parity(last,c)
        kind = 'clean_check' if not state else 'singleton_check' if len(state)==1 else 'failed_check'
        if len(state)==1:
            assert index+1 == len(cs) or c+d < cs[index+1]
            writes.append((c,c+d,state[0]))
        records.append((c,kind,None))
    assert all(t != end for t,_ in hits for _,end,_ in writes)
    records += [(t,'toggle',b) for t,b in hits]
    records += [(end,'commit',None) for _,end,_ in writes if end <= H]
    records.sort()

    def bad_until(time):
        return any(c < t < end and t <= time and b != origin
                   for c,end,origin in writes for t,b in hits)

    fp=fi=False; trace=[]
    for time,kind,bit in records:
        last_write=max([F(0)]+[end for _,end,_ in writes if end <= time])
        last_check=max([F(0)]+[c for c in cs if c <= time])
        physical,ideal=parity(last_write,time),parity(last_check,time)
        fp |= len(physical)>=2; fi |= len(ideal)>=2
        active=[(end,origin) for c,end,origin in writes if c <= time < end]
        assert len(active)<=1
        row={'time':float(time),'kind':kind,'physical':physical,'ideal':ideal,
             'pending_origin':active[0][1] if active else None,
             'pending_commit':float(active[0][0]) if active else None,
             'physical_failure':fp,'ideal_failure':fi,'B':bad_until(time)}
        if kind=='toggle': row['bit']=bit
        trace.append(row)
    labels=[sorted({b for t,b in hits if bisect.bisect_right(cs,t)==index}) for index in range(len(cs)+1)]
    P=any(len(s)>=2 for s in labels); B=bad_until(H)
    return {'physical_failure':fp,'ideal_failure':fi,'B':B,'P':P,
            'old_inclusion_holds':not fp or fi or B,'repaired_inclusion_holds':not fp or P or B,
            'pending_at_horizon':any(c <= H < end for c,end,_ in writes),
            'physical_at_horizon':parity(max([F(0)]+[end for _,end,_ in writes if end <= H]),H),
            'ideal_at_horizon':parity(max([F(0)]+cs),H),
            'labels_by_interval':labels,'trace':trace}


def compare_case(events, checks, delay, H, bits):
    expected=oracle(events,checks,delay,H,bits)
    actual=production.run_trace(events,checks,delay,H,bits)
    assert actual==expected, (events,actual,expected)
    fp,fi,B,P=bitmask.run([e['bit'] for e in events],[e['time'] for e in events],checks,delay,H,bits)
    assert (fp,fi,B,P)==tuple(expected[k] for k in ('physical_failure','ideal_failure','B','P'))
    assert expected['repaired_inclusion_holds']
    return expected


def implementation_checks():
    cfg=json.loads(original('config.json'))['trace_check']
    total=old=0
    for marks in itertools.product(cfg['symbols'], repeat=len(cfg['arrival_slots'])):
        events=[{'time':t,'bit':b} for t,b in zip(cfg['arrival_slots'],marks) if b>=0]
        r=compare_case(events,cfg['check_times'],cfg['write_delay'],cfg['horizon'],cfg['bits'])
        total+=1; old+=not r['old_inclusion_holds']
    assert (total,old)==(4096,60)
    event=lambda t,b:{'time':t,'bit':b}
    # Non-frozen, bounded boundary probes, with exactly representable timings.
    cases={
      'clean_no_write':([event(1.125,0)],[1.0],.25,1.5,3),
      'initial_first_passage':([event(.125,0),event(.25,1)],[1.0],.25,1.5,3),
      'pending_safe_at_H':([event(.5,0)],[1.0],.25,1.125,3),
      'pending_failure_at_H':([event(.5,0),event(1.125,1)],[1.0],.25,1.1875,3),
      'commit_exactly_H':([event(.5,0),event(1.125,1)],[1.0],.25,1.25,3),
      'same_bit_cleared_while_pending':([event(.5,0),event(1.0625,0)],[1.0],.25,1.125,3),
      'final_partial_pair':([event(1.25,0),event(1.375,1)],[.5,1.0],.125,1.5,3),
      'nonuniform_actual_checks':([event(.125,0),event(.5,0),event(.9375,1)],[.25,.75],.125,1.0,3),
      '32bit_labels':([event(.125,31),event(.75,31),event(.875,0)],[.5],.125,1.0,32),
    }
    flags={}
    for name,args in cases.items():
        r=compare_case(*args)
        flags[name]={k:r[k] for k in ('physical_failure','ideal_failure','P','B','pending_at_horizon')}
    return {'frozen_streams':total,'old_inclusion_violations':old,
            'new_inclusion_violations':0,'main_full_trace_matches':total+len(cases),
            'RE_bitmask_four_indicator_matches':total+len(cases),'boundary_probes':flags}


def export_comparison():
    full=json.loads((COPY/'outputs/executor_check.json').read_text())
    summary=json.loads(original('outputs/executor_summary.json'))
    for key in ('checks','physical_slice','scientific_acceptance_rate_interface'):
        assert full[key]==summary[key],key
    for key in ('streams','old_inclusion_violations','repaired_inclusion_violations'):
        assert full['exhaustive'][key]==summary['exhaustive'][key],key
    assert full['exhaustive']['first_old_violation']['marks']==summary['exhaustive']['first_old_violation_marks']
    ce=json.loads(original('traces/counterexample_input.json'))
    expected=oracle(ce['events'],ce['check_times'],ce['write_delay'],ce['horizon'],3)
    assert full['targeted']['mandatory_counterexample']['result']==expected
    assert all(v['pass'] if isinstance(v,dict) else v for v in full['targeted'].values())
    results={'executor_summary':'complete specified projection matches; full executor output not committed'}
    for name in ('counterexample_trace.json','independent_check.json','probability_qa.json'):
        old=original('outputs/'+name); new=(COPY/'outputs'/name).read_bytes()
        assert json.loads(old)==json.loads(new),name
        results[name]={'semantic_match':True,'byte_match':old==new,
                       'published_sha256':hashlib.sha256(old).hexdigest(),
                       'reproduced_sha256':hashlib.sha256(new).hexdigest()}
    return results


def arithmetic_check():
    # Enumerate the Bernoulli occupied/not-occupied cells, not RE's 3p^2-2p^3.
    p=1-(-Decimal('.01')).exp()
    safe=sum((p**sum(s))*(1-p)**(3-sum(s)) for s in itertools.product((0,1),repeat=3) if sum(s)<2)
    enlarged=1-safe**2
    qa=json.loads(original('outputs/probability_qa.json'))
    assert abs(enlarged-Decimal(qa['distinct_arrival_event_probability']))<Decimal('1e-55')
    # A scalar past-known random window is not a deterministic envelope.
    # Pure expectation identity fixture, not a physical model or new rate input.
    conditional=[1-(-Decimal(x)).exp() for x in ('.01','.4')]
    unconditional=sum(conditional)/2
    expected_integral=(Decimal('.01')+Decimal('.4'))/2
    assert unconditional>Decimal('.01') and unconditional<=expected_integral
    return {'enlarged_event_probability':str(enlarged),
            'random_window_toy_unconditional_probability':str(unconditional),
            'random_window_small_realization_integral':'.01',
            'random_window_expected_integral':str(expected_integral)}


print(json.dumps({'reviewed_target':TARGET,'exports':export_comparison(),
                  'independent_implementation_checks':implementation_checks(),
                  'independent_arithmetic':arithmetic_check()},indent=2,sort_keys=True))

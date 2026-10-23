"""Offline replay: frozen text inputs, exact window example and app counts only."""
import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from windows import Contract, app_accounting

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def canonical_bytes(path):
    return path.read_bytes().replace(b'\r\n', b'\n')


def exact(value):
    if isinstance(value, Fraction):
        return int(value) if value.denominator == 1 else str(value)
    if isinstance(value, dict):
        return {k: exact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [exact(x) for x in value]
    return value


def build():
    versions = json.loads((HERE/'versions.json').read_text(encoding='utf-8'))
    for item in versions['inputs']:
        observed = hashlib.sha256(canonical_bytes(ROOT/item['path'])).hexdigest()
        if observed != item['canonical_lf_sha256']:
            raise ValueError('frozen input changed: ' + item['path'])
    cfg = json.loads((HERE/'example.json').read_text(encoding='utf-8'))
    c = Contract(**cfg['contract'])
    danger = cfg['danger_intervals']
    windows = c.small_windows(danger)
    candidate = json.loads((HERE.parent/'candidate.json').read_text(encoding='utf-8'))
    common = json.loads((ROOT/'experiments/t186-method-comparison/code-strength/common-input.json').read_text(encoding='utf-8'))
    app = candidate['inherited_contract']['application']
    for key in ('epoch_ns', 'read_offset_ns', 'write_offset_ns', 'first_ns',
                'address_multiplier', 'data_bits', 'inbound_ns', 'ready_ns',
                'outbound_ns', 'backpressure_ns', 'read_repair'):
        if app[key] != common['application'][key]:
            raise ValueError('application differs from accepted v4: ' + key)
    if (candidate['memory']['words'] != common['words']
            or Fraction(candidate['mission']['duration_s']) != Fraction(common['mission_s'])
            or Fraction(candidate['mission']['epsilon']) != Fraction(common['epsilon'])):
        raise ValueError('W/T/epsilon changed')
    return exact(dict(
        status='PARAMETRIC_CONSTRUCTION_READY_FOR_REVIEW_PHYSICAL_INPUT_OPEN',
        frozen_inputs_checked=len(versions['inputs']),
        synthetic_example=dict(
            time_unit=cfg['time_unit'], status=cfg['status'],
            H_fast=c.H_fast, lookahead=c.lookahead,
            potential_slots=c.N, J_FAST_ranges=c.fast_ranges(danger),
            startup_and_FAST_ranges=c.ranges(danger),
            LOW_progression=dict(first=0, step=c.low_stride, end_exclusive=c.N),
            mandatory_count=c.count(danger),
            count_by_word=[c.count(danger, word=w) for w in range(c.words)],
            completed_count=c.count(danger, completed_only=True),
            sample_windows=[v for v in windows if v['j'] in (0, 7, 8, 17, 18, 27)],
            all_loss_actual_scrub_count=c.N,
            guaranteed_subset_count_is_cost_upper=False),
        application=app_accounting(candidate),
        physical_result=dict(
            numeric_SAC_C_package=None, numeric_PROBA_file=None,
            Q_position=None, Q_OFF39=None, Q_OFF44=None,
            physical_service_guarantee=None, hardware_cost=None,
            risk_margin=None, timing_margin=None, resource_margin=None,
            additional_channel_numeric_requirement=None,
            physical_point_confirmed=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true', help='check saved results byte for byte (LF)')
    group.add_argument('--write', action='store_true', help='regenerate only this subdirectory results.json')
    args = parser.parse_args()
    rendered = (json.dumps(build(), ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    target = HERE/'results.json'
    if args.check:
        if canonical_bytes(target) != rendered:
            raise SystemExit('results differ; inspect inputs and rerun --write only intentionally')
        print('Frozen inputs and deterministic results match; physical Q remains UNKNOWN.')
    elif args.write:
        target.write_bytes(rendered)
        print('Wrote', target.name)
    else:
        print(rendered.decode('utf-8'), end='')

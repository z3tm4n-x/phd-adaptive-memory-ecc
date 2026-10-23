"""Exact necessary GEO price gate; accepted Q/price campaigns are not rerun."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COMMON = 'experiments/t186-method-comparison/code-strength/common-input.json'
ACCEPTED = 'experiments/mission-rise-rate-20261022/cfe-application/outputs/result.json'
NS = 10**9


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, default=str) + '\n').encode()


def load(root=ROOT):
    manifest = json.loads((HERE / 'frozen-inputs.json').read_text('utf-8'))
    for name, digest in manifest['sha256'].items():
        data = (root / name).read_bytes().replace(b'\r\n', b'\n')
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Frozen premise changed; recertify fixed/OFF and price: ' + name)
    cfg = json.loads((root / COMMON).read_text('utf-8'))
    accepted = json.loads((root / ACCEPTED).read_text('utf-8'))
    return cfg, accepted, manifest


def support_floor(A, D, T, P):
    """D=W*R_minus seconds; two complete passes cover horizon edges."""
    if P <= 0:
        raise ValueError('Period must be positive')
    return A + D * max(F(0), 1 / F(P) - 2 / T)


def startup_floor(A, D, T, Ps, length):
    """Only startup, never added to the overlapping support count."""
    if length < 0:
        raise ValueError('Startup duration cannot be negative')
    return A + D / T * max(F(0), min(F(length), T) / Ps - 2)


def gate(A, D, T, Ps, fixed_upper, gain=F(5)):
    if min(A, D, T, Ps, fixed_upper, gain) <= 0:
        raise ValueError('Positive common prices, times and target required')
    target = fixed_upper / gain
    budget = target - A
    if budget <= 0:
        return dict(status='excluded_by_application_floor', target=target,
                    available_control_budget=budget, passes_necessary_price=False)
    pmin = D / (budget + 2 * D / T)
    hmax = Ps * (T * budget / D + 2)
    # A valid current T119 row has H0 >= P. Relax it to H0=P.
    full_fast_excluded = startup_floor(A, D, T, Ps, T) > target
    excluded = full_fast_excluded and pmin > hmax
    return dict(status='excluded_by_startup_and_support' if excluded else 'not_excluded',
                target=target, available_control_budget=budget,
                support_period_min_s=pmin, support_period_min_h=pmin / 3600,
                startup_duration_max_s=hmax, startup_duration_max_min=hmax / 60,
                relaxed_period_max_s=hmax if full_fast_excluded else None,
                startup_full_mission_excluded=full_fast_excluded,
                support_at_period_min=support_floor(A, D, T, pmin),
                startup_at_period_min=startup_floor(A, D, T, Ps, pmin),
                fixed_over_startup_at_period_min=fixed_upper / startup_floor(A, D, T, Ps, pmin),
                startup_at_period_min_over_target=startup_floor(A, D, T, Ps, pmin) / target,
                passes_necessary_price=not excluded,
                interpretation='Necessary core-price gate only; not a Q certificate or physical qualification')


def evaluate():
    cfg, accepted, manifest = load()
    W, T = cfg['words'], F(cfg['mission_s'])
    s = cfg['service']; cal = cfg['calendar']
    J = F(s['operation_endpoint_span_ns']) / NS
    rminus = ((3 * s['read_beat_ns'] + s['decode39_ns']) * F(s['clock_lower'])
              - F(s['operation_endpoint_span_ns'])) / NS
    ps_no_j = W * cal['g_ticks'] * F(s['clock_upper']) / NS
    ps = ps_no_j + J
    if rminus <= 0 or ps_no_j <= J or W % cal['batch_size']:
        raise ValueError('Frozen calendar lower-count premises failed')
    A = F(accepted['screen']['mandatory_app39_core_lower'])
    rows = accepted['screen']['rows']
    fixed_upper = F(rows['fixed44']['price']['core_upper'])
    if not rows['fixed44']['sufficient'] or F(rows['fixed44']['risk']['upper']) > F(cfg['epsilon']):
        raise ValueError('The common strong-code comparator is not sufficient')
    result = gate(A, W * rminus, T, ps, fixed_upper)
    comparison = {}
    for name in ('OFF39', 'OFF44', 'fixed44'):
        row = rows[name]
        comparison[name] = dict(k=row['k'], Q_upper=F(row['risk']['upper']),
            sufficient=row['sufficient'], core_upper=F(row['price']['core_upper']),
            note='Accepted result reused on byte-frozen common input; failed OFF upper is not exclusion')
    return dict(schema=1, scope='Conditional common-input core occupancy, including serialized codec/bus',
        unchanged=dict(W=W, T_s=T, epsilon=F(cfg['epsilon']), application='accepted cFE PR239',
                       baseline_environment_snapshot=cfg['environment']),
        information_basis=dict(candidate='uniform m0/mj replacing rho, with T119 geometry retained',
                               reference_rho_used_by_price=False, numerical_masses_supplied=False,
                               common_fixed_moments='same b/B/FS and parent law; independent of rho'),
        constants=dict(app39_lower=A, read39_lower_s=rminus, W_read_lower_s=W * rminus,
                       fast_pass_upper_s=ps, endpoint_span_s=J,
                       fixed44_upper=fixed_upper),
        geometry=dict(basis='T119 section2 and T196 priority-methods section3',
            permitted_relaxation='All positive P,w,h and arbitrary timer representation, while retaining T119 geometry',
            initial_FAST='H0 >= h_plus + tau >= h_minus >= w_minus > P_plus',
            minimum_h_minus_over_P_margin_s=ps_no_j + J,
            charged_duration_relaxation='min(P_plus,T), less than the actual initial FAST',
            lower_count='W*max(duration/Ps_plus-2,0)',
            combination='max(support_floor,startup_floor); never their sum',
            unchanged_rule_required=True),
        gate=result, competitors=comparison,
        unknown=dict(physical_Q=None, whole_hardware_gain=None,
                     weights='Nonnegative unknown CPU/energy/veto terms remain in accepted cFE cost vectors',
                     shorter_startup_Q=None),
        computations=dict(new_ERR_Q_calls=0, new_hold_price_calls=0, archive_rows_processed=0),
        provenance=dict(base=manifest['base_main'], plan_commit=manifest['plan_commit'],
                        frozen_files=len(manifest['sha256']), accepted_result_sha256=manifest['sha256'][ACCEPTED]))


def overview(result):
    g = result['gate']
    return dict(status=g['status'], period_min_h=float(g['support_period_min_h']),
                startup_max_min=float(g['startup_duration_max_min']),
                startup_lower_at_period_min=float(g['startup_at_period_min']),
                fixed44_upper=float(result['constants']['fixed44_upper']),
                necessary_price_passes=g['passes_necessary_price'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--probe', action='store_true')
    group.add_argument('--write', action='store_true')
    group.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = evaluate(); data = encoded(result); path = HERE / 'outputs/result.json'
    if args.write:
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
    if args.check and path.read_bytes() != data:
        raise AssertionError('Exact replay differs from committed result')
    print(json.dumps(dict(**overview(result), exact_replay=args.check), indent=2))


if __name__ == '__main__':
    main()

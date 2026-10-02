"""One offline command: pinned T80 pilot THEN its bounded full grid."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from fractions import Fraction as F
import gzip
import hashlib
import io
import itertools
import json
import lzma
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

from t80_engine import (HERE, CONFIG, FAMILY, SOURCE, MODES, source_check,
                        context, ident, short_gate, choose_monitor, t58, errors)
from t80_err import err_scan
from timing import tick_bounds, resources, minimum_resource_g, calculate


def decimal_text(x, upward=True, places=24):
    if not isinstance(x, F):
        return x
    scale = 10**places
    num = t58.ceil(x*scale) if upward else t58.floor(x*scale)
    sign = '-' if num < 0 else ''
    whole, frac = divmod(abs(num), scale)
    return f'{sign}{whole}.{frac:0{places}d}'


def json_write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                              default=lambda x: str(x) if isinstance(x, F) else x)+'\n', encoding='utf-8')


def csv_write(path, rows, fields=None):
    if fields is None:
        fields = list(dict.fromkeys(k for r in rows for k in r))
    raw = path.open('wb')
    binary = (lzma.LZMAFile(raw, mode='wb', preset=6) if path.suffix=='.xz' else
              gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) if path.suffix=='.gz' else raw)
    with io.TextIOWrapper(binary, encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            def down(k):
                return (any(s in k for s in ('lower','slack','safe','_min_','admissible','overhead_available')) or
                        k in ('mR','required_joint_upper_s','mu_required_upper') or
                        (k=='required' and row.get('parameter') in ('s_nom_upper_per_s','rho_e','joint_U_upper_s')))
            writer.writerow({k: decimal_text(row.get(k), upward=not down(k)) for k in fields})
    raw.close()


def contexts():
    return [context(v, m, a, si) for v in source_check()
            for a in ('internal38', 'external39') for m in CONFIG['margins'] for si in range(2)]


def fixed_row(p):
    # Reuse T72/T58 integer-period, resource and moment engines; full39 is
    # its own CONDITIONAL mark/load assumption, not a data32 multiplier.
    cfg = json.loads(json.dumps(p['cfg']))
    cfg['scenario']['n'] = p['n']
    v = calculate(cfg, p['env'])
    T, W = p['T'], p['W']
    # Recompute the arbitrary-phase witness with the NEW required J.
    tmin = W*p['cm']/(F('.01')+2*W*p['cp']/T)
    J = t58.floor(F(115776)/tmin)+2
    ell = (F(115776)-J*p['cp'])/(4*J)
    x = p['B']*ell/W
    exponent = 2*W*J*F(p['n']-1, 2*p['n'])*x*x*t58.exp_neg(x)[0]
    lower = t58.poisson_event(exponent)[0]-F(p['q']['delta_exec'])
    result = {k: v[k] for k in ('fixed_strong_M','fixed_risk_upper','fixed_risk_next_quantum',
                 'fixed_cost_lower','fixed_peak_upper','fixed_delay_upper_s','fixed_resource_ok')}
    return dict(**ident(p), **result, new_J=J, witness_lower=lower,
                full_block_occupied_assumption=True, physical_occupied_lower_s=None,
                witness_admissible=True,
                app_margin_pass=(1+p['margin'])*v['fixed_delay_upper_s']<=F('.000003'))


def short_repairs(p, mode):
    row = short_gate(p, mode)
    if row['short_pass']:
        return None
    # Largest c, with original channel envelope, permitting g <= risk gmax.
    # Repairs just the stated short gate; long risk/LOW must still be tested.
    import copy
    best = None
    for c in range(1, p['c']+1):
        cfg = copy.deepcopy(p['cfg'])
        cfg['service']['c_ticks'] = cfg['service']['fence_ticks'] = c
        rv = resources(cfg, row['g_max_short'])
        if rv['ok'] and (1+p['margin'])*rv['delay'] <= F('.000003'):
            best = (c, rv)
    if best is None:
        return dict(**ident(p), mode=mode, condition='short risk', value=row['short_risk_upper'],
                    sufficient_change='no c in declared lower bracket repairs risk/resource', price=None)
    c, rv = best
    return dict(**ident(p), mode=mode, condition='short risk without long term', value=row['short_risk_upper'],
                sufficient_change='joint_U_upper <= required bound, c <= stated c and g = gmax; only first gate repaired',
                required_c=c, required_g=row['g_max_short'],
                required_joint_upper_s=c*p['tm']/(1+p['margin']),
                all_short_tax_upper=c*p['tp']/(row['g_max_short']*p['tm'])+p['CX']+(2*c*p['tp']+p['sigmaX'])/p['T'],
                resulting_peak_upper=rv['peak'], resulting_delay_upper_s=rv['delay'],
                Dstar_unchanged=True, remaining='positive long-risk reserve, LOW, price and physical qualification')


GRID_FIELDS = ['context_id','kind','mode','qratio','rho_e','DQ','aM','w','d','status',
               'quiet_upper','returns_upper','risk_upper','ka','theta','z','k','mR','H',
               'mu_upper','pM_upper','lease_min_s','lease_slack_s','d_safe_upper_budget_s',
               'LOW_slack','next_k_slack_upper','aM_k0_sufficient','risk_slack',
               'base_tax','quiet_start_component','quiet_ERR_component','quiet_monitor_component',
               'quiet_global_component','channel_component','DM','DE','return_boundary','full_goal_pass']
GRID_FIELDS += ['kmax','next_odd_risk','threshold_trials','theta_trials']


def grid(out, ps, stage):
    from t80_report import hard_tax
    axes = SOURCE['pilot'] if stage=='pilot' else FAMILY
    ams = axes['a_M'] if stage=='pilot' else axes['channel_a_M']
    ws = axes['w_s'] if stage=='pilot' else axes['window_s']
    ds = axes['d_s'] if stage=='pilot' else axes['delivery_compute_s']
    counter, summaries = Counter(), []
    # All rejected tuples are retained. Very repetitive CSV is compressed
    # deterministically; no large raw file or random histories in git.
    def records():
        start = time.monotonic()
        for ci, p in enumerate(ps):
            for kind, mode, qr, rho, DQ in itertools.product(FAMILY['monitor_types'], MODES[:2],
                     FAMILY['q_R_over_bbar_separate_classes'], FAMILY['rho_e_per_s_separate_classes'],
                     FAMILY['D_Q_s_separate_classes']):
                best = None
                for am, w, d in itertools.product(ams, ws, ds):
                    result = choose_monitor(p, F(am), F(w), F(d), F(qr), F(rho), F(DQ), kind, mode)
                    row = dict(context_id=ci, kind=kind, mode=mode, qratio=qr, rho_e=rho, DQ=DQ,
                               aM=am, w=w, d=d, **result)
                    counter[row['status']] += 1
                    if row['status']=='certified_conditional':
                        if best is None or row['quiet_upper']<best['quiet_upper']:
                            best = row
                    yield row
                # Never minimize over environment classes; this summary
                # only compares the declared channel settings WITHIN one.
                summaries.append(dict(context_id=ci, kind=kind, mode=mode, qratio=qr, rho_e=rho, DQ=DQ,
                                      best_upper=None if best is None else best['quiet_upper'],
                                      best_certified_tax_upper=None if best is None else min(best['quiet_upper'],hard_tax(p)),
                                      best_aM=None if best is None else best['aM'],
                                      best_w=None if best is None else best['w'],
                                      best_d=None if best is None else best['d']))
            print(f'{stage}: context {ci+1}/{len(ps)} done, {time.monotonic()-start:.1f}s', flush=True)
    csv_write(out/(stage+'_grid.csv.xz'), records(), GRID_FIELDS)
    csv_write(out/(stage+'_classes.csv.xz'), summaries)
    result = dict(stage=stage, channel_combinations=len(ams)*len(ws)*len(ds),
                  rows=sum(counter.values()), counts=dict(counter), contexts=len(ps))
    json_write(out/(stage+'_summary.json'), result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['pilot','full','all'], default='all')
    parser.add_argument('--out', type=Path, default=HERE/'outputs/t80')
    parser.add_argument('--skip-tests', action='store_true', help='development only; recorded in protocol')
    args = parser.parse_args()
    out = args.out.resolve()
    if not out.is_relative_to(HERE):
        raise ValueError('Outputs must remain inside T82')
    out.mkdir(parents=True, exist_ok=True)
    ps = contexts()
    json_write(out/'contexts.json', [dict(context_id=i, **{k:v for k,v in p.items() if k not in ('cfg','env')}) for i,p in enumerate(ps)])
    csv_write(out/'short_gate.csv', [short_gate(p, mode) for p in ps for mode in MODES])
    csv_write(out/'short_repairs.csv', [r for p in ps for mode in MODES if (r:=short_repairs(p,mode))])
    csv_write(out/'fixed_comparator.csv', [fixed_row(p) for p in ps])
    stages = []
    if args.phase in ('pilot','all'):
        stages.append(grid(out, ps, 'pilot'))
        err_rows, err_best = [], []
        for i, p in enumerate(ps):
            rows, best = err_scan(p)
            err_rows.extend(dict(context_id=i, **r) for r in rows)
            err_best.append(dict(context_id=i, **ident(p), **(best or {'status':'short_risk_or_no_ERR_certificate'})))
            print(f'ERR-only: context {i+1}/{len(ps)} done', flush=True)
        csv_write(out/'ERR_grid.csv.xz', err_rows)
        csv_write(out/'ERR_best.csv', err_best)
    if args.phase in ('full','all'):
        if not (out/'pilot_summary.json').exists() or not (out/'ERR_best.csv').exists():
            raise ValueError('Run and preserve pilot before full grid')
        stages.append(grid(out, ps, 'full'))
    from t80_report import build
    build(out,ps,csv_write,json_write)
    json_write(out/'protocol.json', dict(theory_sha=CONFIG['theory_sha'], architecture_sha=CONFIG['architecture_sha'],
        preregistration_sha='eec2120328aedfe2d12fb50f521805e5194bb54c', python=platform.python_version(),
        stages=stages, tests_skipped=args.skip_tests, physical_qualification=False,
        quantity_semantics='directed formula upper/lower bounds, not physical confidence intervals; requirements rounded to safe side',
        formula_versions_unchanged=True,
        hashes={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                sorted(HERE.glob('t80*.py'))+sorted(HERE.glob('run_t80.py'))+[HERE/'t80_config.json',HERE/'T80_METHOD.md']}))
    if not args.skip_tests:
        result = subprocess.run([sys.executable,'-X','utf8','-B','-m','unittest','discover',
                                 '-s',str(HERE),'-p','test_t80*.py','-v'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/'tests.log').write_text(result.stdout,encoding='utf-8')
        if result.returncode or 'Ran 0 tests' in result.stdout or '\nOK' not in result.stdout:
            raise RuntimeError('Missing/pending/failed tests; see tests.log')
        from t80_validate import independent_checks
        checks=independent_checks(out,ps)
        json_write(out/'independent_checks.json',checks)
        protocol=json.loads((out/'protocol.json').read_text())
        protocol.update(unit_tests_passed=int(re.search(r'Ran (\d+) tests',result.stdout).group(1)),
                        independent_points=checks['points'])
        json_write(out/'protocol.json',protocol)
    print(json.dumps(stages, ensure_ascii=False), flush=True)


if __name__=='__main__':
    main()

"""Offline one-command T82 early-stage delivery. Never runs GOES or RTL."""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

from timing import (HERE, ROOT, T72, bounds, evaluate_old, old_channel_diagnostics,
                    load_config, inputs, retime, calculate, err_only_fallback)
from independent import check


def printable(value, key=''):
    if isinstance(value, F):
        lower = ('lower' in key or 'slack' in key or 'available_min' in key or
                 key == 'admissible_upper_s')
        return bounds(value)[0 if lower else 1]
    return value


def csvout(path, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows({k: printable(v, k) for k, v in row.items()} for row in rows)


def jsonout(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def figures(out, rows, channel):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({'svg.hashsalt': 't82-early-v1', 'font.size': 10,
                                'axes.spines.top': False, 'axes.spines.right': False})
    labels = ['T73', 'T72 extended', 'T72 revision 1', 'T72 revision 2']
    names = [v['set'] for v in inputs()]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), layout='constrained')
    colors = ['#0072B2', '#D55E00', '#009E73', '#CC79A7']
    for i, (name, label, color) in enumerate(zip(names, labels, colors)):
        for shield, style in [('2.5', '-'), ('3', '--')]:
            selected = sorted([r for r in rows if r['set'] == name and r['shield_g_cm2'] == shield and
                               r['stage'] == 'retimed_all_deadlines_g' and r['architecture'].startswith('internal')],
                              key=lambda r: F(r['margin']))
            x = [float(F(r['margin'])*100) for r in selected]
            axes[0].plot(x, [float(r['risk_upper'])*1000 for r in selected], style+'o', color=color,
                         label=f'{label}, {shield}')
            axes[1].plot(x, [float(r['quiet_returns_upper'])*100 for r in selected], style+'o', color=color)
    axes[0].axhline(1, color='black', lw=1, label='risk / tax limits')
    axes[1].axhline(1, color='black', lw=1)
    for ax in axes:
        ax.set(xlabel='Nominal-basis design margin (%)', xticks=[5, 10], xlim=(4.5, 10.5))
        ax.grid(alpha=.2)
    axes[0].set(ylabel='Risk formula (8) value (×10⁻³)', title='Some certificate tests fail: see CSV')
    axes[1].set(ylabel='Return-tax formula upper (%)', title='Not a qualified implementation')
    axes[0].legend(fontsize=8, ncol=2, loc='best')
    fig.suptitle('Old T73 certificate replay — not new-method optimized curves', fontsize=12)
    fig.savefig(out/'timing_replay.png', dpi=180, metadata={'Software': 'T82'})
    fig.savefig(out/'timing_replay.svg', metadata={'Date': None})
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.5, 3.8), layout='constrained')
    x = range(4)
    limits = [float(next(r for r in channel if r['set'] == n)['positive_LOW_requires_lease_below_s']) for n in names]
    ax.bar(x, limits, color='#0072B2', label='Old LOW: lease must be below this bound')
    ax.axhline(8, color='#D55E00', label='IREM: 8 s broadcast gap alone')
    ax.axhline(200, color='#009E73', label='REM: 2 × 100 s integration, even d=0')
    ax.set(yscale='log', ylim=(1, 300), xticks=list(x), xticklabels=labels, ylabel='Seconds',
           title='Timing obstruction for old LOW — independent of increasing a_M')
    ax.legend(fontsize=8, loc='upper center')
    ax.grid(axis='y', alpha=.2)
    fig.savefig(out/'channel_window_obstruction.png', dpi=180, metadata={'Software': 'T82'})
    fig.savefig(out/'channel_window_obstruction.svg', metadata={'Date': None})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE/'outputs')
    args = parser.parse_args()
    out = args.out.resolve()
    if not out.is_relative_to(HERE):
        raise ValueError('T82 outputs must stay inside the T82 directory')
    out.mkdir(parents=True, exist_ok=True)
    config = load_config()
    if config['new_theory_80_sha'] is not None or config['new_method_grid'] is not None:
        raise ValueError('New theory requires an explicitly reviewed adapter, not silent old-formula reuse')
    # Re-run existing T73 tests, including full-W phase edges, not the GOES pipeline.
    commands = [
        [sys.executable, '-X', 'utf8', '-B', '-m', 'unittest', 'discover', '-s', str(T72), '-p', 'test_t73*.py', '-v'],
        [sys.executable, '-X', 'utf8', '-B', '-m', 'unittest', 'discover', '-s', str(HERE), '-p', 'test_t82.py', '-v'],
    ]
    with (out/'tests.log').open('w', encoding='utf-8') as log:
        for command, expected in zip(commands, [21, 10], strict=True):
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    cwd=ROOT, text=True, encoding='utf-8')
            log.write(result.stdout)
            log.flush()
            if result.returncode:
                raise RuntimeError('Tests failed; see '+str(out/'tests.log'))
            if re.search(r'Ran '+str(expected)+r' tests in .*?\n\nOK', result.stdout) is None:
                raise RuntimeError('Missing completed test protocol; see '+str(out/'tests.log'))
    rows, directed, margins, expanded, fixed, edges = evaluate_old()
    csvout(out/'replay.csv', rows)
    csvout(out/'timing_margins.csv', margins)
    csvout(out/'fixed_comparator.csv', fixed)
    csvout(out/'resource_boundaries.csv', edges)
    for row in directed:
        value = row.pop('value')
        row['lower'], row['upper'] = (str(value), str(value)) if isinstance(value, bool) else bounds(value)
    csvout(out/'directed_bounds.csv', directed)
    jsonout(out/'expanded_inputs.json', dict(accepted_theory_sha=config['accepted_theory_sha'], variants=expanded))
    independent = []
    for variant in inputs():
        for margin in config['margins']:
            cfg = retime(variant['input'], margin, 'internal38_nominal_projection', True, True)
            for env in cfg['environments']:
                v = calculate(cfg, env)
                independent.append(dict(set=variant['set'], margin=margin,
                                        shield_g_cm2=env['shield_g_cm2'], **check(cfg, env, v)))
    jsonout(out/'independent_checks.json', independent)
    channel, hypotheses = old_channel_diagnostics()
    csvout(out/'channel_timing.csv', channel)
    csvout(out/'count_hypotheses.csv', hypotheses)
    csvout(out/'ERR_only_old_fallback.csv', err_only_fallback())
    # These cells are intentionally absent, not zeros or interpolated curves.
    csvout(out/'pending_curves.csv', [dict(mode=mode, best_certified_tax=None,
        status='pending_agreed_80_SHA', reason='new_model_and_bounded_grid_not_received')
        for mode in ['ERR+monitor', 'ERR-only', 'monitor-only']])
    figures(out, rows, channel)
    dependencies = [T72/'verify_t73.py', T72/'confirm_t73_sync.py', T72/'t73_calendar.py',
                    T72/'t73_resources.py', HERE.parent/'t58-fixed-baseline-r0b/certificate.py',
                    ROOT/'theory/t73-burst-mode-count-inputs.json', HERE/'config.json', HERE/'METHOD.md',
                    HERE/'monitor_profiles.json', HERE/'CHANNEL.md']
    own = sorted(HERE.glob('*.py'))
    jsonout(out/'protocol.json', dict(base_sha=config['base_sha'], accepted_theory_sha=config['accepted_theory_sha'],
        new_theory_80_sha=None, architecture_81_sha=config['architecture_81_sha'], python=platform.python_version(),
        stage='early_independent_timing_and_documented_channel_audit', replay_rows=len(rows),
        margin_rows=len(margins), directed_metrics=len(directed), independent_points=len(independent),
        resource_boundaries=len(edges), unit_tests_passed=31, previous_tests=21, new_tests=10,
        source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies+own},
        physical_qualification=False, new_method_grid_run=False, GOES_processed=False, RTL_run=False,
        caveat='formula bounds are not physical confidence intervals; external39 risk is not evaluated'))
    print(f'T82: {len(rows)} replay rows, {len(margins)} timing rows, {len(independent)} independently checked points.')
    print('New-method grid NOT RUN: agreed #80 SHA is absent. Physical qualification NOT ESTABLISHED.')


if __name__ == '__main__':
    main()

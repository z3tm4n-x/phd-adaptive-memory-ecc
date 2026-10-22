"""Addressed author-applicability checks; not an independent full review.

Read a selective exact PR211 checkout. Does not change source/output files.
Recompute every stored q-cell coefficient, not the old T119 anchor alone.
The weak-E witness refutes the one-parent/one-repair charging lemma, not Q.
"""
import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
import sys


def fractions(value):
    if isinstance(value, dict):
        return {k: fractions(v) for k, v in value.items()}
    if isinstance(value, list):
        return [fractions(v) for v in value]
    if isinstance(value, str):
        try:
            return F(value)
        except ValueError:
            pass
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('snapshot', type=Path)
    args = parser.parse_args()
    root = args.snapshot.resolve()
    here = Path(__file__).resolve().parent
    manifest = json.loads((here / 'versions.json').read_text())
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    for entry in manifest['files']:
        raw = (root / entry['path']).read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        check('git blob ' + entry['path'], blob == entry['git_blob'])
    package = root / 'experiments/t186-method-comparison/code-strength'
    raw = (package / 'common-input.json').read_bytes()
    check('exact v4 input SHA256', hashlib.sha256(raw).hexdigest() == manifest['input_sha256'])
    cfg = json.loads(raw)
    info = fractions(json.loads((package / 'outputs/informational.json').read_text()))
    result = fractions(json.loads((package / 'outputs/results.json').read_text()))
    sys.path.insert(0, str(package))
    from informational import calendar, coefficient
    from comparison import period, service, risk, read_bounds, count_apps, NS, timing
    from codec import Code
    from parents import projected_groups, witness_coefficients
    from cost import per_bit_moment_caps

    W = cfg['words']
    factor = F(39, 152)
    cell_counts = {}
    phase_counts = {}
    for row in info['candidates']:
        k = row['k']
        c, env, ma = row['calendar'], row['environment'], row['majorant']
        check(f'k{k} exact new calendar', calendar(cfg, k) == c)
        check(f'k{k} shared nu ell scale', env['rate_scale'] == factor and
              all(env[x] == factor * F(cfg['environment'][y]) for x, y in
                  [('b', 'reference_background_per_s'), ('B', 'reference_peak_per_s'),
                   ('FS', 'reference_solar_mass'), ('ell', 'reference_growth_threshold_per_s')]))
        check(f'k{k} full-word lower channel', c['phi'] == 1 - F(1, W) and
              env['lower_channel_a'] == 1 and env['multiword_fraction'] == 0)
        check(f'k{k} protected/PAIR/NR bounds', c['w'] == min(c['short_timer']['lower'], c['source_PAIR']['lower'])
              and c['protected_window'] >= c['Pl'] + c['Ps'] + c['d']
              and c['h'] >= c['w'] > c['tau']
              and c['recovery']['lower'] >= c['long_timer']['upper'] + c['tau'])
        check(f'k{k} integer timer capacities',
              all(c[x]['count'] < 2**34 for x in ('short_timer', 'long_timer', 'recovery'))
              and c['source_PAIR']['count'] < 2**64)
        M = cfg['adaptive']['information_numeric']['phase_cells']
        ratio = c['TP'] / c['TM']
        excess = (F(W, k*M)*(ratio-1) + F(7*(c['g']-c['c']), k*c['g'])*ratio
                  + 2 + 2*c['J']/(k*c['g']*c['TM']))
        check(f'k{k} analytic four-word discrepancy', excess < 4)
        phases = [k*c['g']*r + (c['c']-c['g'])*(k*r % 8) for r in range(W)]
        check(f'k{k} inverse-address permutation',
              all((k*r*c['inverse_address']) % W == r for r in range(W)))
        circ = phases + [x + k*W*c['g'] for x in phases]
        end, count = 0, 0
        for start in range(W):
            while end < start+W and M*(circ[end]-circ[start]) <= W*c['g']:
                end += 1
            count = max(count, end-start)
        check(f'k{k} cyclic exact phase count', count <= F(W, k*M)+4)
        phase_counts[str(k)] = {'maximum_words': count, 'analytic_excess': excess}
        cells = ma['cells']
        check(f'k{k} entire q domain', cells[0]['lo'] == env['b'] and cells[-1]['hi'] == env['B']
              and all(a['hi'] == b['lo'] for a, b in zip(cells, cells[1:])))
        check(f'k{k} q below background', ma['u'] >= c['Pl']*env['b']**2)
        for i, cell in enumerate(cells):
            lo, hi, K = cell['lo'], cell['hi'], cell['K_upper']
            check(f'k{k} cell{i} directed K', coefficient(lo, env['rho'], env['ell'], c, M) == K)
            # Exact analytic K is nonincreasing (lower cone masses increase).
            # On [lo,hi], L(q)-K(lo)*q^2 is concave, so endpoints suffice.
            left = ma['u'] + ma['v']*(lo-env['b']) - K*lo*lo
            right = ma['u'] + ma['v']*(hi-env['b']) - K*hi*hi
            check(f'k{k} cell{i} whole-cell enclosure', K >= 0 and lo < hi and
                  left == cell['left_slack'] >= 0 and right == cell['right_slack'] >= 0)
        J = min(c['Pl']*env['S2'], ma['u']*env['T'] + ma['v']*env['FS'])
        beta = F(1, 2*W)
        d = service(cfg, 39)['upper']['E']/NS
        X1 = beta*(k*d+c['Pl']/W)*env['S2']
        v = 2*beta*d*(env['T']/c['Ps_min']+1)
        X2 = min(env['B']*c['Pl'], env['F'])*min(env['B']*v,
             env['b']*v+2*beta*env['FS']/W, 2*beta*env['F']/W)
        expected = F(cfg['lifetime_other_budget']) + beta*J + min(X1, X2)
        check(f'k{k} lifetime Q components', expected == row['risk']['upper'] and
              ma['integral'] == J and row['risk']['coupling_beta'] == beta)
        cell_counts[str(k)] = len(cells)
        print(json.dumps({'progress_k': k, 'cells': len(cells)}), file=sys.stderr, flush=True)

    rows = result['rows']
    m = per_bit_moment_caps(cfg)
    check('selected greatest registered k', info['selected']['k'] == max(r['k'] for r in info['candidates']
          if r['risk']['upper'] <= F(cfg['epsilon'])/2) == 27)
    check('main adaptive uses the checked certificate', rows['t1_adaptive']['risk'] == info['selected']['risk'])
    for name in ('t1_constant', 't2_constant'):
        row = rows[name]
        n, t, k = row['n'], row['t'], row['k_passes']
        P = period(cfg, k)['upper_ns']/NS
        d = service(cfg, n)['upper']['E']/NS
        a2 = F(n*(n-1), 2) if t == 1 else F(0)
        a3 = F(n*(n-1)*(n-2), 6) if t == 2 else F(0)
        expected = F(cfg['lifetime_other_budget']) + W*(a2*P*m['M2']+a3*P*P*m['M3']
                   + 2*a2*m['peak_per_bit']*d*m['M1']
                   + 3*a3*(m['peak_per_bit']*d*P*m['M2']+m['peak_per_bit']**2*d*d*m['M1']))
        check(name+' independent singleton moment/E substitution', expected == row['risk']['upper'])
        check(name+' selected sufficient grid point', expected <= F(cfg['epsilon'])/2 <
              risk(cfg, n, t, period(cfg, k+1)['upper_ns'], d*NS)['upper'])
    # Algebra of mixed/direct cells, not a new mixture information theorem.
    for n, t in ((39, 1), (44, 2)):
        for p2 in (F(0), F(1, 10**7)):
            for p3 in (F(0), F(1, 10**8)):
                lam = projected_groups(n, {1: 1-p2-p3, 2: p2, 3: p3})
                a = witness_coefficients(n, t, lam)
                x, y = lam[1], lam[2]
                quad = F(n-1, 2*n)*x*x if t == 1 else F(n-2,n)*x*y + (1-F(2,n*(n-1)))*y*y/2
                cubic = F(0) if t == 1 else F((n-1)*(n-2), 6*n*n)*x**3
                check(f'projected group cells {n} {p2} {p3}', a['quadratic'] == quad and
                      a['cubic'] == cubic and a['linear_direct'] == sum(lam[t+1:]))

    # A weak-E counterexample within the new n39 services/calendars.
    # Choose a word whose full-write application first occurs after both E's.
    witnesses = []
    for mode, k in [('fixed', 11), ('adaptive', 27)]:
        j = 1
        word = 3 if mode == 'fixed' else pow(k, -1, W)
        start0 = 164
        start1 = start0 + W*196*(k if mode == 'fixed' else 1)
        appq = word*pow(5, -1, W) % W
        appstart = 100000+500000+appq*1000020
        check(mode+' witness respects application', appstart > start1+125)
        code = Code(1)
        clean = code.encode(0x13579bdf)
        error_birth = start0+1
        live = {0: error_birth}
        repairs, publications = 0, 0
        trace = []
        for start in (start0, start1):
            snapshot = clean ^ sum(1 << b for b in live)
            decoded = code.decode(snapshot)
            repairs += int(decoded['ERR'])
            publications += int(decoded['ERR'])
            live = {b: born for b, born in live.items() if born >= start}
            trace.append({'start_ns': start, 'snapshot_ns': start+48,
                          'release_ns': start+service(cfg,39)['nominal']['E'],
                          'ERR': decoded['ERR'], 'survivors': len(live)})
        check(mode+' weak-E one-parent two-repair witness', repairs == publications == 2 and not live)
        witnesses.append(dict(mode=mode, word=word, first_app_write_ns=appstart,
            parent_ns=error_birth, parents=1, repairs=repairs, publications=publications,
            max_error_weight=1, bad_history=False, trace=trace))

    # Minimal universally safe local repair: double the parent repair budget.
    # Read/hold upper already uses two publications; no change to Q or timers.
    corrected = {}
    for name, row in rows.items():
        cost = row['cost']; n = row['n']; k = row['k_passes']
        hard = read_bounds(cfg, 1 if name == 't1_adaptive' else k)['upper']
        old = cost['repair_count_upper']
        new = min(cost['read_count_upper'], 2*cost['expected_parent_count_upper']+row['risk']['upper']*hard)
        delta = (new-old)*(service(cfg,n)['upper']['E']-service(cfg,n)['upper']['R'])/(cfg['mission_s']*NS)
        corrected[name] = dict(old_repair_upper=old, safe_repair_upper=new,
                              SRAM_addition=delta, safe_SRAM_upper=cost['core_SRAM_fraction_upper']+delta)
        check(name+' original timing calculation', timing(cfg, n, k) == row['timing'])
    a = rows['t1_adaptive']['cost']; f = rows['t1_constant']['cost']; two = rows['t2_constant']['cost']
    check('robust t2 comparison needs no disputed repair lemma',
          two['all_history_SRAM_core_upper'] < a['core_SRAM_fraction_lower'])
    check('minimal repair preserves adaptive vs selected fixed',
          corrected['t1_adaptive']['safe_SRAM_upper'] < f['core_SRAM_fraction_lower'])
    gap = f['core_SRAM_fraction_lower'] - corrected['t1_adaptive']['safe_SRAM_upper']
    v_bound = gap/a['veto_core_fraction_slope_per_notification_per_s']
    check('conservative veto threshold 1057 per second remains valid', v_bound > 1057)
    # Fixed-t2 can alternatively retain one-parent repair: deterministic app
    # visits remove all old births between consecutive scrub starts.
    app_revisit = W*cfg['application']['epoch_ns'] + cfg['constraints']['application_deadline_ns']
    fixed2_gap = period(cfg,rows['t2_constant']['k_passes'])['lower_ns']
    check('t2 app intervenes between scrub visits', app_revisit+service(cfg,44)['upper']['E'] < fixed2_gap)
    output = dict(reviewed_head=manifest['reviewed_head'], input_sha256=manifest['input_sha256'],
        scope='addressed coauthor applicability, not independent acceptance',
        check_count=len(checks), checks=checks, verified_files=len(manifest['files']),
        cell_counts=cell_counts, total_q_cells=sum(cell_counts.values()), phase_counts=phase_counts,
        phase_words=W*len(info['candidates']), risk={name: row['risk'] for name,row in rows.items()},
        repair_witnesses=witnesses, minimal_safe_repair=corrected,
        safe_extra_veto_threshold_per_s=v_bound,
        robust_t2_hard_comparison_gap=a['core_SRAM_fraction_lower']-two['all_history_SRAM_core_upper'],
        full_engineering_203_suite_repeated=False, accepted_codec_suite_repeated=False)
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True, default=str))


if __name__ == '__main__':
    main()

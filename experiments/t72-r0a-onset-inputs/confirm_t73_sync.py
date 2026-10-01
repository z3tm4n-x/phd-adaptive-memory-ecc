"""Addressed, offline confirmation of T73 3ad0462, appendix Ж.3.

The four inputs are expanded from the NEW JSON, not reconstructed from the
old report. Exact-rational computations reuse verify_t73/T58. Old evidence
is read-only. All displayed intervals enclose formula values, not physical
confidence intervals. No raw GOES data are opened by this command.
"""
from __future__ import annotations

import argparse
import copy
import csv
from fractions import Fraction as F
import hashlib
import json
from math import gcd
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile

from verify_t73 import HERE, bounds, calculate, t58

THEORY_SHA = '3ad0462eac34d47176a6e1b36052855114a508df'
PARENT_ENGINEER_SHA = '426704a12cffddf01463ef11a21c1eaa20baee05'
SOURCE = HERE / 'inputs/t73_3ad0462'
STEMS = ['t73-burst-mode-count.md', 't73-burst-mode-count-appendix.md',
         't73-burst-mode-count-inputs.json']
SOURCE_HASHES = {
    STEMS[0]: ('d2e02860491870e138fb02ebc27814073fb006b777dc756642d2453bf116c121',
               'cd2876f7f6b86c6875156dbdf843c1c370eced47'),
    STEMS[1]: ('9fd2453087b9783d50f6cf43dadcd30b7acc703435a034c2dcb82b5e61314364',
               '9a1a2bab81cf0b69ee0d8e8931cf855be5a4e18c'),
    STEMS[2]: ('1ee101815fd7f388213a4c69e8aaac9ff5c36eca6ce3b42560e917a3ddbfbc20',
               '1f57e163b9d7afab4f5361b3436f54c4193b1cc7'),
}
SETS = ['T73_published', 'T72_budgets_explicit_T73_extension',
        'T72_explicit_same_method_revision', 'T72_revision_shorter_return_hold']


def require(condition, context):
    if not condition:
        raise AssertionError(context)


def source_check():
    result = {}
    for name, (sha256, blob) in SOURCE_HASHES.items():
        data = (SOURCE / name).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        git_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        require((actual, git_blob) == (sha256, blob), 'source bytes: ' + name)
        result[name] = dict(sha256=actual, git_blob=git_blob, bytes=len(data))
    return result


def read_new():
    return json.loads((SOURCE / STEMS[2]).read_text(encoding='utf-8'))


def merge(base, override):
    """Recursive object merge; lists/scalars replaced, no in-place mutation."""
    if isinstance(base, dict) and isinstance(override, dict):
        result = copy.deepcopy(base)
        for key, value in override.items():
            result[key] = merge(result.get(key), value)
        return result
    return copy.deepcopy(override)


def expand(doc):
    core = {k: doc[k] for k in doc['synchronization']['core_input_fields']}
    rows = []
    for variant in doc['variant_definitions']:
        require(variant['base'] == 'root core_input_fields', 'variant base')
        rows.append(dict(set=variant['set'], status=variant['status'],
                         input=merge(core, variant['overrides'])))
    require([r['set'] for r in rows] == SETS, 'four independent variants/order')
    return rows


def leaves(value, prefix=''):
    if isinstance(value, dict):
        for key, sub in value.items():
            yield from leaves(sub, prefix + '.' + key if prefix else key)
    elif isinstance(value, list):
        for i, sub in enumerate(value):
            yield from leaves(sub, f'{prefix}[{i}]')
    else:
        yield prefix, value


def compare_inputs(doc, expanded):
    old = json.loads((HERE / 'outputs/t73_checked_inputs.json').read_text())
    original = json.loads((HERE / 'inputs/t73_7ed0f6c.json').read_text())
    sync = doc['synchronization']
    require(sync['source_engineer_sha'] == PARENT_ENGINEER_SHA, 'engineer parent')
    require(hashlib.sha256((HERE / 'inputs/t73_7ed0f6c.json').read_bytes()).hexdigest()
            == sync['source_original_json_sha256'], 'original JSON hash')
    for key in sync['core_input_fields']:
        require(doc[key] == original[key], 'original root core: ' + key)
    prior = {r['set']: r['input'] for r in old['variants']}
    rows, changed = [], []
    for variant in expanded:
        name = variant['set']
        for block in sync['core_input_fields']:
            before = dict(leaves(prior[name][block], block))
            after = dict(leaves(variant['input'][block], block))
            require(before.keys() == after.keys(), (name, block, 'field coverage'))
            for path, value in after.items():
                same = type(value) is type(before[path]) and value == before[path]
                if not same:
                    changed.append((name, path, before[path], value))
                rows.append(dict(set=name, field=path, previous=before[path], current=value,
                                 status='same' if same else 'descriptive_129_to_85'))
    expected = [(name, 'service.mandatory_slots', 'j divisible by 129', 'j divisible by 85')
                for name in SETS[2:]]
    require(changed == expected, ('unexpected input change', changed))
    return rows


def directed(value):
    if isinstance(value, bool):
        return [str(value), str(value)]
    lo, hi = bounds(value)
    require(F(lo) <= value <= F(hi), 'decimal rounding enclosure')
    return [lo, hi]


def evaluate(doc, expanded):
    with (HERE / 'outputs/t73_directed_bounds.csv').open() as handle:
        old = {(r['set'], r['shield_g_cm2'], r['metric']): [r['lower'], r['upper']]
               for r in csv.DictReader(handle)}
    with (HERE / 'outputs/t73_summary.csv').open() as handle:
        old_summary = {(r['set'], r['shield_g_cm2']): r for r in csv.DictReader(handle)}
    copied = {(r['set'], r['shield_g_cm2']): r for r in doc['verified_results']}
    require(len(copied) == len(doc['verified_results']) == 8, 'eight unique JSON result rows')
    rows, summaries, exact, keys = [], [], {}, set()
    for variant in expanded:
        name, cfg = variant['set'], variant['input']
        for env in cfg['environments']:
            shield = env['shield_g_cm2']
            v = calculate(cfg, env)
            exact[name, shield] = v
            for metric, value in v.items():
                lo, hi = directed(value)
                key = (name, shield, metric)
                keys.add(key)
                require(old[key] == [lo, hi], ('numerical regression', key, old[key], [lo, hi]))
                rows.append(dict(set=name, shield_g_cm2=shield, metric=metric, lower=lo, upper=hi,
                                 theory_sha=THEORY_SHA))
            for metric, interval in copied[name, shield]['directed_formula_bounds'].items():
                require(directed(v[metric]) == [interval['lower'], interval['upper']],
                        ('new JSON directed result', name, shield, metric))
            summary = dict(set=name, shield_g_cm2=shield)
            for metric in old_summary[name, shield]:
                if metric in summary:
                    continue
                value = v[metric]
                summary[metric] = value if isinstance(value, bool) else directed(value)[
                    0 if metric.endswith('_lower') else 1]
                require(summary[metric] == copied[name, shield][metric],
                        ('new JSON summary', name, shield, metric))
                require(str(summary[metric]) == old_summary[name, shield][metric], 'old summary')
            summaries.append(summary)
    require(keys == set(old), 'all previous numerical metrics retained')
    return exact, rows, summaries


def paired_edge(N, c, M):
    """Exact extrema at every floor-phase start/end; no time discretization.

    D(t)=occupied(t)-N*2c*t/M is linear between these breakpoints and
    periodic. Its oscillation bounds EVERY real window, including windows
    spanning arbitrarily many periods. Numerators below have denominator M.
    This check uses actual full-block occupancy, NOT an upper-only WCET.
    """
    d = 2*c
    require(N > 0 and c > 0 and M//N >= d, 'paired nonoverlap')
    low, high, min_gap = 0, 0, M
    for i in range(N):
        start = i*M//N
        end = start+d
        following = (i+1)*M//N
        min_gap = min(min_gap, following-start)
        low = min(low, i*d*M-N*d*start)
        high = max(high, (i+1)*d*M-N*d*end)
    # Independent closed form from residues i*M mod N.
    formula_max = d*(M-N*d+N-gcd(N, M))
    require(low == 0 and high == formula_max, 'prefix extrema / residue formula')
    require(high-low <= d*M, '2c oscillation edge')
    return dict(N=N, c_ticks=c, M=M, breakpoints_checked=2*N,
                min_frame_gap_ticks=min_gap, prefix_min_numerator=low,
                prefix_max_numerator=high, denominator=M, allowed_oscillation_numerator=d*M,
                arbitrary_real_window_edge_ticks=d)


def full_paired_checks(expanded, exact):
    rows = []
    for variant in expanded:
        name, cfg = variant['set'], variant['input']
        s = cfg['service']
        for env in cfg['environments']:
            shield = env['shield_g_cm2']
            v = exact[name, shield]
            result = paired_edge(cfg['scenario']['W']//2, s['c_ticks'], int(v['fixed_strong_M']))
            gap = result['min_frame_gap_ticks'] * F(s['constant_clock_scale_min'])
            width = 2*s['c_ticks'] * F(s['constant_clock_scale_max'])
            require(gap >= width, 'robust interframe gap')
            rows.append(dict(set=name, shield_g_cm2=shield, **result,
                             robust_gap_margin_ticks=str(gap-width)))
    return rows


def table(text, header_fragment):
    lines = text.splitlines()
    hits = [i for i, line in enumerate(lines) if line.startswith('|') and header_fragment in line]
    require(len(hits) == 1, ('unique table', header_fragment))
    rows = []
    for line in lines[hits[0]+2:]:
        if not line.startswith('|'):
            break
        rows.append([x.strip().replace('**', '') for x in line.strip('|').split('|')])
    return rows


def text_claims(exact):
    """Check the synchronized tables against fresh formulas, including direction."""
    main = (SOURCE / STEMS[0]).read_text()
    appendix = (SOURCE / STEMS[1]).read_text()
    claims = []
    aliases = {'T73': SETS[:1], 'T72 расширенный': SETS[1:2],
               'T72, рев. 1': SETS[2:3], 'T72, рев. 2': SETS[3:],
               'T72, обе ревизии': SETS[2:], 'T72, все три': SETS[1:]}

    def check(location, name, shield, metric, printed, direction, scale=1):
        value = exact[name, shield][metric]*scale
        claim = F(printed.replace(',', '.'))
        ok = {'upper': value <= claim, 'lower': value >= claim, 'exact': value == claim}[direction]
        require(ok, ('text direction', location, name, shield, metric, printed, bounds(value)))
        lo, hi = bounds(value)
        claims.append(dict(location=location, set=name, shield_g_cm2=shield, metric=metric,
                           scale=scale, printed=printed, direction=direction,
                           formula_lower=lo, formula_upper=hi, pass_check=ok))

    specifications = [
        ('main §6', main, 'Налог за тихий срок',
         [('risk_upper', 'upper', 1), ('quiet_mission_upper', 'upper', 100),
          ('quiet_returns_upper', 'upper', 100), ('fixed_cost_lower', 'lower', 100)]),
        ('Д.5', appendix, 'Подготовленные 24 ч',
         [('risk_upper', 'upper', 1), ('quiet_mission_upper', 'upper', 100),
          ('quiet_24h_prepared_upper', 'upper', 100), ('quiet_returns_upper', 'upper', 100)]),
        ('Е.1 period/price', appendix, '$M$, тактов',
         [('fixed_strong_M', 'exact', 1), ('fixed_period_upper_s', 'exact', 1),
          ('fixed_cost_lower', 'lower', 100)]),
        ('Е.1 M/M+1', appendix, '$U_F(M',
         [('fixed_risk_upper', 'upper', 1), ('fixed_risk_next_quantum', 'lower', 1)]),
    ]
    for location, text, header, metrics in specifications:
        for row in table(text, header):
            alias, shield = row[0].split(' / ')
            shield = shield.replace(',', '.')
            require(len(row) == len(metrics)+1, ('table columns', location))
            for name in aliases[alias]:
                for printed, (metric, direction, scale) in zip(row[1:], metrics):
                    check(location, name, shield, metric, printed, direction, scale)
    for row, names in zip(table(appendix, 'Сервис |'), [SETS[:2], SETS[2:]], strict=True):
        lower, upper = row[1].strip('[]').split('; ')
        for name in names:
            for shield in ['2.5', '3']:
                check('Е.2 tau_min_any', name, shield, 'E3_arbitrary_phase_tau_min_s', lower, 'lower')
                check('Е.2 tau_min_any', name, shield, 'E3_arbitrary_phase_tau_min_s', upper, 'upper')
                check('Е.2 J0', name, shield, 'E3_arbitrary_phase_J_required', row[2], 'exact')
    for row, names in zip(table(appendix, 'Набор / сервис'), [SETS[:1], SETS[1:2], SETS[2:]], strict=True):
        for name in names:
            for shield, printed in zip(['2.5', '3'], row[1:], strict=True):
                check('Е.2 witness risk', name, shield, 'E3_risk_lower', printed, 'lower')
    # Prose resource values in Е.1: require literal presence before checking.
    for names, peaks, delays in [
        (SETS[:1], ['65,478055', '32,647527'], ['0.472195', '0.303851']),
        (SETS[1:2], ['70,535361', '35,172952'], ['0.599215', '0.308094']),
        (SETS[2:], ['69,764554', '34,788548'], ['0.575021', '0.305549']),
    ]:
        for name in names:
            for shield, peak, delay in zip(['2.5', '3'], peaks, delays, strict=True):
                require(peak in appendix and delay in appendix, 'resource text claim presence')
                check('Е.1 peak percent', name, shield, 'fixed_peak_upper', peak, 'upper', 100)
                check('Е.1 delay microseconds', name, shield, 'fixed_delay_upper_s', delay, 'upper', 1000000)
    return claims


def csvout(path, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def jsonout(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def historical_regressions(out):
    """Repeat the unchanged grid and old protocol; keep a log, not duplicate tables."""
    with tempfile.TemporaryDirectory(prefix='t72-numerical-regression-') as folder:
        regression_out = Path(folder)
        command = [sys.executable, '-X', 'utf8', '-B', str(HERE / 'run.py'), '--cache',
                   str(regression_out / 'UNUSED_NO_GOES'), '--out', str(regression_out), '--numerical-only']
        with (out / 'regression.log').open('w', encoding='utf-8') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        require(result.returncode == 0, 'regression failed; see regression.log')
        test_match = re.search(r'Ran (\d+) tests in .*?\n\nOK', (out / 'regression.log').read_text(encoding='utf-8'))
        require(test_match is not None, 'completed unittest protocol')
        regressions = ['t73_directed_bounds.csv', 't73_summary.csv', 't73_checked_inputs.json',
                       'verification_protocol.json', 'early/conditional_inputs.csv',
                       'early/reference_method.csv', 'early/fixed_necessity.csv',
                       'early/T68_16_63_audit.csv', 'early/theorist_inputs.json']
        for name in regressions:
            require((regression_out / name).read_text(encoding='utf-8') == (HERE / 'outputs' / name).read_text(encoding='utf-8'),
                    'historical regression: ' + name)
        import gzip
        grid = 'early/method_grid.csv.gz'
        with gzip.open(regression_out / grid, 'rt', encoding='utf-8') as fresh, gzip.open(HERE / 'outputs' / grid, 'rt', encoding='utf-8') as old:
            require(fresh.read() == old.read(), 'original 1728-row grid changed')
        regressions.append(grid)
        protocol = json.loads((regression_out / 'verification_protocol.json').read_text(encoding='utf-8'))
        provenance = json.loads((regression_out / 'provenance.json').read_text(encoding='utf-8'))
    return regressions, protocol, int(test_match.group(1)), provenance['numpy']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    # Only the NEW addressed output directory may be a committed output target.
    old_out = (HERE / 'outputs').resolve()
    require(not out.is_relative_to(HERE) or out == old_out / 'sync_3ad0462',
            'do not overwrite historical outputs')
    out.mkdir(parents=True, exist_ok=True)
    source_hashes = source_check()
    doc = read_new()
    expanded = expand(doc)
    comparisons = compare_inputs(doc, expanded)
    exact, directed_rows, summaries = evaluate(doc, expanded)
    claims = text_claims(exact)
    edge_rows = full_paired_checks(expanded, exact)
    print('New source, four inputs, eight formula rows, text directions and paired edges: OK', flush=True)
    # Repeat all old regressions/grid/calendar/resource checks, plus new tests.
    # --numerical-only is compulsory here; cache is a never-opened placeholder.
    regressions, protocol, tests_run, numpy_version = historical_regressions(out)
    jsonout(out / 'expanded_inputs.json', dict(theory_sha=THEORY_SHA, variants=expanded))
    csvout(out / 'input_comparison.csv', comparisons)
    csvout(out / 'directed_bounds.csv', directed_rows)
    csvout(out / 'summary.csv', summaries)
    csvout(out / 'text_claims.csv', claims)
    csvout(out / 'paired_edge.csv', edge_rows)
    source_paths = [HERE / name for name in ['confirm_t73_sync.py', 'test_t73_sync.py',
                    'verify_t73.py', 't73_calendar.py', 't73_resources.py', 'test_t73.py',
                    'test_t72.py', 'run.py', 'config.json', 'inputs/t72_explicit_changes.json']]
    source_paths += [HERE.parent / 't58-fixed-baseline-r0b/certificate.py',
                     HERE.parent / 't68-v21-inputs/outputs/numerics.csv',
                     HERE.parent / 't68-v21-inputs/outputs/service.csv']
    record = dict(theory_sha=THEORY_SHA, previous_engineer_sha=PARENT_ENGINEER_SHA,
                  engineer_sha='commit containing this protocol; pinned pair in PR #77 (no self-reference)',
                  python=platform.python_version(), numpy=numpy_version, source_files=source_hashes,
                  source_sha256={str(p.relative_to(HERE.parents[1])): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in source_paths},
                  input_fields_compared=len(comparisons), descriptive_changes=2,
                  unexpected_input_changes=0, numerical_metrics_compared=len(directed_rows),
                  new_JSON_rows_confirmed=len(summaries), text_claims_confirmed=len(claims),
                  unit_tests_passed=tests_run, historical_tests=27, added_tests=7,
                  LOW_integer_counts_enumerated=[18501, 840001],
                  paired_full_word_calendars=len(edge_rows), historical_regressions=regressions,
                  repeated_geometry=protocol['geometry'], repeated_resources=protocol['resources'],
                  historical_scientific_sha=protocol['theory_sha'],
                  arbitrary_phase_edge='2Wc_plus/T; only E3_arbitrary_phase_* justifies J0',
                  paired_edge='2c_plus/T; full occupied blocks and floor(iM/(W/2)) only',
                  physical_qualification=False, scientific_review_performed=False,
                  GOES_reprocessed=False, original_grid_changed=False,
                  remaining_conditions=['full38/ERR/Theta coverage', 'joint U-WCET <=89.9991 ns for revisions',
                                        'monitor a=1e11, A/a=1.001, actual delivery+compute <=9 ms'])
    jsonout(out / 'protocol.json', record)
    print(json.dumps({k: record[k] for k in ['theory_sha', 'input_fields_compared',
                     'numerical_metrics_compared', 'text_claims_confirmed', 'GOES_reprocessed']}, indent=2))
    print('All regressions passed; historical results unchanged. Conditional engineering confirmation only.')


if __name__ == '__main__':
    main()

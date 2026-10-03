"""T90: six addressed evaluations; no search, new proof, driver or switch rule."""
from __future__ import annotations

import argparse
from functools import lru_cache
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / 't88-dstar-sensitivity'))
import engine as t88  # noqa: E402; immutable accepted implementation

CFG = json.loads((HERE / 'config.json').read_text())


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2,
                      default=lambda v: str(v) if isinstance(v, F) else v) + '\n'


def verify_sources():
    """Check actual input bytes and all imported project Python against T88 SHA.

    T82's source_check separately verifies theory blobs and all four T73 sets.
    No GitHub, downloads, network or recomputation of the T88 search is needed.
    """
    t88.j.source_check()
    paths = set(CFG['source_files'])
    for module in tuple(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            p = Path(filename).resolve()
            if p.suffix == '.py' and p.is_relative_to(ROOT) and not p.is_relative_to(HERE):
                paths.add(str(p.relative_to(ROOT)))
    checks = []
    for rel in sorted(paths):
        original = subprocess.check_output(
            ['git', 'show', f"{CFG['accepted_T88_sha']}:{rel}"], cwd=ROOT)
        actual = (ROOT / rel).read_bytes()
        if actual != original:
            raise ValueError(f'Accepted dependency changed: {rel}')
        checks.append(dict(path=rel, sha256=hashlib.sha256(actual).hexdigest()))
    return checks


def selected():
    rows = json.loads((ROOT / CFG['source_files'][1]).read_text())
    result = []
    for shield in CFG['selection']['shields']:
        matches = [r for r in rows if r['purpose'] == 'working' and
                   r['mode'] == 'combined' and r['shield'] == shield]
        if len(matches) != 1:
            raise ValueError(f'Unique T88 working row required: {shield}')
        result.append(matches[0])
    return result


def same_exact(a, b):
    if a is None or isinstance(a, (bool, int)):
        return a == b
    if isinstance(a, F):
        return a == F(b)
    return a == b


def evaluate_row(source):
    p = t88.calendar(t88.context(source['shield'], 'combined'), source['g'])
    p['Dstar'] = F(source['Dstar'])
    spec = {k: source[k] for k in ('ka', 'vc', 'vc_kind', 'theta', 'k', 'z')}
    row = t88.evaluate(p, spec, p['Dstar'])
    differences = [k for k, v in source.items() if k != 'purpose' and
                   (k not in row or not same_exact(row[k], v))]
    if differences:
        raise ValueError(f'T88 exact reproduction failed: {differences}')
    m = t88.window(p)  # IMPORTANT: recompute at selected g, not always g=131
    timing = dict(
        window=m, margin=p['margin'],
        joint_U_required_upper_s=F(p['cfg']['service']['required_joint_U_WCET_physical_s']),
        physical_joint_U_WCET_s=None,
        program_delay_with_margin_s=(1+p['margin'])*row['delay_upper_s'],
        program_delay_margin_slack_s=F('3e-6')-(1+p['margin'])*row['delay_upper_s'],
        peak_slack=F('.8')-row['peak_upper'],
        physical_delivery_compute_upper_s=None,
        required_delivery_compute_upper_s=m['d'],
        required_loss_notice_from_last_good_end_s=m['Delta_p']+m['dp'],
        loss_notice_scope='Proposed complete deadline handler; clocks, polling, queues and handling included in d. Not measured; not an ERR switch guarantee.',
        post_bad_message_strip_upper_s=row['DM'],
        recovery_scope='Accepted T80 direct-fast strip, conditional on subsequent admissible timely messages; excludes an unbounded outage.',
        diagnostic_peak_count_rate_lower_per_s=m['aM']*p['B'],
        capacity_scope='Required ideal full-response rate at nu=B, not an inferred actual detector count or a hard saturation conclusion.')
    return p, row, timing


def profile_gaps(profile):
    c = profile['physical_contract']
    return [key for key, value in c.items() if value is None]


@lru_cache(maxsize=1)
def calculate():
    provenance = verify_sources()
    src = selected()
    effective = json.loads((ROOT / CFG['source_files'][2]).read_text())
    baselines, diagnostics, contexts = [], [], []
    for source in src:
        p, row, timing = evaluate_row(source)
        ei = next(x for x in effective if x['shield'] == source['shield'])
        for key, value in ei['environment'].items():
            if not same_exact(p[key], value):
                raise ValueError(f'T88 environment mismatch: {key}')
        assert p['margin'] == F(CFG['margin'])
        assert p['CX'] == F(CFG['diagnostic_profile']['resource_rate'])
        assert p['sigmaX'] == F(CFG['diagnostic_profile']['resource_sigma_s'])
        baselines.append(dict(source_selection=dict(purpose='working', mode='combined', shield=p['shield']),
                              all_published_fields_equal=True, result=row, timing=timing))
        contexts.append(dict(shield=p['shield'], selected_source_row=source,
                             effective_T88_input=ei, actual_window_at_selected_g=timing['window']))
        for case in CFG['addressed_cases']:
            m = t88.j.window(p, F(CFG['diagnostic_profile']['a_M']), F(case['window_s']),
                            F(CFG['diagnostic_profile']['delivery_compute_nominal_s']),
                            F(2), 'total_load', case['stride_divisor'])
            result = t88.j.evaluate(p, m, source['ka'], F(source['vc']), 'direct-fast',
                                   F(0), theta=source['theta'], vc_kind=source['vc_kind'])
            certified = result['status'] == 'certified_conditional'
            diagnostics.append(dict(case=case, shield=p['shield'], Dstar=p['Dstar'],
                                    g=p['g'], ka=source['ka'], vc=F(source['vc']),
                                    window=m, result=result,
                                    certified_risk_upper=result['risk_upper'] if certified else None,
                                    full_price_upper=result.get('objective'),
                                    full_goal_pass=certified and result['full_goal_pass'] and p['resource_pass'],
                                    resource_envelope_unchanged=True,
                                    physical_qualification=False))
    profiles = json.loads((HERE / 'monitor_profiles.json').read_text())
    checks = [dict(id=p['id'], verdict=p['verdict'], unknown_parameters=profile_gaps(p),
                   diagnostic_is_not_physical=True, full_contract_confirmed=False)
              for p in profiles['profiles']]
    handoff = dict(issue=95, status='inputs only; #95 not started by T90',
                   T88_sha=CFG['accepted_T88_sha'], T89_sha=CFG['accepted_T89_sha'],
                   scientific_formula_sha=CFG['scientific_formula_sha'], formulas_changed=False,
                   exact_inputs='outputs/pinned_inputs.json', checks='outputs/reproduction.json',
                   profiles='monitor_profiles.json', interface='INTERFACE.md',
                   confirmed_real_monitor=None, main_shield_g_cm2='3',
                   working_rows=[dict(shield=x['result']['shield'], Dstar=x['result']['Dstar'],
                                      g=x['result']['g'], ka=x['result']['ka'],
                                      conditional_risk_upper=x['result']['risk_upper'],
                                      conditional_full_price_upper=x['result']['objective'],
                                      full_goal_pass=x['result']['full_goal_pass']) for x in baselines],
                   physical_Dstar_upper=None, physical_ERR_token_lower=None,
                   physical_loss_detection_bound_s=None, physical_recovery_bound_s=None,
                   expected_lost_time_s=None, expected_recovery_count=None,
                   required_next_checks=[
                       'One common risk budget and start condition; separate certificates do not prove a switch.',
                       'Recognized outage duration/recoveries, plausible wrong counts, pending operations, and timer expiry are distinct.',
                       'ERR-only physical lower token contract remains conditional; ERR is not DED.',
                       'Do not reuse T82 sufficient a_M at another D*, or replace the 2.5 working row by its interior 1% row.'],
                   author_options=[
                       'Keep T88 conditional full-channel requirements; prefer IREM only as the more documented interface reference, not a qualified selection.',
                       'Carry the separate no-monitor/ERR-reserve branch into #95 with its explicit channel and cost conditions; do not claim <=1% or automatic switching.'])
    return dict(provenance=provenance, contexts=contexts, baselines=baselines,
                diagnostics=diagnostics, checks=checks, handoff=handoff)


def number(value, scale=F(1)):
    return '—' if value is None else f'{float(F(value)*scale):.10g}'


def report(data):
    lines = ['# Воспроизводимые числа T90', '',
             'JSON содержит точные дроби; десятичные числа ниже — только отображение. '
             'Все оценки условные; physical_qualification=false.', '',
             '| Защита, г/см² | D* | g / k_a | Риск upper | Тихий налог, % | С возвращениями, % | Пик upper, % | Задержка ×1,1, мкс | ≤1% |',
             '|---|---|---|---|---|---|---|---|---|']
    for item in data['baselines']:
        r, t = item['result'], item['timing']
        lines.append(f"| {r['shield']} | {number(r['Dstar'])} | {r['g']} / {r['ka']} | "
                     f"{number(r['risk_upper'])} | {number(r['quiet_upper'],100)} | "
                     f"{number(r['returns_upper'],100)} | {number(r['peak_upper'],100)} | "
                     f"{number(t['program_delay_with_margin_s'],10**6)} | {r['full_goal_pass']} |")
    lines += ['', 'Основная строка 3 и отдельная рабочая строка 2,5 воспроизведены по всем полям, не только округлённым метрикам.', '',
              '| Защита | Диагностический случай | w / Δ, с ном. | h_F upper, с | m_F lower | k | Условный полный налог, % | Итог |',
              '|---|---|---|---|---|---|---|---|']
    for item in data['diagnostics']:
        m, r = item['window'], item['result']
        lines.append(f"| {item['shield']} | {item['case']['id']} | {m['w']} / {m['w']/m['divisor']} | "
                     f"{number(m['hF_max'])} | {number(r['mass_lower'])} | {r['k']} | "
                     f"{number(item['full_price_upper'],100)} | {r['status']}; ≤1%={item['full_goal_pass']} |")
    lines += ['', 'Пустая цена при LOW_uninformative не равна нулю. Формальная сумма рискового бюджета '
              'без пригодного LOW не названа сертификатом. Длинные окна используют быстрый рост ρ_b=0,048 с⁻¹.', '',
              '| Защита | w− / w+, с | Δ− / Δ+, с | d+, с | h_F− / h_F+, с | Запас Б8 после 10%, с |',
              '|---|---|---|---|---|---|']
    for item in data['baselines']:
        m = item['timing']['window']
        lines.append(f"| {item['result']['shield']} | {number(m['wm'])} / {number(m['wp'])} | "
                     f"{number(m['Delta_m'])} / {number(m['Delta_p'])} | {number(m['dp'])} | "
                     f"{number(m['hF_min'])} / {number(m['hF_max'])} | {number(m['hF_slack'])} |")
    lines += ['', 'Точечная диагностическая подстановка не подтверждает физические a_M, A_M, '
              'статистику, WCET или доступность окон. Все неизвестные сохранены в monitor_profiles.json.', '']
    return '\n'.join(lines)


def artifacts(data):
    return {
        'provenance.json': encode(dict(accepted_sha=CFG['accepted_T88_sha'], files=data['provenance'])),
        'pinned_inputs.json': encode(data['contexts']),
        'reproduction.json': encode(data['baselines']),
        'diagnostics.json': encode(data['diagnostics']),
        'contract_checks.json': encode(data['checks']),
        'handoff.json': encode(data['handoff']),
        'tables.md': report(data),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify committed outputs without rewriting')
    args = parser.parse_args()
    data = calculate()
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern='test_*.py')
    if not unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful():
        raise SystemExit(1)
    out = HERE / 'outputs'
    if not args.check:
        out.mkdir(exist_ok=True)
    for name, contents in artifacts(data).items():
        path = out / name
        if args.check:
            if not path.exists() or path.read_text() != contents:
                raise ValueError(f'Output differs: {path}')
        else:
            path.write_text(contents, encoding='utf-8')
    print('T90: two exact T88 rows, four addressed hypotheses, tests and source pins OK.')
    print('Real monitors: full contract NOT confirmed; see outputs/tables.md and INTERFACE.md.')


if __name__ == '__main__':
    # Keep one module instance when unittest imports run.
    sys.modules['run'] = sys.modules[__name__]
    main()

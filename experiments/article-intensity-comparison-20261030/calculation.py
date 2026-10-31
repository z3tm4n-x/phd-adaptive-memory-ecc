"""Same-service comparison. Exact fractions; only the accepted lower helper is reused."""
from copy import deepcopy
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction as F
from functools import lru_cache
from hashlib import sha256
import importlib.util
import json
from math import isfinite, isqrt, nextafter, inf
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CFG = json.loads((HERE / 'inputs.json').read_text(encoding='utf-8'))
PREREGISTRATION = 'e9adc21b2b57cc985f54cf6810713b32a4e1fb3a'


def lf_hash(path):
    return sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def verify_sources():
    for rel, expected in CFG['source_sha256_lf'].items():
        actual = lf_hash(ROOT / rel)
        if actual != expected:
            raise ValueError(f'Accepted source changed: {rel}: {actual}')


verify_sources()
SOURCE = json.loads((ROOT / CFG['accepted_inputs']).read_text(encoding='utf-8'))
ACCEPTED = json.loads((ROOT / CFG['accepted_results']).read_text(encoding='utf-8'))
spec = importlib.util.spec_from_file_location('accepted_t340', ROOT / CFG['accepted_lower_code'])
accepted = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accepted)  # No main(), small_validation(), or reference_period() calls.
T, EPS, N = F(SOURCE['T_s']), F(SOURCE['epsilon']), SOURCE['n']
ENV = SOURCE['environment']
DREF = ENV['reference_bits']
BREF = F(ENV['background_reference_s_inv'])
PEAKREF = F(ENV['peak_reference_s_inv'])
FSREF = F(ENV['equivalent_peak_s']) * (PEAKREF - BREF)
RMAX = PEAKREF / BREF
RHO = F(SOURCE['service']['rho'])
BW = F(N - 1, 2 * N)


def floor(q):
    return q.numerator // q.denominator


def ceil(q):
    return -floor(-q)


def interval(q, upper=None):
    return accepted.interval(F(q), None if upper is None else F(upper))


def value(q):
    return dict(exact=str(q), **interval(q))


def display(q, digits=7, up=False):
    """Readable downward rounded decimal; exact periods remain in JSON."""
    if q is None:
        return '—'
    if isinstance(q, dict):
        q = F(q.get('exact', q['lower']))
    with localcontext() as ctx:
        ctx.prec, ctx.rounding = digits, ROUND_CEILING if up else ROUND_FLOOR
        return str(+(Decimal(q.numerator) / Decimal(q.denominator)))


def parameters(row):
    return (row['W'], F(row['duration_s']), F(row['peak_ratio']),
            F(row['c_s']), F(row['delta_s']), row['rule'])


def profile_statistics(W, d, r):
    assert W > 0 and F(10800) <= d <= F(864000)
    assert 1 <= r <= RMAX and BREF * (r - 1) * d <= FSREF
    scale = F(N * W, DREF)
    b, peak = scale * BREF, scale * BREF * r
    excess, global_cap = (peak - b) * d, scale * FSREF
    s_event = b * b * T + (peak + b) * excess
    s_rectangle = b * b * (T - d) + peak * peak * d
    assert s_event == s_rectangle
    s_mean = T * (b + excess / T)**2
    s_peak = T * peak**2
    s_global = min(s_peak, b*b*T + (peak+b)*global_cap)
    assert s_mean <= s_event <= s_global <= s_peak
    return dict(scale=scale, b=b, peak=peak, excess=excess, global_cap=global_cap,
                mean=b + excess / T, S_mean=s_mean, S_event=s_event,
                S_peak=s_peak, S_global=s_global)


def kernel(P, W, delta, rule):
    return P if rule == 'B' or delta == 0 else (1 + F(1, W))*P + delta


def upper(S, P, W, delta, rule):
    return BW / W * S * kernel(P, W, delta, rule)


def root(S, W, delta, rule):
    p0 = EPS / (BW / W * S)
    return p0 if rule == 'B' or delta == 0 else (p0 - delta)/(1 + F(1, W))


def binary64_down(q):
    assert q > 0
    x = float(q)
    assert isfinite(x) and x > 0
    if F(x) > q:
        x = nextafter(x, -inf)
    # Rational comparison, not a floating tolerance.
    assert F(x) <= q < F(nextafter(x, inf))
    return F(x)


def horizon_reservation(W, P, c, delta, end=T):
    """Starts j*P/W, j>=0, start<end. Reserve only intersection with [0,end]."""
    h = P / W
    assert 0 <= delta <= c <= h and end > 0
    starts = ceil(end / h)
    complete_blocks = max(0, floor((end - c) / h) + 1)
    complete_blocks = min(complete_blocks, starts)
    partial = starts - complete_blocks
    assert partial in (0, 1)
    tail = end - complete_blocks*h if partial else F(0)
    assert 0 <= tail <= c
    occupied = complete_blocks*c + tail
    completed_actions = min(starts, max(0, floor((end - delta) / h) + 1))
    return dict(started_actions=starts, completed_actions=completed_actions,
                full_reserved_blocks=complete_blocks, cropped_blocks=partial,
                cropped_reserved_s=value(tail), reserved_to_T_s=value(occupied),
                horizon_fraction=value(occupied / end),
                execution_after_failure='continues; no proof-stopping cost shortcut')


def prescription(S, actual_S, W, c, delta, rule, name):
    h = root(S, W, delta, rule)
    pmin = W*c/RHO
    p = binary64_down(h) if h > 0 else None
    analytic_feasible = h >= pmin
    feasible = p is not None and p >= pmin
    if h <= 0:
        status = 'nonpositive_root'
    elif not analytic_feasible:
        status = 'positive_root_resource_infeasible'
    elif not feasible:
        status = 'rounding_loses_resource_boundary'
    elif name == 'avg' and actual_S > S:
        status = 'average_candidate_not_certified'
    else:
        status = 'sufficient_and_resource_feasible'
    out = dict(exact_root_s=value(h), selected_P_s=value(p) if p is not None else None,
               binary64_hex=float(p).hex() if p is not None else None,
               analytic_resource_feasible=analytic_feasible, resource_feasible=feasible,
               status=status, root_input_test=value(upper(S, p, W, delta, rule)) if p else None,
               candidate_bus_fraction=value(W*c/p) if p else None,
               nonoverlap=bool(p is not None and delta <= c <= p/W),
               period_margin_s=value(p-pmin) if p else None,
               rounding_loss_s=value(h-p) if p else None,
               actual_profile_U=value(min(F(1), upper(actual_S, p, W, delta, rule))) if feasible else None,
               actual_profile_U_applicable=feasible,
               horizon=horizon_reservation(W, p, c, delta) if feasible else None)
    if p:
        assert upper(S, p, W, delta, rule) <= EPS
    if name in ('event', 'peak') and feasible:
        assert upper(actual_S, p, W, delta, rule) <= EPS
    return out


@lru_cache(maxsize=None)
def new_lower(W, P, delta, d, r):
    # Accepted exact free-cell count and rational outward exp enclosure.
    return accepted.lower_free_cells(W, P, delta, accepted.profile(d, r))


def comparison_row(old, index):
    W, d, r, c, delta, rule = parameters(old)
    stats = profile_statistics(W, d, r)
    choices = {name: prescription(stats[key], stats['S_event'], W, c, delta, rule, name)
               for name, key in [('avg', 'S_mean'), ('event', 'S_event'), ('peak', 'S_peak')]}
    h_event = F(choices['event']['exact_root_s']['exact'])
    # Exact identity with the accepted rational corrected root; do not solve it again.
    assert h_event == F(old['corrected_root_rational'])
    assert choices['event']['analytic_resource_feasible'] == old['corrected_feasible']
    p0 = root(stats['S_event'], W, F(0), rule)
    both = choices['event']['resource_feasible'] and p0 >= W*c/RHO
    operation = 100*(1-h_event/p0) if both else None
    if operation is not None:
        assert 0 <= operation <= F(200, W+2)
    lower = None
    if old['label'] == 'main' and choices['avg']['resource_feasible']:
        pavg = F(choices['avg']['selected_P_s']['exact'])
        enclosure, counts = new_lower(W, pavg, delta, d, r)
        lower = dict(value=enclosure, counts=counts, period_rational=str(pavg),
                     profile='rectangle centred at T/2; admissible lower witness',
                     verdict='violation_proved' if F(enclosure['lower']) > EPS else 'violation_not_established')
        assert F(enclosure['lower']) <= F(choices['avg']['actual_profile_U']['upper'])
    ratio = (h_event / F(choices['peak']['exact_root_s']['exact'])
             if h_event > 0 and F(choices['peak']['exact_root_s']['exact']) > 0 else None)
    comparison = dict(information_scope=CFG['event_information_scope'],
        resource_floor_s=value(W*c/RHO), beta=value(BW/W),
        statistics={k: value(v) for k, v in stats.items()},
        statistics_units={'b':'1/s','peak':'1/s','mean':'1/s','excess':'inversions',
                          'global_cap':'inversions','S_mean':'1/s','S_event':'1/s',
                          'S_peak':'1/s','S_global':'1/s','scale':'1','beta':'1'},
        excess_reference=value(BREF*(r-1)*d), global_cap_reference=value(FSREF),
        E_over_Fs=value(stats['excess']/stats['global_cap']),
        choices=choices, lower_at_selected_P_avg=lower,
        P_event_over_P_peak=value(ratio) if ratio is not None else None,
        ratio_is_algebraic_only=not all(choices[x]['resource_feasible'] for x in ('event','peak')),
        operation_reduction_percent=value(operation) if operation is not None else None,
        operation_bound_percent=value(F(200,W+2)),
        wider_Fs_class_diagnostic=prescription(stats['S_global'],stats['S_global'],W,c,delta,rule,'event'))
    return dict(id=f'a{index:02d}', accepted=deepcopy(old), comparison=comparison)


def collect():
    rows = [comparison_row(row,i) for i,row in enumerate(ACCEPTED['sensitivity'],1)]
    assert len(rows) == CFG['expected_rows']
    # Canonical alias identifies a numerically duplicated registered row without dropping it.
    seen = {}
    for row in rows:
        key = parameters(row['accepted'])
        row['same_input_as'] = seen.get(key)
        seen.setdefault(key,row['id'])
    main = [x for x in rows if x['accepted']['label']=='main']
    return dict(task=346, status='OWN RESULT; conditional model; awaiting independent review',
        preregistration_commit=PREREGISTRATION, accepted_base=CFG['accepted_base'],
        source_sha256_lf=CFG['source_sha256_lf'],
        common=dict(n=N,T_s=str(T),epsilon=str(EPS),rho=str(RHO),
                    other_failure_budget='0 by accepted assumption; not measured',
                    runtime_energy_application_cost='UNKNOWN; bus reservation only'),
        rows=rows, checks=dict(rows=len(rows), distinct_input_rows=len(seen),
          main_lower_rows=len(main), unique_new_lower_substitutions=len({
             (x['accepted']['W'],x['comparison']['lower_at_selected_P_avg']['period_rational'],
              x['accepted']['delta_s'],x['accepted']['duration_s'],x['accepted']['peak_ratio']) for x in main}),
          accepted_small16_recomputed=False, accepted_P_ref_recomputed=False,
          source_hashes_verified=True, exact_event_root_matches_accepted=True,
          safe_binary64_rounding=True, accepted_rows_copied_without_change=True))


def square_root_enclosure(q, digits=36):
    assert q >= 0
    den = 10**digits
    k = isqrt(q.numerator*den*den//q.denominator)
    lo, hi = F(k,den), F(k+1,den)
    assert lo*lo <= q < hi*hi
    return lo, hi


def resource_ratio_boundary(W,d,c,delta,rule,kind):
    b = F(N*W,DREF)*BREF
    capacity = EPS/(BW/W * kernel(W*c/RHO,W,delta,rule))
    if kind=='event':
        squared = 1+(capacity/b**2-T)/d
    elif kind=='peak':
        squared = capacity/(b*b*T)
    else:
        raise ValueError(kind)
    return square_root_enclosure(squared)


def table_markdown(data):
    lines = ['# Общая таблица 34 принятых строк', '',
      'Периоды в секундах показаны с округлением вниз до 7 значащих цифр. Для воспроизведения',
      'и исполнения используются точные рациональные значения `selected_P_s.exact` из results.json.',
      '`Р` — положительный корень ниже P_min: предписание не помещается в ресурс; это не невозможность защиты.',
      '`С` — достаточный период и ресурс; `К` — средний кандидат без сертификата переменного профиля.',
      '`!` — нижняя проверка при точном выбранном P_avg доказала Q>epsilon; `?` — нарушение не установлено.',
      '`—` в нижнем столбце — эта строка не назначена для новой нижней проверки.',
      'P_ref скопирован из принятого источникового контроля и отличается от P_avg.', '',
      '| ID | Срез; МиБ; r; d, s; правило | c / Delta, ns | P_min | P_ref (контроль) | P_avg | P_event | P_peak | Статусы avg/event/peak | L(P_avg) ≥ | P_event/P_peak |',
      '|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|']
    tags={'sufficient_and_resource_feasible':'С','average_candidate_not_certified':'К',
          'positive_root_resource_infeasible':'Р','nonpositive_root':'Н',
          'rounding_loses_resource_boundary':'О'}
    for row in data['rows']:
        old,q=row['accepted'],row['comparison']
        choices=q['choices']; lower=q['lower_at_selected_P_avg']
        desc=f"{old['label']}; {old['useful_MiB']}; {display(F(old['peak_ratio']))}; {old['duration_s']}; {old['rule']}"
        flags='/'.join(tags[choices[k]['status']] for k in ('avg','event','peak'))
        lowtext='—' if lower is None else display(F(lower['value']['lower']))+(' !' if lower['verdict']=='violation_proved' else ' ?')
        ps=[display(choices[k]['selected_P_s']) for k in ('avg','event','peak')]
        ratio=display(q['P_event_over_P_peak'])+('*' if q['ratio_is_algebraic_only'] else '')
        lines.append(f"| {row['id']} | {desc} | {display(F(old['c_s'])*10**9)} / {display(F(old['delta_s'])*10**9)} | {display(q['resource_floor_s'])} | {display(F(old['P_ref_s']['lower']))} | {' | '.join(ps)} | {flags} | {lowtext} | {ratio} |")
    lines += ['', '* Отношение положительных алгебраических корней. Если один корень вне ресурса,',
              'это не выигрыш между двумя исполнимыми режимами. Сравнивается достаточный тест, не глобальный оптимум.',
              'a33 повторяет a12; сохранён как принятая строка, но не является новым исполнением.', '',
              '## Ресурс и операционный сдвиг', '',
              'u=Wc/P — доля резервируемой шины (1=100%). При u>rho это требование не исполнимо.',
              'Процент операционного сокращения дан только при существовании обоих допустимых периодов.', '',
              '| ID | u_avg | u_event | u_peak | E/F_s | Сокращение от операции, % | Верх для сокращения, % | P_event при одном глобальном F_s, s |',
              '|---|---:|---:|---:|---:|---:|---:|---:|']
    for row in data['rows']:
        q=row['comparison']; v=q['choices']
        lines.append('| '+ ' | '.join([row['id'],*[display(v[k]['candidate_bus_fraction']) for k in ('avg','event','peak')],
              display(q['E_over_Fs']),display(q['operation_reduction_percent']),display(q['operation_bound_percent'],up=True),
              display(q['wider_Fs_class_diagnostic']['selected_P_s'])])+' |')
    lines += ['', 'Последний столбец — диагностический корень для более широкого класса, с теми же b,B,',
              'но только общим F_s; его ресурсный статус сохранён в JSON. Он не заменяет основной E-подкласс.',
              'Расход за весь T, число начатых/завершённых действий и обрезанный последний резерв —',
              'в `choices.*.horizon`; у неосуществимых предписаний эти поля отсутствуют (null).', '']
    return '\n'.join(lines)

"""One c01 control-price ledger. Loads accepted results; no Q/RTL/model rerun.

All cost coefficients remain UNKNOWN. --write saves only local JSON/Markdown.
Default verifies the saved ledger. Unit ceilings are conditional requirements,
not measured costs, allocated simultaneous budgets, or new policy parameters.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAP = ROOT / 'experiments/regime-map-methodology-20261019/predictability-volume-20261028'


def numeric(x):
    if isinstance(x, dict):
        return {k: numeric(v) for k, v in x.items()}
    if isinstance(x, list):
        return [numeric(v) for v in x]
    if isinstance(x, str):
        try:
            return F(x)
        except ValueError:
            pass
    return x


def sha(p):
    return hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def encoded(x):
    return (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2,
                       default=str) + '\n').encode('utf-8')


def ceil(x):
    return -(-x.numerator // x.denominator)


def display(x, places=6, up=False):
    """Outward decimal rounding, never float formatting a bound."""
    x = F(x)
    scale = 10**places
    k = ceil(x*scale) if up else (x*scale).numerator//(x*scale).denominator
    return f'{k//scale}.{k%scale:0{places}d}'


def evaluate(rows, coefficients, budget_us_per_s):
    if any(coefficients.get(r['id']) is None for r in rows):
        return dict(status='not_established', upper_us_per_s=None)
    assert all(coefficients[r['id']] >= 0 for r in rows)
    upper = sum((r['mean_multiplier']*coefficients[r['id']] for r in rows), F(0))
    return dict(status='condition_met' if upper < budget_us_per_s
                else 'not_met_by_this_upper', upper_us_per_s=upper)


def calculate():
    cfg = json.loads((HERE/'inputs.json').read_text('utf-8'))
    for path, expected in cfg['source_sha256_LF'].items():
        assert sha(ROOT/path) == expected, path
    old = numeric(json.loads((ROOT/'theory/t196-window-application-20261029/result.json').read_text('utf-8')))
    grid = numeric(json.loads((MAP/'map-14/result.json').read_text('utf-8')))
    cell = grid['cells']['c01']
    inp = numeric(json.loads((MAP/'inputs.json').read_text('utf-8')))
    method = cell['methods']['M']
    bundle = cell['price_bounds'][method['price']]
    price, mg = bundle['price'], bundle['management']
    T, W = F(cell['mission_s']), cell['cell']['words']
    assert (W, T, cell['cell']['alpha'], cell['cell']['epsilon'], method['pair']) == (
        1048576, F(315576000), 0, F(1, 1000), [26, 208])
    assert old['M_pair'] == method['pair']
    assert old['M_accepted_Q_upper'] == method['Q_upper']
    assert old['M_reads_upper'] == price['reads_upper']
    assert old['M_repairs_upper'] == price['repairs_upper']
    assert old['M_local_selector_checks_upper'] == mg['local_slot_selector_checks_upper']
    assert old['M_calendar_action_counts_upper'] == mg['calendar_action_counts_upper']
    assert price['work_after_first_failure_paid'] and price['full_started_tail_paid']
    assert sum(price['read_terms_upper'].values()) == price['reads_upper']
    assert sum(price['repair_terms_upper'].values()) == price['repairs_upper']
    counts = dict(mg['calendar_action_counts_upper'])
    # Verify finite all-horizon counts, retaining exceptional/edge actions.
    info, svc = inp['information'], inp['service']
    hminus = svc['xi_minus'] - svc['J_ns']/10**9
    P = T/hminus + 2
    delta = info['lifetime_delta_exec'] + info['lifetime_delta_calendar']
    R = min(P+1, 1+info['loss_episodes_upper']+
            info['false_expected_per_s']*T+delta*P)
    assert counts == dict(check=P, command=P+R+1, timer=P+2*R+2, extra_bundle=P)
    counts['slot'] = mg['local_slot_selector_checks_upper']
    app = cell['resource']['application']
    assert not app['read_emits_ERR'] and not app['read_repair'] and app['useful_writes'] == 0
    # No data beats/codec charged twice: dispatch is only additional control.
    counts['dispatch'] = price['reads_upper'] + app['offered_reads'] + W
    # Conservative logical-source bound, including post-A. Retries/empty polls
    # require a bounded per-record bundle or the explicitly separate state row.
    counts['ERR'] = price['reads_upper']
    counts['state_rate'] = T
    counts['state_edges'] = F(1)

    specs = [
        ('check', 'Календарная проверка времени/здоровья', 'мкс/действие', F(1,10**6),
         'PR320 §4 / ENGINEERING §4; не включает частый gate'),
        ('command', 'Установка/подтверждение календарной команды', 'мкс/действие', F(1,10**6),
         'Обычные/возвратные/ложные/плохие истории и краевой +1 уже в числе'),
        ('timer', 'Периодическое событие, постановка/истечение hold', 'мкс/действие', F(1,10**6),
         'Один активный hold; события recovery и краевые +2 уже в числе'),
        ('extra_bundle', 'Ограниченный дополнительный пакет на poll', 'мкс/пакет', F(1,10**6),
         'Ровно прежний bounded bundle, не безразмерный резерв на все работы'),
        ('slot', 'Локальный селектор и его фиксированная адресная/фазовая работа', 'нс/проверку', F(1,10**9),
         'До Nmax, включая пропуски; старый local RTL не реализует M(26,208)'),
        ('dispatch', 'Добавочная подготовка/завершение транзакции', 'нс/транзакцию', F(1,10**9),
         'NR + app offered + W init; без уже оплаченных beats/ECC/repair и без gate'),
        ('ERR', 'Включённый логический ERR: сбор и ограниченная обработка/очередь', 'нс/запись', F(1,10**9),
         'Консервативно ≤NR при ≤1 публикации/scrub; повторы внутри bundle; статус включения UNKNOWN'),
        ('state_rate', 'Остальная фоновая работа, сохранность состояния, пустой polling', 'мкс/с', F(1,10**6),
         'Сверх строк выше; размещение/защита/фон/дополнительные события, включая post-A'),
        ('state_edges', 'Остаток запуска, завершения и drain после T', 'с за миссию', F(1),
         'Один совокупный полный край; не повторяет init данных, хвост E и +1/+2 календаря'),
    ]
    rows = []
    for ident, label, unit, scale, basis in specs:
        n = counts[ident]
        rows.append(dict(id=ident, label=label, count_upper=n, coefficient_unit=unit,
                         coefficient_seconds_scale=scale,
                         mean_multiplier=n*scale*10**6/T, basis=basis,
                         coefficient_bus=None, coefficient_serial=None,
                         CPU_coefficient=None, energy_coefficient=None))
    results = {}
    reserve = mg['window_action_mean_sufficient_for_any_composition']
    for coord in ('bus', 'serial'):
        c = old['costs'][coord]
        assert price['coordinates'][coord] == c['M_accepted_price']
        exact = c['fixed_class_with_common_lower_s']-c['M_accepted_price']['all_known_upper_s']
        assert exact == c['unknown_M_minus_uniform_unknown_F_lower_budget_s']
        B = F(cfg['strict_sufficient_budget_us_per_s'][coord])
        assert 0 < B < exact*10**6/T
        limits = {r['id']: B/r['mean_multiplier'] for r in rows}
        residual = B - reserve*10**6
        results[coord] = dict(
            accepted_margin_s=exact, conservative_strict_budget_us_per_s=B,
            conservative_strict_budget_s=B*T/10**6,
            verdict=evaluate(rows, {r['id']: None for r in rows}, B),
            sole_term_coefficient_ceilings=limits,
            conditional_calendar_allocation_us_per_s=reserve*10**6,
            conditional_remaining_after_calendar_us_per_s=residual,
            conditional_slot_ceiling_after_calendar_ns=residual/(counts['slot']/T/1000),
            accepted_M_known_upper_s=price['coordinates'][coord]['all_known_upper_s'],
            fixed_class_known_lower_s=c['fixed_class_with_common_lower_s'],
            actual_control_upper_s=None)
    # Pure requirement diagnostic; not an assigned cost or real impossibility.
    one_beat_upper_ns = 16*svc['xi_plus']+svc['J_ns']
    diagnostic = counts['slot']/T*one_beat_upper_ns/1000
    return dict(
        status='OWN RESULT; conditional cost ledger, not accepted hardware qualification',
        base_main=cfg['base_main'], input_sha256_LF=sha(HERE/'inputs.json'),
        implementation_sha256_LF=sha(Path(__file__)), source_sha256_LF=cfg['source_sha256_LF'],
        cell='c01', M_pair=method['pair'], words=W, mission_s=T,
        accepted_Q_loaded_only=method['Q_upper'], accepted_calculations_rerun=False,
        already_paid=price['coordinates'],
        reads_upper=price['reads_upper'], repairs_upper=price['repairs_upper'],
        calendar_recoveries_upper=R, costs_uniform_after_first_failure=True,
        counts=counts, ledger=rows, coordinates=results,
        ERR_scope=dict(logical_source_upper=price['reads_upper'],
                       if_export_exactly_matches_charged_repair_upper=price['repairs_upper'],
                       actual_export_disabled=None, matched_export_path=False,
                       expected_count_not_burst=True,
                       duplicates_and_empty_polling='bounded bundle or separately paid state work; no unlimited retries'),
        resource_conditions=dict(
            management_progress_s=mg['guaranteed_progress_s'],
            frame_upper_s=mg['frame_upper_s'], atomic_upper_s=mg['atomic_upper_s'],
            local_processing_conditional_budget_s=mg['conditional_local_processing_budget_s'],
            calendar_bundle_conditional_upper_s=mg['conditional_burst_work_upper_s'],
            calendar_mean_sufficient_for_any_composition=reserve,
            peak_including_full_reserved_slot=mg['peak_including_reserved_management'],
            peak_cap=cell['resource']['resource']['serial_cap'],
            app_response_ns=app['inherited_response_envelope_ns'],
            app_deadline_ns=app['response_deadline_ns'],
            hold_20tick_quanta=price['hold']['ticks']//20,
            raw_data_bytes=cell['resource']['raw_storage_required_bytes'],
            actual_M_state_bytes=None, actual_CPU_upper=None, actual_energy_upper=None,
            actual_shared_resource_mapping=False, actual_M_WCET=None),
        diagnostic_one_beat_per_slot=dict(
            unit_upper_ns=one_beat_upper_ns, budgeted_upper_us_per_s=diagnostic,
            conditional_model_only=True, not_real_cost_lower=True,
            verdict={x:'not_met_by_this_upper' for x in ('bus','serial')}),
        accounting_rules=[
            'Exactly one row owns each incremental operation; combined gate/dispatch must not be charged twice.',
            'All unit costs are full nonnegative upper bounds including interconnect/queue/arbitration overhead.',
            'Control state is isolated from corrupted application data and all work is bounded after A and on exceptional histories.',
            'Calendar lost/false/restore count terms already included; do not add them a second time.',
            'Zero bus requires proved locality; zero serial additionally requires no service interference.',
            'Zero ERR only with a verified disable path compatible with M; no supplied disable is assumed.',
            'A mission-mean bound cannot establish peak, deadline, buffer capacity or CPU/energy.',
        ],
        CPU_energy='Separate sums of counts times own unit costs, data read/repair/app/init costs and background over T; all UNKNOWN.',
        audit_scope='Pinned mathematical model and candidate T104/T105 modules; no matched M executable identified.',
        no_new_RTL=True, no_new_policy=True, no_new_Q=True)


def table(r):
    lines = [
        '# Ведомость добавочной цены M c01', '',
        '29.10.2026, #186. Один неизменённый M(26,208), 4 МиБ, T=315576000 с.',
        'Счёт выведен из принятых количеств за весь срок; верх ожидаемой работы не заменяет burst-ограничение.',
        'Коэффициент b с индексом строки задаётся **отдельно** для bus и serial в единицах столбца.',
        'Все b пока UNKNOWN; указанные множители не являются измеренными затратами.',
        'Первые четыре строки — редкие календарные события. Частый селектор оплачивается отдельно.', '',
        '| Операция | Верх количества за T | Единица b | Вклад в верх u_x, мкс/с | Основание / точный остаток |',
        '|---|---:|---|---:|---|',
    ]
    for row in r['ledger']:
        n = row['count_upper']
        # State rows are integrated background and one residual whole-edge bundle.
        lines.append('| '+row['label']+' | '+display(n,3,True)+' | '+
                     row['coefficient_unit']+' | '+display(row['mean_multiplier'],12,True)+
                     ' · b_'+row['id']+' | '+row['basis']+' |')
    lines += ['', 'Множители/количества округлены вверх. В result.json — точные дроби.',
              'u_x — сумма всех строк; U_ctl,x=T·u_x/10⁶. Это одна совместная граница, не отдельный бюджет каждой строке.',
              'Диспетчеризация может объединяться с gate: тогда операции переносят между коэффициентами один раз, с явным основанием.',
              'При неограниченных повторах/пустом polling нет подтверждённого конечного b_ERR или b_state_rate.',
              'Структурная локальность старого кода не назначает эти b нулями для нового M.',
              '', 'Уже оплачены и повторно не добавляются: чтения/кодек/repair, app/init данных,',
              'быстрые полосы при loss/restore/false, старт/хвост E и post-A по сохранённой цене.',
              'Дополнительные управляющие работы этих ветвей остаются в непересекающихся строках выше.',
              'CPU/энергия имеют собственные коэффициенты и фон; они не выводятся из bus/serial.',
              '', 'Выводы и численные ограничения — [REPORT](REPORT.md); [точные числа](result.json).', '']
    return '\n'.join(lines).encode('utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write', action='store_true')
    args = p.parse_args()
    r = calculate()
    for name, raw in (('result.json', encoded(r)), ('LEDGER.md', table(r))):
        path = HERE/name
        if args.write:
            path.write_bytes(raw)
        else:
            assert path.read_bytes().replace(b'\r\n', b'\n') == raw, name
    print('c01 only; frozen sources / complete ledger: PASS; no Q or RTL rerun')
    for x, c in r['coordinates'].items():
        print(x, c['verdict']['status'], 'strict budget', c['conservative_strict_budget_us_per_s'],
              'us/s; isolated slot ceiling', display(c['sole_term_coefficient_ceilings']['slot'],9), 'ns')
    print('result SHA256(LF):', hashlib.sha256(encoded(r)).hexdigest())


if __name__ == '__main__':
    main()

"""Conditional residual-price algebra only: no new Q or controller execution."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STRENGTH = ROOT / 'experiments/t186-method-comparison/code-strength'
sys.path.insert(0, str(STRENGTH))
import comparison as cmp
import informational

NS = cmp.NS
COMMON = 'experiments/t186-method-comparison/code-strength/common-input.json'
CFE = 'experiments/mission-rise-rate-20261022/cfe-application/outputs/result.json'


def encoded(x):
    return (json.dumps(x, indent=2, sort_keys=True, default=str) + '\n').encode()


def load():
    manifest = json.loads((HERE / 'frozen-inputs.json').read_text('utf-8'))
    for name, digest in manifest['sha256'].items():
        data = (ROOT / name).read_bytes().replace(b'\r\n', b'\n')
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Frozen premise changed: ' + name)
    return (json.loads((ROOT / COMMON).read_text('utf-8')),
            json.loads((ROOT / CFE).read_text('utf-8')),
            json.loads((HERE / 'analysis-input.json').read_text('utf-8')), manifest)


def context():
    cfg, cfe, plan, manifest = load()
    if (F(plan['cold_start_extra_fast_s']) != 0 or F(plan['veto_slice_per_s']) != 0
            or list(map(F, plan['p_bad_slices'])) != [F(0), F(cfg['epsilon'])]):
        raise ValueError('Only the preregistered conditional slices are implemented')
    original = encoded(cfg)
    hypothetical = deepcopy(cfg)
    for key in ('short_hold_s', 'long_hold_s', 'source_pair_window_s', 'timer_quantum_ticks'):
        hypothetical['adaptive'][key] = plan[key]
    ps = cmp.period(cfg, 1)['nominal_ns'] / F(NS)
    # Odd inverse-address period, next grid point above the registered4h.
    k = cmp.ceil(F(plan['diagnostic_period_at_least_s']) / ps)
    if k % 2 == 0:
        k += 1
    cal = informational.calendar(hypothetical, k)  # calendar only; never compute()
    if encoded(cfg) != original:
        raise AssertionError('Common input mutated')
    W, T = cfg['words'], F(cfg['mission_s'])
    s = cmp.service(cfg, 39); fresh = F(cfg['adaptive']['source_to_fresh_rule_upper_ns'], NS)
    S = lambda length: F(2 + cmp.ceil((length * NS + s['J']) /
                                    (cfg['calendar']['c_ticks'] * s['xminus'])))
    tau = cal['tau'] + fresh
    wp, hp = cal['w_upper'] + fresh, cal['h_upper'] + fresh
    pair = cal['source_PAIR']['upper'] + 2 * cal['J']
    d, V, H, L = pair + tau, wp + tau, hp + tau, hp + pair + 2 * tau
    e = cfg['environment']; factor = F(W * 39, e['reference_words'] * e['reference_bits'])
    b, fs = factor * F(e['reference_background_per_s']), factor * F(e['reference_solar_mass'])
    parents = b * T + fs
    a = cfg['adaptive']; false = F(a['ordinary_false_expected_per_s']) * T
    support, hard = cmp.read_bounds(cfg, k), cmp.read_bounds(cfg, 1)['upper']
    recover_one = S(cal['recovery']['upper'] + fresh)
    terms = dict(support=support['upper'], recovery=a['recoveries_upper'] * recover_one,
                 loss_duration=F(a['ordinary_outage_fraction']) * T * NS /
                               (cfg['calendar']['c_ticks'] * s['xminus']),
                 loss_edges=F(2 * a['ordinary_loss_episodes_upper']),
                 false=S(L) * false, background_first=S(V) * b * T,
                 background_pairs=S(H) * b * b * d * T,
                 solar_and_cross=S(H) * (1 + b * d) * fs,
                 weak_E_repeat=S(L) * F(plan['active_words_m']) * parents / W)
    app = cfe['screen']['rows']['OFF39']['price']
    A = F(cfe['screen']['mandatory_app39_core_lower'])
    Au = F(app['core_upper'])
    Cf = F(cfe['screen']['rows']['fixed44']['price']['core_upper'])
    target = Cf / F(plan['target_gain'])
    return dict(cfg=cfg, cfe=cfe, plan=plan, manifest=manifest, W=W, T=T, s=s,
                cal=cal, k=k, S=S, fresh=fresh, parents=parents, false_count=false,
                support=support, hard=hard, terms=terms, recover_one=recover_one,
                b=b, fs=fs, tau=tau, w_upper=wp, h_upper=hp, pair_upper=pair,
                d=d, V=V, H=H, L=L, A=A, Au=Au, Cf=Cf, target=target, app=app)


def account(c, p_bad=F(0), veto=F(0), include_long_cold_start=False):
    """Sufficient counting upper IF stated service/age/expiry/Q premises hold.

    Removing startup is done before clipping, never by subtracting from an
    already capped upper. Quotas stay unchanged; optional-event lower is0.
    """
    if not 0 <= p_bad <= 1 or veto < 0:
        raise ValueError('Invalid probability or veto rate')
    cfg, T, s, S = c['cfg'], c['T'], c['s'], c['S']
    source_edge = F(NS) / (4 * s['xminus']) + 2 / T
    if veto > source_edge:
        raise ValueError('Veto rate exceeds the preserved source-edge cap')
    terms = dict(c['terms'])
    terms.update(initial_long_FAST=c['recover_one'] if include_long_cold_start else F(0),
                 bad_histories=p_bad * c['hard'], extra_veto=S(c['fresh']) * veto * T)
    refined = sum(terms.values(), F(0))
    old_ordinary = (2 * c['parents'] + c['false_count']) * S(c['H'])
    ordinary_names = ('false', 'background_first', 'background_pairs', 'solar_and_cross', 'weak_E_repeat')
    old_upper = refined - sum(terms[k] for k in ordinary_names) + old_ordinary
    N = min(c['hard'], refined, old_upper)
    repairs = min(N, 2 * c['parents'] + p_bad * c['hard'] + terms['extra_veto'])
    control = (s['upper']['R'] * N + (s['upper']['E'] - s['upper']['R']) * repairs) / (T * NS)
    upper, hard_core = c['Au'] + control, c['Au'] + s['upper']['E'] * c['hard'] / (T * NS)
    rates = {k: F(v) for k, v in c['app']['full_cost_rates'].items()}
    for key, add in dict(scrub_reads=N/T, scrub_corrections=repairs/T, decodes=N/T,
                         read_beats=3*N/T, write_beats=3*repairs/T, turnarounds=repairs/T).items():
        rates[key] = rates.get(key, F(0)) + add
    source = min(source_edge, (2 * c['parents'] + c['false_count'] +
                 2 * cfg['adaptive']['ordinary_loss_episodes_upper']) / T + p_bad * source_edge + veto)
    rates.update(cuts=F(NS)/(cfg['observation']['cut_ns'] * s['xminus']) + 2/T,
                 captures=source, records=source, decisions=c['hard']/T,
                 # Keep startup controller setup even when its long FAST is removed.
                 timer_events=2*source + F(2*(cfg['adaptive']['recoveries_upper']+1), T))
    cpu = {k+'_ns': rates[k]/NS for k in ('app_dispatch', 'initialization', 'cuts',
                                        'captures', 'records', 'decisions', 'timer_events')}
    energy = dict(rates, transport_requests=rates['application_reads']+rates['application_writes'],
                  transport_replies=rates['application_reads']+rates['application_writes'],
                  transport_records=source, transport_cuts=rates['cuts'], extra_veto=veto)
    return dict(p_bad=p_bad, veto_per_s=veto, includes_long_cold_start=include_long_cold_start,
                terms_read_count_upper=terms, refined_uncapped_read_upper=refined,
                old_publication_uncapped_read_upper=old_upper, hard_read_upper=c['hard'],
                reads_upper=N, repairs_upper=repairs, core_upper=upper,
                added_control_core_upper=control, all_history_core_upper=hard_core,
                upper_below_fivefold_witness_target=upper <= c['target'],
                unconditional_price_certificate=False, new_Q_certificate=False,
                full_cost_rates=rates, CPU_fraction_coefficients=cpu,
                CPU_extra_veto_ns_coefficient=veto/NS,
                veto_domain_per_s=[F(0), source_edge],
                energy_coefficients_per_second=energy,
                transport_plus_loss_state_bytes=131136,
                physical_memory_copies='accepted two cFE images inside W; external buffers remain parameters',
                energy_formula='T*sum(rate_action*incremental_nonoverlapping_J_per_action)+T*idle_W',
                transport_formula='accepted cFE payload/requests/replies +32*source_records + cuts*cut_header',
                unknown_price='controller bus work, CPU, energy, memory and veto retain common unknown coefficients',
                numeric_scope='conditional expression slice, not measured/qualified price or gain')


def evaluate():
    c = context(); s, T = c['s'], c['T']
    no_start = account(c)
    epsilon_slice = account(c, F(c['cfg']['epsilon']))
    with_start = account(c, include_long_cold_start=True)
    support_lower = c['A'] + s['lower']['R'] * c['support']['lower'] / (T * NS)
    baseline_upper = (c['Au'] + s['upper']['R'] * c['support']['upper'] / (T * NS)
                      + (s['upper']['E'] - s['upper']['R']) * 2 * c['parents'] / (T * NS))
    residual = c['target'] - baseline_upper
    # Price allowance for the existing additive upper expression, not a lower
    # on realized FAST, not a change to any quota, and not an admissible Q.
    allowed_extra_reads = max(F(0), residual * T * NS / s['upper']['R'])
    allowed_single_band = max(F(0), ((allowed_extra_reads - 3) *
        c['cfg']['calendar']['c_ticks'] * s['xminus'] - s['J']) / NS)
    optional_lower = {k: F(0) for k in ('recovery', 'loss', 'false', 'physical_holds',
                                       'weak_E_repeat', 'bad_histories', 'extra_veto')}
    term_prices = {k: s['upper']['R'] * v / (T * NS) for k, v in c['terms'].items()}
    rows = c['cfe']['screen']['rows']
    return dict(schema=1, status='price diagnosis only; new initial Q remains with T196',
        unchanged=dict(W=c['W'], T=T, epsilon=F(c['cfg']['epsilon']),
                       environment=c['cfg']['environment'], cFE_profile='PR239',
                       quotas={k:c['cfg']['adaptive'][k] for k in ('recoveries_upper',
                           'ordinary_loss_episodes_upper', 'ordinary_outage_fraction',
                           'ordinary_false_expected_per_s', 'source_to_fresh_rule_upper_ns')}),
        diagnostic_calendar=dict(k=c['k'], period_s=cmp.period(c['cfg'], c['k'])['upper_ns']/NS,
             short_hold_s=c['plan']['short_hold_s'], long_hold_s=c['plan']['long_hold_s'],
             timer_quantum_ticks=c['plan']['timer_quantum_ticks'], calendar=c['cal'],
             price_times={k:c[k] for k in ('tau','w_upper','h_upper','pair_upper','d','V','H','L')},
             implementation_approved=False, Q=None),
        mandatory_lower=dict(application=c['A'], application_plus_support=support_lower,
                             optional_additional_lower=optional_lower,
                             scope='additional lower not proved; zeros are not expected-event estimates',
                             fivefold_not_excluded=support_lower <= c['target']),
        competitors={name:dict(core_upper=F(rows[name]['price']['core_upper']),
            Q_upper=F(rows[name]['risk']['upper']), sufficient=rows[name]['sufficient'])
            for name in ('fixed44','OFF39','OFF44')},
        sufficient_upper_components_before_cap=term_prices,
        optimistic_zero_pbad_v_slice=no_start, conditional_epsilon_zero_v_slice=epsilon_slice,
        startup_only_removal=dict(removed_raw_read_addend=c['recover_one'],
             removed_raw_core_addend=s['upper']['R']*c['recover_one']/(T*NS),
             same_capped_upper_with_start=with_start['core_upper']==no_start['core_upper'],
             no_other_component_removed=True),
        price_contract=dict(fivefold_witness_target=c['target'],
             baseline_app_support_normal_repairs_upper=baseline_upper,
             residual_for_all_other_core_terms=residual, extra_read_count_budget=allowed_extra_reads,
             single_additive_band_budget_s=allowed_single_band,
             meaning='budget for adaptive upper below Cf_upper/5; neither gain certificate nor fixed-class comparison',
             condition='B0+BR+BO+BERR+pbad*NH+Sv*v*T must fit extra-count budget before cap; also pay repairs and hardware',
             cold_start_Q='must be supplied separately; recovery never becomes clean-state'),
        full_cost_preserved_parameters=c['cfe']['full_cost_additional_parameters'],
        computations=dict(new_Q_calls=0, old_k27_replays=0, archive_rows=0,
                          controller_executions=0, new_hold_simulations=0),
        provenance=dict(base=c['manifest']['base_main'], plan=c['manifest']['plan_commit'],
                        frozen_files=len(c['manifest']['sha256'])))


def overview(r):
    return dict(period_h=float(r['diagnostic_calendar']['period_s']/3600),
        mandatory_lower_us_per_s=float(r['mandatory_lower']['application_plus_support']*10**6),
        fivefold_target_us_per_s=float(r['price_contract']['fivefold_witness_target']*10**6),
        component_upper_us_per_s={k:float(v*10**6) for k,v in r['sufficient_upper_components_before_cap'].items()},
        zero_slice_core_upper=float(r['optimistic_zero_pbad_v_slice']['core_upper']),
        epsilon_slice_core_upper=float(r['conditional_epsilon_zero_v_slice']['core_upper']),
        residual_budget_us_per_s=float(r['price_contract']['residual_for_all_other_core_terms']*10**6),
        single_band_budget_s=float(r['price_contract']['single_additive_band_budget_s']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group(required=True)
    for flag in ('probe', 'write', 'check'):
        options.add_argument('--'+flag, action='store_true')
    args = parser.parse_args()
    result = evaluate(); data = encoded(result); out = HERE/'outputs/result.json'
    if args.write:
        out.parent.mkdir(exist_ok=True); out.write_bytes(data)
    if args.check and out.read_bytes() != data:
        raise AssertionError('Exact residual price replay differs')
    print(json.dumps(dict(**overview(result), exact_replay=args.check), indent=2))

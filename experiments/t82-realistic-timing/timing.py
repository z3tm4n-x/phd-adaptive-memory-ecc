"""T82 wrapper: exact old-T73 timing/resource audit, no proof changes."""
from __future__ import annotations

import copy
from fractions import Fraction as F
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T72 = HERE.parent / 't72-r0a-onset-inputs'
sys.path.insert(0, str(T72))
from confirm_t73_sync import expand, read_new, source_check  # noqa: E402
from verify_t73 import bounds, calculate, t58  # noqa: E402


def load_config():
    return json.loads((HERE / 'config.json').read_text(encoding='utf-8'))


def inputs():
    source_check()
    return expand(read_new())


def tick_bounds(cfg):
    s = cfg['service']
    dt = F(s['tick_nominal_s'])
    return dt * F(s['constant_clock_scale_min']), dt * F(s['constant_clock_scale_max'])


def min_ticks(upper, margin, quantum_min):
    return t58.ceil((1 + F(margin)) * F(upper) / quantum_min)


def resources(cfg, g=None):
    s, r = cfg['service'], cfg['resources']
    tm, tp = tick_bounds(cfg)
    c = s['c_ticks'] * tp
    gmin = (s['g_ticks'] if g is None else g) * tm
    h = F(r['peak_window_s'])
    cm, sm = F(r['extra_monitor_control_rate']), F(r['extra_monitor_control_sigma_s'])
    peak = (t58.mask_bound(2*c, 2*gmin, h) + sm + cm*h) / h
    block = 2*c + F(r['application_max_request_s'])
    rate = 1 - block/(2*gmin)
    delay = block + (F(r['application_sigma_s']) + sm)/rate if rate > 0 else None
    ok = (gmin >= c and peak <= F(r['peak_limit']) and
          rate >= F(r['application_rate'])+cm and delay is not None and
          delay <= F(r['application_delay_limit_s']))
    return dict(peak=peak, rate=rate, delay=delay, ok=ok)


def minimum_resource_g(cfg, app_margin=F(0)):
    # An addressed scalar boundary, not a channel/control-parameter search.
    # Finite declared bracket; every preceding integer is checked.
    for g in range(cfg['service']['c_ticks'], 10001):
        rv = resources(cfg, g)
        if rv['ok'] and (1+app_margin)*rv['delay'] <= F(cfg['resources']['application_delay_limit_s']):
            return g
    raise ValueError('No resource boundary within declared g<=10000 ticks')


def low_required(cfg):
    s, m = cfg['service'], cfg['monitor']
    _, tp = tick_bounds(cfg)
    # (5), including all clock upper sides once; f=c after retiming.
    return (2*int(m['window_ticks']) + int(m['delivery_computation_deadline_after_window_ticks'])
            + s['decision_lead_ticks'] + 2*s['g_ticks']-s['c_ticks']
            + s['fence_ticks'] + cfg['scenario']['W']*s['g_ticks']) * tp


def service_upper(architecture, config=None):
    config = load_config() if config is None else config
    if architecture == 'internal38_nominal_projection':
        return F(config['internal_nominal_read_s']) + F(config['internal_nominal_write_s'])
    if architecture == 'external39_resource_projection':
        return F(config['external_conditional_executor_upper_s'])
    raise ValueError(architecture)


def retime(original, margin, architecture, repair_resource=False, program_margin=False):
    cfg = copy.deepcopy(original)
    s, m, r = cfg['service'], cfg['monitor'], cfg['resources']
    tm, tp = tick_bounds(cfg)
    mgn = F(margin)
    cu = service_upper(architecture)
    s['c_ticks'] = max(s['c_ticks'], min_ticks(cu, mgn, tm))
    s['fence_ticks'] = s['c_ticks']
    s['required_joint_U_WCET_physical_s'] = str(F(s['c_ticks'])*tm/(1+mgn))
    s['decision_lead_ticks'] = max(s['decision_lead_ticks'], min_ticks(
        F(r['application_max_request_s'])+F(s['gate_logic_wcet_s']), mgn, tm))
    d = F(m['required_delivery_computation_physical_max_s'])
    m['delivery_computation_deadline_after_window_ticks'] = str(max(
        int(m['delivery_computation_deadline_after_window_ticks']), min_ticks(d, mgn, tm)))
    # Original d_E is an assumed physical upper, not a measured delivery.
    err_upper = F(original['own_ERR']['max_delivery_s'])
    err_ticks = min_ticks(err_upper, mgn, tm)
    cfg['own_ERR']['max_delivery_s'] = str(err_ticks*tp)
    cfg['t82_timing'] = dict(ERR_actual_upper_s=str(err_upper), ERR_budget_ticks=err_ticks,
                             service_basis=str(cu), margin=str(mgn), architecture=architecture)
    if repair_resource:
        s['g_ticks'] = minimum_resource_g(cfg, mgn if program_margin else F(0))
    m['lease_end_from_window_start_ticks'] = str(max(
        int(m['lease_end_from_window_start_ticks']), min_ticks(low_required(cfg), mgn, tm)))
    return cfg


def margin_rows(cfg, margin, architecture):
    s, m, r = cfg['service'], cfg['monitor'], cfg['resources']
    tm, _ = tick_bounds(cfg)
    metadata = cfg.get('t82_timing', {})
    err_upper = F(metadata.get('ERR_actual_upper_s', cfg['own_ERR']['max_delivery_s']))
    err_available = (int(metadata['ERR_budget_ticks'])*tm if metadata else
                     F(cfg['own_ERR']['max_delivery_s']))
    data = [
        ('U', s['c_ticks']*tm, service_upper(architecture),
         'nominal_45+45_not_WCET' if architecture.startswith('internal') else 'conditional_existing_executor_upper'),
        ('delivery_compute', int(m['delivery_computation_deadline_after_window_ticks'])*tm,
         F(m['required_delivery_computation_physical_max_s']), 'T73_assumed_physical_upper'),
        ('gate_with_application_guard', s['decision_lead_ticks']*tm,
         F(r['application_max_request_s'])+F(s['gate_logic_wcet_s']), 'T73_assumed_joint_guard_upper'),
        ('ERR_delivery', err_available, err_upper, 'T73_assumed_ERR_upper_not_measured'),
        ('LOW_lease', int(m['lease_end_from_window_start_ticks'])*tm,
         low_required(cfg), 'T73_equation_5_rational_upper'),
    ]
    rv = resources(cfg)
    data.append(('application_delay', F(r['application_delay_limit_s']),
                 rv['delay'] if rv['rate']>=F(r['application_rate'])+F(r['extra_monitor_control_rate']) else None,
                 'T73_FIFO_upper_if_stable'))
    rows = []
    for name, a, c, source in data:
        if c is None:
            rows.append(dict(bound=name, available_min_s=a, execution_upper_or_basis_s=None,
                             pass_margin=False, source=source, physical_qualification=False))
            continue
        rows.append(dict(bound=name, available_min_s=a, execution_upper_or_basis_s=c,
                 absolute_slack_s=a-c, relative_slack=a/c-1, required_margin=F(margin),
                 required_margin_slack_s=a-(1+F(margin))*c,
                 admissible_upper_s=a/(1+F(margin)), pass_margin=a>=(1+F(margin))*c,
                 overhead_budget_s=a/(1+F(margin))-c if name=='U' else None,
                 source=source, physical_qualification=False))
    return rows


def failures(cfg, values, margins):
    out = []
    if cfg['service']['c_ticks'] > cfg['service']['g_ticks']:
        out.append('calendar_c_gt_g')
    out.extend('margin_'+row['bound'] for row in margins if not row['pass_margin'])
    tests = [('LOW_margin', 'LOW_certificate'), ('alpha_margin', 'mission_alpha'),
             ('time_margin_s', 'LOW_coverage'), ('strip_margin_s', 'price_strip'),
             ('risk_margin', 'risk'), ('peak_margin', 'peak'), ('FIFO_margin', 'FIFO'),
             ('app_delay_margin_s', 'application_delay'), ('quiet_margin', 'quiet_tax')]
    out.extend(reason for key, reason in tests if values[key] < 0)
    if values['quiet_returns_upper'] > F(cfg['resources']['quiet_tax_limit']):
        out.append('return_tax')
    return out


def evaluate_old():
    rows, directed, timing, expanded, fixed, edges = [], [], [], [], [], []
    config = load_config()
    for variant in inputs():
        name, original = variant['set'], variant['input']
        for margin in config['margins']:
            for architecture in ['internal38_nominal_projection', 'external39_resource_projection']:
                for stage in ['original', 'retimed_same_g', 'retimed_resource_g', 'retimed_all_deadlines_g']:
                    cfg = original if stage == 'original' else retime(
                        original, margin, architecture, stage in ['retimed_resource_g', 'retimed_all_deadlines_g'],
                        stage == 'retimed_all_deadlines_g')
                    ident = dict(set=name, margin=margin, architecture=architecture, stage=stage)
                    expanded.append(dict(**ident, input=cfg))
                    mr = margin_rows(cfg, margin, architecture)
                    timing.extend(dict(**ident, **row) for row in mr)
                    internal = architecture.startswith('internal')
                    for env in cfg['environments']:
                        v = calculate(cfg, env)
                        key = dict(**ident, shield_g_cm2=env['shield_g_cm2'])
                        bad = failures(cfg, v, mr)
                        metrics = ['risk_upper', 'quiet_mission_upper', 'quiet_returns_upper',
                                   'peak_upper', 'app_delay_upper_s', 'LOW_margin', 'time_margin_s',
                                   'strip_margin_s', 'short_period_upper_s', 'long_period_upper_s']
                        # External does NOT inherit full38 hazard/cost certificate.
                        public = {k: v[k] if internal or k in ['peak_upper', 'app_delay_upper_s',
                                  'short_period_upper_s', 'long_period_upper_s'] else None for k in metrics}
                        if v['FIFO_margin'] < 0 or v['FIFO_rate_lower'] <= 0:
                            public['app_delay_upper_s'] = None  # T72's 1e9 is a failure sentinel, not a bound.
                        rows.append(dict(**key, c_ticks=cfg['service']['c_ticks'],
                                         g_ticks=cfg['service']['g_ticks'],
                                         quantity_status='conditional_formulas' if internal else 'resources_only_no_risk_transfer',
                                         first_failure=bad[0] if internal and bad else
                                         ('external_not_T73_U_or_full38' if not internal else ''),
                                         failures=';'.join(bad) if internal else ';'.join(
                                             ['external_not_T73_U_or_full38'] + [x for x in bad if x in
                                              ['calendar_c_gt_g', 'peak', 'FIFO', 'application_delay'] or x.startswith('margin_')]),
                                         conditional_scalar_pass=internal and not bad,
                                         physical_qualification=False, **public))
                        if internal:
                            directed.extend(dict(**key, metric=k, value=x) for k, x in v.items())
                            fixed.append(dict(**key, **{k: x for k, x in v.items() if k.startswith('fixed_') or
                                          k.startswith('E3_arbitrary') or k in ['E3_risk_lower', 'E3_cells']}))
                        if stage in ['retimed_resource_g', 'retimed_all_deadlines_g']:
                            prev = resources(cfg, cfg['service']['g_ticks']-1)
                            app_margin = F(margin) if stage == 'retimed_all_deadlines_g' else F(0)
                            edges.append(dict(**key, g_good=cfg['service']['g_ticks'],
                                              g_bad=cfg['service']['g_ticks']-1,
                                              previous_pass=prev['ok'] and (1+app_margin)*prev['delay']<=F(
                                                  cfg['resources']['application_delay_limit_s']), previous_peak=prev['peak'],
                                              previous_delay_s=prev['delay']))
    return rows, directed, timing, expanded, fixed, edges


def old_channel_diagnostics():
    """No channel search: necessary LOW timing limit and author's rate hypotheses."""
    rows = []
    documented = json.loads((HERE/'monitor_profiles.json').read_text(encoding='utf-8'))
    profiles = {p['id']: p for p in documented['profiles']}
    rem_window = F(profiles['REM_ESA_ALC_2001']['typical_integration_s'])
    irem_gap = F(profiles['SREM_PSI']['onboard_broadcast_period_s'])
    for variant in inputs():
        cfg = variant['input']
        m, ec = cfg['monitor'], cfg['environment_contract']
        rho = max(F(ec['rho_entry_upper_per_s']), F(ec['rho_ongoing_upper_per_s']))
        hlimit = F(m['v_c_per_s'])/(rho*F(ec['l_per_s']))
        for label, w, d in [('REM_typical_window', rem_window, F(0)),
                             ('IREM_broadcast_gap_8s_optimistic', F(0), irem_gap)]:
            # d=8 here is an optimistic wait envelope test for this broadcast
            # profile, not a qualified measured delivery bound or window.
            rows.append(dict(set=variant['set'], profile=label,
                             positive_LOW_requires_lease_below_s=hlimit,
                             lease_required_at_least_s=2*w+d,
                             necessary_timing_pass=2*w+d<hlimit,
                             a_M=None, calibration_qualified=False))
    hypotheses = []
    for env in inputs()[0]['input']['environments']:
        b = F(env['bbar_per_s'])
        for area in [F('.25'), F('.5'), F(1), F('1.5')]:
            rate = 4*area
            hypotheses.append(dict(shield_g_cm2=env['shield_g_cm2'], area_cm2=area,
                                   hypothesized_rate_s_inv=rate, single_background_ratio=rate/b,
                                   qualified_a_M=None, status='hypothesis_not_spectral_convolution'))
        for ratio in [20000, 1000000]:
            hypotheses.append(dict(shield_g_cm2=env['shield_g_cm2'], area_cm2=ratio*b/4,
                                   hypothesized_rate_s_inv=ratio*b, single_background_ratio=ratio,
                                   qualified_a_M=None, status='area_required_under_4_count_hypothesis'))
    return rows, hypotheses


def err_only_fallback():
    """Accepted T73 §4: no LOW permits means always S; retain all quotas/cost."""
    rows = []
    for variant in inputs():
        for margin in load_config()['margins']:
            cfg = retime(variant['input'], margin, 'internal38_nominal_projection', True, True)
            sc, q, s, r = [cfg[k] for k in ['scenario', 'whole_mission_quotas', 'service', 'resources']]
            tm, tp = tick_bounds(cfg)
            W, n, T = sc['W'], sc['n'], F(sc['T_s'])
            eps = F(sc['epsilon'])
            intercept = F(cfg['mark_contract']['D_star_full38_direct_exposure_upper'])+sum(
                F(q[k]) for k in ['rho0', 'delta_exec', 'delta_svc', 'delta_E', 'delta_M', 'alpha_M'])
            for env in cfg['environments']:
                B = F(env['bbar_per_s'])+F(env['solar_peak_per_s'])
                slope = tp*(q['K0']*B+F(n-1, 2*n)*F(env['S2_rational_upper_per_s']))
                g = min(t58.floor((eps-intercept)/slope), t58.floor(T/(W*tp)))
                result = resources(cfg, g)
                cp = s['c_ticks']*tp
                hard = cp/(g*tm)+F(r['extra_monitor_control_rate'])
                quiet = hard+(2*cp+F(r['extra_monitor_control_sigma_s']))/T
                returns = hard+(2*cp+F(r['extra_monitor_control_sigma_s']))*1000/(F('.9')*T)
                full_ok = result['ok'] and g>=s['c_ticks'] and (1+F(margin))*result['delay']<=F(r['application_delay_limit_s'])
                rows.append(dict(set=variant['set'], margin=margin, shield_g_cm2=env['shield_g_cm2'],
                    mode='old_T73_ERR_only_always_S', g_ticks=g, c_ticks=s['c_ticks'],
                    risk_upper=intercept+g*slope, risk_next_g=intercept+(g+1)*slope,
                    quiet_upper=quiet, returns_upper=returns, peak_upper=result['peak'],
                    app_delay_upper_s=result['delay'] if result['ok'] else None,
                    resource_pass=full_ok, conditional_risk_resource_pass=full_ok,
                    best_certified_tax_in_this_always_S_family=quiet if full_ok else None,
                    first_failure='quiet_tax' if full_ok else 'resource_or_app_margin',
                    physical_qualification=False, quotas_and_control_cost_retained=True))
    return rows

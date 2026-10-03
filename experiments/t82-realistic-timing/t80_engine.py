"""Pinned T80 (4)--(11). Conditional engineering adapter, no proof changes."""
from __future__ import annotations

import copy
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import json
from math import isqrt

from timing import HERE, inputs, min_ticks, retime, tick_bounds, resources, t58

CONFIG = json.loads((HERE/'t80_config.json').read_text(encoding='utf-8'))
SOURCE = json.loads((HERE/'inputs/t80-realistic-channel-inputs.json').read_text(encoding='utf-8'))
FAMILY = SOURCE['new_family']
PROFILE = CONFIG['diagnostic_profile']
MODES = ('combined', 'monitor-only', 'ERR-only')


def source_check():
    for name, expected in CONFIG['source_blobs'].items():
        data = (HERE/'inputs'/name).read_bytes()
        actual = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual != expected:
            raise ValueError(f'Pinned source changed: {name}: {actual}')
    old = inputs()
    for lhs, rhs in zip(old, SOURCE['accepted_input_sets'], strict=True):
        if lhs['set'] != rhs['set'] or lhs['input'] != rhs['inputs']:
            raise ValueError('Four old sets must remain independently identical')
    handoff = json.loads((HERE/'inputs/t81-handoff.json').read_text())
    assert all(r['fullword_D_upper'] is None for r in handoff['architectures'])
    return old


def errors(q, mode, statistical=True):
    names = ['rho0', 'delta_exec', 'delta_svc']
    if mode != 'monitor-only':
        names.append('delta_E')
    if mode != 'ERR-only':
        names += ['delta_M'] + (['alpha_M'] if statistical else [])
    return sum(F(q[x]) for x in names)


def context(variant, margin, architecture, env_index):
    name = 'internal38_nominal_projection' if architecture == 'internal38' else 'external39_resource_projection'
    cfg = retime(variant['input'], margin, name, True, True)
    sc, s, q, r = [cfg[k] for k in ('scenario', 'service', 'whole_mission_quotas', 'resources')]
    env = cfg['environments'][env_index]
    tm, tp = tick_bounds(cfg)
    W, n, T = sc['W'], (38 if architecture == 'internal38' else 39), F(sc['T_s'])
    b, peak = F(env['bbar_per_s']), F(env['solar_peak_per_s'])
    B, FS = b+peak, 115776*peak
    S2 = F(env['S2_rational_upper_per_s'])
    assert S2 >= t58.rarity(B, b, FS, T)[1]
    return dict(set=variant['set'], margin=F(margin), architecture=architecture,
                shield=env['shield_g_cm2'], cfg=cfg, env=env, W=W, n=n, T=T,
                eps=F(sc['epsilon']), q=q, K=q['K0'], tm=tm, tp=tp,
                c=s['c_ticks'], g=s['g_ticks'], G=s['decision_lead_ticks'],
                cp=s['c_ticks']*tp, cm=s['c_ticks']*tm, gm=s['g_ticks']*tm,
                gp=s['g_ticks']*tp, Gp=s['decision_lead_ticks']*tp,
                f=s['fence_ticks']*tp, gap=(2*s['g_ticks']-s['c_ticks'])*tp,
                Ps=W*s['g_ticks']*tp, b=b, B=B, FS=FS, S2=S2,
                Dstar=F(cfg['mark_contract']['D_star_full38_direct_exposure_upper']),
                beta=F(n-1, 2*n*W), beta0=F(1, 2*W),
                dE=F(cfg['own_ERR']['max_delivery_s']),
                rF=F(PROFILE['false_ERR_rate_per_s']), rloss=F(PROFILE['recognized_ERR_loss_rate_per_s']),
                CX=F(PROFILE['resource_rate']), sigmaX=F(PROFILE['resource_sigma_s']),
                resource=resources(cfg))


def ident(p):
    return {k: p[k] for k in ('set', 'margin', 'architecture', 'shield')}


def short_gate(p, mode):
    beta = p['beta0'] if mode == 'ERR-only' else p['beta']
    intercept = errors(p['q'], mode)+p['Dstar']
    init = p['K']*p['B']*p['Ps']/p['W']
    short = beta*p['Ps']*p['S2']
    slope = p['tp']*(p['K']*p['B']+beta*p['W']*p['S2'])
    gmax = t58.floor((p['eps']-intercept)/slope)
    return dict(**ident(p), mode=mode, c=p['c'], g=p['g'],
                quota_upper=errors(p['q'], mode), direct_conditional_upper=p['Dstar'],
                initial_upper=init, short_pairs_upper=short,
                short_risk_upper=intercept+init+short,
                short_risk_slack=p['eps']-intercept-init-short,
                short_pass=intercept+init+short <= p['eps'],
                g_max_short=gmax, g_next_risk=intercept+(gmax+1)*slope,
                peak_upper=p['resource']['peak'], delay_upper_s=p['resource']['delay'],
                physical_qualification=False)


def smallest_H(J, alpha):
    H = 1
    while J*F(3, 8)**H > alpha:
        H += 1
    return H


@lru_cache(maxsize=20000)
def retrospective(qR, bU, h0min):
    # Every declared qR is below l, so E.3 is EXACT rational here.
    rho, l = F(FAMILY['rho_b_per_s']), F(FAMILY['l_per_s'])
    if not (0 <= bU <= qR < l):
        if qR <= bU:
            return F(0)
        raise ValueError('Declared linear retrospective branch required')
    v = min(h0min, (qR-bU)/(rho*l))
    return (qR-bU)*v-rho*l*v*v/2


@lru_cache(maxsize=1000)
def phi(z):
    lo, hi = t58.exp_neg(z)
    return 1-hi, 1-lo


def monitor_window(p, aM, w, d, qratio, kind):
    # Even tick count preserves h0=Delta=w/2 with a common clock.
    ticks = 2*t58.ceil(w/(2*F(p['cfg']['service']['tick_nominal_s'])))
    wm, wp = ticks*p['tm'], ticks*p['tp']
    delta_m, delta_p = wm/2, wp/2
    dticks = min_ticks(d, p['margin'], p['tm'])
    dp = dticks*p['tp']
    qR = qratio*p['b']
    bU = F(0) if kind == 'total_load' else p['b']
    mR = retrospective(qR, bU, wm/2)
    J = t58.ceil(p['T']/delta_m)  # conservative count of complete delivered windows
    H = smallest_H(J, F(p['q']['alpha_M']))
    mu = wp*(aM*F(PROFILE['upper_to_lower_ratio'])*p['b']+F(PROFILE['eta_per_s']))
    return dict(aM=aM, w=w, d=d, qratio=qratio, kind=kind, qR=qR, bU=bU,
                wm=wm, wp=wp, Delta_m=delta_m, Delta_p=delta_p,
                dticks=dticks, dmin=dticks*p['tm'], dp=dp,
                mR=mR, J=J, H=H, mu=mu)


def threshold(m, z):
    philo, phihi = phi(z)
    k = t58.floor((m['aM']*philo*m['mR']-m['H'])/z)
    # k may be negative: do not turn an uninformative channel into k=0.
    result = dict(k=k, z=z, LOW_slack=m['aM']*philo*m['mR']-z*k-m['H'],
                  next_k_slack_upper=m['aM']*phihi*m['mR']-z*(k+1)-m['H'],
                  aM_for_k0=(F(m['H'])/(philo*m['mR']) if m['mR'] else None))
    if k < 0:
        return result
    x = max(F(0), k-m['mu'])
    exponent = x*x/(2*(m['mu']+x/3)) if x else F(0)
    result['pM_upper'] = t58.exp_neg(exponent)[1] if x else F(1)
    result['tail_exponent'] = exponent
    return result


def lease(p, m, rho_e, theta, finite_zero_growth_lease=None):
    ve, l = F(FAMILY['v_e_per_s']), F(FAMILY['l_per_s'])
    vc = m['qR']+theta*(ve-m['qR'])
    assert m['qR'] < vc < ve <= l
    if rho_e < 0 or (rho_e == 0 and (finite_zero_growth_lease is None or finite_zero_growth_lease<=0)):
        raise ValueError('zero growth requires a chosen positive finite lease')
    L = (vc-m['qR'])/(l*rho_e) if rho_e else F(finite_zero_growth_lease)
    lticks = t58.floor(L/p['tp'])
    lmin = lticks*p['tm']
    extra = p['Gp']+p['gap']+p['f']+p['Ps']
    required = m['Delta_p']+m['dp']+extra
    return dict(vc=vc, theta=theta, lease_ticks=lticks, lease_min_s=lmin,
                coverage_upper_s=required,
                lease_slack_s=lmin-(1+p['margin'])*required,
                d_safe_upper_budget_s=lmin/(1+p['margin'])-m['Delta_p']-extra,
                rho_e_sufficient=(vc-m['qR'])/(l*(1+p['margin'])*required)*p['tm']/p['tp'])


def strips(p, m, DQ):
    h_ticks = min_ticks(F(1), F(0), p['tm'])
    hold = h_ticks*p['tp']
    edge = 2*p['Gp']+p['gap']+p['f']+4*p['gp']
    DE_req = hold+p['dE']+edge
    DQp = min_ticks(DQ, F(0), p['tm'])*p['tp']
    DM_req = DQp+2*m['wp']+2*m['Delta_p']+m['dp']+hold+2*p['Ps']+edge
    # Strict inequalities in (7); one additional physical upper tick.
    DE = (t58.floor(DE_req/p['tp'])+1)*p['tp']
    DM = (t58.floor(DM_req/p['tp'])+1)*p['tp']
    return DE, DM


def odd_candidates(kmax, linear):
    """Exact minimization of 1/k + min(1,A+linear*k), odd bounded k.

    The minimum of the capped expression is the smaller of the minima of
    its two branches. One decreases; the other is convex with turning
    point sqrt(1/linear). No scientific inequality is changed.
    """
    if kmax < 1:
        return []
    kmax -= 1-kmax % 2
    candidates = {1, kmax}
    if linear > 0:
        root = isqrt(linear.denominator//linear.numerator)
        low = root if root % 2 else root-1
        candidates.update(k for k in (low, low+2) if 1 <= k <= kmax)
    return sorted(candidates)


def monitor_candidate(p, m, th, le, DQ, mode):
    beta, Ps, T, b, eps = [p[k] for k in ('beta', 'Ps', 'T', 'b', 'eps')]
    DE, DM = strips(p, m, DQ)
    activeE = mode == 'combined'
    E = DE if activeE else F(0)
    gate = short_gate(p, mode)
    V = min(le['vc']**2*T, b*b*T+(le['vc']+b)*p['FS'])
    slope = beta*Ps*V
    kmax = min(4095, t58.floor(gate['short_risk_slack']/slope))
    if kmax < 1:
        return dict(status='long_risk', kmax=kmax, min_risk=gate['short_risk_upper']+slope)
    cf = p['cp']/p['gm']
    pq0 = errors(p['q'], mode, False)+p['Dstar']+p['K']*b*Ps/p['W']
    pq1 = beta*Ps*b*b*T
    false = th['pM_upper']+F(PROFILE['bad_window_probability'])
    # A recognized own-channel loss is charged with an E band too.
    err_rate = b+p['rF']+p['rloss']
    start = (DM+E*p['K'])/T
    flags = E*err_rate
    monitor = m['J']*DM/T*false
    base = start+flags+monitor+pq0
    best = None
    for ka in odd_candidates(kmax, pq1):
        Pl = ka*Ps
        risk = gate['short_risk_upper']+ka*slope
        pq = min(F(1), pq0+ka*pq1)
        quiet = cf/ka+cf*min(F(1), start+flags+monitor+pq)+(2*p['cp']+p['sigmaX'])/T+p['CX']
        TQ, KQ = F(9, 10)*T, 1000
        boundary = (DM*KQ+E*(p['K']+KQ*p['B']*(Pl+p['dE'])))/TQ
        false_returns = DM*(1/m['Delta_m']+2*KQ*m['wp']/(m['Delta_m']*TQ)+2*F(KQ)/TQ)*false
        returns = cf/ka+cf*min(F(1), boundary+flags+false_returns+min(F(1), risk)) + (2*p['cp']+p['sigmaX'])*KQ/TQ+p['CX']
        row = dict(status='certified_conditional', ka=ka, kmax=kmax,
                   risk_upper=risk, risk_slack=eps-risk,
                   next_odd_risk=gate['short_risk_upper']+(kmax+(1 if kmax%2==0 else 2))*slope,
                   quiet_upper=quiet, returns_upper=returns, base_tax=cf/ka,
                   quiet_start_component=cf*start, quiet_ERR_component=cf*flags,
                   quiet_monitor_component=cf*monitor, quiet_global_component=cf*pq,
                   channel_component=p['CX']+p['sigmaX']/T, DM=DM, DE=E,
                   risk_short=gate['short_pairs_upper'], risk_long=ka*slope,
                   D_allow=eps-risk+p['Dstar'], pM_upper=th['pM_upper'],
                   Vc=V, p_q=pq, return_boundary=cf*boundary,
                   full_goal_pass=quiet<=F('.01') and returns<=F('.01'))
        if best is None or (quiet, ka) < (best['quiet_upper'], best['ka']):
            best = row
    return best


def choose_monitor(p, aM, w, d, qratio, rho_e, DQ, kind, mode):
    gate = short_gate(p, mode)
    if not gate['short_pass']:
        return dict(status='short_risk', short_risk_upper=gate['short_risk_upper'])
    m = monitor_window(p, aM, w, d, qratio, kind)
    ts = [threshold(m, F(z)) for z in FAMILY['z']]
    usable = [t for t in ts if t['k'] >= 0]
    common = dict(mR=m['mR'], H=m['H'], J=m['J'], mu_upper=m['mu'],
                  aM_k0_sufficient=min((t['aM_for_k0'] for t in ts if t['aM_for_k0'] is not None), default=None),
                  threshold_trials=';'.join(f"{t['z']}:{t['k']}" for t in ts))
    if not usable:
        return dict(status='LOW_uninformative', **common)
    # Once k is certified, z affects only the price tail. Same risk/calendar.
    th = min(usable, key=lambda t: t['pM_upper'])  # stable declared z order on ties
    best, failed, fail_detail, trace = None, 'LOW_delay', {}, []
    for theta in map(F, FAMILY['vc_fraction_of_gap_qR_to_ve']):
        le = lease(p, m, rho_e, theta)
        if le['lease_slack_s'] < 0:
            fail_detail = le
            trace.append(f'{theta}:LOW_delay')
            continue
        candidate = monitor_candidate(p, m, th, le, DQ, mode)
        if candidate['status'] != 'certified_conditional':
            failed, fail_detail = 'long_risk', candidate
            trace.append(f'{theta}:long_risk')
            continue
        trace.append(f"{theta}:ka<= {candidate['kmax']}")
        row = dict(**common, **{k: v for k, v in th.items() if k != 'pM_upper'}, **le, **candidate)
        if best is None or (row['quiet_upper'], theta) < (best['quiet_upper'], best['theta']):
            best = row
    if best is not None:
        best['theta_trials'] = ';'.join(trace)
        return best
    return dict(common, **fail_detail) | {'status': failed, 'theta_trials': ';'.join(trace)}

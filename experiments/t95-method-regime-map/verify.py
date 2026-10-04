"""T95: exact rational proof certificates; no simulation or parameter campaign.

Run from any directory with Python >=3.10; standard library only.
--write generates report.json; default compares it byte-for-byte.
Independent engineering confirmation is requested separately via the orchestrator.
"""
from fractions import Fraction as F
from hashlib import sha1, sha256
from pathlib import Path
import argparse
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONFIG = json.loads((HERE / 'inputs.json').read_text())


def floor(x):
    return x.numerator // x.denominator


def decimal(x, upper=True, places=12):
    """Directed decimal, never binary floating point."""
    x = F(x)
    scale = 10**places
    k = -floor(-x*scale) if upper else floor(x*scale)
    sign = '-' if k < 0 else ''
    k = abs(k)
    return f'{sign}{k//scale}.{k%scale:0{places}d}'


def load(path):
    return json.loads((ROOT / path).read_text())


def ratio(x):
    return str(F(x))


def monitor_erasure_gate(mandatory, initial, hold, live, low_covers, err=False):
    # A predicate regression, not implementation #96 / an online controller.
    return mandatory or initial or hold or err or not (live and low_covers)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    checks = []

    def check(name, condition):
        assert condition, name
        checks.append(name)

    source_report = []
    for item in CONFIG['sources']:
        raw = (ROOT / item['path']).read_bytes()
        blob = sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
        check('unchanged:'+item['path'], blob == item['git_blob'])
        source_report.append(dict(item, sha256=sha256(raw).hexdigest()))
    pinned = load('experiments/t90-monitor-physical/outputs/pinned_inputs.json')
    selected = load('experiments/t88-dstar-sensitivity/outputs/selected.json')
    fixed = load('experiments/t88-dstar-sensitivity/outputs/constant_U.json')
    p = next(x for x in pinned if x['shield'] == '3')
    inp = p['effective_T88_input']
    env, svc = inp['environment'], inp['service']
    T, B, b, FS = [F(env[k]) for k in ('T', 'B', 'b', 'FS')]
    W, n = env['W'], env['n']
    eps, beta, S2 = F(env['eps']), F(env['beta']), F(env['S2'])
    tm, tp = F(svc['tick_lower_s']), F(svc['tick_upper_s'])
    cm, cp = svc['c_ticks']*tm, svc['c_ticks']*tp
    de = F(inp['quotas']['delta_exec'])
    L = FS/(B-b)
    P1, mesh = F(CONFIG['bound']['P_split_s']), F(CONFIG['bound']['P_auxiliary_mesh_s'])
    check('witness_plateau', L == 115776 and L < T and b < B)
    check('moderate_domain', 2*P1 < L and B*P1/W < 1 and cp < P1)

    def z_short(P0):
        return beta*B*B*(L-2*P1)*P0*(1-cp/P0)**2*(1-B*P1/W)

    def risk_short(P0):
        z = z_short(P0)
        return z/(1+z)-de

    J = floor(L/P1)+2
    ell = (L-J*cp)/(4*J)
    x = B*ell/W
    zlong = 2*W*J*F(n-1, 2*n)*x*x*(1-x)
    long_lower = zlong/(1+zlong)-de
    check('all_large_periods', ell > 0 and 0 < x < 1 and long_lower > eps)
    coarse = F(CONFIG['bound']['coarse_certificate_P_s'])
    check('coarse_period_certificate', risk_short(coarse) > eps)
    # G(P) strictly increases for P>cp: derivative of P-2cp+cp^2/P >0.
    lo, hi = floor(cp/mesh)+1, floor(P1/mesh)
    check('inversion_bracket', risk_short(lo*mesh) <= eps < risk_short(hi*mesh))
    while hi-lo > 1:
        mid = (lo+hi)//2
        if risk_short(mid*mesh) > eps:
            hi = mid
        else:
            lo = mid
    P0 = hi*mesh
    check('necessary_bound_neighbor', risk_short(P0-mesh) <= eps < risk_short(P0))
    # P0 is an auxiliary proof grid point, not an attainable optimal period.
    cost_lower = W*cm/P0-2*W*cp/T
    coarse_cost = W*cm/coarse-2*W*cp/T
    check('stronger_than_old_1pct', cost_lower > coarse_cost > F('0.01'))

    # Ramp witness: ve=l=0.001, slow linear part then fast exponential.
    # ln(B/l)<6 follows from B/l<256<e^6. Prove e^6>256 by a finite sum.
    factorial = 1
    exp6_lower = F(1)
    for k in range(1, 15):
        factorial *= k
        exp6_lower += F(6**k, factorial)
    l, rhoe, rhob, DQ = F('0.001'), F('0.000001'), F('0.048'), F(300)
    trslow = (l-b)/(l*rhoe)
    er_slow = (l-b)**2/(2*l*rhoe)
    trfast_upper = 6/rhob
    erfast_upper = (B-l)/rhob  # omit the nonnegative b*log term
    check('ramp_growth_and_horizon', B/l < 256 < exp6_lower and DQ+trslow+trfast_upper+L < T)
    check('ramp_fluence', er_slow+erfast_upper < FS)

    rows = []
    anchorD, controlD = F(CONFIG['anchor_Dstar']), F(CONFIG['control_Dstar'])
    base_main = p['selected_source_row']
    control = next(r for r in selected if r['shield']=='3' and r['mode']=='combined' and F(r['Dstar'])==controlD)
    err_work = next(r for r in selected if r['purpose']=='working' and r['shield']=='3' and r['mode']=='ERR-only')
    err_control = next(r for r in selected if r['shield']=='3' and r['mode']=='ERR-only' and F(r['Dstar'])==controlD)
    TQ, KQ, CX, sigma = F('0.9')*T, 1000, F('0.0001'), F('0.0000001')
    S2exact = b*b*T+(B+b)*FS
    for name, D, r, er in [('anchor',anchorD,base_main,err_work),('control',controlD,control,err_control)]:
        check(name+':source_risk', F(r['risk_upper']) <= eps and F(r['Dstar']) == D and r['resource_pass'])
        g, ka = r['g'], r['ka']
        Ps, Pl = W*g*tp, W*g*ka*tp
        check(name+':calendar_not_busy_time', Ps == F(r['period_s_upper']) and Ps > W*cp and Pl == F(r['period_l_upper']))
        vc = F(r['vc'])
        u = (Ps+Pl)*b*b
        v = max((Ps+Pl)*(vc+b),(Ps*B*B-u)/(B-b),F(0))
        Vc = min(vc*vc*T,b*b*T+(vc+b)*FS)
        QM = min(Ps*S2+Pl*Vc,Pl*S2,u*T+v*FS)
        check(name+':same_lifetime_joint_budget', QM==F(r['Q']) and F('0.000006')+D+B*Ps/W+beta*QM==F(r['risk_upper']))
        check(name+':one_global_alpha', r['J']*F(3,8)**r['H'] <= F('0.000001'))
        zlow=F(r['z'])
        check(name+':LOW_z_domain', 0<zlow<=1)
        phi=F(0)
        factorial=1
        for k in range(1,9):
            factorial*=k
            phi += (-1)**(k+1)*zlow**k/factorial
        check(name+':finite_LOW_acceptance', 10**6*phi*F(r['mass_lower']) >= zlow*r['k']+r['H'])
        cf = cp/(g*tm)
        hard = cf + CX+(2*cp+sigma)*KQ/TQ
        US = F('0.000003')+D+B*Ps/W+beta*Ps*S2
        check(name+':S_from_start', US <= eps)
        fix = next(x for x in fixed if x['shield']=='3' and x['mode_context']=='combined' and F(x['Dstar'])==D)
        M = fix['M']
        slope = tp*(beta*S2exact+B/W)
        UF = F('0.000003')+D+M*slope
        UFnext = UF+slope
        check(name+':fixed_M_Mplus1', UF == F(fix['risk_upper']) and UF <= eps < UFnext and UFnext==F(fix['next_risk_upper']) and fix['resource_pass'])
        fixed_price_upper = F(W*svc['c_ticks'],M)+2*cp*KQ/TQ
        check(name+':constant_bracket', cost_lower < fixed_price_upper)
        deltaD = D-F(er['Dstar'])
        check(name+':ERR_D_direction', deltaD >= 0)
        err_risk = F(er['risk_upper'])+deltaD
        err_price = F(er['objective'])+cp/(er['g']*tm)*deltaD
        check(name+':ERR_same_D_model_only', err_risk <= eps)
        price = F(r['objective'])
        gain = cost_lower/price
        reaction = F(svc['gate_upper_s'])+(2*g-svc['c_ticks'])*tp+F(svc['fence_upper_s'])
        check(name+':10pct_margin', cm/F(svc['joint_U_WCET_required_upper_s']) == F('1.1'))
        check(name+':resource', F(r['peak_upper']) <= F('.8') and F('1.1')*F(r['delay_upper_s']) <= F('0.000003'))
        outage_fraction = (F('.01')-price)/cf
        rows.append(dict(name=name,Dstar=ratio(D),g=g,ka=ka,
            risk_upper=ratio(F(r['risk_upper'])),risk_upper_decimal=decimal(F(r['risk_upper'])),
            normal_price_upper=ratio(price),normal_price_percent_upper=decimal(100*price),
            fixed_M=M,fixed_next_risk=ratio(UFnext),fixed_cost_upper=ratio(fixed_price_upper),fixed_percent_upper=decimal(100*fixed_price_upper),
            class_gain_lower=ratio(gain),class_gain_decimal_lower=decimal(gain,False,6),
            from_start_S_risk_upper=ratio(US),from_start_S_risk_decimal=decimal(US),
            loss_forever_risk_upper=ratio(F(r['risk_upper'])),S_full_price_upper=ratio(hard),S_full_price_percent_upper=decimal(100*hard),
            ERR_model_g=er['g'],ERR_model_ka=er['ka'],ERR_model_h_s=er['h'],ERR_model_D_shift=ratio(deltaD),
            ERR_model_risk_upper=ratio(err_risk),ERR_model_risk_decimal=decimal(err_risk),ERR_model_price_upper=ratio(err_price),ERR_model_price_percent_upper=decimal(100*err_price),
            ERR_from_monitor_switch_certified=False,
            alarm_to_first_fence_upper_s=ratio(reaction),alarm_to_all_words_upper_s=ratio(reaction+Ps),
            outage_dilated_fraction_sufficient_for_1pct=ratio(outage_fraction),outage_fraction_decimal_lower=decimal(outage_fraction,False)))

    # General vs paired phase edge: the accepted counterexample, exact units.
    phaseW, c, P, horizon, occupied = 8, 2, 200, 350, 16
    check('reject_paired_edge_for_arbitrary_phases', occupied < F(phaseW*c*horizon,P)-2*c)
    check('general_phase_edge_covers_counterexample', occupied >= F(phaseW*c*horizon,P)-2*phaseW*c)
    # Missing data can only strengthen the execute predicate; no LOW resurrection.
    for mandatory in (False,True):
        for initial in (False,True):
            for hold in (False,True):
                for low in (False,True):
                    ordinary = monitor_erasure_gate(mandatory,initial,hold,True,low)
                    lost = monitor_erasure_gate(mandatory,initial,hold,False,low)
                    check(f'erasure_dominance:{mandatory}:{initial}:{hold}:{low}', lost >= ordinary)
    check('expired_LOW_never_skips', monitor_erasure_gate(False,False,False,True,False))
    check('fresh_LOW_cannot_cancel_hold', monitor_erasure_gate(False,False,True,True,True))
    check('fresh_LOW_can_skip_after_holds', not monitor_erasure_gate(False,False,False,True,True))
    check('ERR_forces_S', monitor_erasure_gate(False,False,False,True,True,True))
    check('mandatory_always_runs', monitor_erasure_gate(True,False,False,True,True))
    check('initial_scan_always_runs', monitor_erasure_gate(False,True,False,True,True))
    check('unknowns_stay_null', all(x is None for x in CONFIG['unknowns'].values()))
    check('zero_outage_addition', cf*0/TQ == 0)
    handoff = load('experiments/t95-method-regime-map/handoff.json')
    check('handoff_calendar', handoff['fixed_contract']['g_ticks']==base_main['g'] and handoff['fixed_contract']['ka']==base_main['ka'])
    check('handoff_fence_deadlines', F(handoff['conditional_timing']['alarm_to_first_new_fence_s'])==F(rows[0]['alarm_to_first_fence_upper_s']) and F(handoff['conditional_timing']['alarm_to_all_words_s'])==F(rows[0]['alarm_to_all_words_upper_s']))
    check('handoff_same_D_and_no_ERR_switch', F(handoff['fixed_contract']['Dstar'])==anchorD and not handoff['loss_policy']['ERR_only_transition_certified'])
    # This is a mathematical regression, not a simulator of latch/fence/CPU-WCET.
    report=dict(task=95,base_sha=CONFIG['base_sha'],independent_engineering_confirmation='requested, not performed by this script',
        algorithm='one monotone rational inversion plus accepted-row substitutions; no search for a controller',
        lower_bound=dict(P0_s=ratio(P0),P0_s_decimal=decimal(P0),P0_predecessor_s=ratio(P0-mesh),
            G_P0=ratio(risk_short(P0)),G_P0_decimal_lower=decimal(risk_short(P0),False,15),G_predecessor=ratio(risk_short(P0-mesh)),
            P_split_s=ratio(P1),J=J,ell_s=ratio(ell),large_period_risk_lower=ratio(long_lower),large_period_risk_decimal_lower=decimal(long_lower,False,15),
            coarse_P0_s=ratio(coarse),coarse_risk_lower=ratio(risk_short(coarse)),coarse_class_percent_lower=decimal(100*coarse_cost,False),
            fixed_class_cost_lower=ratio(cost_lower),fixed_class_percent_lower=decimal(100*cost_lower,False)),
        rows=rows,checks=checks,check_count=len(checks),sources=source_report)
    data=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    target=HERE/'report.json'
    if args.write:
        target.write_text(data)
    else:
        assert target.read_text()==data, 'published report differs'
    print(json.dumps({'checks':len(checks),'P0_s':decimal(P0),'class_price_percent_lower':decimal(100*cost_lower,False),
        'tail_risk_lower':decimal(long_lower,False),'rows':[{k:v for k,v in r.items() if k.endswith('decimal') or 'percent_' in k or k in ('name','class_gain_decimal_lower','fixed_M')} for r in rows]},indent=2))


if __name__ == '__main__':
    main()

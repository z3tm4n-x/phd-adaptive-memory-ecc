"""Targeted arithmetic, not a replay of the upstream controllers or missions."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
from math import ceil, log, expm1, sqrt, gcd
from functools import reduce


def run(cfg):
    W, H = cfg['words'], F(cfg['horizon_s'])
    P, slot, G = map(F, [cfg['pass_s'], cfg['rmw_slot_s'], cfg['G']])
    low, high = F(cfg['b_low']), F(cfg['b_high'])
    eps, beta, num = map(F, [cfg['epsilon'], cfg['beta'], cfg['numeric_reserve']])
    cases = []
    for scale, tau in [(F(1), F(1)), (F(39, 32), F(1)), (F(39, 32), F(1, 2))]:
        lo, hi = low*scale, high*scale
        c = (lo*lo + hi*hi)/2
        n = H/tau
        assert n.denominator == 1 and P < tau
        # Stationary E[b(t)b(s)] <= E[b^2]=c, all D. Discrete scan <= P/2.
        V = (n*tau*tau/2 + (n-1)*P*tau/2)*c/W
        rmw = hi*slot*n
        nu, v = P/30, (hi-lo)*P
        # Probability/TV ledger from the input derivation; upper-bounded
        # rationally using p1<=nu, p2<=nu^2/2, P(Nswitch>=3)<=nu^3/6.
        delta = 18000*(nu**3/6 + nu*(4*v+4*v*v)/(24*512**2)
                 + nu*nu*(40*v+40*v*v)/(2*24*128**2)
                 + P*(hi+nu*(hi-lo))/(4*W*W))
        room = (eps-rmw-beta)/G-num-delta-V
        m=(hi+lo)/2; amplitude=(hi-lo)/2
        corr_lower=m*m+amplitude*amplitude*max(F(0),1-2*(tau+P)/3000)
        measure=n*tau*tau/2+(n-1)*P*(W-1)*tau/(2*W)
        lower=corr_lower*measure/W
        cases.append(dict(rate_scale=str(scale), backup_s=float(tau),
            starts_upper=int(n), auxiliary_initial_upper=float(V),
            rmw_upper=float(rmw), model_tv_upper=float(delta),
            backup_lower_at_D3000=float(lower),
            slack_lower_conditional_on_numeric_reserve=float(room),
            exact_slack_fraction=str(room),
            numeric_reserve_status='assumed_for_modified_backend_not_verified'))
    assert cases[0]['slack_lower_conditional_on_numeric_reserve'] > 0
    assert cases[1]['slack_lower_conditional_on_numeric_reserve'] < 0
    assert cases[1]['backup_lower_at_D3000'] > float((eps-beta)/G-num)
    assert cases[2]['slack_lower_conditional_on_numeric_reserve'] > 0

    # Addressed check of the four input quadrature values governing bus choice.
    reconstructed = []
    with localcontext() as ctx:
        ctx.prec = 70
        d = lambda x: Decimal(str(x))
        for D, ps, source in cfg['backup_witnesses']:
            k=d(2)/d(D); p=d(ps); m=(d(cfg['b_high'])+d(cfg['b_low']))/2
            v=(d(cfg['b_high'])-d(cfg['b_low']))/2
            J=(1-(-k).exp())/k
            f=m*m/2+v*v*(1/k-(1-(-k).exp())/(k*k))
            I=1/k-(1-(-k*p).exp())/(p*k*k)
            value=(d(3600)*f+d(3599)*(m*m*p/2+v*v*I*J))/d(W)
            err=abs(float(value)-source)
            assert err < 2e-15
            reconstructed.append(dict(D=D, pass_s=ps, value=str(value),
                input_value=source, abs_difference=err))

    peak=cfg['inherited_peak_per_hour']/3600
    mean=cfg['inherited_mean_per_hour']/3600
    class_rows=[]
    for label, periods in [('RES_grid_12', cfg['periods_s']),
                          ('input_screen_grid_15', cfg['screen_periods_s'])]:
        for e in [.001,.01,.1]:
            feasible=[]
            for a in periods:
                for b in periods:
                    t=0; complete=0; horizon=3600000000000
                    an=int(round(a*10**9)); bn=int(round(b*10**9))
                    while True:
                        tau=an if t<horizon//2 else bn
                        if t+tau>horizon: break
                        t+=tau; complete+=1
                    partial=int(t+tau-int(P*10**9)<horizon<t+tau)
                    Q=3600*peak**2*max(a,b)/(2*W)
                    guard=peak*float(slot)*(complete+partial)
                    if Q+guard<=e: feasible.append((complete,a,b,Q+guard))
            best=min(feasible)
            class_rows.append(dict(action_class=label, epsilon=e,
                candidates=len(periods)**2, best_complete_passes=best[0],
                first_s=best[1], second_s=best[2], upper=best[3]))
    assert [r['best_complete_passes'] for r in class_rows[:3]]==[120,12,12]
    assert [r['best_complete_passes'] for r in class_rows[3:]]==[120,12,1]
    A=3600*30/(2*W); B=120*float(slot)
    critical=2*.001/(B+sqrt(B*B+4*A*.001))
    headroom=.001-A*peak*peak-B*peak
    # First auxiliary count from clean memory: exact discrete scan exposure.
    info=[]
    for label, rate in [('mean',mean),('peak',peak)]:
        t95=log(20)/rate
        for tau in [30,300]:
            exposure=tau-float(P)*(W-1)/(2*W)
            aux=-expm1(-rate*exposure)
            pair=rate*rate*tau*tau/(2*W)
            rmw=rate*float(slot)
            info.append(dict(anchor=label, tau_s=tau, first_arrival_t95_s=t95,
                auxiliary_first_positive_probability=aux,
                physical_first_positive_lower=max(0,aux-pair-rmw),
                physical_first_positive_upper=min(1,aux+pair+rmw),
                assumptions='clean; constant homogeneous Poisson; qualified full-word ECC/RMW'))
    durations=[45,180,360,100000000,500000000,1000000000]
    quantum=reduce(gcd,durations)
    assert quantum==5
    assert F(100000000,1)/F(15,2) != int(F(100000000,1)/F(15,2))
    return dict(backup_cases=cases, addressed_backup_reconstruction=reconstructed,
        max_gap_classes=class_rows, rate_threshold=dict(critical_per_hour=critical*3600,
        relative_increase_percent=(critical/peak-1)*100,
        direct_event_probability_room=headroom), observation_checks=info,
        time_lattice=dict(coarsest_common_quantum_ns=quantum,
        single_clock_realization_MHz=1000/quantum,
        original_7p5ns_clock_exact_0p1s=False,
        clock_realization='not_synthesized_or_timing_verified'))

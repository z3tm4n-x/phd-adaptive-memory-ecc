"""One feasibility substitution of T196 fixed-window bounds; no T119 integration.

Run from any directory. Default prints exact results; --check compares the
committed result. Decimal sqrt selects a candidate only: admission uses exact
rationals and the frozen directed exponential/logarithm implementation.
"""
from decimal import Decimal, localcontext
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = ROOT / 'experiments/t186-method-comparison/code-strength/common-input.json'
IV = ROOT / 'experiments/t114-two-stage-err/intervals.py'
PINS = {
    INPUT: 'e635327d07e74742247c5ad56cbf865c1bf05c362910dad5e56ce94b8d4c550e',
    IV: '817cdad503f8432fe9d57c0b9340921b1af683b8db4b72aa9314ccf0f53b3be2',
}
for path, digest in PINS.items():
    assert hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest() == digest
spec = importlib.util.spec_from_file_location('t196_window_intervals', IV)
iv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iv)
I = iv.I


def enclosure(x):
    return {'lo': str(x.lo), 'hi': str(x.hi)}


def check_thinned_calendar():
    """Small deterministic checks of the NEW thinned FAST and right guard.

    They supplement the interval inclusion proof, not a mission simulation.
    """
    W, kH, kL, horizon = 4, 2, 16, F(160)
    h, delay, freeze, err, H, aperture = F(2), F(1,2), F(1,4), F(1,8), F(9), F(1,4)
    lead = h+delay+freeze+H
    C = lead+2*err
    checked, missing_right_counterexample = 0, False
    for start in (F(50), F(201,4), F(107,2), F(231,4), F(154)):
        end = min(horizon, start+10)
        for d in (F(0), delay):
            for error in (-err, err):
                for lost in (False, True):
                    for right in (H, F(0)):
                        commands = []
                        for i in range(81):
                            t = F(2*i)
                            fast = (t+error-err <= end+right and t+error+lead+err >= start)
                            # Known loss, followed by a full H recovery; not clean-state.
                            fast |= lost and F(40) <= t <= F(45)+H
                            fast |= t <= H or t >= horizon-C
                            commands.append((t+d, i, fast))
                        active = []
                        for j in range(int(horizon)):
                            q, phi = F(j), F(j)-freeze
                            ready = [c for c in commands if c[0] <= phi]
                            fast = max(ready, key=lambda c:c[1])[2] if ready else True
                            selected = j<W or (j//W)%kL==0 or ((j//W)%kH==0 and fast)
                            if selected:
                                active.append(q)
                            if right and (j//W)%kH==0 and start-H <= q <= end+H:
                                assert selected
                            if right and not lost and fast and q>C and q<horizon-C:
                                assert start-C <= q <= end+C
                        for word in range(W):
                            cuts = [F(0)]+[q for q in active if int(3*q)%W==word and q+aperture<=horizon]+[horizon]
                            for left, upper in zip(sorted(set(cuts)), sorted(set(cuts))[1:]):
                                if max(left,start) < min(upper,end):
                                    if right:
                                        assert upper-left <= W*kH+aperture
                                    elif upper-left > W*kH+aperture:
                                        missing_right_counterexample = True
                        if right:
                            checked += 1
    assert missing_right_counterexample
    return dict(histories=checked, omitted_right_guard_counterexample=True)


def run():
    cfg = json.loads(INPUT.read_text())
    e, s, cal = cfg['environment'], cfg['service'], cfg['calendar']
    W, n, T = cfg['words'], 39, F(cfg['mission_s'])
    den = e['reference_words'] * e['reference_bits']
    b, B, FS, rho, ell = [F(e[k]) for k in (
        'reference_background_per_s', 'reference_peak_per_s',
        'reference_solar_mass', 'reference_growth_per_s',
        'reference_growth_threshold_per_s')]
    xm, xp = F(s['clock_lower']), F(s['clock_upper'])
    J = F(s['operation_endpoint_span_ns']) / 10**9
    E = F(124) * xp / 10**9 + J
    aperture = E + 2 * J
    delta0, delta_p = F(cfg['lifetime_other_budget']), F('0.000001')
    delta = delta0 + delta_p
    eps = F(cfg['epsilon'])
    cycle, duration, uncertainty = F(5400), F(600), F(30)
    h, h_min = xp+J, xm-J  # nominal one-second polling timer
    delay, time_error, H = F('.01'), F('.001'), F(1)
    freeze = cal['freeze_ticks'] * xp / 10**9 + J
    C = h + delay + freeze + H + 2*time_error
    Nwin = int(T / cycle)
    assert Nwin * cycle == T
    nloss = cfg['adaptive']['ordinary_loss_episodes_upper']
    loss_time = F(cfg['adaptive']['ordinary_outage_fraction']) * T
    false_count = F(cfg['adaptive']['ordinary_false_expected_per_s']) * T
    # Outer price bands, including conservative two-sided loss/false padding.
    measure = Nwin*(duration + 2*uncertainty + 2*C)
    measure += loss_time + 2*C*(nloss + false_count)
    components = Nwin + nloss + false_count
    theta = measure/T

    # New witness. Ramps are paid in Fs; only constant 430 s plateaux enter lower Q.
    log = (I(B)/I(ell)).ln()
    rise = (I(1-b/ell)+log)/I(rho)
    ramp_mass = (I((ell-b)**2/(2*ell)+B-ell)-I(b)*log)/I(rho)
    witness_mass = I(256)*(ramp_mass+I((B-b)*430))
    assert F(rise.hi)+430 < duration
    assert F(witness_mass.hi) <= FS
    assert 256 <= Nwin

    K = F(W*n*(n-1), 2*den**2)
    a, z = K*(B+b)*FS, K*b*b*T
    cross = 2*K*B*aperture*(b*T+FS)
    fixed_part = delta + (a+z)*aperture + cross
    # Minimize theta/PH + 1/PL subject to a*PH+z*PL <= eps-fixed_part.
    # This only proposes the single pair; costs below include all omitted terms.
    with localcontext() as ctx:
        ctx.prec = 80
        dec = lambda x: Decimal(x.numerator)/Decimal(x.denominator)
        ratio = dec(a/(z*theta)).sqrt()
        ph = dec(eps-fixed_part)/(dec(a)+dec(z)*ratio)
        pl = ph*ratio
        base_plus = F(W*cal['g_ticks'])*xp/10**9
        kh = int((F(ph)-J)/base_plus)
        multiplier = int((F(pl)-J)/(kh*base_plus))
    kl = kh*multiplier
    assert kh >= 1 and multiplier >= 1
    Pplus = lambda k: F(k*W*cal['g_ticks'])*xp/10**9+J
    Pminus = lambda k: F(k*W*cal['g_ticks'])*xm/10**9-J
    PH, PL = Pplus(kh), Pplus(kl)
    assert PH+aperture <= H
    assert duration+2*uncertainty+2*C < cycle
    terms = dict(old_exceptions=delta0, forecast_exceptions=delta_p,
                 background=z*(PL+aperture),
                 solar_and_background_cross=a*(PH+aperture), E_cross=cross)
    U = sum(terms.values(), F(0))
    assert U <= eps

    # Counterexample for EVERY common constant physical period P >= P0.
    lam = F(n)*B/den
    def lower_q(p0):
        M = F(430)/p0+2
        free = max(F(0), 430-M*aperture)
        squares = free*free/(M+1)
        Z = I(W*256*F(38,39)*lam*lam*squares/2)*I(-lam*430).exp()
        return I(1)-(I(0)-Z).exp()-I(delta0)
    lo, hi = 1, 1000000
    while F(lower_q(F(hi,10**6)).lo) <= eps:
        hi *= 2
    while hi-lo > 1:
        mid = (lo+hi)//2
        if F(lower_q(F(mid,10**6)).lo) > eps:
            hi = mid
        else:
            lo = mid
    P0 = F(hi,10**6)
    assert F(lower_q(F(lo,10**6)).lo) <= eps < F(lower_q(P0).lo)
    assert aperture < P0

    # S_H counts STARTED operations, including terminal unfinished work.
    slots = lambda length: W*(length/Pminus(kh)+2)
    hard = W*(T/Pminus(1)+2)
    read_terms = dict(slow_support=W*(T/Pminus(kl)+2),
        windows_loss_false=W*(measure/Pminus(kh)+2*components),
        startup_and_tail=W+2*slots(C), exceptional_execution=delta*hard)
    reads = min(hard, sum(read_terms.values(), F(0)))
    parents = F(W*n,den)*(b*T+FS)
    repairs = min(reads, 2*parents+U*hard)
    # Data failure never changes the time/health selector; repairs after A still paid.
    read_bus = F(48)*xp/10**9+J
    write_bus = F(56)*xp/10**9+J
    read_core = F(68)*xp/10**9+J
    bus = (read_bus*reads+write_bus*repairs)/T
    core = (read_core*reads+write_bus*repairs)/T
    Lbus = W*(F(48)*xm/10**9-J)*(1/(P0+J)-2/T)
    Lcore = W*(F(68)*xm/10**9-J)*(1/(P0+J)-2/T)

    app = cfg['application']
    app_n = (int(T)*10**9-1-app['first_ns']-app['read_offset_ns'])//app['epoch_ns']+1
    # One common ECC beat per useful read; initialization includes all write beats.
    common_lo = (app_n*(F(16)*xm/10**9-J)+W*(F(56)*xm/10**9-J))/T
    common_hi = (app_n*(F(16)*xp/10**9+J)+W*(F(56)*xp/10**9+J))/T
    positive = Lbus+common_lo-bus-common_hi
    five = (Lbus+common_lo)/5-bus-common_hi
    # Constant k22 remains sufficient over the original larger environment class.
    fixed_upper = delta0+K*Pplus(22)*(b*b*T+(B+b)*FS)+cross
    assert fixed_upper <= eps
    return {
        'status': 'AUTHOR_FEASIBILITY_SUBSTITUTION_NOT_ACCEPTED',
        'base_main': '1275796ef6faece0c42fb008dc5637bf6c7eb0c4',
        'plan_commit': '6bd2de2ba9c6e48784f510837617d56bc0cd6987',
        'small_calendar_check': check_thinned_calendar(),
        'model': {'words': W, 'T_s': T, 'epsilon': eps, 'code': [39,32],
            'cycle_s': cycle, 'nominal_phase_s': 1800, 'duration_s': duration,
            'boundary_error_s': uncertainty, 'windows': Nwin,
            'poll_step_upper_s': h, 'poll_step_lower_s': h_min,
            'command_delay_s': delay, 'time_error_s': time_error,
            'complete_fast_cover_s': H, 'price_padding_s': C,
            'loss_time_upper_s': loss_time, 'loss_episodes_upper': nloss,
            'false_count_expected_upper': false_count, 'price_band_measure_upper_s': measure},
        'witness': {'pulses': 256, 'plateau_s': 430, 'rise_s': enclosure(rise),
            'solar_mass': enclosure(witness_mass), 'solar_budget': FS,
            'P0_s': P0, 'previous_P0_s': F(lo,10**6), 'Q_lower_enclosure': enclosure(lower_q(P0)),
            'previous_Q_enclosure': enclosure(lower_q(F(lo,10**6)))},
        'adaptive': {'continuous_PH_proposal_s': str(ph), 'continuous_PL_proposal_s': str(pl),
            'kH': kh, 'kL': kl, 'PH_upper_s': PH, 'PL_upper_s': PL,
            'Q_upper': U, 'Q_terms': terms, 'slack': eps-U, 'relative_slack': (eps-U)/eps,
            'read_terms': read_terms, 'reads_upper': reads, 'repairs_upper': repairs,
            'original_hard_cap': hard, 'parent_count_upper': parents,
            'pure_bus_upper': bus, 'serial_core_upper': core},
        'fixed': {'admitted_period_upper_s': P0+J,
            'pure_bus_class_lower': Lbus, 'serial_core_class_lower': Lcore,
            'sufficient_k': 22, 'sufficient_Q_upper_conservative': fixed_upper},
        'common_cost': {'useful_reads': app_n, 'useful_writes': 0,
            'ECC_and_initial_bus_lower': common_lo, 'ECC_and_initial_bus_upper': common_hi,
            'payload_two_beats_nominal_fraction': F(app_n*32,10**9)/T,
            'initial_encodes': W, 'initial_write_beats': 3*W,
            'common_app_decodes': app_n, 'active_check_bits': 7*W,
            'padding_bits': 9*W, 'raw_bytes': 6*W},
        'comparison': {'checks_repairs_gain_at_u0': Lbus/bus,
            'protection_gain_at_u0_with_common_ECC': (Lbus+common_lo)/(bus+common_hi),
            'unknown_management_bus_fraction': None,
            'strict_gain_management_budget': positive,
            'fivefold_management_budget': five,
            'polls_upper': T/h_min+2, 'CPU_value': None, 'energy_value': None,
            'channel_memory_value': None, 'physical_Q': None},
    }


if __name__ == '__main__':
    payload = json.dumps(run(), indent=2, sort_keys=True, default=str)+'\n'
    if '--check' in sys.argv:
        assert (HERE/'result.json').read_text() == payload
        print('Exact replay OK; SHA256 '+hashlib.sha256(payload.encode()).hexdigest())
    else:
        print(payload, end='')

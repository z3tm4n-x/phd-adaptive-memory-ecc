"""T140 addressed arithmetic; no trajectory campaign or physical qualification.

Default: recompute and byte-compare only this task's report.json. --write emits
only that new report. Accepted inputs are checked against the author's base.
All decisions use Fraction/integer arithmetic and accepted exp enclosures.
"""
import argparse
from dataclasses import replace
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

BASE = "3a8720ac389ffb9666eecedf7060f398d466b34e"
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCES = (
    "experiments/a2-preflight-20261009/analyze.py",
    "experiments/a2-preflight-20261009/results.json",
    "theory/t57-t58-diagnostic-inputs.json",
    "theory/t57_uniform_budget.py",
    "experiments/t58-fixed-baseline-r0b/certificate.py",
    "experiments/t126-regime-map/bounds.py",
    "experiments/t126-regime-map/grid.json",
    "experiments/t126-regime-map/outputs/map.json",
)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


def verify_sources():
    result = {}
    for path in SOURCES:
        accepted = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)
        actual = (ROOT / path).read_bytes()
        if actual != accepted:
            raise ValueError(f"Accepted input changed: {path}")
        result[path] = hashlib.sha1(b"blob " + str(len(actual)).encode() + b"\0" + actual).hexdigest()
    return result


def combined_lower(W, n, B, b, L, T, c, P0, P1):
    """T126 cell lower summed over the two disjoint constant-level segments.

    A lower PROBABILITY for every deterministic fixed period in [P0,P1],
    conditional on the stated witness/word/window contracts, not a pair upper.
    """
    if not (c < P0 <= P1 < min(L, T-L)/2 and 0 < B*P1/W < 1):
        raise ValueError("fixed lower domain")
    k = F(n-1, 2*n*W)
    square_inner = B*B*(L-2*P1) + b*b*(T-L-2*P1)
    z = k*square_inner*P0*(1-c/P0)**2*(1-B*P1/W)
    return z/(1+z)


def fixed_result(p, cert, bounds):
    W, n = p.W, 39
    risk = cert.Risk(T=p.T, B=p.B, b=p.b, FS=p.FS, q=F(1,W), Q=F(1),
                     chi=F(n-1,n*W), eta=F(n-1,n*W*W), D=p.c)
    res = cert.Resource(W, p.c, p.T, F('.001'), F(1), F('.25'),
                        F('.000003'), p.sigma, p.app_rate, p.request, p.tick)
    witness = cert.fixed_period(risk, res, p.eps, 1, (1 << 64)-1)
    assert witness['selected_tick'] is not None
    L = p.FS/(p.B-p.b)
    P1 = F(64)  # A fixed tail split, not optimized against the result.
    tail = bounds.tail_lower(W, n, p.B, L, p.c, P1, F(0))
    assert tail is not None and tail > p.eps
    low, high = cert.floor(p.c/p.tick)+1, cert.floor(P1/p.tick)
    while low < high:
        mid = (low+high)//2
        q = combined_lower(W,n,p.B,p.b,L,p.T,p.c,mid*p.tick,P1)
        if q > p.eps:
            high = mid
        else:
            low = mid+1
    P0 = low*p.tick
    prev = combined_lower(W,n,p.B,p.b,L,p.T,p.c,P0-p.tick,P1)
    q = combined_lower(W,n,p.B,p.b,L,p.T,p.c,P0,P1)
    assert prev <= p.eps < q
    price_lo = bounds.price_floor(W,p.c,p.c,P0,p.T)
    price_hi = witness['resource']['tax_upper']
    assert 0 < price_lo <= price_hi
    return dict(plateau_L_s=L, plateau_membership='T126 A, initial peak then b; one episode',
                lower_P0_s=P0, lower_split_P1_s=P1, lower_at_P0=q,
                lower_at_previous_tick=prev, lower_tail=tail,
                optimal_fixed_price_lower=price_lo,
                optimal_fixed_price_upper=price_hi,
                witness=witness, risk=witness['upper_components']['total'])


def layer_floor(p, amin, gamma, coefficient):
    """Accepted T57 L.3 necessary condition, with an explicit coefficient.

    coefficient=1/(2W) is the accepted token layer. The different-bit value
    is a favorable hypothetical pointwise layer, NOT a valid T57 substitution.
    """
    L = p.FS/(p.B-p.b)
    umax = (gamma-coefficient*amin*p.B*p.B*L)/(p.T-L)
    umax = min(umax, gamma/p.T)
    assert umax >= coefficient*amin*p.b*p.b > 0
    Db = umax/(coefficient*p.b*p.b)
    lower = (1-p.eps)*max(F(0), p.W*p.c/Db-p.W*p.c/p.T)
    return dict(gamma=gamma, coefficient=coefficient, minimum_period_s=amin,
                u_upper=umax, quiet_period_ceiling_s=Db,
                lifetime_mean_price_lower=lower)


def floor_sum(n, m, a, b=0):
    """sum(floor((a*i+b)/m), i=0..n-1), integers, logarithmic time."""
    ans = 0
    while True:
        if a >= m:
            ans += (n-1)*n*(a//m)//2
            a %= m
        if b >= m:
            ans += n*(b//m)
            b %= m
        y = a*n+b
        if y < m:
            return ans
        n, b, m, a = y//m, y % m, a, m


def visible_exposure(time, W, M, tick, c, delivery=F(0)):
    """Exact zero-history auxiliary exposure, clean start, fixed P=M*tick.

    latch=floor(w*M/W)*tick, fence=latch+c. A correction is available at
    fence+delivery. Inter-latch service windows erase unobserved arrivals;
    those c intervals are subtracted. No physical ERR Poisson claim.
    """
    if min(time, c, delivery) < 0 or M//W*tick < c:
        raise ValueError("observation calendar domain")
    cutoff = time-c-delivery
    if cutoff < 0:
        return F(0)
    P = M*tick
    cycles = cutoff//P
    part = cutoff-cycles*P
    limit = part//tick
    x = F((limit+1)*W, M)
    visited = min(W, -(-x.numerator//x.denominator))
    if cycles == 0:
        return tick*floor_sum(visited,W,M)/W
    mean_phase = tick*floor_sum(W,W,M)/W
    return (cycles-1)*(P-c)+mean_phase+(P-c)*F(visited,W)


def first_available_quantile(p, cert, P, tail, rate=None):
    """Upper grid endpoint where auxiliary no-report probability <= tail.

    The previous tick fails with certified exp bounds. Physical silence on
    unbroken paths is bounded by this auxiliary event; coupling is paid by
    the SAME lifetime gamma, never a fresh per-episode risk allowance.
    """
    rate = p.B if rate is None else rate
    M = cert.ceil(P/p.tick)
    lo, hi = 0, cert.ceil(F(100000)/p.tick)
    def silence(ticks):
        E = visible_exposure(ticks*p.tick,p.W,M,p.tick,p.c)
        return cert.exp_neg(rate*E)
    assert silence(hi)[1] <= tail
    while lo < hi:
        mid = (lo+hi)//2
        if silence(mid)[1] <= tail:
            hi = mid
        else:
            lo = mid+1
    assert silence(lo-1)[0] > tail
    t = lo*p.tick
    return dict(P_s=M*p.tick, tail=tail, time_upper_s=t,
                previous_time_s=t-p.tick, exposure_s=visible_exposure(t,p.W,M,p.tick,p.c),
                silence_upper=silence(lo)[1], physical_scope='silence AND no prior coupling break',
                delivery='0 only for this favorable diagnostic; add actual delivery bound')


def clipped_pair_relaxation(p, cert):
    """Exactly solves the stated TWO-LEVEL CONTINUOUS pair-cost diagnostic.

    Its coefficient and risk functional are not an exact adaptive Q. This
    calculation is not an upper bound on the gain of all causal policies.
    """
    L = p.FS/(p.B-p.b)
    k = F(38,78*p.W)
    A, S = k*p.b*p.b*(p.T-L), k*p.B*p.B*L
    full = p.W*p.c
    Pmin = full/F('.25')  # Favorable long-run necessary density, no tick/end costs.
    # Unconstrained optimum P_peak / P_quiet = b/B.
    P_peak_free = p.eps/(k*p.B*p.F0)
    assert P_peak_free < Pmin
    Pquiet = (p.eps-S*Pmin)/A
    assert Pquiet > Pmin
    # Convex objective in rate and KKT: high-level constraint is active.
    objective = full*((1-L/p.T)/Pquiet+(L/p.T)/Pmin)
    fixed_pair = full*(A+S)/p.eps
    return dict(type='diagnostic_not_universal_lower_or_gain_ceiling',
                P_peak_free_s=P_peak_free,Pmin_s=Pmin,Pquiet_s=Pquiet,
                pair_risk=p.eps, pair_cost=objective, gain=fixed_pair/objective,
                unbounded_resource_gain=p.T*p.S2/p.F0**2,
                unbounded_resource_cost=full*k*p.F0**2/(p.T*p.eps))


def analyze():
    pins = verify_sources()
    pre = module('t140_preflight', SOURCES[0])
    text = json.dumps(pre.analyze(ROOT),indent=2,ensure_ascii=False)+'\n'
    assert text.encode() == (ROOT/SOURCES[1]).read_bytes()
    t57 = module('t140_t57', SOURCES[3])
    cert = module('t140_t58', SOURCES[4])
    bounds = module('t140_t126', SOURCES[5])
    p = t57.model(1935832,256000000)
    fixed = fixed_result(p,cert,bounds)
    target = fixed['optimal_fixed_price_lower']/5
    ar = t57.first_resource_tick(p,F('.25'))*p.tick
    layers = {}
    for name,gamma,k in [('T57_even_free_information',p.eps,p.chi/2),
                         ('T57_alpha_0.001',p.gamma,p.chi/2),
                         ('hypothetical_different_bit_free_information',p.eps,F(38,78*p.W))]:
        row = layer_floor(p,ar+p.tick,gamma,k)
        row['gain_ceiling_with_presented_fixed_upper'] = fixed['optimal_fixed_price_upper']/row['lifetime_mean_price_lower']
        row['target_minus_proved_price_lower'] = target-row['lifetime_mean_price_lower']
        assert row['gain_ceiling_with_presented_fixed_upper'] < 5
        layers[name] = row
    # One explicit causal candidate, no optimization of a new rule family.
    candidate_p = replace(p,theta=F('.55'))
    count = t57.count_and_tax(candidate_p,policy=(F('1.2'),F(8),F(100000)))
    resource = t57.resource(candidate_p,F('1.2'),peak=F('.25'))
    assert count['conditional_price_valid'] and resource['ok']
    candidate = {k:count[k] for k in ('ab','acap','block','epochs','H','count_threshold',
                 'exposure_lower','level_y_upper','forecast_upper','nominal_tax_upper',
                 'hard_mask_tax_upper','conditional_price_valid')}
    statistical_used = count['epochs']*cert.exp_neg(F(count['H']))[1]
    candidate.update(resource=resource, alpha=p.alpha,gamma=p.gamma,
                     statistical_union_upper=statistical_used,
                     risk_upper=p.gamma+statistical_used,
                     risk_remainder=p.eps-p.gamma-statistical_used,
                     extra_control_bus_per_1ms_s=(F('.25')-resource['peak'])*F('.001'),
                     finite_numerical_acceptance=count['numerical_certificate']['success'],
                     finite_numerical_certificate={k:count['numerical_certificate'][k] for k in (
                         'exposure_bits','anchor_bits','inverse_bits','level_bits','log_terms',
                         'exposure_error','total_H_error_bound','D_guard','margin',
                         'issue_delay_bound','rational_operation_bound','normalized_log_rational_bit_bound')},
                     growth={'l':p.b,'rho_upper':F('.000004'),'status':'additional conditional T57 slice, not supplied by A2'},
                     cost_remainder_using_certified_mission_cap=target-count['hard_mask_tax_upper'],
                     CPU='unknown; independent arithmetic, not zero',
                     control_bus='unknown; must fit the same cost/resource contract',
                     extra_hardware='external39 correction counter and protected state not qualified')
    # Necessary reserve length for even the strongest possible numerator
    # (the supplied fixed witness upper) to reach 5 in the token layer.
    optimistic_target = fixed['optimal_fixed_price_upper']/5
    required_Db = (1-p.eps)*p.W*p.c/(optimistic_target+(1-p.eps)*p.W*p.c/p.T)
    L = p.FS/(p.B-p.b)
    required_ab = (p.eps-p.chi*p.b*p.b*required_Db*(p.T-L)/2)/(p.chi*p.B*p.B*L/2)
    N = cert.ceil(p.T/F('1.2'))+1
    observations = {}
    for name,P in [('reserve',F('1.2')),('candidate_long',F(8)),
                   ('equivalent_5x_price',p.W*p.c/target)]:
        M = cert.ceil(P/p.tick)
        q95 = first_available_quantile(p,cert,P,F('.05'))
        qmission = first_available_quantile(p,cert,P,p.alpha/N)
        Efirst = visible_exposure(M*p.tick,p.W,M,p.tick,p.c)
        observations[name] = dict(q95=q95,
             q_for_union_over_N_decisions=qmission, first_pass_exposure_s=Efirst,
             first_pass_silence_at_peak=cert.exp_neg(p.B*Efirst),
             max_lag_for_arrivals_not_erased_before_latch_s=M*p.tick+p.c,
             unseen_service_arrivals='U may erase latch-to-fence arrivals without a count; excluded by exact exposure, not by declaring ERR Poisson',
             phase_note='fixed zero-history calendar; switch can add T57 preannouncement delay, not an instant trigger')
    relaxation = clipped_pair_relaxation(p,cert)
    return dict(task='T140',base=BASE,source_blobs=pins,preflight_byte_identical=True,
        verdict='RED_for_reusable_T57_pointwise_layer; not impossibility of all adaptation',
        inputs=dict(W=p.W,n=39,T_s=p.T,epsilon=p.eps,R_eff=256000000,c_s=p.c,
                    full_busy_pass_s=p.W*p.c,B=p.B,b=p.b,FS=p.FS,F0=p.F0,S2=p.S2,
                    peak=F('.25'),h_s=F('.001'),tick_s=p.tick,app_u=p.app_rate,
                    app_sigma_s=p.sigma,app_atomic_s=p.request,qualified_rho=None,qualified_K=None),
        fixed=fixed,target_adaptive_price=target,T57_min_resource_period_s=ar,
        resource_at_minimum=t57.resource(p,ar,peak=F('.25')),layers=layers,
        relaxation=relaxation,candidate=candidate,
        observation=dict(parent_peak_mean_s=1/p.B,parent_background_mean_s=1/p.b,
                         expected_parents_whole_mission=p.F0,
                         expected_background_parents=p.b*p.T,
                         union_example_N=N,union_example_alpha_per_decision=p.alpha/N,
                         union_is_sufficient_not_necessary=True,calendars=observations),
        budgets=dict(target=target,
                     preflight_unpaid_price_budget=target-relaxation['unbounded_resource_cost'],
                     T57_price_budget_even_with_free_information=target-layers['T57_even_free_information']['lifetime_mean_price_lower'],
                     max_extra_nonnegative_cost_for_5x=None,
                     reason='known LOWER cost already exceeds target; no nonnegative overhead repairs it',
                     candidate_risk_remainder=candidate['risk_remainder'],
                     necessary_reserve_ceiling_for_layer_5x_s=required_ab,
                     implied_reserve_bus_density=p.W*p.c/required_ab,
                     change_required_for_nonzero_channel_errors='reduce gamma and recheck; lifetime quotas not renewed',
                     full_bus_fixed_upper=fixed['optimal_fixed_price_upper']+p.app_rate+p.sigma/p.T,
                     full_bus_candidate_mission_cap=count['hard_mask_tax_upper']+p.app_rate+p.sigma/p.T,
                     nonzero_payload='same arbitrary read-only flow within sigma+u*t, not fixed invented trace'),
        next_step='Recommend two-day LEO-position vs R0-A-star-tracker comparison through orchestrator; do not launch here')


def encode(x):
    if isinstance(x,F):
        return str(x)
    if isinstance(x,dict):
        return {k:encode(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):
        return [encode(v) for v in x]
    return x


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args = parser.parse_args()
    output = json.dumps(encode(analyze()),indent=2,ensure_ascii=False)+'\n'
    destination = HERE/'report.json'
    if args.write:
        destination.write_text(output,encoding='utf-8')
        print('Wrote only experiments/t140-a2-signal/report.json')
    else:
        assert destination.read_bytes() == output.encode(), 'report differs'
        print('T140 report byte-identical; accepted source blobs verified')


if __name__ == '__main__':
    main()

"""T57 addressed deterministic certificate checks; no adaptive simulation.

All admissions use Fraction and outward exp bounds. Display floats are not inputs.
T58 input snapshot has immutable source/blob IDs; accepted files are not modified.
The exp enclosure is the accepted T58 construction, reproduced here so this
branch can be checked without merging main or a network/dependency installation.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
import json
from pathlib import Path


def ceil(x):
    return -(-x.numerator // x.denominator)


def floor(x):
    return x.numerator // x.denominator


def dyadic(x, bits, up=False):
    scale = 1 << bits
    return F(ceil(x * scale) if up else floor(x * scale), scale)


@lru_cache(maxsize=4096)
def exp_neg(x, bits=160):
    """Outward enclosure, adapted verbatim in substance from T58 certificate.py."""
    x = F(x)
    if x < 0 or bits < 16:
        raise ValueError("exp domain")
    if not x:
        return F(1), F(1)
    if x >= bits:
        return F(0), F(1, 1 << bits)
    shifts, y = 0, x
    while y > 1:
        y /= 2
        shifts += 1
    term = total = F(1)
    upper, lower, k = F(1), F(0), 0
    tolerance = F(1, 1 << (bits + shifts + 8))
    while upper - lower > tolerance:
        k += 1
        term *= y / k
        total += term if k % 2 == 0 else -term
        if k % 2:
            lower = total
        else:
            upper = total
    lo, hi = dyadic(lower, bits), dyadic(upper, bits, True)
    for _ in range(shifts):
        lo, hi = dyadic(lo * lo, bits), dyadic(hi * hi, bits, True)
    return max(F(0), lo), min(F(1), hi)


def snapshot():
    return json.loads(Path(__file__).with_name("t57-t58-diagnostic-inputs.json")
                      .read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Model:
    W: int
    rate: int
    T: F
    B: F
    b: F
    FS: F
    eps: F = F("0.01")
    alpha: F = F("0.001")
    gamma: F = F("0.009")
    tick: F = F("0.00000001")
    sigma: F = F("0.0000001")
    request: F = F("0.0000001")
    app_rate: F = F("0.5")
    theta: F = F("0.5")
    delta_o_minus: F = F(0)  # ONE whole-horizon lower-channel quota.

    @property
    def chi(self):
        return F(1, self.W)  # TOKEN, not 38/(39W).

    @property
    def c(self):
        return F(39, self.rate)

    @property
    def F0(self):
        return self.b * self.T + self.FS

    @property
    def S2(self):
        return min(self.B**2 * self.T, self.B * self.F0,
                   self.b**2 * self.T + (self.B + self.b) * self.FS)

    @property
    def u(self):
        return self.theta * self.gamma / self.T

    @property
    def v(self):
        return (1-self.theta) * self.gamma / self.FS


def model(W=262144, rate=64000000):
    data = snapshot()
    h = data["history"]
    if W not in data["grid"]["W"] or rate not in data["grid"]["R_eff_bit_s"]:
        raise ValueError("outside original T58 grid")
    return Model(W, rate, F(h["T_s"]),
                 39 * W * F(h["B_per_bit_s_inverse"]),
                 39 * W * F(h["bbar_per_bit_s_inverse"]),
                 39 * W * F(h["FS_per_bit"]))


def price_cap(x, b, chi, u, v):
    """inf_{0<r<=x} 2[u+v(r-b)+]/(chi r^2); None means +infinity."""
    if min(x, b, chi, u, v) < 0:
        raise ValueError("price domain")
    if x == 0 or chi == 0:
        return None
    if x <= b:
        return 2 * u / (chi * x*x)
    right = 2 * (u + v*(x-b)) / (chi*x*x)
    return min(2*u/(chi*b*b), right) if b else right


def psi_upper(x, h, B, l, rho):
    if min(x, h, B, rho) < 0 or l <= 0 or x > B:
        raise ValueError("growth domain")
    if not rho or not h or x == B:
        return x
    if x < l:
        crossing = (l-x)/(rho*l)
        if h <= crossing:
            return min(B, x+rho*l*h)
        h, x = h-crossing, l
        if x >= B:
            return B
    lo, _ = exp_neg(rho*h)
    if lo == 0 or x >= B*lo:
        return B
    return min(B, x/lo)


def length_admitted(length, x, p):
    cap = price_cap(x, p.b, p.chi, p.u, p.v)
    return cap is None or length <= cap


def design(p):
    # ONE explicit policy template on the unchanged T58 family.
    scale = F(262144, p.W)
    ab = floor(8*scale/p.tick)*p.tick
    acap = floor(50*scale/p.tick)*p.tick
    block = ceil(100000*scale/p.tick)*p.tick
    return ab, acap, block


def action_admitted(p, x, current, candidate, ab, acap, l, rho):
    if not ab <= candidate <= acap:
        return False
    forecast = psi_upper(x, current+candidate, p.B, l, rho)
    reserve = psi_upper(x, current+candidate+ab, p.B, l, rho)
    return (length_admitted(max(current, candidate)+p.tick, forecast, p)
            and length_admitted(max(candidate, ab)+p.tick, reserve, p))


def choose_tick(p, x, current, ab, acap, l, rho):
    """Largest SAFE integer tick in the method cap; at most 64 bisections.

    Current is already committed. Result is for the NEXT cycle. The hardware
    domain remains 1..2^64-1; acap is an explicit policy constraint, not a new grid.
    """
    low, high = ceil(ab/p.tick), min((1 << 64)-1, floor(acap/p.tick))
    check = lambda m: action_admitted(p, x, current, m*p.tick, ab, acap, l, rho)
    if low > high or not check(low):
        return None
    while low < high:
        mid = (low+high+1)//2
        if check(mid):
            low = mid
        else:
            high = mid-1
    return low


def mask(b, gap, h):
    if gap <= 0 or h < 0 or b < 0:
        raise ValueError("mask domain")
    if b >= gap:
        return h
    n = floor(h/gap)
    return n*b + min(b, h-n*gap)


def resource(p, period, peak=F("0.05"), h=F("0.001"),
             delay=F("0.000003")):
    gap = floor(period/(p.W*p.tick))*p.tick
    if gap <= p.c+p.request:
        return dict(ok=False, gap=gap, peak=F(1), delay=None,
                    decision_slack=gap-p.c)
    rp = 1-(p.c+p.request)/gap
    du = p.c+p.request+p.sigma/rp
    pu = mask(p.c, gap, h)/h
    return dict(ok=(gap >= p.c and rp >= p.app_rate and du <= delay and pu <= peak),
                gap=gap, peak=pu, delay=du, decision_slack=gap-p.c)


@lru_cache(maxsize=2048)
def first_resource_tick(p, peak, h=F("0.001"), delay=F("0.000003")):
    low, high = 1, (1 << 64)-1
    if not resource(p, high*p.tick, peak, h, delay)["ok"]:
        return None
    while low < high:
        mid = (low+high)//2
        if resource(p, mid*p.tick, peak, h, delay)["ok"]:
            high = mid
        else:
            low = mid+1
    return low


def old_barriers(p):
    beta = p.B*F(p.W-1, 2*p.W)
    # N*P(residual>0) >= (1-exp(-beta*T))/2, all 0<ab<=T.
    poisson_total_lower = (1-exp_neg(beta*p.T)[1])/2
    return dict(F0q=p.F0/p.W, beta_T=beta*p.T,
                exact_quantile_union_lower=poisson_total_lower,
                pair_ab_upper=2*p.eps*p.W/(p.F0*p.B),
                full_busy_pass=p.W*p.c,
                no_positive_integer_cap=p.F0/p.W > p.eps)


def log2_floor(x):
    """Exact binary range reduction; no floating-point logarithm."""
    if x <= 0:
        raise ValueError("positive logarithm argument required")
    k = x.numerator.bit_length()-x.denominator.bit_length()
    z = x / (F(2)**k)
    if z < 1:
        k, z = k-1, z*2
    if z >= 2:
        k += 1
    return k


def log_tail(n):
    """Uniform remainder of 2*atanh(v), 0<=v<=1/3, n terms."""
    return F(9, 4*(2*n+1)*3**(2*n+1))


@lru_cache(maxsize=8192)
def log_interval(x, n):
    """Fixed n rational terms for z and 2, x=2^k*z, 1<=z<2."""
    if x <= 0 or n < 1:
        raise ValueError("log domain")
    k = log2_floor(x)
    z = x/(F(2)**k)

    def reduced(y):
        v = (y-1)/(y+1)
        power, total = v, F(0)
        for j in range(n):
            total += 2*power/(2*j+1)
            power *= v*v
        remainder = 2*power/((2*n+1)*(1-v*v))
        return total, total+remainder

    zlo, zhi = reduced(z)
    alo, ahi = reduced(F(2))
    return ((zlo+k*alo, zhi+k*ahi) if k >= 0
            else (zlo+k*ahi, zhi+k*alo))


def H_interval(y, l, n):
    if y < 0 or l <= 0:
        raise ValueError("H domain")
    if y <= l:
        return y/l, y/l
    lo, hi = log_interval(y/l, n)
    return 1+lo, 1+hi


def H_inverse_interval(s, B, l, bits):
    if s <= 1:
        value = min(B, l*max(F(0), s))
        return value, value
    elo, ehi = exp_neg(s-1, bits)
    return (min(B, l/ehi) if ehi else B,
            min(B, l/elo) if elo else B)


@lru_cache(maxsize=2048)
def finite_price_certificate(p, ab, acap, block, H, count_max, E_star,
                             l, rho, eta, exposure_bits=40, anchor_bits=40,
                             inverse_bits=80, level_bits=60):
    """Finite uniform certificate for EVERY good block, not just tax arithmetic.

    Exact dyadic exposure accumulation, fixed-term directed log and a rational
    precomputed admission guard. Hardware deadlines remain an explicit contract.
    No measurements, trajectories or full online controller are supplied here.
    """
    if min(ab, acap, block, E_star, l, eta) <= 0 or inverse_bits < 16:
        raise ValueError("numerical certificate domain")
    phi_lo = 1-exp_neg(F(1))[1]
    phi_hi = 1-exp_neg(F(1))[0]
    n_cycles = ceil(block/ab)+1
    exposure_error = n_cycles*F(1, 1 << exposure_bits)
    E_min = E_star-exposure_error
    base = dict(success=False, exposure_bits=exposure_bits, anchor_bits=anchor_bits,
                inverse_bits=inverse_bits, level_bits=level_bits,
                cycles_bound=n_cycles, exposure_error=exposure_error,
                exposure_min=E_min, phi_lower=phi_lo, phi_upper=phi_hi,
                ab=ab, acap=acap, block=block, H=H, count_max=F(count_max),
                l=l, rho=rho, eta=eta)
    if E_min <= 0:
        return dict(base, reason="exposure precision insufficient")
    relative_error = phi_hi*E_star/(phi_lo*E_min)-1
    h_quantum = F(1, 1 << anchor_bits)
    if relative_error > eta or h_quantum >= eta:
        return dict(base, reason="anchor error budget insufficient",
                    relative_input_error=relative_error)
    y_min = F(H)/block
    y_max = (count_max+H)/(phi_lo*E_min)
    y_star = (count_max+H)/(phi_lo*E_star)
    max_k = max(0, log2_floor(max(y_max, p.B)/l))
    n = 1
    # Uniform bound for all good inputs, computed once, not data-dependent retries.
    while (max_k+1)*log_tail(n)+h_quantum > eta:
        n += 1
    log_error = (max_k+1)*log_tail(n)
    # Good counts are integers, but H may be rational. Its denominator must
    # appear in BOTH bounds for (count+H)/(phi_lo*exposure*l).
    # Bound operand sizes before online work; z=2^-k*y/l, v=(z-1)/(z+1).
    exposure_integer_max = ceil(block*(1 << exposure_bits))
    H_denominator = F(H).denominator
    arg_num_max = (H_denominator*ceil(count_max+H)*(1 << exposure_bits)
                   *phi_lo.denominator*l.denominator)
    arg_den_max = H_denominator*phi_lo.numerator*exposure_integer_max*l.numerator
    reduced_ratio_bits = (arg_num_max+arg_den_max*(1 << max_k)).bit_length()
    # Shared-power denominators in the atanh sums and their remainder; includes
    # log(2), range exponent, and combining endpoints. See appendix I.5.
    log_rational_bits = ((4*n+8)*reduced_ratio_bits
                         +2*(n+1)*(2*n+1).bit_length()+(max_k+1).bit_length()+16)
    Hlo, Hhi = H_interval(y_star, l, n)
    Hguard = dyadic(Hhi, anchor_bits, True)
    horizon = 2*block+3*acap+ab
    S_guard = Hguard+rho*horizon+2*eta
    xlo, xhi = H_inverse_interval(S_guard, p.B, l, inverse_bits)
    X_guard = min(p.B, dyadic(xhi, level_bits, True))
    D_guard = price_cap(X_guard, p.b, p.chi, p.u, p.v)
    margin = None if D_guard is None else D_guard-(acap+p.tick)
    success = y_star < p.B and (margin is None or margin > 0)
    return dict(base, success=success,
                reason="finite positive certificate" if success else "no strict admission margin",
                relative_input_error=relative_error, log_terms=n,
                log_error_bound=log_error, anchor_rounding_bound=h_quantum,
                total_H_error_bound=relative_error+log_error+h_quantum,
                y_min=y_min, y_max=y_max, y_star=y_star, max_binary_exponent=max_k,
                horizon=horizon, S_guard=S_guard, X_guard=X_guard,
                inverse_error_bound=xhi-xlo+F(1, 1 << level_bits),
                D_guard=D_guard, margin=margin, issue_delay_bound=acap,
                rational_loop_iterations=2*n, rational_operation_bound=100+40*n,
                exposure_integer_bits=(exposure_integer_max+1).bit_length(),
                reduced_ratio_bit_bound=reduced_ratio_bits,
                normalized_log_rational_bit_bound=log_rational_bits,
                extra_reserve_fraction=F(0))


def accumulate_exposure(total, a, p, bits=40):
    """One per-cycle update; downward error <2^-bits seconds per cycle."""
    A = 1-F(1, p.W)-p.tick/a  # Diagnostic singleton phase weight.
    exact = a*max(F(0), A)**2/2
    return total+dyadic(exact, bits)


def install_block_bound(cert, count, exposure_down, block_start, issue_time,
                        old_intercept, *, valid=True, skip=False, numeric_failure=False):
    """Executable addressed update; no hidden state and no optional good-block skip."""
    result = dict(intercept=old_intercept, installed=False, timely=False)
    if skip or numeric_failure or not valid or not cert["success"]:
        return dict(result, reason="safe skip/failure: no numerical price claim for this block")
    if not (block_start+cert["block"] <= issue_time
            <= block_start+cert["block"]+cert["issue_delay_bound"]):
        return dict(result, reason="late update: no numerical price claim for this block")
    if not (0 <= count <= cert["count_max"]
            and F(count).denominator == 1
            and cert["exposure_min"] <= exposure_down <= cert["block"]
            and (exposure_down*(1 << cert["exposure_bits"])).denominator == 1):
        return dict(result, reason="outside small-count block certificate")
    y_up = (count+cert["H"])/(cert["phi_lower"]*exposure_down)
    _, Hhi = H_interval(y_up, cert["l"], cert["log_terms"])
    H_up = dyadic(Hhi, cert["anchor_bits"], True)
    candidate = H_up-cert["rho"]*block_start
    return dict(intercept=min(old_intercept, candidate), installed=True, timely=True,
                candidate=candidate, y_upper=y_up, reason="finite mandatory update")


def guarded_action(p, cert, intercept, time, current, *, promise=None,
                   numeric_failure=False):
    """Long-action fast path, otherwise a PREVIOUSLY proved reserve only.

    Promise records the next cycle/time and the nonincreasing H-intercept.
    This small proof harness is not a complete online memory controller.
    """
    ab, acap = cert["ab"], cert["acap"]
    if not ab <= current <= acap:
        raise ValueError("current period outside declared policy")
    startup = length_admitted(ab+p.tick, p.B, p)
    if not startup:
        raise ValueError("global reserve was not proved at startup")
    coordinate = intercept+cert["rho"]*(time+current+acap+ab)
    if (not numeric_failure and cert["success"]
            and coordinate <= cert["S_guard"]):
        return dict(period=acap, long_accepted=True, reason="rational guard accepted",
                    promise=dict(time=time+current, current=acap, intercept=intercept,
                                 global_reserve=False))
    promised = (promise is not None and promise["time"] == time
                and promise["current"] == current and intercept <= promise["intercept"])
    if not startup or not (current == ab or promised):
        raise ValueError("no previously proved reserve: cannot claim safety")
    return dict(period=ab, long_accepted=False, reason="previously proved reserve",
                promise=dict(time=time+current, current=ab, intercept=intercept,
                             global_reserve=True))


def count_and_tax(p, rho=F("0.000004"), overcount=0,
                  channel_bad=F(0), l=None, eta=F("0.0000000001"),
                  policy=None, numerical_contract=True, precision=None):
    """Certified nominal upper, CONDITIONAL channel/initial/service contracts.

    No zero-parent-over-mission event. Block tails are separate; they need not
    be independent. Whole-horizon coupling for PRICE uses the hard action cap.
    """
    if not 0 <= p.delta_o_minus <= 1:
        raise ValueError("lower-channel quota must lie in [0,1]")
    ab, acap, block = design(p) if policy is None else policy
    if not 0 < ab <= acap or block <= 6*acap:
        raise ValueError("policy/block domain")
    l = p.b if l is None else l
    epochs = ceil(p.T/block)
    H = 1
    while epochs*exp_neg(F(H))[1] > p.alpha:
        H += 1
    phase_A = 1-F(1, p.W)-p.tick/ab
    if phase_A <= 0:
        raise ValueError("scalar phase weight is zero, no nominal usefulness test")
    kappa = phase_A**2/2
    E = kappa*(block-2*acap)
    ztail, Htail = F(1, 4), F(12)
    mu = p.b*(block+acap)
    exp_pos_upper = 1/exp_neg(ztail)[0]
    k = ceil((mu*(exp_pos_upper-1)+Htail)/ztail)
    y = (k+overcount+H)/((1-exp_neg(F(1))[1])*E)
    horizon = 2*block+3*acap+ab
    # Store an upper H-intercept within 2*eta; no repeatedly rounded forecasts.
    forecast = psi_upper(y, F(1), p.B, l, rho*horizon+2*eta) if y <= p.B else p.B
    observation_useful = y < p.B and length_admitted(acap+p.tick, forecast, p)
    numeric = finite_price_certificate(p, ab, acap, block, H, k+overcount, E,
                                       l, rho, eta, **(precision or {}))
    coupling_quiet = min(F(1), p.chi*(acap+p.tick)*p.b*p.b*p.T/2+p.delta_o_minus)
    tail = exp_neg(Htail)[1]
    gap_b = floor(ab/(p.W*p.tick))*p.tick
    gap_s = floor(acap/(p.W*p.tick))*p.tick
    fast, slow = p.c/gap_b, p.c/gap_s
    fraction = min(F(1), 2*block/p.T+3*acap/block+tail+channel_bad+coupling_quiet)
    tax_expression = slow+(fast-slow)*fraction+4*p.c*(epochs+1)/p.T
    conditional_price_valid = (observation_useful and numerical_contract and numeric["success"]
                               and gap_b >= p.c
                               and length_admitted(ab+p.tick, p.B, p)
                               and p.alpha+p.gamma+p.delta_o_minus <= p.eps)
    tax = tax_expression if conditional_price_valid else None
    fixed_chi = F(38, 39*p.W)  # Valid ONLY for accepted singleton T58 baseline.
    fixed_tick = floor((2*p.eps/(fixed_chi*p.S2))/p.tick)
    fixed_period = fixed_tick*p.tick
    baseline_lb = max(F(0), p.W*p.c/fixed_period-p.W*p.c/p.T)
    ratio_reduction = 1-tax/baseline_lb if tax is not None and baseline_lb else None
    # Necessary bound for THIS price-density layer, on its joint good event.
    price_tax_lower = (1-p.eps)*max(
        F(0), p.chi*p.W*p.c*p.b*p.b*p.T/(2*p.gamma)-p.W*p.c/p.T)
    return dict(ab=ab, acap=acap, block=block, epochs=epochs, H=H,
                kappa=kappa, exposure_lower=E, mean_count_upper=mu,
                count_threshold=k, level_y_upper=y, forecast_upper=forecast,
                forecast_horizon=horizon, rho=rho, l=l, H_rounding_eta=eta,
                numerical_certificate=numeric, numerical_contract=numerical_contract,
                whole_horizon_undercount_quota=p.delta_o_minus,
                hard_mask_tax_upper=fast+p.c/p.T,
                informative_and_long_action=observation_useful,
                tail_upper=tail, quiet_coupling_upper=coupling_quiet,
                fast_density=fast, slow_density=slow, bad_time_fraction=fraction,
                nominal_tax_upper=tax, candidate_tax_expression=tax_expression,
                conditional_price_valid=conditional_price_valid, fixed_tick=fixed_tick,
                fixed_period=fixed_period, fixed_tax_lower=baseline_lb,
                reduction_vs_presented_fixed_lower=ratio_reduction,
                price_layer_nominal_tax_lower=price_tax_lower)


def rho_threshold(p, bits=32):
    """Certified lower endpoint, with l=b and exact nominal counter."""
    low, high = F(0), F(1, 1000)
    if not count_and_tax(p, low)["informative_and_long_action"]:
        return None
    for _ in range(bits):
        mid = (low+high)/2
        if count_and_tax(p, mid)["informative_and_long_action"]:
            low = mid
        else:
            high = mid
    return low, high


def launch_ceiling(p):
    """Maximin D(B) over nonnegative affine prices with budget gamma.

    Endpoint balancing gives S2-envelope denominator b^2*T+(B+b)*FS.
    This is a necessary launch ceiling for the price layer, not all policies.
    """
    return 2*p.gamma/(p.chi*(p.b*p.b*p.T+(p.B+p.b)*p.FS))


def price_tradeoff(p, peak, tax, h=F("0.001"), delay=F("0.000003")):
    """Necessary constraints WITHIN this affine-price/resource certificate."""
    m = first_resource_tick(p, peak, h, delay)
    if m is None:
        return dict(possible=False)
    a = m*p.tick+p.tick
    Lpeak = p.FS/(p.B-p.b)
    if not 0 < Lpeak < p.T:
        raise ValueError("diagnostic tradeoff domain")
    umax = (p.gamma-p.chi*a*p.B*p.B*Lpeak/2)/(p.T-Lpeak)
    umin_launch = p.chi*a*p.b*p.b/2
    umin_tax = p.chi*p.b*p.b/2 * (
        p.W*p.c/(tax/(1-p.eps)+p.W*p.c/p.T))
    return dict(theta_max=umax*p.T/p.gamma,
                theta_min_tax=umin_tax*p.T/p.gamma,
                possible=max(umin_launch, umin_tax) <= min(umax, p.gamma/p.T))


def alternate_design(p):
    scale = F(262144, p.W)
    return (floor(6*scale/p.tick)*p.tick,
            floor(72*scale/p.tick)*p.tick,
            ceil(200000*scale/p.tick)*p.tick)


def grid_diagnostic():
    """All 1458 ORIGINAL resource tuples, no policy trajectories or search.

    A and B use different explicit growth rectangles. A success is conditional
    on that rectangle, not on a chosen favorable future sample path.
    """
    from dataclasses import replace
    from itertools import product
    data = snapshot()["grid"]
    records = []
    for W, speed in product(data["W"], data["R_eff_bit_s"]):
        pa = model(W, speed)
        pb = replace(pa, theta=F("0.7"))
        da = count_and_tax(pa)
        db = count_and_tax(pb, rho=F("0.0000005"), policy=alternate_design(pb))
        for tax, peak, h, delay in product(*[list(map(F, data[key])) for key in
                                            ("tax", "peak", "h_s", "delay_s")]):
            def valid(p, d):
                return (length_admitted(d["ab"]+p.tick, p.B, p)
                        and d["informative_and_long_action"]
                        and resource(p, d["ab"], peak, h, delay)["ok"]
                        and d["nominal_tax_upper"] is not None
                        and d["nominal_tax_upper"] <= tax)
            records.append(dict(W=W, rate=speed, tax=tax, peak=peak, h=h,
                                delay=delay, A=valid(pa, da), B=valid(pb, db),
                                layer_not_excluded=price_tradeoff(pa, peak, tax, h, delay)["possible"]))
    return records


def report():
    from dataclasses import replace
    data = snapshot()
    reference = model()
    ref = count_and_tax(reference)
    ref["resource"] = resource(reference, ref["ab"])
    ref["rho_domain"] = rho_threshold(reference)
    ref["numerical_witness"] = numerical_witness(reference, ref)
    # A second explicit deterministic witness for the same family, at peak 25%.
    alternate_model = replace(model(262144, 16000000), theta=F("0.7"))
    alternate = count_and_tax(alternate_model, rho=F("0.0000005"),
                              policy=(F(6), F(72), F(200000)))
    alternate["resource_at_peak_25"] = resource(alternate_model, F(6), F("0.25"))
    alternate["numerical_witness"] = numerical_witness(alternate_model, alternate)
    rows = []
    for W in data["grid"]["W"]:
        for speed in data["grid"]["R_eff_bit_s"]:
            p = model(W, speed)
            d = count_and_tax(p)
            ceilings = {}
            for peak in map(F, data["grid"]["peak"]):
                mr = first_resource_tick(p, peak)
                amin = None if mr is None else mr*p.tick
                ceilings[str(peak)] = dict(
                    resource_period_min=amin,
                    some_price_split_can_launch=(amin is not None
                        and amin+p.tick <= launch_ceiling(p)),
                    template_launch=(resource(p, d["ab"], peak)["ok"]
                        and length_admitted(d["ab"]+p.tick, p.B, p)))
            rows.append(dict(W=W, R_eff_bit_s=speed, launch=ceilings,
                             nominal_tax_upper=d["nominal_tax_upper"],
                             useful_count=d["informative_and_long_action"],
                             price_layer_tax_lower=d["price_layer_nominal_tax_lower"],
                             fixed_period=d["fixed_period"],
                             fixed_tax_lower=d["fixed_tax_lower"],
                             tradeoff_tax_1pct={str(pk):price_tradeoff(p, pk, F("0.01"))
                                               for pk in map(F, data["grid"]["peak"])}))
    grid = grid_diagnostic()
    grid_summary = dict(tuples=len(grid), template_A=sum(r["A"] for r in grid),
                        template_B=sum(r["B"] for r in grid),
                        layer_not_excluded=sum(r["layer_not_excluded"] for r in grid),
                        unresolved_by_templates=sum(r["layer_not_excluded"] and not
                                                    (r["A"] or r["B"]) for r in grid))
    delta_example = count_and_tax(replace(reference, delta_o_minus=F("0.02"), eps=F("0.03")))
    no_numeric = count_and_tax(reference, numerical_contract=False)
    return dict(scope="deterministic inequalities; no adaptive campaign; conditional T58 inputs",
                reference=ref, alternate=alternate,
                review_regressions=dict(
                    delta_002_tax_upper=delta_example["nominal_tax_upper"],
                    without_numerical_contract_tax_upper=no_numeric["nominal_tax_upper"],
                    without_numerical_contract_hard_mask_upper=no_numeric["hard_mask_tax_upper"]),
                old_reference=old_barriers(model(1935832, 256000000)),
                family=rows, original_grid=grid_summary)


def numerical_witness(p, d):
    """Execute worst small-count update/admission, not an adaptive campaign."""
    c = d["numerical_certificate"]
    if not c["success"]:
        return dict(success=False)
    _, r0_hi = H_interval(p.B, c["l"], c["log_terms"])
    r0 = dyadic(r0_hi,c["anchor_bits"],True)
    E_down = dyadic(c["exposure_min"], c["exposure_bits"], True)
    issue = c["block"]+c["acap"]
    update = install_block_bound(c, c["count_max"], E_down, F(0), issue, r0)
    first = guarded_action(p, c, update["intercept"], issue, c["ab"])
    latest = guarded_action(p, c, update["intercept"], 2*c["block"]+c["acap"], c["acap"])
    fallback = guarded_action(p, c, update["intercept"], issue+c["ab"], c["acap"],
                              promise=first["promise"], numeric_failure=True)
    return dict(success=update["installed"] and first["long_accepted"] and latest["long_accepted"],
                installed=update["installed"], finite_count=c["count_max"],
                dyadic_exposure=E_down, issue_time=issue,
                first_period=first["period"], worst_age_period=latest["period"],
                reserve_after_forced_failure=fallback["period"])


def display(obj):
    if isinstance(obj, F):
        return {"exact": str(obj), "approx": float(obj)}
    if isinstance(obj, dict):
        return {k: display(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [display(v) for v in obj]
    return obj


if __name__ == "__main__":
    print(json.dumps(display(report()), ensure_ascii=False, indent=2))

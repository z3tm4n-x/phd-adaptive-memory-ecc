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


def count_and_tax(p, rho=F("0.000004"), overcount=0,
                  channel_bad=F(0), l=None, eta=F("0.0000000001"),
                  policy=None):
    """Certified nominal upper, CONDITIONAL channel/initial/service contracts.

    No zero-parent-over-mission event. Block tails are separate; they need not
    be independent. Whole-horizon coupling for PRICE uses the hard action cap.
    """
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
    coupling_quiet = min(F(1), p.chi*(acap+p.tick)*p.b*p.b*p.T/2)
    tail = exp_neg(Htail)[1]
    gap_b = floor(ab/(p.W*p.tick))*p.tick
    gap_s = floor(acap/(p.W*p.tick))*p.tick
    fast, slow = p.c/gap_b, p.c/gap_s
    fraction = min(F(1), 2*block/p.T+3*acap/block+tail+channel_bad+coupling_quiet)
    tax_expression = slow+(fast-slow)*fraction+4*p.c*(epochs+1)/p.T
    conditional_price_valid = (observation_useful and gap_b >= p.c
                               and length_admitted(ab+p.tick, p.B, p)
                               and p.alpha+p.gamma <= p.eps)
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
    # A second explicit deterministic witness for the same family, at peak 25%.
    alternate_model = replace(model(262144, 16000000), theta=F("0.7"))
    alternate = count_and_tax(alternate_model, rho=F("0.0000005"),
                              policy=(F(6), F(72), F(200000)))
    alternate["resource_at_peak_25"] = resource(alternate_model, F(6), F("0.25"))
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
    return dict(scope="deterministic inequalities; no adaptive campaign; conditional T58 inputs",
                reference=ref, alternate=alternate,
                old_reference=old_barriers(model(1935832, 256000000)),
                family=rows, original_grid=grid_summary)


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

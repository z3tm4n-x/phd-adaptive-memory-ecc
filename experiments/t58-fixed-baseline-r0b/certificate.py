"""T52 pinned implementation. Rational algebra; outward transcendental bounds.

No scientific-input defaults. Probabilities concern first exceedance on [0,T].
The caller supplies/qualifies the full mark, preparation and execution contracts.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
from math import isqrt


def ceil(x):
    return -(-x.numerator // x.denominator)


def floor(x):
    return x.numerator // x.denominator


def dyadic(x, bits, up=False):
    scale = 1 << bits
    return F(ceil(x * scale) if up else floor(x * scale), scale)


@lru_cache(maxsize=4096)
def exp_neg(x, bits=180):
    """Certified enclosure of exp(-x), x>=0, using alternating Taylor.

    For x>=bits, exp(-x)<=2**(-bits) since e>2. Otherwise reduce x to
    [0,1], enclose the alternating series, and square outward on dyadics.
    No libm/Decimal accuracy assumption is used by a decision.
    """
    x = F(x)
    if x < 0 or bits < 16:
        raise ValueError("exp domain/precision")
    if not x:
        return F(1), F(1)
    if x >= bits:
        return F(0), F(1, 1 << bits)
    shifts = 0
    y = x
    while y > 1:
        y /= 2
        shifts += 1
    term = total = F(1)
    upper, lower = F(1), F(0)
    k = 0
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


def poisson_event(x):
    lo, hi = exp_neg(F(x))
    return 1 - hi, 1 - lo


def sqrt_bounds(x, bits=180):
    x = F(x)
    if x < 0:
        raise ValueError("negative square root")
    rn, rd = isqrt(x.numerator), isqrt(x.denominator)
    if rn * rn == x.numerator and rd * rd == x.denominator:
        return F(rn, rd), F(rn, rd)
    scale = 1 << bits
    n = isqrt((x.numerator * scale * scale) // x.denominator)
    return F(n, scale), F(n + 1, scale)


def rarity(B, b, FS, T):
    if not (T > 0 and B >= b >= 0 and FS >= 0):
        raise ValueError("rarity domain")
    exposure = min(B*T, b*T + FS)
    square = min(B*B*T, B*exposure, b*b*T + (B+b)*FS)
    return exposure, square


@dataclass(frozen=True)
class Risk:
    T: F
    B: F
    b: F
    FS: F
    q: F
    Q: F
    chi: F
    eta: F
    d: F = F(0)
    K0: int = 0
    rho0: F = F(0)
    delta_exec: F = F(0)
    D: F = F(0)
    Ds: F = F(0)
    mode: str = "U"
    # Optional independently justified moment bounds, e.g. a known trajectory.
    F_cap: F | None = None
    S2_cap: F | None = None

    def validate(self):
        if any(x is not None and not isinstance(x, (int, F)) for x in self.__dict__.values()
               if not isinstance(x, str)):
            raise ValueError("use exact Fraction/int inputs, not binary floating arithmetic")
        rarity(self.B, self.b, self.FS, self.T)
        if (self.mode not in ("U", "C") or self.K0 < 0 or
            not isinstance(self.K0, int) or not 0 <= self.q <= 1 or
            not 0 <= self.d <= 1 or not 0 <= self.rho0 <= 1 or
            not 0 <= self.delta_exec <= 1 or min(self.Q, self.chi,
                                               self.eta, self.D, self.Ds) < 0 or
            self.eta > self.chi or self.chi > self.Q or self.q > self.Q):
            raise ValueError("mark/initial/execution domain")
        if any(x is not None and x < 0 for x in (self.F_cap, self.S2_cap)):
            raise ValueError("negative moment cap")

    def moments(self):
        self.validate()
        exposure, square = rarity(self.B, self.b, self.FS, self.T)
        if self.F_cap is not None:
            exposure = min(exposure, self.F_cap)
        square = min(square, self.B * exposure)
        if self.S2_cap is not None:
            square = min(square, self.S2_cap)
        return exposure, square


def components(p, tau_lo, tau_hi=None):
    """Original (4)-(6), upper interval box for a physical period range.

    D/Ds are physical WCETs; positive tau factors use hi, reciprocal factors lo.
    At a point this is exactly (6) with the exponential rounded outward.
    """
    tau_hi = tau_lo if tau_hi is None else tau_hi
    if not 0 < tau_lo <= tau_hi:
        raise ValueError("period interval")
    exposure, square = p.moments()
    v = p.chi*p.D*(p.T/tau_lo + 1)
    cross = F(0)
    if p.mode == "C" and p.D:
        cross = min((p.chi*p.D + tau_hi*p.eta)*square/2,
                    min(p.B*tau_hi, exposure) *
                    min(p.B*v, p.b*v+p.eta*p.FS, p.eta*exposure))
    vq = p.Q*p.Ds*(p.T/tau_lo + 1)
    result = dict(initial_failure=p.rho0, execution_failure=p.delta_exec,
                  direct=poisson_event(p.d*exposure)[1],
                  initial_dirty=min(F(1), p.q*p.K0)*min(exposure, p.B*tau_hi),
                  pairs=p.chi*tau_hi*square/2, cross=cross,
                  sensitive=min(p.B*vq, p.b*vq+p.q*p.FS, p.q*exposure))
    result["total"] = sum(result.values(), F(0))
    return result


def branches(p, stretch_lo=F(1), stretch_hi=F(1)):
    """At most 42 (a,b,e), equal to components(p,t*lo,t*hi).

    Clock treatment is a conservative interval box, not an unproved test of
    endpoints of a minimum. Only one constant clock scale per run is supported.
    """
    if not 0 < stretch_lo <= stretch_hi:
        raise ValueError("clock interval")
    exposure, square = p.moments()
    k0 = min(F(1), p.q*p.K0)
    common = (p.chi*square*stretch_hi/2,
              p.rho0+p.delta_exec+poisson_event(p.d*exposure)[1], F(0))
    initial = [(k0*p.B*stretch_hi, F(0), F(0)), (F(0), k0*exposure, F(0))]
    cross = [(F(0), F(0), F(0))]
    if p.mode == "C" and p.D:
        cross = [(p.eta*square*stretch_hi/2, p.chi*p.D*square/2, F(0))]
        v = p.chi*p.D
        for L, R in [(p.B*v*p.T/stretch_lo, p.B*v),
                     (p.b*v*p.T/stretch_lo, p.b*v+p.eta*p.FS),
                     (F(0), p.eta*exposure)]:
            cross += [(p.B*stretch_hi*R, p.B*stretch_hi*L, F(0)),
                      (F(0), exposure*R, exposure*L)]
    v = p.Q*p.Ds
    service = [(F(0), p.B*v, p.B*v*p.T/stretch_lo),
               (F(0), p.b*v+p.q*p.FS, p.b*v*p.T/stretch_lo),
               (F(0), p.q*exposure, F(0))] if p.Ds else [(F(0),)*3]
    return [tuple(sum(xs, F(0)) for xs in zip(common, i, x, s))
            for i, x, s in product(initial, cross, service)]


def admissible_interval(triple, epsilon):
    """Closed inner enclosure; lower 0 means strictly positive; None is +inf.

    All degeneracies handled exactly. Irrational roots are rounded inward.
    """
    a, b, e = triple
    if min(a, b, e) < 0:
        raise ValueError("negative certificate coefficient")
    E = epsilon-b
    if a == 0:
        if e == 0:
            return (F(0), None) if E >= 0 else None
        return (e/E, None) if E > 0 else None
    disc = E*E-4*a*e
    if E < 0 or disc < 0 or (E == 0 and e == 0):
        return None
    root_lo, _ = sqrt_bounds(disc)
    upper = (E+root_lo)/(2*a)
    lower = 2*e/(E+root_lo) if e else F(0)
    return (lower, upper) if 0 < upper and lower <= upper else None


def merge_intervals(intervals):
    result = []
    for lo, hi in sorted(intervals, key=lambda x: x[0]):
        if result and (result[-1][1] is None or lo <= result[-1][1]):
            old = result[-1][1]
            result[-1] = (result[-1][0], None if old is None or hi is None else max(old, hi))
        else:
            result.append((lo, hi))
    return result


def integer_interval(triple, epsilon, tick, low, high):
    """Exact rational boundary correction on the ENTIRE integer domain.

    Inner radical enclosures alone could lose a feasible tick arbitrarily close
    to an irrational root. The integer quadratic is convex; its discrete minimum
    is at an endpoint or one of the two integers adjacent to its vertex. Two
    monotone bisections recover both boundaries without rounding sqrt at all.
    """
    if low > high:
        return None
    a, b, e = triple
    E = epsilon-b
    if a == 0:
        if E < 0 or (E == 0 and e > 0):
            return None
        lower = max(low, ceil(e/(E*tick))) if E > 0 else low
        return (lower, high) if lower <= high else None
    if E <= 0:
        return None
    if e == 0:
        upper = min(high, floor(E/(a*tick)))
        return (low, upper) if low <= upper else None
    A, C = a*tick*tick, -E*tick
    poly = lambda M: A*M*M+C*M+e
    vertex_floor = floor(-C/(2*A))
    seeds = {max(low, min(high, vertex_floor)), max(low, min(high, vertex_floor+1))}
    seed = min(seeds, key=poly)
    if poly(seed) > 0:
        return None
    left, right = low, seed
    while left < right:
        mid = (left+right)//2
        if poly(mid) <= 0:
            right = mid
        else:
            left = mid+1
    first = left
    left, right = seed, high
    while left < right:
        mid = (left+right+1)//2
        if poly(mid) <= 0:
            left = mid
        else:
            right = mid-1
    return first, left


def mask_bound(b, a, h):
    if min(a, h) <= 0 or b < 0:
        raise ValueError("mask domain")
    if b >= a:
        return h
    k = floor(h/a)
    return k*b + min(b, h-k*a)


@dataclass(frozen=True)
class Resource:
    W: int
    c: F
    H: F
    h: F
    tax: F
    peak: F
    delay: F
    sigma: F
    u: F
    g: F
    tick: F
    clock_error: F = F(0)

    def validate(self):
        if any(not isinstance(x, (int, F)) for x in self.__dict__.values()):
            raise ValueError("use exact Fraction/int resource inputs")
        if (self.W < 1 or not isinstance(self.W, int) or min(self.c, self.H,
            self.h, self.tick, self.delay) <= 0 or self.h > self.H or
            not 0 <= self.clock_error < 1 or not 0 <= self.u < 1 or
            not 0 <= self.g <= self.sigma or not 0 <= self.tax <= 1 or
            not 0 <= self.peak <= 1):
            raise ValueError("resource domain")


def resources(r, M):
    r.validate()
    if M < 1 or not isinstance(M, int):
        raise ValueError("integer action")
    dlo, dhi = r.tick*(1-r.clock_error), r.tick*(1+r.clock_error)
    a = M*dlo/r.W
    tax = r.c/a+2*r.c/r.H
    peak = mask_bound(r.c+dhi, a, r.h)/r.h
    b = r.c+r.g+dhi
    rate = max(F(0), 1-b/a)
    empty = r.sigma == 0 and r.u == 0 and r.g == 0
    delay = F(0) if empty else (b+r.sigma/rate if rate and r.u <= rate else None)
    return dict(tau_lo=M*dlo, tau_hi=M*dhi, tax_upper=tax,
                peak_upper=peak, delay_upper=delay, service_rate_lower=rate,
                schedule_ok=(M//r.W)*dlo >= r.c,
                tax_ok=tax <= r.tax, peak_ok=peak <= r.peak,
                delay_ok=delay is not None and delay <= r.delay,
                mandatory_U_block_exclusion=r.g > 0 and r.delay < r.c)


def resource_ok(v):
    return all(v[k] for k in ("schedule_ok", "tax_ok", "peak_ok", "delay_ok"))


def first_resource_tick(r, low, high):
    """Monotone sufficient resource tests; all integer actions covered."""
    if low > high or not resource_ok(resources(r, high)):
        return None
    while low < high:
        mid = (low+high)//2
        if resource_ok(resources(r, mid)):
            high = mid
        else:
            low = mid+1
    return low


def fixed_period(p, r, epsilon, M_min, M_max):
    """Largest admitted action for U; C result is merely a safe candidate.

    For C price optimization use select_conditional on an explicitly finite
    complete action table. No C cost monotonicity is claimed here.
    """
    p.validate()
    r.validate()
    if (not 0 < epsilon < 1 or M_min < 1 or M_max < M_min or
        not isinstance(M_min, int) or not isinstance(M_max, int) or
        max(p.D, p.Ds) > r.c or r.H > p.T or p.K0 > r.W or
        (p.B > 0 and (p.Q < 1 or p.Q > r.W or p.q*r.W < 1))):
        raise ValueError("action/certificate/executor contract")
    triples = branches(p, 1-r.clock_error, 1+r.clock_error)
    intervals = merge_intervals([iv for tr in triples
                                if (iv := admissible_interval(tr, epsilon)) is not None])
    low_resource = first_resource_tick(r, M_min, M_max)
    intervals_ticks = []
    candidates = []
    if low_resource is not None:
        for triple in triples:
            minimum = max(M_min, low_resource,
                          floor(p.D/(r.tick*(1-r.clock_error)))+1)
            iv = integer_interval(triple, epsilon, r.tick, minimum, M_max)
            if iv is not None:
                low, high = iv
                intervals_ticks.append((low, high))
                for M in {low, high}:
                    v = resources(r, M)
                    risk = components(p, v["tau_lo"], v["tau_hi"])
                    if risk["total"] <= epsilon and resource_ok(v):
                        candidates.append((M, risk, v))
    winner = max(candidates, key=lambda x: x[0]) if candidates else None
    return dict(branch_count=len(triples), risk_intervals_inner=intervals,
                certified_tick_intervals=merge_intervals(intervals_ticks),
                first_resource_tick=low_resource,
                selected_tick=winner[0] if winner else None,
                upper_components=winner[1] if winner else None,
                resource=winner[2] if winner else None,
                kind="sufficient_constant" if winner else "no_certificate_not_impossibility")


def conditional_cost(p, r, M, read, write, m, b_nom, chi_gross, eta_gross):
    """Appendix G1, whole-horizon expected cost; not a survival-conditioned cost.

    Requires proved syndrome/token attribution and release of unused write slot.
    Otherwise callers must use reserved cost. Gross coefficients are sum/max q_w².
    """
    if (p.mode != "C" or not 0 <= read or write < 0 or read+write > r.c or
        not 1 <= m <= r.W or not 0 <= b_nom <= p.b or
        chi_gross < p.chi or eta_gross < p.eta):
        raise ValueError("conditional-cost contract")
    v = resources(r, M)
    N = ceil(r.H*r.W/v["tau_lo"]+2)
    nominal = replace(p, T=r.H, B=b_nom, b=b_nom, FS=F(0),
                      chi=chi_gross, eta=eta_gross, F_cap=None, S2_cap=None)
    bad = min(F(1), components(nominal, v["tau_lo"], v["tau_hi"])["total"])
    writes = min(F(N), p.K0+m*b_nom*r.H+N*bad)
    return dict(checks_upper=N, bad_probability_upper=bad,
                writes_upper=writes, reserved_upper=r.c*N/r.H,
                actual_upper=min(r.c*N, read*N+write*writes)/r.H)


def select_conditional(p, r, epsilon, action_table, **cost_contract):
    """Exhaustive finite-table selection only; no large-range C optimum."""
    p.validate()
    r.validate()
    if not 0 < epsilon < 1 or r.H > p.T or p.K0 > r.W:
        raise ValueError("conditional certificate domain")
    if p.mode != "C" or not action_table or len(action_table) > 100000:
        raise ValueError("explicit finite C table required (<=100000)")
    feasible = []
    for M in sorted(set(action_table)):
        v = resources(r, M)
        if max(p.D, p.Ds) > r.c or not p.D < v["tau_lo"]:
            continue
        risk = components(p, v["tau_lo"], v["tau_hi"])
        if risk["total"] <= epsilon and v["schedule_ok"] and v["peak_ok"] and v["delay_ok"]:
            cost = conditional_cost(p, r, M, **cost_contract)
            if cost["actual_upper"] <= r.tax:
                feasible.append(dict(M=M, upper=risk, cost=cost, resource=v))
    return min(feasible, key=lambda x: (x["cost"]["actual_upper"], x["M"])) if feasible else None


def preparation(Fpre, zeta, W, m, d, chi_gross, delta_prep, max_terms=10000):
    """A1 with certified Poisson quantile; failure to certify is explicit."""
    if not (Fpre >= 0 and 0 < zeta < 1 and 1 <= m <= W and
            0 <= d <= 1 and chi_gross >= 0 and 0 <= delta_prep <= 1):
        raise ValueError("preparation domain")
    exp_lo, _ = exp_neg(Fpre)
    if not exp_lo:
        raise ValueError("Poisson quantile requires higher exponential precision")
    total = term = F(1)
    Q = 0
    while 1-exp_lo*total > zeta:
        Q += 1
        if Q > max_terms:
            raise ValueError("Poisson quantile uncertified: increase precision/limit")
        term *= Fpre/Q
        total += term
    return dict(Q=Q, K0=min(W, m*Q), rho0=min(F(1), delta_prep+zeta+
                poisson_event(d*Fpre)[1]+chi_gross*Fpre*Fpre/2))


def class_lower(W, n, B, L, c, read, H, tax, ell=None, delta_exec=F(0),
                *, witness_admissible, deterministic_window_contract):
    """T52 (12)-(13), deterministic uniform fixed class, all periods/phases.

    The declared single-bit initial-peak witness must belong to Theta/Lambda.
    This does NOT cover mixtures with only seed-averaged tax, or adaptive rules.
    """
    if not witness_admissible or not deterministic_window_contract:
        return dict(applicable=False, reason="witness_or_window_contract_missing")
    if (W < 1 or n < 2 or B < 0 or L < 0 or min(read, H, c) <= 0 or
        read > c or tax < 0 or not 0 <= delta_exec <= 1):
        raise ValueError("lower domain")
    tmin = W*read/(tax+2*read/H)
    J = floor(L/tmin)+2
    ell = (L-J*c)/(4*J) if ell is None else ell
    if ell <= 0:
        return dict(applicable=True, tau_min=tmin, J=J, ell=ell, N=0, lower=F(0))
    N = max(0, ceil(W*L/ell-W*J*(c/ell+2)))
    x = B*ell/W
    p_lo = F(n-1, 2*n)*x*x*exp_neg(x)[0]
    lower = max(F(0), poisson_event(N*p_lo)[0]-delta_exec)
    return dict(applicable=True, tau_min=tmin, J=J, ell=ell, N=N, x=x,
                cell_probability_lower=p_lo, lower=lower)


def direct_lower(d_star, witness_exposure, *, structural_mark_contract):
    if not structural_mark_contract:
        return None
    if not 0 <= d_star <= 1 or witness_exposure < 0:
        raise ValueError("direct lower domain")
    return poisson_event(d_star*witness_exposure)[0]

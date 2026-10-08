"""T126: necessary-witness arithmetic only; no new sufficient certificate.

All decisions use integers/Fraction. Scientific membership (marks, start,
growth and application class) is an explicit prerequisite, not inferred here.
"""
from fractions import Fraction as F


def exact(*values):
    if any(x is not None and (isinstance(x, bool) or not isinstance(x, (int, F))) for x in values):
        raise ValueError("use exact int/Fraction inputs, not binary floats")
    return tuple(None if x is None else F(x) for x in values)


def plateau(T, B, b0, FS, *, F_cap=None, S2_cap=None,
            excess_cap=None, initial_peak_allowed=True):
    """Appendix A: initial B plateau followed by constant b0.

    A rejected b0-witness does not assert emptiness of Lambda. In particular,
    b0=0 can remain admissible when b0=bbar no longer is.
    """
    T,B,b0,FS,F_cap,S2_cap,excess_cap=exact(T,B,b0,FS,F_cap,S2_cap,excess_cap)
    if min(T, B) <= 0 or not 0 <= b0 <= B or FS < 0:
        raise ValueError("witness domain")
    if any(x is not None and x < 0 for x in (F_cap, S2_cap, excess_cap)):
        raise ValueError("negative cap")
    if not initial_peak_allowed:
        return dict(admissible=False, reason="initial_peak_not_allowed")
    if ((F_cap is not None and F_cap < b0*T) or
            (S2_cap is not None and S2_cap < b0*b0*T)):
        return dict(admissible=False, reason="this_background_exceeds_cap")
    if B == b0:
        L = T
    else:
        limits = [T, FS/(B-b0)]
        if F_cap is not None:
            limits.append((F_cap-b0*T)/(B-b0))
        if S2_cap is not None:
            limits.append((S2_cap-b0*b0*T)/(B*B-b0*b0))
        if excess_cap is not None:
            limits.append(excess_cap/(B*B-b0*b0))
        L = min(limits)
    return dict(admissible=L > 0, reason=None if L > 0 else "no_positive_plateau",
                L=L, F=b0*T+(B-b0)*L,
                S2_background=b0*b0*T, S2_excess=(B*B-b0*b0)*L,
                S2=b0*b0*T+(B*B-b0*b0)*L, solar_exposure=(B-b0)*L)


def moderate_lower(W, n, B, L, removed, P0, P1, delta_exec):
    """Accepted T95 B.2 lower on probability, not pair upper."""
    if type(W) is not int or type(n) is not int:raise ValueError("integer geometry")
    B,L,removed,P0,P1,delta_exec=exact(B,L,removed,P0,P1,delta_exec)
    if not (W >= 1 and n >= 2 and 0 < removed < P0 <= P1 < L/2
            and 0 < B*P1/W < 1 and 0 <= delta_exec <= 1):
        return None
    beta = F(n-1, 2*n*W)
    z = beta*B*B*(L-2*P1)*P0*(1-removed/P0)**2*(1-B*P1/W)
    return max(F(0), z/(1+z)-delta_exec)


def tail_lower(W, n, B, L, removed, P1, delta_exec):
    """Accepted T95 B.3, all periods >= P1 and all fixed phases."""
    if type(W) is not int or type(n) is not int:raise ValueError("integer geometry")
    B,L,removed,P1,delta_exec=exact(B,L,removed,P1,delta_exec)
    if min(W, B, L, removed, P1) <= 0 or n < 2 or not 0 <= delta_exec <= 1:
        raise ValueError("tail domain")
    J = L//P1+2
    ell = (L-J*removed)/(4*J)
    x = B*ell/W
    if not 0 < x < 1:
        return None
    z = 2*W*J*F(n-1, 2*n)*x*x*(1-x)
    return max(F(0), z/(1+z)-delta_exec)


def price_floor(W, paid_lower, paid_upper, P0, H, components=1):
    """Necessary finite-horizon price, arbitrary fixed word phases.

    Requires proved P<P0 and mandatory paid operation at every word visit.
    Upper WCET alone is NOT a paid_lower. For E use mandatory read, not E max.
    """
    if type(W) is not int or type(components) is not int:raise ValueError("integer geometry/components")
    paid_lower,paid_upper,P0,H=exact(paid_lower,paid_upper,P0,H)
    if not (0 < paid_lower <= paid_upper and P0 > 0 and H > 0
            and W >= 1 and components >= 1):
        raise ValueError("price domain")
    return max(F(0), W*paid_lower/P0-2*W*paid_upper*components/H)


def ratio_or_status(numerator, denominator):
    numerator,denominator=exact(numerator,denominator)
    if numerator is None or denominator is None:
        return dict(value=None, status="missing")
    if min(numerator, denominator) < 0:
        raise ValueError("nonnegative coordinate")
    if denominator == 0:
        return dict(value=None, status="undefined_0_over_0" if numerator == 0 else "infinity")
    return dict(value=numerator/denominator, status="finite")


def status(*, constant_ok=False, adaptive_ok=False,
           fixed_excluded=False, period_excluded=False):
    """Evidence-label protocol, not a theorem giving new evidence.

    Caller must establish identical comparison domain and price metric.
    Passing an upper-bound failure as an exclusion violates this interface.
    """
    if period_excluded and (constant_ok or adaptive_ok):
        raise ValueError("contradictory certificates")
    if constant_ok and fixed_excluded:
        raise ValueError("contradictory constant evidence")
    if period_excluded:
        return "period_class_excluded"
    if constant_ok:
        return "constant_sufficient"
    if adaptive_ok:
        return "adaptation_needed_and_sufficient" if fixed_excluded else "adaptive_sufficient_necessity_unknown"
    return "unknown"

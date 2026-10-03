"""T89: reuse T81's zero-count formula, with explicit unknowns and safe rounding.

Only fixed-exposure prospective zero-count calculations; no measured events.
No accepted code is executed at top level or modified. Python stdlib only.
"""
from __future__ import annotations

import ast
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def rational(value):
    if value is None or isinstance(value, bool):
        raise ValueError("A finite explicit value is required")
    try:
        return Q(str(value)) if not isinstance(value, Q) else value
    except (ValueError, ZeroDivisionError) as e:
        raise ValueError("A finite explicit value is required") from e


def load_t81():
    """Load the exact three accepted functions; do not import T68 or rerun T81."""
    p = REPO / "experiments/t81-direct-architecture/run.py"
    tree = ast.parse(p.read_text(encoding="utf-8"))
    names = {"mu_upper", "sigma_upper", "allocation_fluence"}
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in tree.body} != names:
        raise ValueError("T81 formula source changed")
    namespace = {"math": math}
    # chi2 is intentionally not supplied: only mu_upper(0, alpha) is used.
    exec(compile(tree, str(p) + ":zero_count_functions", "exec"), namespace)
    return namespace["allocation_fluence"]


T81_ALLOCATION = load_t81()


def log_mean_bounds(alpha, precision=70):
    """Bound -ln(alpha) via correctly rounded Decimal.ln and adjacent values.

    Alpha is rational. First enclose its decimal conversion, then exploit
    monotonicity. All subsequent algebra uses exact Fractions.
    """
    a = rational(alpha)
    if not 0 < a < 1:
        raise ValueError("0 < alpha < 1 required")
    with localcontext() as ctx:
        ctx.prec = precision
        x = Decimal(a.numerator) / Decimal(a.denominator)
        lo_a, hi_a = x.next_minus(), x.next_plus()
        lower = -hi_a.ln().next_plus()
        upper = -lo_a.ln().next_minus()
        return Q(lower), Q(upper)


def decimal_text(value, places=15, up=True):
    """Outward fixed-point serialization, exact before decimal formatting."""
    x = rational(value) * 10**places
    n = -((-x.numerator)//x.denominator) if up else x.numerator//x.denominator
    sign = "-" if n < 0 else ""
    digits = str(abs(n)).zfill(places+1)
    return sign + (digits[:-places] + "." + digits[-places:] if places else digits)


def ceil_quantum(value, quantum):
    q = rational(quantum)
    if q <= 0:
        raise ValueError("positive rounding quantum required")
    x = rational(value) / q
    return (-((-x.numerator)//x.denominator)) * q


def zero_fluence(C, b, alpha, E_old, theta, q, g, quantum="0.001", n_new=0):
    """T81 allocation, unknown-safe, with independent directed verification."""
    if isinstance(n_new, bool) or n_new != 0:
        raise ValueError("This is exclusively a prospective zero-count formula")
    supplied = dict(C=C, b=b, alpha=alpha, E_old=E_old, theta=theta, q=q, g=g)
    unknown = [k for k, v in supplied.items() if v is None]
    if unknown:
        return {"status": "undefined", "missing": unknown, "F_required": None}
    C, b, a, E, t, q, g = map(rational, supplied.values())
    if C < 0 or b <= 0 or E < 0 or not 0 < a < 1 or not 0 <= t < 1 or not 0 <= q <= 1 or g < 0:
        raise ValueError("Invalid exposure, allocation, coverage or normalization")
    ml, mu = log_mean_bounds(a)
    nl, nu = max(Q(0), ml*C/b-E), max(Q(0), mu*C/b-E)
    if q == 0 or g == 0:
        if nu == 0:
            return {"status": "old_exposure_sufficient", "F_required": "0.000"}
        return {"status": "no_finite_exposure", "reason": "zero_effective_new_exposure", "F_required": None}
    s = (1-t)*q*g
    fl, fu = nl/s, nu/s
    f = ceil_quantum(fu, quantum)
    inherited = T81_ALLOCATION(*map(float, (C, b, a, E, t, q, g)))
    # Double precision is a regression, not the basis for outward acceptance.
    if not math.isclose(inherited, float(fu), rel_tol=2e-12, abs_tol=1e-9):
        raise ArithmeticError("T81/independent formula mismatch")
    effective = E + s*f
    upper = mu*C/effective if C and effective else Q(0)
    if upper > b:
        raise ArithmeticError("Rounded sufficient exposure failed its own budget")
    return {"status": "conditional_finite", "F_required": decimal_text(f, 3),
            "F_lower": decimal_text(fl, 18, False), "F_upper": decimal_text(fu, 18),
            "T81_double": inherited, "contribution_upper": decimal_text(upper, 24),
            "effective_exposure_lower": decimal_text(effective, 18, False)}


def allocation_budget(D0, R, strata, alpha_theta):
    """Validate the declared family; no missing parameter receives a default."""
    if any(x is None for x in (D0, R, alpha_theta)):
        return {"status": "undefined", "F_required": None}
    d, r, a = map(rational, (D0, R, alpha_theta))
    if d <= 0 or r < 0 or not 0 < a < 1 or not strata:
        raise ValueError("Invalid target, remainder, alpha or empty family")
    if any(s.get(k) is None for s in strata for k in ("b", "alpha")):
        return {"status": "undefined", "F_required": None}
    if r >= d:
        return {"status": "no_positive_covered_budget", "F_required": None}
    budgets = [rational(s["b"]) for s in strata]
    alphas = [rational(s["alpha"]) for s in strata]
    if any(b <= 0 for b in budgets) or any(not 0 < x < 1 for x in alphas):
        raise ValueError("Positive stratum budgets and valid alpha required")
    if sum(budgets) > d-r or sum(alphas) > a:
        raise ValueError("Allocation exceeds its mean or statistical budget")
    return {"status": "valid_conditional_budget", "remaining_mean_budget": str(d-r-sum(budgets)),
            "unused_alpha": str(a-sum(alphas))}


def validate_threshold_handoff(handoff):
    """Fail closed: no zeros, upper bracket endpoints or unpinned T88 values."""
    rows = handoff["rows"]
    keys = [(r["variant"], rational(r["shield_g_cm2"])) for r in rows]
    expected = {(v, s) for v in ("combined", "monitor-only", "ERR-only") for s in (Q(3), Q("2.5"))}
    if len(keys) != 6 or set(keys) != expected:
        raise ValueError("Require six separate variant/shield rows")
    for row in rows:
        d = row.get("Dcrit_1pct_safe")
        if d is None:
            continue
        sha = handoff.get("source_sha")
        if not isinstance(sha, str) or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
            raise ValueError("Exact scientific/numerical T88 source SHA is required")
        if rational(d) <= 0 or row.get("safe_endpoint_confirmed") is not True:
            raise ValueError("A positive verified safe endpoint is required")
        if row.get("architecture") != "internal38" or rational(row.get("timing_margin")) != Q("0.1"):
            raise ValueError("Handoff architecture/margin mismatch")
        if row.get("threshold_kind") not in ("Dcrit_1pct", "largest_found_certified_1pct") or not row.get("certificate_ref"):
            raise ValueError("Do not substitute Dcert or a working point for Dcrit_1pct")
    return rows

"""Pair bounds for the nominal, piecewise-intensity, 16-word bench only."""

from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext
from fractions import Fraction as F

from policies import e

EPS = F(1, 1000)
NS = 10**9
L = e.L
B0 = F(1, 524288)


def word_limits(profile):
    """Outward integrals S1, S2 and peak of the nominal per-word rate."""
    if profile.name == "stress":
        return F(2, 5), F(4), F(10)
    if profile.name == "class_plateau":
        s1, s2, peak = map(F, ("187464.000001", "134874.447", ".981301"))
    else:
        s1, s2, peak = map(F, ("164214.596366", "15631.396", ".525"))
        assert (profile.low + profile.slope).max() < float(peak)
    assert profile.notes["S2_reference_per_s"] < s2 and profile.notes["S1_reference"] < s1
    return s1 * B0, s2 * B0**2, peak * B0


def risk_upper(profile, rounds):
    # In each repeated cycle a word is visited twice, separated by L/2 and
    # P-L/2. The fixed 256L skeleton is contained in both adaptive policies.
    half = L // 2
    longest = rounds * L - half
    # In each interval J between mandatory starts, pair mass <= |J| int_J ell^2 / 2.
    # A surviving old bit can also meet a hit within EDGE of the next start.
    s1, s2, peak = word_limits(profile)
    same_gap = F(longest, 2 * NS) * s2
    between_phases = F(e.EDGE, NS) * peak * s1
    return min(F(1), e.W * F(37, 38) * (same_gap + between_phases))


def fixed_candidate(profile):
    feasible = [1 << j for j in profile.spec["fixed_log2_L"]
                if risk_upper(profile, 1 << j) < EPS]
    return max(feasible, default=1)


def stress_gap_lower():
    """Two single-word parents while the quiet-start policies are idle."""
    period = e.CELL * L
    # At t=2 s a clean ladder has traversed the whole promotion sequence.
    assert e.REQ[-1] * period + e.INSTALL < 2 * NS
    start, stop = 2 * NS, 2 * NS + 20_000_000
    a = -(-start // period) * period
    assert a == 698 * period and a + period <= stop
    rate = F(160 * 5, 6)
    before = rate * F(a + L - start, NS)
    z = rate * F(period - L, NS)
    def exp_interval(x, below):
        # Enclose the rational exponent before calling correctly rounded exp.
        with localcontext() as ctx:
            ctx.prec = 60
            ctx.rounding = ROUND_FLOOR if below else ROUND_CEILING
            value = (Decimal(-x.numerator) / Decimal(x.denominator)).exp()
            return F(value.next_minus() if below else value.next_plus())
    quiet = exp_interval(before, True)
    at_least_two = 1 - exp_interval(z, False) * (1 + z)
    return quiet * at_least_two * F(4, 5)**2 * F(1, e.W) * F(37, 38)

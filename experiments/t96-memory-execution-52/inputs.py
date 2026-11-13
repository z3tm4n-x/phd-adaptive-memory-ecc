"""Reachable directed cases, fixed random streams and analytical checks."""
from fractions import Fraction as F
from math import exp, expm1, fsum, lgamma, log, log1p
import numpy as np

from reference import CFG, CHECKPOINT, L


def parents(trial):
    gen = np.random.Generator(np.random.PCG64(np.random.SeedSequence([CFG["seed"], trial])))
    rows = []
    for lo, hi in CFG["pulse_rounds"]:
        for _ in range(gen.poisson(2/3)):
            t = int(gen.integers(lo*L, hi*L))
            word = int(gen.integers(4))
            pair = gen.integers(5) == 4
            bit = int(gen.integers(38))
            second = int(gen.integers(38)) if pair else -1
            rows.append((t, word, bit, second))
    return sorted(rows, key=lambda p: p[0])


def directed():
    # The bin before/after an edge is unambiguous; no analogue timing is claimed.
    # Rows carry time, ring anchor, position, optional neighbour position.
    def one(t, word, bit):
        return (t, word, bit, -1)
    c = CHECKPOINT
    yield "clean", 3*L, []
    for bit in range(38):
        yield f"position_{bit}", L, [one(1, 2, bit)]
    yield "ring_wrap", 2*L, [(50, 3, 36, 4)]
    yield "last_address", 2*L, [one(1900, 3, 37)]
    yield "partner_hit", 2*L, [one(1001, 0, 24)]
    yield "cancel_before_read", L, [one(214, 1, 8), one(223, 1, 8)]
    yield "interread_exceed_cancel", L, [one(110, 0, 3), one(111, 0, 5), one(113, 0, 3)]
    yield "same_bucket", L, [one(110, 0, 8), one(110, 0, 9), one(110, 0, 8)]
    yield "same_bit_reborn", 2*L, [one(11, 1, 32), one(310, 1, 32), one(340, 1, 32)]
    yield "sample_before", L, [one(59, 0, 2)]
    yield "sample_after", L, [one(60, 0, 2)]
    yield "write_before", L, [one(1, 1, 3), one(399, 1, 36)]
    yield "write_after", L, [one(1, 1, 3), one(400, 1, 36)]
    yield "old_canceled_after_sample", L, [one(230, 1, 7), one(302, 1, 7)]
    yield "terminal_read", 252, [one(251, 1, 16)]
    yield "terminal_before_write", 400, [one(99, 1, 37), one(399, 1, 33)]
    yield "terminal_after_write", 405, [one(99, 1, 37), one(399, 1, 33)]
    yield "late_terminal_parent", 2775, [one(2703, 3, 17), one(2774, 3, 37)]
    yield "positive_on_promotion", c+3*L, [one(c+2050,3,37)]
    yield "first_slow_then_fallback", c+6*L, [one(c+L+101,1,32)]
    yield "pause_exceed_cleared", c+6*L, [one(c+L+100,1,0),one(c+L+101,1,37),one(c+L+102,1,0)]
    yield "positive_just_before_common", c+3*L, [one(c-L+1401,3,31)]


def bound():
    t = CFG["T_ns"]
    pulses = [(a*L, b*L) for a,b in CFG["pulse_rounds"]]
    def mass(left, right):
        return sum((F(max(0,min(right,b)-max(left,a)), b-a) / 5 for a,b in pulses), F())
    pieces = []
    for phase in CFG["phases_ns"]:
        starts = [r*L + k + phase for r in range(0, (t+L-1)//L)
                  if r <= CFG["checkpoint_round"] or r%2==0 for k in (0,1400)
                  if r*L+k+phase < t]
        boundaries = sorted({0,t,*starts})
        same = overlap = previous = F()
        for left,right in zip(boundaries,boundaries[1:]):
            m = mass(left,right)
            same += m*m/2
            overlap += previous * mass(left,min(left+CFG["write_edge_ns"],right))
            previous = m
        pieces.append((same,overlap))
    incident = sum((s+d for s,d in pieces), F()) * F(37,38)
    return {"word_pair_terms": [[str(s),str(d)] for s,d in pieces],
            "first_upper_exact": str(min(F(1),incident)), "first_upper":float(min(F(1),incident))}


def cp(hits, n):
    # Invert exact binomial tails. Start the summation on the low-probability
    # side of the mode to avoid cancellation or overflow at both endpoints.
    def cdf(k,p):
        if k<0: return 0.0
        if k>=n: return 1.0
        lower = k < n*p
        a = k if lower else k+1
        term = exp(lgamma(n+1)-lgamma(a+1)-lgamma(n-a+1)+a*log(p)+(n-a)*log1p(-p))
        terms = [term]
        if lower:
            while a and term > 1e-19:
                term *= a/(n-a+1)*(1-p)/p
                terms.append(term)
                a-=1
        else:
            while a<n and term > 1e-19:
                term *= (n-a)/(a+1)*p/(1-p)
                terms.append(term)
                a+=1
        return fsum(terms) if lower else 1-fsum(terms)
    def invert(k,target):
        lo,hi=0.0,1.0
        for _ in range(55):
            mid=(lo+hi)/2
            if cdf(k,mid)>target: lo=mid
            else: hi=mid
        return (lo+hi)/2
    alpha=float(F(CFG["alpha"]))
    return [0.0 if hits==0 else invert(hits-1,1-alpha/2),
            1.0 if hits==n else invert(hits,alpha/2)]


def no_events_upper(n):
    return -expm1(log(float(F(CFG["alpha"])))/n)

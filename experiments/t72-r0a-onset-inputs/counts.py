"""Conditional single-bit diagnostic; never interprets ERR as a Poisson count."""
from __future__ import annotations
import math
import numpy as np


def weight_one(mu_word, bits):
    """Exact XOR weight-one probability from a clean word, independent bit NHPP."""
    if mu_word < 0 or bits < 2:
        raise ValueError("Invalid word exposure")
    p = -math.expm1(-2*mu_word/bits)/2
    return bits*p*(1-p)**(bits-1)


class Integral:
    """Piecewise-constant native-bin model; outside the provided interval is zero."""
    def __init__(self, values, cadence):
        self.x = np.asarray(values, float)
        if cadence <= 0 or np.any(~np.isfinite(self.x)) or np.any(self.x < 0):
            raise ValueError("Missing/negative values cannot be integrated")
        self.cad = cadence
        self.prefix = np.r_[0., np.cumsum(self.x)*cadence]
        self.end = len(self.x)*cadence
        self.maximum = float(np.max(self.x, initial=0.))

    def __call__(self, t):
        t = np.clip(np.asarray(t, float), 0, self.end)
        i = np.minimum((t/self.cad).astype(int), len(self.x)-1)
        if not len(self.x):
            return t*0
        return self.prefix[i] + self.x[i]*(t-i*self.cad)

    def lattice_mean(self, first, step, size):
        """Exact mean F(first+k*step), using linearity inside each native bin."""
        if step <= 0 or size <= 0:
            raise ValueError("Invalid phase lattice")
        total = 0.
        # At most ceil(period/cadence)+2 pieces, not W samples per query.
        lo = max(0, math.ceil(-first/step))
        hi = min(size, math.ceil((self.end-first)/step))
        if hi > lo:
            left = first+lo*step
            right = first+(hi-1)*step
            a = max(0, int(left//self.cad))
            b = min(len(self.x)-1, int(right//self.cad))
            for j in range(a, b+1):
                p = max(lo, math.ceil((j*self.cad-first)/step))
                q = min(hi, math.ceil(((j+1)*self.cad-first)/step))
                if q > p:
                    mid = first + .5*(p+q-1)*step
                    total += (q-p)*float(self(mid))
        # Values >= end are constant, those <0 are zero.
        after = max(0, size-max(0, math.ceil((self.end-first)/step)))
        return (total+after*self.prefix[-1])/size


def available(integral, elapsed, period, phase_fraction, delay, words=2**19, phase_span=None):
    """Expected inversion tokens already visited, and rigorous oracle-ERR bracket.

    Uniform word phases, ideal instantaneous U, clean at interval start.
    A token is visited at the next word visit, delivered after delay.
    Correctable ERR can merge/cancel tokens: sum(mu_i^2) bounds the deficit.
    This is NOT a confidence interval or a physical detection guarantee.
    """
    if elapsed < 0 or period <= 0 or delay < 0 or words <= 0:
        raise ValueError("Invalid observation contract")
    mu = float(integral(elapsed))
    deadline = elapsed-delay
    if deadline < 0:
        tokens = 0.
    else:
        span = period if phase_span is None else phase_span
        if not 0 < span <= period:
            raise ValueError('Invalid full-pass phase span')
        step = span/words
        origin = phase_fraction*period
        ratio = (deadline-origin)/period
        base = origin+math.floor(ratio+4*math.ulp(ratio))*period
        phase = (deadline-base)/step
        # Decimal periods represented as doubles: include an exactly due latch.
        tolerance = 8*math.ulp(max(abs(deadline), abs(base), period))/step
        k = min(words, max(0, math.floor(phase+tolerance)+1))
        tokens = integral.lattice_mean(base, step, k)*k/words if k else 0.
        if k < words:
            tokens += integral.lattice_mean(base-period+k*step, step, words-k)*(words-k)/words
    tokens = min(mu, max(0., tokens))
    max_word_mu = period*integral.maximum/words
    return {
        "inversions_expected": mu,
        "visited_tokens_expected": tokens,
        "ERR_oracle_expected_lower": max(0., tokens*(1-max_word_mu)),
        "ERR_oracle_expected_upper": tokens,
        "pending_tokens_expected": mu-tokens,
        "phase_free_visited_lower": float(integral(max(0., elapsed-delay-period))),
        "phase_free_visited_upper": float(integral(max(0., elapsed-delay))),
        "count_law": "ideal_clean_U_singletons; expectation bracket, not probability coverage",
    }

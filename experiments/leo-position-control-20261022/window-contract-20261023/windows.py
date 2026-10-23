"""T206: deterministic mandatory slots at fixed z, not a physical Q estimator.

All times use one declared unit and exact rationals. No observed error/position
history is an input. See CONSTRUCTION.md for the conditions behind this subset.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from math import gcd


def ceilq(x):
    x = F(x)
    return -(-x.numerator // x.denominator)


def floorq(x):
    x = F(x)
    return x.numerator // x.denominator


def merge_ranges(ranges):
    """Union of closed integer ranges, merging adjacent ranges as well."""
    out = []
    for lo, hi in sorted(ranges):
        if lo > hi:
            continue
        if out and lo <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(out[-1][1], hi))
        else:
            out.append((lo, hi))
    return out


def count_residue(lo, hi, residue, step):
    """Number of integers j in [lo,hi] with j = residue mod step."""
    if lo > hi:
        return 0
    return (hi - residue) // step - (lo - 1 - residue) // step


@dataclass(frozen=True)
class Contract:
    words: int
    low_stride: int
    T: F
    g: F
    freeze: F
    e: F
    c: F
    check_gap: F
    command_delay: F

    def __post_init__(self):
        for name in ('T', 'g', 'freeze', 'e', 'c', 'check_gap', 'command_delay'):
            object.__setattr__(self, name, F(getattr(self, name)))
        if (self.words <= 0 or self.low_stride <= 0
                or gcd(self.words, self.low_stride) != 1):
            raise ValueError('positive W,k and gcd(W,k)=1 required')
        if (self.T <= 0 or self.g <= 0 or self.freeze < 0
                or not 0 <= self.e < self.c <= self.g
                or self.check_gap <= 0 or self.command_delay < 0):
            raise ValueError('invalid horizon, reservation, freeze or channel bounds')

    @property
    def N(self):
        return ceilq(self.T / self.g)  # starts strictly before T

    @property
    def H_fast(self):
        return self.words * self.g + self.c

    @property
    def lookahead(self):
        return self.check_gap + self.command_delay + self.freeze + self.H_fast

    @property
    def startup_end(self):
        # Negative freezes are precommitted FAST; at least the first W slots.
        return min(self.N, max(self.words, ceilq(self.freeze / self.g))) - 1

    def fast_ranges(self, danger):
        ranges = []
        for a, b in danger:
            a, b = F(a), F(b)
            if not 0 <= a <= b <= self.T:
                raise ValueError('danger intervals must be closed subsets of [0,T]')
            lo = max(0, ceilq((a - self.H_fast) / self.g))
            hi = min(self.N - 1, floorq((b + self.freeze) / self.g))
            ranges.append((lo, hi))
        return merge_ranges(ranges)

    def ranges(self, danger):
        return merge_ranges([(0, self.startup_end), *self.fast_ranges(danger)])

    def mandatory(self, j, danger):
        return (0 <= j < self.N and (j % self.low_stride == 0
                or any(lo <= j <= hi for lo, hi in self.ranges(danger))))

    def count(self, danger, *, word=None, completed_only=False):
        """Analytic count, independent of T/g; at most O(number of zone entries)."""
        hi = self.N - 1
        if completed_only:
            hi = min(hi, floorq((self.T - self.c) / self.g))
        if word is None:
            residue, period = 0, self.low_stride
        else:
            if not 0 <= word < self.words:
                raise ValueError('word outside memory')
            # j=0 mod k and j=w mod W; gcd(k,W)=1.
            residue = self.low_stride * ((word * pow(self.low_stride, -1, self.words)) % self.words)
            period = self.low_stride * self.words
        count = count_residue(0, hi, residue, period)
        for lo, end in self.ranges(danger):
            end = min(end, hi)
            if word is None:
                all_in_range = max(0, end - lo + 1)
            else:
                all_in_range = count_residue(lo, end, word, self.words)
            count += all_in_range - count_residue(lo, end, residue, period)
        return count

    def window(self, j):
        if not 0 <= j < self.N:
            raise ValueError('slot not started before T')
        return j * self.g + self.e, j * self.g + self.c

    def small_windows(self, danger, *, limit=10000):
        """Explicit output only for small synthetic regression examples."""
        if self.N > limit:
            raise ValueError('use compressed ranges/counts for mission calendars')
        return [dict(j=j, word=j % self.words, left=self.window(j)[0],
                     right=self.window(j)[1],
                     completed_by_T=self.window(j)[1] <= self.T)
                for j in range(self.N) if self.mandatory(j, danger)]


def app_accounting(candidate):
    """Only deterministic arrival/operation counts, no inherited service or risk."""
    inherited = candidate['inherited_contract']
    a = inherited['application']
    W = candidate['memory']['words']
    T = F(candidate['mission']['duration_s']) * 10**9
    epoch = a['epoch_ns']
    multiplier = a['address_multiplier']
    if gcd(multiplier, W) != 1 or epoch <= 0:
        raise ValueError('application addresses are not a full permutation')
    D = inherited['constraints']['application_deadline_ns']
    first_r = a['first_ns'] + a['read_offset_ns']
    first_w = a['first_ns'] + a['write_offset_ns']
    nr = max(0, ceilq((T - first_r) / epoch))
    nw = max(0, ceilq((T - first_w) / epoch))
    period = W * epoch
    inv = pow(multiplier, -1, W)
    pending_writes = []
    sample_words = []
    # O(W), never O(number of requests); exact wordwise tail and prefix checks.
    counts, firsts, tails = [], [], []
    for w in range(W):
        first = first_w + (w * inv % W) * epoch
        n = max(0, ceilq((T - first) / period))
        last = first + (n - 1) * period if n else None
        counts.append(n)
        firsts.append(min(T, first))
        tails.append(T - last if n else T)
        if n and last + D > T:
            pending_writes.append(w)
        if w in {0, W - 1}:
            sample_words.append(dict(word=w, first_arrival_ns=first,
                                     count=n, last_arrival_ns=last))
    if sum(counts) != nw:
        raise AssertionError('per-word counts disagree with offered requests')
    return dict(
        status='DETERMINISTIC_RESEARCH_APPLICATION_ONLY',
        period_ns=period, aperture_requirement_ns=D,
        first_write_ns=first_w, reads_offered_before_T=nr,
        writes_offered_before_T=nw, min_writes_per_word=min(counts),
        max_writes_per_word=max(counts), sample_words=sample_words,
        largest_first_cell_ns=max(firsts), largest_last_cell_ns=max(tails),
        pending_write_words=pending_writes,
        operations=dict(read_beats=3*(nr+nw), write_beats=3*(nw+W),
                        decodes=nr+nw, encodes=nw+W, turnarounds=nw+W,
                        initial_encodes=W, initial_write_beats=3*W,
                        app_dispatches=nr+nw, app_requests=nr+nw,
                        app_replies=nr+nw),
        counts_include_full_pending_work=True,
        all_pre_T_offers_paid_even_if_execution_starts_after_T=True,
        KM_service_deadline_established=False, Q_upper=None, scalar_price=None)

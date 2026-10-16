"""Exact empty-calendar integrals, NOT a replacement for arbitrary RTL traces.

All times are integer nominal ns. The caller must separately discharge the
empty/settled guard and split every permit/freeze transition. No production
update functions or independent checker helpers are imported here.
"""
from dataclasses import dataclass

WORDS = 524288
PERIOD = 4704
DURATION = 92


def slot(j):
    if j < 0:
        raise ValueError('negative slot')
    return 1568*(j//8)+164*(j%8)


def address(j):
    return (174763*j) % WORDS


def first_slot(t):
    """Index of the first start >= t, including the long application gap."""
    if t <= 0:
        return 0
    frame, phase = divmod(t, 1568)
    k = (phase+163)//164
    return frame*8+min(k, 8)


@dataclass(frozen=True)
class EmptyGuard:
    clean: bool
    pending_operations: int
    pending_applications: int
    pending_cdc: int
    permit_stable: bool
    frozen_prefix_settled: bool
    next_external_ns: int | None
    next_rule_boundary_ns: int | None

    def check(self, begin, end):
        if not 0 <= begin < end:
            raise ValueError('empty interval ordering')
        if self.clean is not True:
            raise ValueError('dirty or unknown memory')
        if (self.pending_operations, self.pending_applications, self.pending_cdc) != (0, 0, 0):
            raise ValueError('pending work cannot be skipped')
        if self.permit_stable is not True or self.frozen_prefix_settled is not True:
            raise ValueError('unsettled permission/freeze boundary')
        for t in (self.next_external_ns, self.next_rule_boundary_ns):
            if t is not None and t < end:
                raise ValueError('event or rule boundary inside skipped interval')


def _ranges(low, words):
    # [lo, hi) in slot indices, restricted to a residue mod24.
    for r in range(24):
        if not low or r % 3 == 0:
            yield r, 0, None
        else:
            yield r, 0, words


def _residue_limits(r, lo, hi):
    return max(0, (lo-r+23)//24), None if hi is None else max(0, (hi-r+23)//24)


def _prefix(t, low, words):
    """Occupied ns in [0,t), by at most24 arithmetic progressions."""
    if t <= 0:
        return 0
    total = 0
    for r, lo, hi in _ranges(low, words):
        q0, q1 = _residue_limits(r, lo, hi)
        origin = slot(r)
        # All starts strictly before t; their last one may be truncated.
        n = max(0, (t-1-origin)//PERIOD+1)
        if q1 is not None:
            n = min(n, q1)
        if n <= q0:
            continue
        total += (n-q0-1)*DURATION + min(DURATION, t-origin-(n-1)*PERIOD)
    return total


def _starts_before(t, low, words):
    count = 0
    for r, lo, hi in _ranges(low, words):
        q0, q1 = _residue_limits(r, lo, hi)
        n = max(0, (t-1-slot(r))//PERIOD+1)
        if q1 is not None:
            n = min(n, q1)
        count += max(0, n-q0)
    return count


def integrate(begin, end, low=False, words=WORDS):
    """Accounting only; callers must not infer a legal state jump from it.

    completed counts releases in (begin,end]; partial_begin/end are indicators
    of operations straddling those boundaries. Thus no free terminal drain.
    """
    if not 0 <= begin <= end or words < 2:
        raise ValueError('interval or word count')
    starts_a = _starts_before(begin, low, words)
    starts_b = _starts_before(end, low, words)
    done_a = _starts_before(begin-DURATION+1, low, words)
    done_b = _starts_before(end-DURATION+1, low, words)
    return {'occupied_ns': _prefix(end, low, words)-_prefix(begin, low, words),
            'started': starts_b-starts_a, 'completed': done_b-done_a,
            'partial_begin': starts_a-done_a, 'partial_end': starts_b-done_b}


def peak(begin, end, width=1000000, low=False, words=WORDS):
    """Exact max over continuous windows wholly inside [begin,end].

    Within either side of warmup, differences of periodic integrals repeat.
    Only one period at each endpoint and the warmup +/- width boundary needs
    enumerating. Include every breakpoint and its -width translation there.
    """
    if end-begin < width or width <= 0:
        raise ValueError('peak window does not fit')
    last = end-width
    candidates = {begin, last}
    warm = slot(words)
    centers = [begin, last]
    if low:
        centers += [warm-width, warm]
    for center in centers:
        a, b = max(begin, center-PERIOD), min(last, center+PERIOD)
        if a > b:
            continue
        candidates.update((a, b))
        for offset in (0, width):
            j0 = first_slot(max(0, a+offset-DURATION))-1
            j1 = first_slot(b+offset)+1
            for j in range(max(0, j0), j1+1):
                if low and j >= words and j % 3:
                    continue
                for x in (slot(j)-offset, slot(j)+DURATION-offset):
                    if a <= x <= b:
                        candidates.add(x)
    work, negtime = max((integrate(x, x+width, low, words)['occupied_ns'], -x)
                        for x in candidates)
    return {'occupied_ns': work, 'window_start_ns': -negtime,
            'window_ns': width, 'fraction': work/width}


def skip(begin, end, guard, low=False):
    guard.check(begin, end)
    result = integrate(begin, end, low)
    if result['partial_begin'] or result['partial_end']:
        raise ValueError('jump splits an atomic operation')
    return result

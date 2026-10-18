"""Own registered numerical policies. No policy receives the injection stream."""
from bisect import bisect_right
from collections import deque
from fractions import Fraction

NS = 1_000_000_000
HOUR = 3600 * NS
CUT = 188160
STRIDES = (1, 3, 9, 27)


def next_cut(t, cut=CUT):
    return (t // cut + 1) * cut


class Policy:
    def __init__(self, words=524288, cut=CUT):
        self.words, self.cut = words, cut
        self.k = 1
        self.times, self.modes = [0], [1]
        self.observations = self.updates = 0
        self.timer = None

    def mode(self, t):
        return self.modes[max(0, bisect_right(self.times, t) - 1)] if t >= 0 else 1

    def set_mode(self, t, k):
        assert k in STRIDES and t >= self.times[-1]
        if self.k != k:
            if t == self.times[-1]:
                self.modes[-1] = k
            else:
                self.times.append(t)
                self.modes.append(k)
            self.k = k

    def choose(self, seconds):
        return max((k for k in STRIDES if Fraction(k*self.words*196, NS) <= seconds), default=1)

    def publish(self, t):
        pass

    def observe(self, t, source):
        self.observations += 1

    def wake(self, t):
        self.timer = None

    def finish(self, t):
        pass

    def costs(self, horizon):
        return dict(delivered_ERR=self.observations, logical_updates=self.updates,
                    nominal_cut_services=horizon//self.cut if not isinstance(self, Constant) else 0,
                    CPU_use_percent=None, CPU_time_ns=None, energy=None)


class Constant(Policy):
    def __init__(self, k=1, **kw):
        super().__init__(**kw)
        self.k = self.modes[0] = k


class Our(Policy):
    def __init__(self, cfg=None, **kw):
        super().__init__(**kw)
        self.cfg = cfg or dict(NW=4500045002, NH=9000090002, NR=9015504896,
                               timer_tick_ns=20, pair_source_ticks=22500225010,
                               source_tick_ns=4)
        self.short = self.long = self.pending = 0
        self.recovery = self.cfg['NR'] * self.cfg['timer_tick_ns']
        self.last = None
        self.timer = next_cut(self.recovery, self.cut)

    def publish(self, t):
        self.pending += 1
        self.set_mode(t, 1)

    def observe(self, t, source):
        super().observe(t, source)
        self.updates += 1
        self.pending -= 1
        self.short = max(self.short, t+self.cfg['NW']*self.cfg['timer_tick_ns'])
        if self.last is not None and source-self.last <= self.cfg['pair_source_ticks']*self.cfg['source_tick_ns']:
            self.long = max(self.long, t+self.cfg['NH']*self.cfg['timer_tick_ns'])
        self.last = source
        self.timer = next_cut(max(self.short, self.long, self.recovery), self.cut)

    def wake(self, t):
        self.updates += 1
        self.timer = None
        if not self.pending and t > max(self.short, self.long, self.recovery):
            self.set_mode(t, 3)


class Krasnikov(Policy):
    def __init__(self, Ms='0.001', zero='longest', **kw):
        super().__init__(**kw)
        self.Ms, self.zero = Fraction(Ms), zero
        assert self.Ms > 0 and zero in ('hold', 'longest')
        self.target = Fraction(1)
        self.count = 0
        self.anchor = 0
        self.timer = self.period if zero == 'longest' else None

    @property
    def period(self):
        return self.k*self.words*196

    def advance(self, t):
        # Only the first pending/nonstationary cycle needs an actual update.
        end = self.anchor+self.period
        if t < end:
            return
        if self.count or (self.zero == 'longest' and self.k != 27):
            p = Fraction(self.period, NS)
            self.updates += 1
            if self.count and self.count != self.target:
                self.target = 1+2*self.words*self.Ms*p/(self.count*315576000)
                pstar = 315576000*self.target*(self.target-1)/(2*self.Ms*self.words)
                self.set_mode(end, self.choose(pstar))
            elif not self.count and self.zero == 'longest':
                self.set_mode(end, 27)
            self.count = 0
            self.anchor = end
        # After a nonzero cycle, longest may change once at its next end.
        if self.zero == 'longest' and self.k != 27 and t >= self.anchor+self.period:
            self.anchor += self.period
            self.updates += 1
            self.set_mode(self.anchor, 27)
        empty = (t-self.anchor)//self.period
        self.updates += empty
        self.anchor += empty*self.period
        self.timer = self.anchor+self.period if self.count or (self.zero == 'longest' and self.k != 27) else None

    def observe(self, t, source):
        self.advance(t)  # close [anchor,end) before a boundary arrival
        super().observe(t, source)
        self.count += 1
        self.timer = self.anchor+self.period

    def wake(self, t):
        self.advance(t)

    def finish(self, t):
        self.advance(t)


class Patent(Policy):
    def __init__(self, window_s=60, **kw):
        super().__init__(**kw)
        self.window = window_s*NS
        self.sources = deque()
        self.timer = self.window

    def update(self, t):
        while self.sources and self.sources[0] <= t-self.window:
            self.sources.popleft()
        self.updates += 1
        n = len(self.sources)
        if n*30*NS > self.window:
            self.set_mode(t, 1)
        elif t >= self.window and n*60*NS < self.window:
            self.set_mode(t, 27)
        candidates = [self.sources[0]+self.window] if self.sources else []
        if t < self.window:
            candidates.append(self.window)
        self.timer = min(candidates) if candidates else None

    def observe(self, t, source):
        super().observe(t, source)
        if source > t-self.window:
            self.sources.append(source)
        self.update(t)

    def wake(self, t):
        self.update(t)


class Chen(Policy):
    def __init__(self, weights, fault_budget='0.1', **kw):
        super().__init__(**kw)
        assert len(weights) == 7
        self.weights = tuple(Fraction(x) for x in weights)
        self.budget = Fraction(fault_budget)
        assert self.budget > 0
        self.bins = {}
        self.hour = 1
        self.timer = next_cut(HOUR, self.cut)
        self.cache = {}

    def observe(self, t, source):
        super().observe(t, source)
        h = t//HOUR
        self.bins[h] = self.bins.get(h, 0)+1

    def wake(self, t):
        self.updates += 1
        if self.hour >= 6:
            x = tuple(self.bins.get(h, 0) for h in range(self.hour-6, self.hour))
            if x not in self.cache:
                pred = max(Fraction(0), self.weights[0]+sum(a*b for a,b in zip(self.weights[1:],x)))
                z = pred/self.budget
                n = max(1, -(-z.numerator//z.denominator))
                self.cache[x] = self.choose(Fraction(3600, n))
            self.set_mode(t, self.cache[x])
            self.bins.pop(self.hour-6, None)
        self.hour += 1
        self.timer = next_cut(self.hour*HOUR, self.cut)


def make(spec, words=524288, weights=None, our_cfg=None, cut=CUT):
    kw = dict(words=words, cut=cut)
    family = spec['family']
    if family == 'constant':
        return Constant(spec['k'], **kw)
    if family == 'our':
        return Our(our_cfg, **kw)
    if family == 'krasnikov':
        return Krasnikov(spec['Ms'], spec['zero'], **kw)
    if family == 'patent':
        return Patent(spec['window_s'], **kw)
    if family == 'chen_analog':
        return Chen(weights, spec['fault_budget'], **kw)
    raise ValueError(family)

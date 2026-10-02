"""Finite integer reference state transitions for Appendix B.3 / G.2 tests.

This is a regression oracle, not RTL or a simulated adaptive comparison.
"""
from dataclasses import dataclass, field


def join(old, new):
    if old is None or new[0] > old[1]:
        return new
    return min(old[0], new[0]), max(old[1], new[1])


@dataclass
class MonitorState:
    w: int
    stride: int
    h0: int
    d: int
    DQ: int
    lease: int
    k: int
    hE: int
    hM: int
    Q: tuple | None = None
    LOW: tuple | None = None
    holdE: int = 0
    holdM: int = field(init=False)
    last_index: int = -1
    decisions: dict = field(default_factory=dict)

    def __post_init__(self):
        assert 0 < self.h0 < self.w and 0 < self.stride <= self.w-self.h0
        self.holdM = self.hM

    def err(self, now):
        self.holdE = max(self.holdE, now+self.hE)

    def message(self, index, value, now, good=True):
        start = index*self.stride
        deadline = start+self.w+self.d
        if now < deadline:
            raise ValueError('early messages must wait for the fixed deadline')
        valid = (good and now == deadline and index>self.last_index and
                 type(value) is int and 0 <= value <= self.k and value < 2**64)
        self.last_index = max(index, self.last_index)
        if not valid:
            self.Q = self.LOW = None
            self.holdM = max(self.holdM, now+self.hM)
            return False
        self.Q = join(self.Q, (start+self.h0, start+self.w))
        if self.Q[1]-self.Q[0] >= self.DQ:
            self.LOW = join(self.LOW, (self.Q[1], self.Q[1]+self.lease))
        return True

    def execute(self, slot, decision_time, fence, Ps, ka, T):
        if slot not in self.decisions:
            required = (max(0, fence-Ps), min(T, fence+Ps))
            covered = self.LOW is not None and self.LOW[0]<=required[0] and self.LOW[1]>=required[1]
            skip = (decision_time>=0 and slot%ka and decision_time>=self.holdE and
                    decision_time>=self.holdM and covered)
            self.decisions[slot] = not bool(skip)
        return self.decisions[slot]  # a promise/pending write is never revoked


@dataclass
class ERRState:
    h: int
    tau: int
    hold: int = field(init=False)
    decisions: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.h <= self.tau:
            raise ValueError('h must exceed tau')
        self.hold = self.h

    def flag_or_loss(self, now):
        self.hold = max(self.hold, now+self.h)

    def execute(self, slot, now, ka):
        if slot not in self.decisions:
            self.decisions[slot] = slot%ka==0 or now < self.hold or now < 0
        return self.decisions[slot]

"""Executable state semantics, not RTL, a bus driver or a timing simulator.

Time arguments are absolute integer core ticks. In one tick process health
and ERR first, then freeze an uncommitted slot. An issued decision is immutable.
"""
from dataclasses import dataclass, field


@dataclass
class Rule:
    W: int
    ka: int
    w: int
    h: int
    tau: int
    stage: int = 2
    short_until: int = -1
    long_until: int = -1
    last_err: int | None = None
    healthy: bool = True
    forced_until: int = 0
    now: int = 0
    cursor: int = 0
    pending: tuple | None = None
    counted_transaction: int | None = None
    transaction: int = 0
    decisions: dict = field(default_factory=dict)
    mission_budget_id: str = 'one-lifetime-budget'

    def __post_init__(self):
        assert self.W > 0 and self.ka > 0 and self.ka % 2 and self.h >= self.w > self.tau >= 0
        self.forced_until = self.h+self.tau

    def at(self, t):
        assert isinstance(t, int) and t >= self.now
        self.now = t

    def fast(self, t):
        return not self.healthy or t <= max(self.short_until, self.long_until, self.forced_until)

    def flag(self, t):
        self.at(t)
        self.short_until = max(self.short_until,t+self.w)
        if self.stage == 1 or (self.last_err is not None and t-self.last_err <= self.w):
            self.long_until = max(self.long_until,t+self.h)
        self.last_err = t

    def begin(self, word, kind='control'):
        assert self.pending is None and 0 <= word < self.W
        assert kind in ('control','write16','write32')
        self.transaction += 1
        self.pending = (self.transaction, word, kind)
        return self.transaction

    def err(self, t, transaction):
        self.at(t)
        assert self.pending is not None and self.pending[0] == transaction
        if self.counted_transaction == transaction:
            return False
        self.counted_transaction = transaction
        self.flag(t)
        return True

    def release(self, transaction):
        assert self.pending is not None and self.pending[0] == transaction
        self.pending = None

    def loss(self, t):
        self.at(t); self.healthy = False
        # Do not discard a committed skip, pending repair, cursor or budget.

    def recover(self, t):
        self.at(t); self.healthy = True
        self.forced_until = max(self.forced_until,t+self.h+self.tau)
        # Old absolute holds and last ERR are preserved; forgetting is not needed.

    def freeze(self, j, t):
        self.at(t)
        assert j == self.cursor and j not in self.decisions
        decision = j < self.W or j % self.ka == 0 or self.fast(t)
        self.decisions[j] = decision
        self.cursor += 1
        return decision

    def word(self, j):
        return (pow(self.ka,-1,self.W)*j) % self.W

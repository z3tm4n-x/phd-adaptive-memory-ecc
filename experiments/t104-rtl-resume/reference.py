"""New E reference, not the accepted A model or a physical SRAM model.

Time is an absolute integer xi tick; one core edge is four ticks.  A grant
starts an indivisible operation.  Queue capture and reply consumption are
separate events.  No rule parameters or radiation estimator live here.
"""
from dataclasses import dataclass, field
from fractions import Fraction as F
import json
from pathlib import Path

U64 = (1 << 64) - 1
CONTROL, READ32, WRITE32 = range(3)


@dataclass(frozen=True)
class ServiceConfig:
    words: int = 524288
    ka: int = 3
    batch: int = 8
    g: int = 196
    c: int = 164
    lead: int = 320
    app_offset: int = 1312
    app_charge: int = 240
    core: int = 4

    def validate(self):
        if (self.words < 8 or self.words & (self.words - 1)
                or self.words % self.batch or self.ka < 1 or not self.ka & 1
                or self.ka >= self.words):
            raise ValueError("word count / permutation")
        # First implementation accepts the pinned, mutually compatible service
        # tuple, not arbitrary values that happen to fit one trace.
        if (self.batch, self.g, self.c, self.lead, self.app_offset,
                self.app_charge, self.core) != (8, 196, 164, 320, 1312, 240, 4):
            raise ValueError("unqualified service tuple")
        if self.ka != 3:
            raise ValueError("rule/permutation tuple not registered")
        return self

    @property
    def frame(self):
        return self.batch * self.g

    def start(self, j):
        if not 0 <= j <= U64:
            raise ValueError("slot index overflow")
        s = self.frame * (j // self.batch) + self.c * (j % self.batch)
        if s > U64:
            raise ValueError("calendar overflow")
        return s

    def address(self, j):
        return (pow(self.ka, -1, self.words) * (j % self.words)) % self.words

    def mandatory(self, j):
        return j < self.words or j % self.ka == 0


@dataclass(frozen=True)
class Request:
    kind: int
    word: int
    data: int = 0
    byte_enable: int = 15
    request_id: int = 0

    def validate(self, words):
        if (self.kind not in (CONTROL, READ32, WRITE32)
                or not 0 <= self.word < words or not 0 <= self.data < 1 << 32
                or not 0 <= self.request_id <= U64
                or not 0 < self.byte_enable < 16):
            raise ValueError("invalid atomic request")
        return self


@dataclass
class ETransaction:
    """Pin-level schedule at nominal xi ticks, with externally supplied DQ/ERR.

    step returns the new pin state at that edge.  No host reset cancels this
    object.  Pins use active-high semantic enables (CE/OE/WE), not pin polarity.
    sample and flag are separate; ERR is always captured coherently with DQ.
    """
    request: Request
    start: int
    latch_err: int = 0
    sampled_low: int = 0
    sampled_high: int = 0
    last_t: int = -1

    def step(self, t, dq=0, err=False):
        if t < self.start or t % 4 or t <= self.last_t or not 0 <= dq < 65536:
            raise ValueError("time or DQ")
        self.last_t = t
        age = t - self.start
        kind = self.request.kind
        if age == 60:
            self.sampled_low, self.latch_err = dq, int(bool(err))
        if kind == READ32 and age == 152:
            self.sampled_high = dq
        repair = kind == WRITE32 or (kind == CONTROL and self.latch_err)
        end = 216 if kind == WRITE32 else 184 if kind == READ32 else 148 if repair else 92
        if age > end:
            raise ValueError("operation already released")
        pins = dict(busy=int(age < end), ce=0, oe=0, we=0, drive=0,
                    alias=0, be=3, dout=0, sample=0, flag=0, done=int(age == end),
                    commit=0, pending=int(age >= 60 and repair and age < end),
                    data=self.sampled_low | (self.sampled_high << 16))
        if 4 <= age < 64:
            pins.update(ce=1, oe=1)
        if age == 60:
            pins["sample"] = 1
        if age == 64 and kind != READ32:
            pins["flag"] = self.latch_err
        if repair:
            if 64 <= age < 132:
                pins["ce"] = 1
            if 92 <= age < 140:
                merged = self.sampled_low
                if kind == WRITE32:
                    for byte in range(2):
                        if self.request.byte_enable & (1 << byte):
                            mask = 255 << (8 * byte)
                            merged = (merged & ~mask) | (self.request.data & mask)
                pins.update(drive=1, dout=merged)
            if 92 <= age < 132:
                pins["we"] = 1
            # First alias always reads/writes BOTH bytes, even for high-only
            # user writes: corrected unrequested low bytes come from the latch.
            if age == 132:
                pins["commit"] = 1
        if kind == READ32 and age >= 92:
            pins["alias"] = 1
            if 96 <= age < 156:
                pins.update(ce=1, oe=1)
            if age == 152:
                pins["sample"] = 1
        if kind == WRITE32 and age >= 148:
            pins.update(alias=1, be=self.request.byte_enable >> 2)
            if 152 <= age < 200:
                pins["ce"] = 1
            if 152 <= age < 208:
                pins.update(drive=1, dout=self.request.data >> 16)
            if 160 <= age < 200:
                pins["we"] = 1
            if age == 200:
                pins["commit"] = 1
        return pins


@dataclass(frozen=True)
class Permission:
    mission: int
    sequence: int
    issued: int
    not_before: int
    deadline: int
    expires: int
    integrity: bool = True


@dataclass
class Calendar:
    """Authorized skip input; this is deliberately NOT the T119/T114 policy.

    Caller orders alarm/loss, command delivery, freeze, then start.  Only a
    correctly generated permission may enable skips; this interface cannot
    establish the scientific legitimacy of that permission.
    """
    config: ServiceConfig
    mission: int = 104
    now: int = 0
    sequence: int = 0
    revoked: int = -1
    healthy: bool = True
    active: Permission | None = None
    shadow: Permission | None = None
    committed: dict = field(default_factory=dict)
    started: int = 0
    err_count: int = 0
    overflow: bool = False
    phase_valid: bool = True

    def __post_init__(self):
        self.config.validate()

    def at(self, t):
        if t < self.now or not 0 <= t <= U64:
            self.phase_valid = False
            self.loss(self.now)
            raise ValueError("lost absolute time; no new mission")
        self.now = t
        if self.active is not None and t >= self.active.expires:
            self.active = None
        if self.shadow is not None:
            if t > self.shadow.deadline:
                self.loss(t)
            elif t >= self.shadow.not_before:
                if self.healthy and not self.overflow and self.shadow.issued > self.revoked:
                    self.active = self.shadow
                self.shadow = None

    def loss(self, t):
        self.now = max(t, self.now)
        self.revoked = max(self.revoked, self.now)
        self.active = self.shadow = None
        self.healthy = False

    def err(self, t):
        self.at(t)
        if self.err_count == U64:
            self.overflow = True
        else:
            self.err_count += 1
        self.loss(t)

    def recovered(self, t):
        self.at(t)
        # This does not re-enable old LOW: a fresh authorized permission is
        # still needed, issued strictly after loss and after policy hold(s).
        self.healthy = True

    def command(self, p, t):
        self.at(t)
        valid = (p.integrity and p.mission == self.mission
                 and self.sequence < p.sequence <= U64
                 and self.revoked < p.issued <= t
                 and p.issued <= p.not_before <= p.deadline < p.expires <= U64
                 and t <= p.deadline and self.healthy and self.phase_valid
                 and not self.overflow)
        if not valid:
            self.loss(t)
            return False
        self.sequence = p.sequence
        if t < p.not_before:
            self.shadow = p
        else:
            self.active, self.shadow = p, None
        return True

    def freeze(self, j, t):
        self.at(t)
        expected = max(0, self.config.start(j) - self.config.lead)
        if j in self.committed or t != expected:
            raise ValueError("duplicate or mistimed freeze")
        go = (self.config.mandatory(j) or not self.phase_valid or not self.healthy
              or self.overflow or self.active is None)
        self.committed[j] = go
        return go

    def start_slot(self, j, t):
        self.at(t)
        if j != self.started or t != self.config.start(j) or j not in self.committed:
            raise ValueError("phase/commit mismatch")
        self.started += 1
        return self.committed.pop(j), self.config.address(j)


@dataclass
class QueueEntry:
    request: Request
    offered: int
    state: str = "queued"
    granted: int | None = None
    completed: int | None = None


class ApplicationQueue:
    """Two places INCLUDING busy/held replies; no invented cancellation.

    This domain-side model receives a complete captured offer with its original
    first-VALID timestamp. CDC correctness/bounds are a separate obligation.
    """
    def __init__(self, words=524288, capacity=2):
        self.words, self.capacity = words, capacity
        self.entries = []
        self.fault = False
        self.seen = set()

    def offer(self, request, first_valid, captured):
        request.validate(self.words)
        if request.kind == CONTROL or first_valid > captured or first_valid < 0:
            raise ValueError("not an application offer")
        if request.request_id in self.seen:
            raise ValueError("offer replay")
        if len(self.entries) == self.capacity:
            self.fault = True
            return False
        self.seen.add(request.request_id)
        self.entries.append(QueueEntry(request, first_valid))
        return True

    def grant(self, t, bus_free=True):
        if t % 1568 != 1312 or not bus_free:
            return None
        if any(e.state == "active" for e in self.entries):
            raise ValueError("global lock already held")
        for e in self.entries:
            if e.state == "queued":
                e.state, e.granted = "active", t
                return e.request
        return None

    def complete(self, request_id, t):
        e = next(e for e in self.entries if e.request.request_id == request_id)
        duration = 216 if e.request.kind == WRITE32 else 184
        if e.state != "active" or t != e.granted + duration:
            raise ValueError("completion is not release")
        e.state, e.completed = "reply", t

    def consume(self, request_id, t):
        e = next(e for e in self.entries if e.request.request_id == request_id)
        if e.state != "reply" or t < e.completed:
            raise ValueError("reply before completion")
        self.entries.remove(e)

    def soft_reset(self):
        self.fault = True  # obligations/occupancy are deliberately preserved


def resource_contract():
    """Independent rational substitution into accepted T114 §4, not new Q(T)."""
    b, rho = F(1), F(180000)
    base = F("0.760353512607")
    # Accepted decimal is rounded for display; round it OUT by one last unit.
    base_up = base + F(1, 10**12)
    app_s = F("217.002160") / 10**9
    peak = base_up + app_s / F("0.001") * (b + rho * F("0.001003"))
    # At b=1 all offers are separated by >=1/rho >3us, hence no earlier
    # application job can be pending. Wait <= one complete frame + CDC;
    # use the slower comparison server frame (1700 xi), not only 1568.
    response_ns = (F("16.500160") + F("1700.517000")
                   + F("217.002160") + F("40.500400") + 100)
    return {"joint_burst": str(b), "joint_rate_per_s": str(rho),
            "peak_upper": str(peak), "peak_upper_float": float(peak),
            "response_ns_upper_with_10pct": str(response_ns * F(11, 10)),
            "passes": peak <= F(4, 5) and response_ns * F(11, 10) <= 3000,
            "scope": "conditional bound; not measured FPGA timing or traffic"}


def load_config():
    x = json.loads(Path(__file__).with_name("config.json").read_text(encoding="utf-8"))
    return ServiceConfig(words=x["word_count"], ka=x["ka"], batch=x["batch"],
                         g=x["g_ticks"], c=x["control_charge_ticks"],
                         lead=x["freeze_lead_ticks"], app_offset=x["app_grant_offset_ticks"],
                         app_charge=x["app_write_charge_ticks"], core=x["core_ticks"]).validate()

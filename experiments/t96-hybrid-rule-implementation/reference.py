"""T96-A executable specification, directly from T95. Not production firmware.

Time is an integer T95 virtual tick, not a Python runtime or a physical FPGA clk.
The model has no radiation generator, CY62167 hidden-bit decoder, or WCET claim.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, replace
from fractions import Fraction as F
from hashlib import sha1
import json
from pathlib import Path
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
U64 = (1 << 64) - 1


def ceil(x):
    x = F(x)
    return -(-x.numerator // x.denominator)


def uint(x):
    if type(x) is not int or not 0 <= x <= U64:
        raise ValueError("not uint64")
    return x


def add(a, b):
    return uint(uint(a) + uint(b))


def load_inputs():
    cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    for path, wanted in cfg["sources"].items():
        raw = (ROOT / path).read_bytes()
        # Normalize checkout CRLF for a Windows text checkout, like Git's blob.
        raw = raw.replace(b"\r\n", b"\n")
        actual = sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != wanted:
            raise ValueError(f"accepted input changed: {path}")
    handoff = json.loads((ROOT / cfg["handoff_path"]).read_text(encoding="utf-8"))
    pinned = json.loads((ROOT / "experiments/t90-monitor-physical/outputs/pinned_inputs.json")
                        .read_text(encoding="utf-8"))
    row = next(x for x in pinned if x["shield"] == "3")
    return cfg, handoff, row


@dataclass(frozen=True)
class Parameters:
    W: int
    ka: int
    c: int
    g: int
    fence: int
    lead: int
    window: int
    stride: int
    delivery: int
    lease: int
    hold: int
    k: int
    J: int
    end: int
    mission_id: str
    config_id: str

    @classmethod
    def accepted(cls):
        cfg, h, row = load_inputs()
        v, m = h["fixed_contract"], h["monitor"]
        tick = F(v["tick_nominal_s"])
        tick_min = tick * F(v["clock_constant_scale_lower"])
        window = row["actual_window_at_selected_g"]
        return cls(v["W"], v["ka"], v["c_ticks"], v["g_ticks"],
                   v["fence_ticks"], v["decision_lead_ticks"],
                   int(F(m["nominal_window_s"]) / tick),
                   int(F(m["nominal_stride_s"]) / tick), window["dticks"],
                   m["lease_ticks"], ceil(F(v["hold_ERR_s"]) / tick_min),
                   m["k"], m["J"], ceil(F(v["T_s"]) / tick_min),
                   cfg["reference_profile"]["mission_id"],
                   cfg["reference_profile"]["monitor_config_id"])

    @property
    def Ps(self):
        return self.W * self.g

    def deadline(self, index):
        if type(index) is not int or not 0 <= index < self.J:
            raise ValueError("outside the original finite window family")
        return add(add(uint(index * self.stride), self.window), self.delivery)


@dataclass(frozen=True)
class Slot:
    j: int
    word: int
    start: int
    decision: int
    fence: int
    mandatory: bool
    initial: bool


class Calendar:
    def __init__(self, p):
        self.p = p
        self.inverse = pow(p.ka, -1, p.W)

    def slot(self, j):
        uint(j)
        p = self.p
        start = uint(2 * p.g * (j // 2) + p.c * (j % 2))
        return Slot(j, self.inverse * j % p.W, start, start - p.lead,
                    add(start, p.fence), j % p.ka == 0, j < p.W)


@dataclass(frozen=True)
class Message:
    index: int
    epoch: int
    sequence: int
    config_id: str
    start: int
    end: int
    count: int | None = None
    loss_upper: int | None = None
    live_ticks: int | None = None
    complete: bool = False
    calibration_ok: bool = False
    clock_ok: bool = False
    integrity_ok: bool = False
    loss_contract_ok: bool = False
    overflow: bool = False
    saturation: bool = False
    reset: bool = False
    selftest_bad: bool = False


@dataclass(frozen=True)
class Permission:
    mission_id: str
    config_id: str
    sequence: int
    issued_at: int
    apply_by: int
    valid_until: int
    low_left: int
    low_right: int
    holdE: int
    holdM: int
    window_index: int
    force_S: bool
    crc: int = 0

    def checksum(self):
        d = asdict(self)
        del d["crc"]
        return zlib.crc32(json.dumps(d, sort_keys=True, separators=(",", ":")).encode())

    def sealed(self):
        return replace(self, crc=self.checksum())


class Rule:
    """Raw full-window-count variant of T90; three records, no online exp/log.

    The caller buffers early packets and schedules one result/loss at each
    absolute deadline. That scheduling contract is explicit, not measured here.
    """
    def __init__(self, p):
        self.p = p
        self.low = None
        self.holdE, self.holdM = 0, p.hold
        self.last_index = -1
        self.last_sequence = -1
        self.epoch = None
        self.epoch_start = 0
        self.snapshots = deque(maxlen=3)
        self.health = "no_monitor"
        self.now = 0
        self.command_sequence = 0
        self.timing_valid = True
        # Immutable identity only: NOT a replenishable runtime risk account.
        self.lifetime_certificate = (p.mission_id, p.J, "same lifetime U_M")

    def time(self, now):
        try:
            uint(now)
            if now < self.now:
                raise ValueError("clock rollback")
        except ValueError:
            self.low = None
            self.holdM = U64
            self.timing_valid = False
            self.health = "invalid_time"
            raise
        self.now = now

    def loss(self, now, reason="loss"):
        self.time(now)
        self.low = None
        self.snapshots.clear()
        self.holdM = max(self.holdM, min(U64, now + self.p.hold))
        self.health = reason

    def epoch_begin(self, epoch, now, config_id):
        self.time(now)
        if config_id != self.p.config_id or type(epoch) is not int or not 0 <= epoch <= U64:
            self.loss(now, "epoch_invalid")
            return False
        if self.epoch is not None and epoch <= self.epoch:
            self.loss(now, "retired_epoch")
            return False
        self.loss(now, "epoch_change")
        self.epoch, self.epoch_start, self.last_sequence = epoch, now, -1
        # Deliberately preserve last_index, holdE and lifetime_certificate.
        return True

    def err(self, now):
        self.time(now)
        self.holdE = max(self.holdE, min(U64, now + self.p.hold))

    def message(self, m, now):
        self.time(now)
        p = self.p
        try:
            deadline = p.deadline(m.index)
        except (ValueError, TypeError):
            self.loss(now, "index_invalid")
            return "invalid"
        if m.index <= self.last_index:
            return "duplicate_or_reordered"  # no new trial or lease extension
        if now < deadline:
            return "buffer_until_deadline"  # not used; no statistical selection
        if m.index > self.last_index + 1:
            # Last missed window was due before now. Late software cannot undo
            # the hardware expiry; its timing contract is separately invalid.
            self.loss(now, "gap")
        self.last_index = m.index  # burn even invalid/late/large-count results
        start = m.index * p.stride
        try:
            y = add(m.count, m.loss_upper)
            uint(m.sequence)
            valid = (now == deadline and m.epoch == self.epoch
                     and m.sequence > self.last_sequence
                     and m.config_id == p.config_id and m.start == start
                     and m.end == start + p.window and m.start >= self.epoch_start
                     and m.live_ticks == p.window and m.complete
                     and m.calibration_ok and m.clock_ok and m.integrity_ok
                     and m.loss_contract_ok and not (m.overflow or m.saturation
                           or m.reset or m.selftest_bad))
        except (ValueError, TypeError):
            valid, y = False, None
        if m.epoch == self.epoch and type(m.sequence) is int and 0 <= m.sequence <= U64:
            self.last_sequence = max(self.last_sequence, m.sequence)
        if now > deadline:
            self.timing_valid = False
        if not valid or y > p.k:
            self.loss(now, "invalid_or_high")
            return "alarm"
        new = (deadline, add(start, p.lease))
        if self.low is None or new[0] > self.low[1]:
            self.low = new
        else:
            self.low = (min(self.low[0], new[0]), max(self.low[1], new[1]))
        self.snapshots.append((m.index, m.epoch, m.start, m.end, y))
        self.health = "fresh"
        return "LOW"

    def missing(self, index, now):
        self.time(now)
        if now < self.p.deadline(index):
            raise ValueError("not a missing window yet")
        if now > self.p.deadline(index):
            self.timing_valid = False
        if index > self.last_index:
            self.last_index = index
            self.loss(now, "missing")

    def permission(self, now, apply_by=None):
        self.time(now)
        self.command_sequence = add(self.command_sequence, 1)
        # No heartbeat can move this beyond the next original window deadline.
        until = self.p.deadline(self.last_index + 1) if self.last_index + 1 < self.p.J else now
        left, right = self.low or (0, 0)
        return Permission(self.p.mission_id, self.p.config_id, self.command_sequence,
                          now, now if apply_by is None else apply_by, until, left, right,
                          self.holdE, self.holdM, self.last_index,
                          self.low is None or self.health != "fresh").sealed()


@dataclass(frozen=True)
class Decision:
    slot: Slot
    execute: bool
    reason: str
    low_witness: tuple | None


class Gate:
    def __init__(self, p):
        self.p = p
        self.active = None
        self.applied_at = None
        self.last_sequence = -1
        self.holdE = 0
        self.holdM = 0
        self.revoked_at = -1
        self.blocked = False
        self.err_count = 0
        self.err_overflow = False
        self.decisions = {}  # specification trace, NOT production state size
        self.ack = None

    def receive(self, cmd, now):
        try:
            for field in (cmd.sequence, cmd.issued_at, cmd.apply_by, cmd.valid_until,
                          cmd.low_left, cmd.low_right, cmd.holdE, cmd.holdM, now):
                uint(field)
            valid = (cmd.crc == cmd.checksum() and cmd.mission_id == self.p.mission_id
                     and cmd.config_id == self.p.config_id and cmd.sequence > self.last_sequence
                     and cmd.issued_at <= now <= cmd.apply_by
                     and now <= cmd.valid_until and cmd.low_left <= cmd.low_right
                     and (cmd.force_S or cmd.issued_at > self.revoked_at))
        except (ValueError, TypeError):
            valid = False
        if not valid:
            self.active = None
            self.ack = (cmd.sequence, now, "rejected_default_S")
            return False
        self.active = cmd  # atomic swap; never an incremental field update
        self.applied_at = now
        self.last_sequence = cmd.sequence
        self.ack = (cmd.sequence, now, "applied")
        return True

    def loss(self, now):
        uint(now)
        self.active = None  # decisions and pending work belong to other state
        self.revoked_at = max(self.revoked_at, now)
        self.holdM = max(self.holdM, min(U64, now + self.p.hold))

    def err(self, now):
        uint(now)
        self.holdE = max(self.holdE, min(U64, now + self.p.hold))
        if self.err_count == U64:
            self.err_overflow = True
            self.blocked = True
        else:
            self.err_count += 1

    def freeze(self, slot, now):
        if slot.j in self.decisions:
            return self.decisions[slot.j]
        p, a = self.p, self.active
        left, right = max(0, slot.fence - p.Ps), min(p.end, slot.fence + p.Ps)
        timely = now == slot.decision and now >= 0
        good = (timely and left <= right and a is not None and not a.force_S and not self.blocked
                and self.applied_at <= now < a.valid_until
                and now >= max(a.holdE, self.holdE, a.holdM, self.holdM)
                and a.low_left <= left and a.low_right >= right)
        skip = bool(good and not slot.mandatory and not slot.initial)
        reason = ("initial" if slot.initial else "mandatory" if slot.mandatory else
                  "two_sided_LOW" if skip else "default_S")
        result = Decision(slot, not skip, reason, (left, right) if skip else None)
        self.decisions[slot.j] = result
        return result


class Executor:
    """Functional full-word slot, no CY pin waveform or hidden-bit model.

    Supplying decoded_data is the conditional clean-U input, not an ECC decoder.
    CPU acceptance is grant, not an earlier offer while READY is low.
    """
    def __init__(self, p, gate, functional_writes=False):
        self.p, self.gate = p, gate
        self.j = 0
        self.busy = None
        self.pending = None
        self.app_pending = None
        self.values = {}
        self.versions = {}
        self.functional_writes = functional_writes
        self.probability_scope = not functional_writes
        self.service_valid = True
        self.hidden_failure = False
        self.trace = []

    def start(self, decision, now):
        s = decision.slot
        if (s != Calendar(self.p).slot(self.j) or now != s.start
                or self.busy is not None or self.app_pending is not None):
            self.service_valid = False
            raise ValueError("missed/duplicate/shifted reservation")
        self.trace.append(("start" if decision.execute else "skip", s.j, now, s.word))
        if decision.execute:
            self.busy = s
        else:
            self.j += 1

    def latch(self, now, decoded_data, err=False):
        s = self.busy
        if s is None or self.pending is not None or not s.start <= now < s.fence:
            raise ValueError("latch outside active slot")
        if type(decoded_data) is not int or not 0 <= decoded_data < (1 << 32):
            raise ValueError("not data32")
        self.pending = (s.word, decoded_data, self.versions.get(s.word, 0))
        self.trace.append(("latch", s.j, now, bool(err)))
        if err:
            self.gate.err(now)

    def finish(self, now, qualified=True):
        s = self.busy
        if s is None or now != s.fence or self.pending is None:
            self.service_valid = False
            raise ValueError("missing pending write/fence")
        word, value, version = self.pending
        if self.versions.get(word, 0) != version:
            raise AssertionError("older repair would overwrite a newer accepted write")
        # Full write even ERR=0. Hidden failure does not suppress future costs.
        self.values[word] = value
        self.service_valid = self.service_valid and qualified
        self.trace.append(("fence", s.j, now, qualified))
        self.busy = self.pending = None
        self.j += 1

    def write(self, word, value, now, duration, next_reserved):
        if not self.functional_writes:
            return False
        if self.busy is not None or self.app_pending is not None or not can_grant(now, duration, next_reserved):
            return False  # offer only; no acceptance, no newer version yet
        if not 0 <= word < self.p.W or not 0 <= value < (1 << 32):
            raise ValueError("invalid application write")
        self.probability_scope = False
        self.app_pending = (word, value, now + duration)
        self.trace.append(("app_write", word, now, now + duration))
        return True

    def application_finish(self, now):
        if self.app_pending is None or now != self.app_pending[2]:
            raise ValueError("not application commit")
        word, value, _ = self.app_pending
        self.versions[word] = self.versions.get(word, 0) + 1
        self.values[word] = value
        self.app_pending = None

    def program_reset(self, now):
        self.gate.loss(now)  # no j/pending/phase/mission reset

    def clock_reset(self, now):
        self.gate.loss(now)
        self.gate.blocked = True
        self.service_valid = False  # not a newly clean epoch


def can_grant(now, duration, next_reserved):
    return (type(duration) is int and duration > 0 and 0 <= now <= U64
            and now + duration <= min(next_reserved, U64))


def fifo_grants(offers, reservations):
    """Finite functional oracle: FIFO offered work, never crossing a reservation.

    offers = [(offer_tick, duration, label)]. Tied offers use list order (CPU first).
    Resource envelope is a caller assumption, not inferred from passing a trace.
    """
    out, free = [], 0
    for offer, duration, label in offers:
        if duration <= 0:
            raise ValueError("nonpositive transaction")
        start = max(offer, free)
        for lo, hi in reservations:
            if start + duration <= lo:
                break
            if start < hi and start + duration > lo:
                start = hi
        out.append((label, offer, start, start + duration))
        free = start + duration
    return out


def mask_max(length, period, busy):
    """Exact maximum measure in ANY sliding interval of a contiguous periodic mask."""
    length, period, busy = F(length), F(period), F(busy)
    return (length // period) * busy + min(busy, length % period)


def resource_bounds(row):
    """T80 (11), independently substituted, no ready report used as a formula."""
    service = row["effective_T88_input"]["service"]
    a = service["application_contract"]
    cp = F(service["c_ticks"]) * F(service["tick_upper_s"])
    gm = F(row["selected_source_row"]["g"]) * F(service["tick_lower_s"])
    gp, sx, sp = map(F, (a["application_max_request_s"],
                         a["extra_monitor_control_sigma_s"], a["application_sigma_s"]))
    cx, up, h = map(F, (a["extra_monitor_control_rate"], a["application_rate"], a["peak_window_s"]))
    block = 2 * cp + gp
    rate = 1 - block / (2 * gm)
    return {"peak_upper": (mask_max(h, 2 * gm, 2 * cp) + sx + cx * h) / h,
            "service_rate": rate, "stability_slack": rate - up - cx,
            "application_delay_upper_s": block + (sp + sx) / rate,
            "application_delay_margin_upper_s": F(11, 10) * (block + (sp + sx) / rate)}


def mapping_report(p, h, row, core=4):
    v = h["fixed_contract"]
    tm = F(v["tick_nominal_s"]) * F(v["clock_constant_scale_lower"])
    tp = F(v["tick_nominal_s"]) * F(v["clock_constant_scale_upper"])
    margin = 1 + F(v["time_margin"])
    w = row["actual_window_at_selected_g"]
    align = all(x % core == 0 for x in (2 * p.g, p.c, p.fence, p.lead, p.window, p.stride))
    return {"core_ticks": core, "calendar_exact": align,
            "earlier_delivery_deadline_ticks": p.delivery // core * core,
            "post_window_required_s": (p.delivery // core * core) * tm / margin,
            "joint_U_required_s": p.c * tm / margin,
            "naive_rounded_45_plus_45_s": 2 * ceil(F(45, core)) * core * F(1, 10**9),
            "lease_kept_exact_ticks": p.lease,
            "wrong_rounded_lease_margin_s": (p.lease // core * core) * tm - margin * F(w["hF_required"]),
            "correct_lease_margin_s": p.lease * tm - margin * F(w["hF_required"]),
            "hold_ticks": p.hold, "hold_min_s": p.hold * tm,
            "mission_end_conservative_ticks": p.end,
            "alarm_to_first_fence_upper_s": (p.lead + 2 * p.g - p.c + p.fence) * tp,
            "phase_and_clock_qualification": None}

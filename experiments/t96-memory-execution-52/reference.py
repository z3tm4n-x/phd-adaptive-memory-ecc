"""Independent event and calendar oracle. Timestamps label the open ns bucket."""
from bisect import bisect_right
from dataclasses import dataclass, field
import json
from pathlib import Path

CFG = json.loads((Path(__file__).parent / "config.json").read_text())
L = CFG["L_ns"]
CHECKPOINT = CFG["checkpoint_round"] * L
METRICS = ("first_ns", "passes", "read_ns", "write_ns", "writes", "sealed",
           "positive", "switches", "fast_ns")
PAYLOAD = tuple(0xA5BC3410 + 0x10001 * w for w in range(4))


@dataclass
class Run:
    words: list = field(default_factory=lambda: [dict() for _ in range(4)])
    first_ns: int = -1
    passes: int = 0
    read_ns: int = 0
    write_ns: int = 0
    writes: int = 0
    sealed: int = 0
    positive: int = 0
    switches: int = 0
    fast_ns: int = 0
    step: int = 1
    last_bad_cell: int = 0
    trace: list = field(default_factory=list)


def oracle(parents, horizon, *, prefix=None, record_from=0):
    # A first-hit time is latched as each parent's mark is applied, including
    # during pauses and after the final sample. Birth times distinguish
    # surviving old bits from newly re-created bits at the very same position.
    run = Run() if prefix is None else prefix
    begin = CHECKPOINT if prefix is not None else 0
    r = begin // L
    j = 0
    fast_since = begin
    pending = []
    def event(t, priority, row):
        if record_from <= t < horizon:
            pending.append((t, priority, len(pending), row))
    def advance(t):
        nonlocal j
        while j < len(parents) and parents[j][0] < min(t, horizon):
            instant, anchor, bit, other = parents[j]
            for w, pos in ((anchor, bit), ((anchor+1)%4, other)):
                if pos < 0:
                    continue
                errors = run.words[w]
                if pos in errors:
                    del errors[pos]
                else:
                    errors[pos] = instant
                if run.first_ns < 0 and len(errors) >= 2:
                    run.first_ns = instant
            masks = tuple(sum(1 << b for b in word) for word in run.words)
            event(instant, 10, ("H", *masks))
            j += 1
    while r * L < horizon:
        start = r * L
        advance(start)
        run.passes += 1
        count = 0
        for addr in range(8):
            launch = start + (addr // 4) * CFG["frame_ns"] + CFG["phases_ns"][addr % 4]
            if launch >= horizon:
                break
            advance(launch)
            word = addr % 4
            run.read_ns += min(100, horizon-launch)
            event(launch, 0, ("P", addr, 1, 0, 1, 0))
            advance(launch+60)
            if launch+60 >= horizon:
                break
            hit = bool(run.words[word])
            dq = (PAYLOAD[word] >> (16*(addr//4))) & 65535
            event(launch+60, 1, ("S", addr, int(hit), dq))
            event(launch+70, 0, ("P", addr, 1, 1, 1, 0))
            if hit:
                run.write_ns += max(0, min(100, horizon-launch-100))
                event(launch+100, 0, ("P", addr, 1, 1, 1, 1))
                event(launch+110, 0, ("P", addr, 1, 1, 0, 1))
                event(launch+160, 0, ("P", addr, 1, 1, 1, 1))
                event(launch+180, 0, ("P", addr, 1, 1, 1, 0))
                advance(launch+160)
                if launch+160 < horizon:
                    live = run.words[word]
                    run.words[word] = {b: birth for b, birth in live.items() if birth >= launch}
                    run.writes += 1
                    mask = sum(1 << b for b in run.words[word])
                    event(launch+160, 2, ("W", addr, dq, mask))
            release = launch + (200 if hit else 100)
            event(release, 0, ("P", addr, 0, 1, 1, 0))
            if release < horizon:
                count += hit
                if addr == 7:
                    run.sealed += 1
                    run.positive += int(count > 0)
                    event(release, 2, ("R", count))
        if start+2500 < horizon:
            if count:
                run.last_bad_cell = (r+255)//256
                proposal = 1
            elif r % 256 == 0:
                proposal = 1 << bisect_right(CFG["clean_cells"], r//256-run.last_bad_cell)
            else:
                proposal = run.step
            event(start+2500, 1, ("C", proposal))
        if start+2700 < horizon:
            old, run.step = run.step, proposal
            if old != run.step:
                run.switches += 1
                if old == 1:
                    run.fast_ns += start+2700-fast_since
                if run.step == 1:
                    fast_since = start+2700
            event(start+2700, 1, ("I", run.step))
        r += run.step
    advance(horizon)
    if run.step == 1:
        run.fast_ns += horizon-fast_since
    run.trace = [(t, *row) for t, _, _, row in sorted(pending)]
    return run


def metrics(run):
    return tuple(getattr(run, field) for field in METRICS) + (run.step,) + tuple(
        sum(1 << b for b in word) for word in run.words)

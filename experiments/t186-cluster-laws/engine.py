"""Nominal x16 port and 38-bit XOR oracle. Times are integer ns.

A hit labelled t lies strictly between edges t and t+1. Positive fixed_stride
is in baseline rounds. Zero selects the registered common-cell ladder.
"""
import json
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "inputs.json").read_bytes())
W = CFG["words"]
D = CFG["addresses"]
FRAME = CFG["frame_ns"]
L = D // 4 * FRAME
PHASE = tuple(CFG["phases_ns"])
SAMPLE = CFG["sample_ns"]
EDGE = CFG["write_edge_ns"]
READ = CFG["read_ns"]
WRITE = CFG["repair_extra_ns"]
CUT = L - CFG["cut_before_end_ns"]
INSTALL = L - CFG["install_before_end_ns"]
CELL = CFG["cell_rounds"]
REQ = tuple(CFG["clean_cells"])

(FIRST, PASSES, READ_NS, WRITE_NS, REPORTS, RESETS, CELLS, DOWNS,
 SWITCHES, FAST_NS, REPAIRS, REMAIN) = range(12)
FIELDS = ("first_ns", "passes", "read_ns", "write_ns", "positive_reports",
          "resets", "reset_cells", "downshifts", "switches", "fast_ns",
          "completed_writes", "terminal_wrong_bits")


@njit(cache=True)
def pop(mask):
    count = 0
    while mask:
        mask &= mask - 1
        count += 1
    return count


@njit(cache=True)
def hits_before(t, w, b, i, end, limit, masks, occupied, observed_word, recent, stat):
    """Apply in-order toggles, retaining the live positions born in this visit."""
    while i < end and t[i] < limit:
        word = w[i]
        bit = 1 << b[i]
        value = masks[word] ^ bit
        masks[word] = value
        if value:
            occupied |= 1 << word
        else:
            occupied &= ~(1 << word)
        if word == observed_word:
            recent = (recent & ~bit) | (value & bit)
        if stat[FIRST] < 0 and (value & (value - 1)):
            stat[FIRST] = t[i]
        i += 1
    return i, occupied, recent


@njit(cache=True)
def visit_pass(t, w, b, i, end, start, horizon, masks, occupied, stat):
    """Port events for one pass, including any partial terminal operation."""
    repairs = 0
    for address in range(D):
        launch = start + (address // 4) * FRAME + PHASE[address % 4]
        if launch >= horizon:
            break
        word = address % W
        i, occupied, _ = hits_before(t, w, b, i, end, launch, masks, occupied, -1, 0, stat)
        stat[READ_NS] += min(READ, horizon - launch)
        i, occupied, recent = hits_before(t, w, b, i, end, min(launch + SAMPLE, horizon),
                                          masks, occupied, word, 0, stat)
        if launch + SAMPLE >= horizon or masks[word] == 0:
            continue
        stat[WRITE_NS] += max(0, min(WRITE, horizon - launch - READ))
        i, occupied, recent = hits_before(t, w, b, i, end, min(launch + EDGE, horizon),
                                          masks, occupied, word, recent, stat)
        if launch + EDGE < horizon:
            masks[word] = recent
            if not recent:
                occupied &= ~(1 << word)
        if launch + READ + WRITE < horizon:
            repairs += 1
    return i, occupied, repairs


@njit(cache=True)
def trajectory(t, w, b, i, end, horizon, fixed_stride, accelerate=True):
    stat = np.zeros(len(FIELDS), dtype=np.int64)
    stat[FIRST] = -1
    masks = np.zeros(W, dtype=np.int64)
    occupied = 0
    level = last_bad = r = fast_since = 0
    step = fixed_stride if fixed_stride else 1
    while r * L < horizon:
        start = r * L
        i, occupied, _ = hits_before(t, w, b, i, end, start, masks, occupied, -1, 0, stat)
        next_hit = t[i] if i < end else horizon
        if accelerate and start + L <= min(next_hit, horizon):
            if not occupied:
                # Every such pass finishes before the first new hit. Account
                # them together up to (excluding) the next possible promotion.
                count = 1 + (min(next_hit, horizon) - start - L) // (step * L)
                if fixed_stride == 0 and step < CELL:
                    due = (last_bad + REQ[level]) * CELL
                    count = min(count, max(0, (due - r) // step))
                if count:
                    stat[PASSES] += count
                    stat[READ_NS] += count * D * READ
                    r += count * step
                    continue
            # With no arriving hits, each dirty word is repaired on its
            # first alias. The second half then sees a clean word.
            repairs = pop(occupied)
            masks[:] = 0
            occupied = 0
            stat[READ_NS] += D * READ
            stat[WRITE_NS] += repairs * WRITE
        else:
            i, occupied, repairs = visit_pass(t, w, b, i, end, start, horizon,
                                               masks, occupied, stat)
        stat[PASSES] += 1
        stat[REPAIRS] += repairs
        # A positive report here means the count available at the cut.
        if repairs and start + CUT < horizon:
            stat[REPORTS] += 1
        if not fixed_stride and start + INSTALL < horizon:
            old = step
            if r and repairs:
                cell = (r + CELL - 1) // CELL
                stat[RESETS] += 1
                stat[CELLS] += int(cell != last_bad)
                last_bad = cell
                level = 0
            if r % CELL == 0:
                clean = r // CELL - last_bad
                level = 0
                while level < len(REQ) and clean >= REQ[level]:
                    level += 1
            step = 1 << level
            if step != old:
                stat[SWITCHES] += 1
                stat[DOWNS] += int(step < old)
                if old == 1:
                    stat[FAST_NS] += start + INSTALL - fast_since
                if step == 1:
                    fast_since = start + INSTALL
        r += step
    hits_before(t, w, b, i, end, horizon, masks, occupied, -1, 0, stat)
    if step == 1:
        stat[FAST_NS] += horizon - fast_since
    for value in masks:
        stat[REMAIN] += pop(value)
    return stat


@njit(cache=True)
def block(t, w, b, offsets, horizon, strides):
    out = np.empty((len(strides), len(offsets) - 1, len(FIELDS)), dtype=np.int64)
    for j, stride in enumerate(strides):
        for k in range(len(offsets) - 1):
            out[j, k] = trajectory(t, w, b, offsets[k], offsets[k + 1], horizon, stride)
    return out

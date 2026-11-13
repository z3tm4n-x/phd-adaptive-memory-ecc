"""Threshold with one complete clean cell of hold. Use the original SRAM service."""

import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent / "t186-cluster-laws"
sys.path.insert(0, str(BENCH))
import engine as e


def krasnikov_step(period, target, count, design_s=315576000):
    """Substitute (9) and (10) exactly. Period is a stride in units of L."""
    ms = Fraction(1, 1000)
    scan = Fraction(e.L, 10**9)
    if count == 0 or count == target:
        return period, target
    new = 1 + 2 * e.W * ms * (period * scan) / (count * design_s)
    ideal = design_s * new * (new - 1) / (2 * ms * e.W)
    eligible = [2**i for i in range(9) if 2**i * scan <= ideal]
    return max(eligible, default=1), new


@njit(cache=True)
def threshold(t, w, b, i, end, horizon, jump=True):
    stat = np.zeros(len(e.FIELDS), dtype=np.int64)
    stat[e.FIRST] = -1
    masks = np.zeros(e.W, dtype=np.int64)
    occupied = r = last_install = 0
    step, due = 1, e.CELL
    while r * e.L < horizon:
        start = r * e.L
        i, occupied, _ = e.hits_before(t, w, b, i, end, start, masks, occupied, -1, 0, stat)
        next_hit = t[i] if i < end else horizon
        if jump and not occupied and start + e.L <= min(horizon, next_hit):
            count = 1 + (min(horizon, next_hit) - start - e.L) // (step * e.L)
            if step == 1:
                count = min(count, max(0, due - r))
            if count:
                stat[e.PASSES] += count
                stat[e.READ_NS] += count * e.D * e.READ
                r += count * step
                continue
        i, occupied, repairs = e.visit_pass(t, w, b, i, end, start, horizon, masks, occupied, stat)
        stat[e.PASSES] += 1
        stat[e.REPAIRS] += repairs
        if repairs and start + e.CUT < horizon:
            stat[e.REPORTS] += 1
        if start + e.INSTALL < horizon:
            old = step
            if repairs:
                stat[e.RESETS] += 1
                due = ((r + e.CELL - 1) // e.CELL + 1) * e.CELL
                step = 1
            elif r >= due:
                step = e.CELL
            if step != old:
                stat[e.SWITCHES] += 1
                stat[e.DOWNS] += int(step < old)
                if old == 1:
                    stat[e.FAST_NS] += start + e.INSTALL - last_install
                last_install = start + e.INSTALL
        r += step
    e.hits_before(t, w, b, i, end, horizon, masks, occupied, -1, 0, stat)
    if step == 1:
        stat[e.FAST_NS] += horizon - last_install
    for mask in masks:
        stat[e.REMAIN] += e.pop(mask)
    return stat


@njit(cache=True)
def threshold_block(t, w, b, edges, horizon):
    out = np.empty((len(edges) - 1, len(e.FIELDS)), dtype=np.int64)
    for k in range(len(out)):
        out[k] = threshold(t, w, b, edges[k], edges[k + 1], horizon)
    return out

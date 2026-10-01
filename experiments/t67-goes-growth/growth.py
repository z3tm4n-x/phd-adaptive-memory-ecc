"""Binned descriptive metrics, never a continuous/future growth certificate."""
from __future__ import annotations
import heapq
import math
import numpy as np


def h_l(x, level):
    if not math.isfinite(level) or level <= 0:
        raise ValueError("positive finite threshold required")
    x = np.asarray(x, float)
    if np.any(x[np.isfinite(x)] < 0):
        raise ValueError("negative intensity")
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(x <= level, x / level, 1 + np.log(x / level))


def segments(time, valid, signature, cadence):
    """Every retained interval is connected, same processing and native cadence."""
    if not len(time):
        return
    connected = valid[1:] & valid[:-1] & (np.diff(time) == cadence) & (signature[1:] == signature[:-1])
    starts = np.flatnonzero(valid & ~np.r_[False, connected])
    ends = np.flatnonzero(valid & ~np.r_[connected, False]) + 1
    yield from zip(starts.tolist(), ends.tolist())


def window_extreme(time, x, valid, signature, cadence, lag, level):
    if lag % cadence or lag < cadence:
        return {"status": "unresolved_at_native_resolution", "pairs": 0}
    k = lag // cadence
    best_h, best_log, count_h, count_log = None, None, 0, 0
    hx = h_l(x, level)
    for a, b in segments(time, valid & np.isfinite(x), signature, cadence):
        if b - a <= k:
            continue
        i = np.arange(a, b-k)
        dh = (hx[i+k] - hx[i]) / lag
        count_h += len(i)
        j = int(np.argmax(dh))
        if best_h is None or dh[j] > best_h[0]:
            best_h = (float(max(0, dh[j])), int(i[j]), int(i[j]+k))
        keep = (x[i] >= level) & (x[i+k] >= level) & (x[i] > 0)
        ii = i[keep]
        count_log += len(ii)
        if len(ii):
            dl = np.log(x[ii+k]/x[ii])/lag
            j = int(np.argmax(dl))
            if best_log is None or dl[j] > best_log[0]:
                best_log = (float(max(0, dl[j])), int(ii[j]), int(ii[j]+k))
    return {"status": "descriptive_bin_increment", "pairs": count_h, "log_pairs_above_level": count_log,
            "h": best_h, "log": best_log}


def fastest_e_fold(time, x, valid, signature, cadence, level):
    best, completed = None, 0
    for a, b in segments(time, valid & np.isfinite(x) & (x >= level) & (x > 0), signature, cadence):
        heap = []
        for j in range(a, b):
            while heap and heap[0][0] <= x[j]:
                _, i = heapq.heappop(heap)
                dt = float(time[j] - time[i])
                completed += 1
                if best is None or (dt, i, j) < best:
                    best = (dt, i, j)
            heapq.heappush(heap, (math.e * x[j], j))
    return {"completed_starts": completed, "fastest": best}


def transitions(time, x, valid, signature, cadence, low, high):
    if not (0 < low < high):
        raise ValueError("ordered positive levels required")
    out = []
    for a, b in segments(time, valid & np.isfinite(x), signature, cadence):
        start = None
        armed = x[a] < low
        for j in range(a+1, b):
            if x[j] < low:
                start = None
                armed = True
            elif armed:
                start, armed = j, False
            if start is not None and x[j] >= high:
                # The first-bin overshoot can be unresolved (< one bin), not 0s.
                dt = float(time[j] - time[start])
                out.append({"start_index": start, "end_index": j,
                            "elapsed_bin_starts_s": dt, "unresolved_same_bin": j == start,
                            "binned_expected_inversions": float(np.sum(x[start:j]) * cadence) if j > start else None,
                            "start_bracket": [float(time[start-1]), float(time[start])],
                            "end_bracket": [float(time[j-1]), float(time[j])]})
                start = None
    return out

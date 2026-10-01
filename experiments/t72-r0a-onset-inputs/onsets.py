"""Predeclared native-bin onset segmentation; no interpolation or peak lookahead."""
from __future__ import annotations
import numpy as np


def inspect(t, x, valid, signature, cadence, quiet, history, levels, start, end, peak):
    """Return target upcrossings and statuses; indices refer to the input arrays."""
    rows = []
    quiet_bins = 0
    root = None
    episode = 0
    seen = set()
    below_start = {level: None for level in levels}
    prev = None
    roots = 0
    for i in range(len(t)):
        if t[i] >= end:
            break
        ok = bool(valid[i] and np.isfinite(x[i]) and x[i] >= 0)
        adjacent = (prev is not None and i == prev+1 and
                    t[i]-t[prev] == cadence and signature[i] == signature[prev])
        if not ok:
            quiet_bins, root, prev = 0, None, None
            seen.clear()
            below_start = {level: None for level in levels}
            continue
        if not adjacent:
            quiet_bins, root = 0, None
            seen.clear()
            below_start = {level: None for level in levels}
        if adjacent and x[prev] <= quiet < x[i] and quiet_bins*cadence >= history:
            root = i
            roots += 1
            episode += 1
            seen.clear()
        if x[i] <= quiet:
            quiet_bins += 1
        else:
            quiet_bins = 0
        for level in levels:
            if x[i] < level:
                if below_start[level] is None:
                    below_start[level] = i
                continue
            crossing = adjacent and x[prev] < level <= x[i]
            left_censored = not adjacent
            if (crossing or left_censored) and start <= t[i] < end:
                target_first = level not in seen
                label = ("unassigned_peak" if peak is None else
                         "post_peak_growth" if t[i] > peak else
                         "primary_entry" if target_first and root is not None else
                         "repeat_pre_peak" if not target_first else "unconfirmed_pre_peak")
                rows.append({"target_level_s_inv": level, "target_index": i,
                             "quiet_root_index": root, "quiet_episode": episode if root is not None else None,
                             "rise_start_index": below_start[level],
                             "segment_type": label, "first_target_in_quiet_episode": target_first,
                             "status": "left_censored_target" if left_censored else
                                       "confirmed_quiet_reference" if root is not None else "no_confirmed_quiet_history"})
                seen.add(level)
            below_start[level] = None
        prev = i
    covered = (t >= start) & (t < end) & valid & np.isfinite(x)
    status = []
    for level in levels:
        level_rows = [r for r in rows if r["target_level_s_inv"] == level]
        status.append({"target_level_s_inv": level, "retained_bins": int(np.sum(covered)),
                       "crossing_rows": len(level_rows),
                       "confirmed_quiet_crossings": sum(r["quiet_root_index"] is not None for r in level_rows),
                       "status": "no_retained_bins" if not np.any(covered) else
                                 "not_reached" if not np.any(x[covered] >= level) else
                                 "crossings_reported" if level_rows else "already_above_or_no_upcrossing"})
    return rows, status

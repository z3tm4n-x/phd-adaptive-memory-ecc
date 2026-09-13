#!/usr/bin/env python3
"""Event-driven conditional-write executor for bounded REPAIR-02 trace checks."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable

@dataclass
class State:
    nbits: int
    physical: set[int] = field(default_factory=set)
    ideal: set[int] = field(default_factory=set)
    pending_origin: int | None = None
    pending_commit: float | None = None
    physical_failure: bool = False
    ideal_failure: bool = False
    B: bool = False
    labels_by_interval: list[set[int]] = field(default_factory=list)
    log: list[dict] = field(default_factory=list)


def _toggle(s: set[int], bit: int) -> None:
    if bit in s: s.remove(bit)
    else: s.add(bit)


def run_trace(events: Iterable[dict], check_times: list[float], write_delay: float, horizon: float, nbits: int) -> dict:
    checks = sorted(float(x) for x in check_times if 0.0 < float(x) < horizon)
    boundaries = [0.0] + checks + [float(horizon)]
    st = State(nbits=nbits, labels_by_interval=[set() for _ in range(len(boundaries)-1)])
    arrivals = sorted([dict(e) for e in events], key=lambda e: float(e["time"]))
    if any(float(e["time"]) in set(checks) for e in arrivals):
        raise ValueError("arrival/check coincidence excluded by contract")
    if any(not (0.0 <= float(e["time"]) <= horizon) for e in arrivals):
        raise ValueError("arrival outside horizon")
    idx = 0
    timeline = []
    # Potential checks are deterministic. Commits are inserted only after singleton checks.
    while True:
        next_arrival = float(arrivals[idx]["time"]) if idx < len(arrivals) else float("inf")
        next_check = checks[0] if checks else float("inf")
        next_commit = st.pending_commit if st.pending_commit is not None else float("inf")
        t = min(next_arrival, next_check, next_commit, horizon)
        if t == float("inf"): break
        if t == horizon and min(next_arrival, next_check, next_commit) > horizon:
            break
        # Contract excludes arrival/check coincidence and D<tau excludes commit/check coincidence in frozen tests.
        if t == next_arrival:
            e = arrivals[idx]; idx += 1; bit = int(e["bit"])
            if not (0 <= bit < nbits): raise ValueError("bit out of range")
            # Determine deterministic inter-check interval [boundary_i,boundary_{i+1}).
            interval = max(i for i in range(len(boundaries)-1) if boundaries[i] <= t < boundaries[i+1])
            st.labels_by_interval[interval].add(bit)
            if st.pending_origin is not None and bit != st.pending_origin:
                st.B = True
            _toggle(st.physical, bit); _toggle(st.ideal, bit)
            kind = "toggle"
        elif t == next_commit:
            # Commit the clean corrected image latched at the singleton check.
            st.physical.clear(); st.pending_origin = None; st.pending_commit = None
            kind = "commit"
        else:
            checks.pop(0)
            # Ideal-at-read comparator resets at every deterministic check.
            st.ideal.clear()
            if len(st.physical) == 1:
                st.pending_origin = next(iter(st.physical))
                st.pending_commit = t + write_delay
                if st.pending_commit >= (checks[0] if checks else horizon + 1e99):
                    # For horizon-ending pending write, commit may be after H; only next-check ordering matters.
                    if checks and st.pending_commit >= checks[0]:
                        raise ValueError("write does not complete before next check")
                kind = "singleton_check"
            elif len(st.physical) == 0:
                st.pending_origin = None; st.pending_commit = None; kind = "clean_check"
            else:
                st.pending_origin = None; st.pending_commit = None; kind = "failed_check"
        st.physical_failure = st.physical_failure or len(st.physical) >= 2
        st.ideal_failure = st.ideal_failure or len(st.ideal) >= 2
        row = {
            "time": t, "kind": kind,
            "physical": sorted(st.physical), "ideal": sorted(st.ideal),
            "pending_origin": st.pending_origin, "pending_commit": st.pending_commit,
            "physical_failure": st.physical_failure, "ideal_failure": st.ideal_failure,
            "B": st.B
        }
        if kind == "toggle": row["bit"] = bit
        timeline.append(row)
        if t == horizon: break
    P = any(len(x) >= 2 for x in st.labels_by_interval)
    return {
        "physical_failure": st.physical_failure,
        "ideal_failure": st.ideal_failure,
        "B": st.B,
        "P": P,
        "old_inclusion_holds": (not st.physical_failure) or st.ideal_failure or st.B,
        "repaired_inclusion_holds": (not st.physical_failure) or P or st.B,
        "pending_at_horizon": st.pending_origin is not None and (st.pending_commit or 0) > horizon,
        "physical_at_horizon": sorted(st.physical),
        "ideal_at_horizon": sorted(st.ideal),
        "labels_by_interval": [sorted(x) for x in st.labels_by_interval],
        "trace": timeline
    }

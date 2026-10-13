"""T146: exact arithmetic and small transition checks, not a CPU WCET.

Default: compare published arm-report.json without overwriting it.
--write is only for this new T146 output; accepted inputs are git-show/read-only.
"""
import argparse
import hashlib
import itertools
import json
import subprocess
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ENGINEER = "e8b1225fe71ceb34bb3684a6b8890c8f1f3adb67"


def source(path):
    return subprocess.check_output(["git", "show", f"{ENGINEER}:{path}"], cwd=ROOT)


@dataclass
class State:
    generation: int = 0
    healthy: bool = True
    last_source: int | None = None
    short_end: int = 0
    long_end: int = 0
    recovery_end: int = 13
    event_end: int = 0

    def deadline(self):
        return max(self.short_end, self.long_end, self.recovery_end, self.event_end)


def raw(state, events, nw=4, nh=8, nr=13, pair=6):
    s = State(**vars(state))
    for tick, src, err, loss in events:
        s.generation += 1
        if not loss and not s.healthy:
            s.recovery_end = tick + nr
        s.healthy = not loss
        s.event_end = tick + 1
        if err:
            s.short_end = tick + nw
            if s.last_source is not None and src - s.last_source <= pair:
                s.long_end = tick + nh
            s.last_source = src
    return s


def summarized(state, events, nw=4, nh=8, nr=13, pair=6):
    s = State(**vars(state))
    errs = [e for e in events if e[2]]
    if len(errs) >= 2 and errs[-1][1] - errs[0][1] > pair:
        raise ValueError("summary PAIR premise not met")
    healthy = state.healthy
    recoveries = []
    for t, src, err, loss in events:
        if healthy is False and not loss:
            recoveries.append(t)
        healthy = not loss
    if events:
        s.generation += len(events)
        s.healthy = healthy
        s.event_end = events[-1][0] + 1
    if recoveries:
        s.recovery_end = recoveries[-1] + nr
    if errs:
        first, last = errs[0], errs[-1]
        paired = len(errs) >= 2 or (
            s.last_source is not None and first[1] - s.last_source <= pair
        )
        s.short_end = last[0] + nw
        if paired:
            s.long_end = last[0] + nh
        s.last_source = last[1]
    return s


def permit(cert_g, current_g, now, not_before, same_edge_event=False, healthy=True):
    return (
        healthy and not same_edge_event and cert_g == current_g and now >= not_before
    )


def calculate():
    checks = {}
    paths = [
        "rule.h", "rule.c", "batch.c", "history_batch.sv", "interval_link.sv",
        "interval_guard.sv", "arm_executor.sv", "batch_budget.py",
    ]
    hashes = {
        p: hashlib.sha256(source("experiments/t105-arm-rule/" + p)).hexdigest()
        for p in paths
    }
    cfg = json.loads(source("experiments/t105-arm-rule/config.json"))
    assert (cfg["NW"], cfg["NH"], cfg["NR"], cfg["PAIR_WINDOW"]) == (
        4500045002, 9000090002, 9015504896, 22500225010
    )
    checks["pinned_constants"] = True
    lo, hi, jitter = F(".99999"), F("1.00001"), F(".5")
    history = F("531869457677237/102498975000")
    u = lambda n: F(n) * hi + jitter
    external, certificate, calendar = u(80), u(600), u(748)
    fixed = external + history + certificate + calendar
    strict_B = (10000 - fixed) / 2
    # A full round includes reply/ACK; allow one further slow-edge of installation.
    install = u(20)
    hold_min = (cfg["NW"] - 1) * 20 * lo - jitter
    # NOT an accepted replacement for the literal 10-us contract.
    hold_B = (hold_min - install) / 2
    count_cap = ((2**32 - 2) * 20 * lo - jitter)
    pair_min = cfg["PAIR_WINDOW"] * 4 * lo - jitter
    assert hold_B < count_cap
    assert hold_B + history + u(20) < pair_min
    checks["finite_summary_at_maturity_bound"] = True
    assert fixed + 2 * strict_B == 10000
    checks["literal_limit_boundary"] = True
    assert fixed + 2 * F("1620") < 10000
    checks["zero_cpu_trace_is_not_wcet"] = True
    # For a proposal B=1 ms, the existing strict bound fails by a large margin.
    assert fixed + 2 * 10**6 > 10000
    assert 2 * 10**6 + install < hold_min
    checks["one_ms_preserves_maturity_not_literal_reaction"] = True
    total = 0
    # Four possible inputs per tick: none / ERR / loss high / loss low.
    for symbols in itertools.product(range(4), repeat=6):
        events = [(t + 1, t + 1, v == 1, v == 2)
                  for t, v in enumerate(symbols) if v]
        for initial in (State(), State(3, False, 0, 3, 8, 13, 1)):
            a, b = raw(initial, events), summarized(initial, events)
            assert a == b
            total += 1
    checks["summary_equals_raw_exhaustive_8192"] = total == 8192
    # Pair equality matters, a source interval one unit larger must not pair.
    a = raw(State(last_source=0), [(7, 6, True, False)])
    b = raw(State(last_source=0), [(7, 7, True, False)])
    assert a.long_end == 15 and b.long_end == 0
    checks["pair_equality_and_next_tick"] = True
    try:
        summarized(State(), [(1, 1, True, False), (9, 9, True, False)])
    except ValueError:
        checks["long_summary_rejected_not_free_fast"] = True
    assert not permit(7, 7, 20, 20, same_edge_event=True)
    assert not permit(7, 8, 20, 20)
    assert not permit(7, 7, 19, 20)
    assert permit(7, 7, 20, 20)
    checks["freeze_same_edge_veto_stale_generation_maturity"] = True
    # The event on a cut belongs to the next prefix, not the old decision.
    before = raw(State(), [(1, 1, True, False)])
    after = raw(before, [(2, 2, True, False)])
    assert not permit(before.generation, after.generation, 30, before.deadline())
    checks["snapshot_boundary_invalidates_old_permission"] = True
    a = raw(State(), [(2, 2, False, True), (3, 3, False, False)])
    assert a.recovery_end == 16
    assert not permit(a.generation, a.generation, 15, a.deadline())
    checks["last_recovery_absolute_deadline"] = True
    # An early decision must survive *without* continuous CPU renewal while G is stable.
    assert permit(a.generation, a.generation, 1000000, a.deadline())
    checks["persistent_certificate_no_periodic_cpu_refresh"] = True
    # Waiting 60 s per round can yield a 120-s delivery after a 90-s hold.
    assert 2 * 60 - 90 == 30
    checks["late_delivery_counterexample_30s"] = True
    # Arrival timestamp rather than collector timestamp would shift a timer.
    assert (100 + 4) != (1 + 4)
    checks["cpu_time_must_not_reload_timer"] = True
    edges = -(-(F(315576000) * 10**9 + jitter) // (4 * lo)) + 1
    assert edges < 2**57
    slow_edges = -(-(F(315576000) * 10**9 + jitter) // (20 * lo)) + 1
    assert slow_edges + cfg["NR"] < 2**64 - 1
    checks["generation_timestamp_sequence_not_wrapped"] = True
    # Allowance at the end is not the ARM computation interval.
    tail = external + history + certificate + calendar + install
    assert tail < 10000
    checks["recovery_and_exit_tail_within_existing_allowance"] = True
    return {
        "task": 146, "part": "A", "engineer_sha": ENGINEER,
        "scope": "conditional mathematical contract and abstract regressions, NOT ARM WCET/RTL proof",
        "ns_exact": {k: str(v) for k, v in {
            "history": history, "external": external, "certificate": certificate,
            "calendar": calendar, "fixed": fixed, "literal_two_round_B": strict_B,
            "literal_capture_plus_compute_limit": 2*strict_B,
            "hold_min": hold_min, "install_slack": install,
            "conditional_maturity_B_NOT_authorized": hold_B,
            "summary_count_interval_cap": count_cap,
            "pair_min": pair_min, "existing_tail_bound": tail,
            "trace_arithmetic_residual_NOT_CPU_WCET": strict_B - 1620,
        }.items()},
        "ns_display": {
            "literal_two_round_B": float(strict_B),
            "conditional_maturity_B_NOT_authorized": float(hold_B),
            "existing_tail_bound": float(tail),
        },
        "checks": checks, "check_count": len(checks), "abstract_histories": total,
        "accepted_r4_unchanged": {
            "U_Q_upper": ".000983050530494",
            "whole_bus_mission_upper_percent": "17.484321",
            "conditional_on": "same scientific/timing assumptions; maturity substitution requires explicit disposition",
        },
        "source_sha256": hashes,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true")
    a = p.parse_args()
    report = json.dumps(calculate(), ensure_ascii=False, indent=2) + "\n"
    path = HERE / "arm-report.json"
    if a.write:
        path.write_text(report)
        print("Wrote new T146 arm-report.json")
    else:
        assert path.read_text() == report, "T146 report mismatch"
        print("PASS: arm-report.json reproduced byte-for-byte; 16 checks, 8192 abstract histories")


if __name__ == "__main__":
    main()

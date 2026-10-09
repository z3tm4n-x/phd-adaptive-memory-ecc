"""Exact conditional timing arithmetic for #135; not WCET or new Q(T).

No imports of old timing calculators. ns, xi in [0.99999,1.00001],
per-endpoint edge error +/-0.25 ns. Atomic SRAM times are NOT CDC times.
"""
import json
from fractions import Fraction as F
from pathlib import Path


def interval(ticks, apertures=1):
    return {"min_ns": str(ticks*F("0.99999")-F(apertures, 2)),
            "max_ns": str(ticks*F("1.00001")+F(apertures, 2))}


def calculate():
    proposed = {"source_sampling": 20, "request_preparation_budget": 80,
                "request_slow_queue_and_handshake_to_fast_consumer": 144,
                "fast_prefetch_dispatch": 8, "wait_one_calendar_frame": 1568,
                "reply_outbox": 4, "response_handshake_and_slow_queue_to_consumer": 208}
    # These are upper budgets, not fixed-duration operations. An empty FIFO
    # can respond much sooner than its documented worst case.
    components = {k: {"min_ns": "0", "max_ns": interval(v)["max_ns"]}
                  for k, v in proposed.items()}
    components["observed_write32"] = interval(216, 2)
    total = sum(F(v["max_ns"]) for v in components.values()) + 100
    upper = total*F(11, 10)
    assert upper < 3000
    operations_250 = {k: interval(v, a) for k, v, a in
                      [("R", 92, 1), ("E", 148, 1), ("write16", 68, 1),
                       ("read32", 184, 2), ("observed_write32", 216, 2)]}
    # Feasible integer-edge candidate, not merely ceil(old_age / 10).
    # R: CE10, sample70, OEoff80, release110.
    # E: same prefix, WE/drive110, WEoff150, driveoff160, release170.
    # Second write: drive180, WE190..230, driveoff240, release250.
    candidate_100 = {k: interval(v, a) for k, v, a in
                     [("R", 110, 1), ("E", 170, 1), ("write16", 80, 1),
                      ("read32", 220, 2), ("observed_write32", 250, 2)]}
    def slack(start, end, required):
        return end*F("0.99999")-start*F("1.00001")-F(1, 2)-required
    checks_100 = {"read_capture": slack(10, 70, 4+45+2+1),
                  "turnaround": slack(80, 110, 4+18),
                  "write_pulse": slack(110, 150, 4+35),
                  "write_data_setup": slack(110, 150, 4+25),
                  "write_data_hold": slack(150, 160, 4),
                  "second_write_pulse": slack(190, 230, 4+35),
                  "second_write_setup": slack(180, 230, 4+25),
                  "second_write_hold": slack(230, 240, 4)}
    assert min(checks_100.values()) > 0
    # Separate exact old schedule argument, including the longest all-ERR E.
    min_frame = 1568*F("0.99999")
    extended = F(10**6)+F(operations_250["E"]["max_ns"])+F(1, 2)
    frames, rem = divmod(extended, min_frame)
    def start(j):
        return (1568*(j//8)+164*(j%8))*F("0.99999")
    additional = max(sum(start(j+k)-start(j)<=rem for k in range(8)) for j in range(8))
    owners = 8*int(frames)+additional
    x_work = F(209)+F("0.0001")*10**6
    count_app = 1+180000*F("0.001003")
    load = (owners*F(operations_250["E"]["max_ns"])+x_work
            +count_app*F(operations_250["observed_write32"]["max_ns"]))/10**6
    assert load < F(4, 5)
    return {"type": "conditional calculated bounds; no physical measurement or new certificate",
            "xi_ns": ["0.99999", "1.00001"], "endpoint_jitter_ns": "0.25",
            "operations_250": operations_250,
            "ERR_250_snapshot_from_grant": interval(60),
            "ERR_250_publication_from_grant": interval(64),
            "components_250_50": components,
            "runtime_loss_to_fast_veto": {"min_ns": "0", "max_ns": interval(36)["max_ns"]},
            "request_preparation_status": "80xi is a proposed allocation, not implemented/measured",
            "transport_basis": "empty, reset-released slow FWFT queue <=4Ts; idle XPM handshake <=2Tsrc+6Tdst; destination ready; conditional digital IP bound, not analog metastability guarantee",
            "end_to_end_upper_with_10pct_ns": str(upper),
            "end_to_end_upper_float_ns": float(upper),
            "end_to_end_headroom_ns": str(3000-upper),
            "reply_backpressure_ns": 100,
            "queue_assumption": "joint burst1/rate<=180000 per s; no earlier pending application at arrival; reserved service each1568xi; empty queues and idle handshakes; not yet integrated",
            "scrub_transport_constraint": "control slots every164xi MUST be generated locally from a preloaded frame, NOT sent one-by-one over this handshake; full frame protocol not implemented",
            "worst_case_all_ERR_bus_upper": str(load),
            "worst_case_all_ERR_bus_upper_float": float(load),
            "bus_bound_condition": "same slot schedule and unchanged X_work209ns+0.0001*t; preparatory compute/CDC not SRAM traffic",
            "freeze_lead_xi": 320, "freeze_policy": "local ERR veto at freeze, no retroactive cancellation of committed skips",
            "rounding": "fast4xi exact; slow20xi; lower release not_before rounded up, upper expiry rounded down; latency paid before freeze",
            "actual_command_preparation_to_freeze_upper": None,
            "actual_ERR_to_slow_rule_upper": None,
            "exact_board_pad_timing": None,
            "candidate_100_status": "arithmetic fallback only, not RTL/STA and not approved calendar",
            "candidate_100_operations": candidate_100,
            "candidate_100_ERR_snapshot": interval(70),
            "candidate_100_ERR_publication": interval(80),
            "candidate_100_pin_slacks_ns": {k: str(v) for k, v in checks_100.items()},
            "candidate_100_queue_CDC_and_Q": None}


if __name__ == "__main__":
    result = calculate()
    path = Path(__file__).with_name("timing_balance.json")
    path.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))

"""Exact full-horizon work and affine price, with explicit unknown coefficients.

All counts include work after first exceedance. Charging full started work
includes the unfinished tail conservatively; it is an upper, not exact bus
occupancy truncated at T. No value of an unknown unit cost is supplied here.
"""
from dataclasses import dataclass
from fractions import Fraction as F


def exact(x):
    if isinstance(x, (bool, float)) or x is None:
        raise ValueError("an exact rational, not an unknown/float, is required")
    return F(x)


def packing(W, n, k=32, bus_bits=16):
    if any(type(x) is not int or x <= 0 for x in (W, n, k, bus_bits)) or n < k:
        raise ValueError("integer memory geometry required")
    beats = (n + bus_bits - 1) // bus_bits
    return dict(words=W, n=n, k=k, useful_bits=W*k, code_bits=W*n,
                parity_bits_per_word=n-k, unused_bits_per_word=beats*bus_bits-n,
                allocated_bits=W*beats*bus_bits, word_read_beats=beats,
                word_write_beats=beats, observed_RMW_beats=2*beats,
                address_rule=f"{beats}*word + beat")


@dataclass(frozen=True)
class Work:
    scrub_reads: F
    application_reads: F
    application_writes: F
    scrub_repairs: F
    application_read_repairs: F
    bus_turnarounds: F
    source_records: F
    cuts: F
    processed_records: F
    decisions: F
    timer_updates: F
    extra_source_veto: F
    scope: str = "whole_horizon_full_started_work"

    def validate(self):
        if self.scope != "whole_horizon_full_started_work":
            raise ValueError("counts stopped at first exceedance are not a full cost")
        for name, value in self.__dict__.items():
            if name != "scope" and exact(value) < 0:
                raise ValueError("negative work count")
        if self.scrub_repairs > self.scrub_reads or self.application_read_repairs > self.application_reads:
            raise ValueError("a repair requires a corresponding coherent read")
        if self.processed_records > self.source_records:
            raise ValueError("processed records exceed all captured source records")
        if self.extra_source_veto > self.source_records:
            raise ValueError("additional source veto exceeds all source records")


def work_vector(work, n, resources):
    work.validate()
    if resources["n"] != n:
        raise ValueError("codec and memory disagree")
    beats = (n + 15) // 16
    decodes = work.scrub_reads + work.application_reads + work.application_writes
    encodes = work.application_writes
    writes = work.scrub_repairs + work.application_read_repairs + work.application_writes
    requests = work.application_reads + work.application_writes
    return dict(sram_read_beats=beats*decodes, sram_write_beats=beats*writes,
                decodes=decodes, encodes=encodes, lookup_operations=decodes,
                syndrome_xors=resources["syndrome_two_input_xors"]*decodes,
                correction_xors=n*decodes, encoder_xors=resources["encoder_two_input_xors"]*encodes,
                # Application read payload is in the reply, write payload in the request.
                payload_data_bytes=4*requests,
                requests=requests, replies_upper=requests,
                source_record_bytes=32*work.source_records,
                processed_record_bytes=32*work.processed_records,
                bus_turnarounds=work.bus_turnarounds, cuts=work.cuts,
                source_records=work.source_records, processed_records=work.processed_records,
                decisions=work.decisions, timer_updates=work.timer_updates,
                extra_source_veto=work.extra_source_veto,
                codec_ROM_bits=resources["lookup_bits"],
                transport_plus_loss_state_bytes=131072+64,
                charge_kind="upper: full started work, including pending and post-A")


def affine_prices(vector, horizon_ns):
    """Each coordinate has a declared unit. CPU/energy/bytes are not summed."""
    H = exact(horizon_ns)
    if H <= 0:
        raise ValueError("positive horizon required")
    v = vector
    return dict(
        SRAM_fraction={"read_beat_ns": v["sram_read_beats"]/H,
                       "write_beat_ns": v["sram_write_beats"]/H,
                       "turnaround_ns": v["bus_turnarounds"]/H,
                       "decode_bus_block_ns": v["decodes"]/H,
                       "encode_bus_block_ns": v["encodes"]/H,
                       "control_bus_ns_per_decision": v["decisions"]/H},
        CPU_fraction={"CPU_ns_per_cut": v["cuts"]/H,
                      "CPU_ns_per_capture": v["source_records"]/H,
                      "CPU_ns_per_record": v["processed_records"]/H,
                      "CPU_ns_per_decision": v["decisions"]/H,
                      "CPU_ns_per_timer": v["timer_updates"]/H,
                      "CPU_ns_per_extra_veto": v["extra_source_veto"]/H,
                      "CPU_ns_per_app_dispatch": v["requests"]/H},
        # Decoding/encoding here is hardware. A software implementation instead
        # moves its work into CPU, and removes the separate hardware charge.
        codec_busy_fraction={"decode_ns": v["decodes"]/H, "encode_ns": v["encodes"]/H},
        transport_bytes={"request_header_bytes": v["requests"],
                         "reply_header_bytes": v["replies_upper"],
                         "cut_header_bytes": v["cuts"],
                         "constant_one": v["payload_data_bytes"]+v["source_record_bytes"]},
        dynamic_energy_J={"read_beat_J": v["sram_read_beats"], "write_beat_J": v["sram_write_beats"],
                          "decode_J": v["decodes"], "encode_J": v["encodes"],
                          "control_J_per_cut": v["cuts"], "control_J_per_capture": v["source_records"],
                          "control_J_per_record": v["processed_records"], "control_J_per_decision": v["decisions"],
                          "control_J_per_timer": v["timer_updates"], "control_J_per_app": v["requests"],
                          "control_J_per_extra_veto": v["extra_source_veto"],
                          "transport_J_per_request": v["requests"], "transport_J_per_reply": v["replies_upper"],
                          "transport_J_per_record": v["source_records"], "transport_J_per_cut": v["cuts"],
                          "idle_W": H/F(10**9)},
        controller_memory_bytes={"constant_one": F(v["transport_plus_loss_state_bytes"]),
                                 "policy_state_bytes": F(1), "payload_buffer_bytes": F(1)},
        codec_storage_bytes={"constant_one": F(v["codec_ROM_bits"], 8), "codec_register_bytes": F(1)})


def evaluate(coefficients, parameters):
    missing = [name for name, coefficient in coefficients.items() if coefficient and parameters.get(name) is None]
    if missing:
        raise ValueError("unknown costs must remain parameters: " + ", ".join(missing))
    out = F(0)
    for name, coefficient in coefficients.items():
        if not coefficient:
            continue
        p = exact(parameters[name])
        if p < 0 or (name == "constant_one" and p != 1):
            raise ValueError("unit costs nonnegative; constant_one must equal one")
        out += exact(coefficient)*p
    return out


def threshold(a0, a1, b0, b1):
    """Region a0+a1*x < b0+b1*x for x>=0, same units and bound types.

    This algebra does not turn two sufficient uppers into a proven ordering
    of true costs. The caller must state candidate equality or upper/lower.
    """
    a0, a1, b0, b1 = map(exact, (a0, a1, b0, b1))
    if min(a0, a1, b0, b1) < 0:
        raise ValueError("nonnegative prices required")
    delta, slope = a0-b0, a1-b1
    if slope == 0:
        return dict(region="all x>=0" if delta < 0 else "none", equality=None)
    point = -delta/slope
    if slope > 0:
        return dict(region="0<=x<point" if point > 0 else "none", equality=point)
    return dict(region="x>point and x>=0", equality=point)


def allowable_delay(used_ns, operations, limit_ns):
    """Remaining one-coefficient budget, not a WCET estimate."""
    used_ns, operations, limit_ns = map(exact, (used_ns, operations, limit_ns))
    if min(used_ns, operations, limit_ns) < 0:
        raise ValueError("negative resource")
    if used_ns > limit_ns:
        return dict(feasible=False, maximum=None)
    return dict(feasible=True, maximum=(limit_ns-used_ns)/operations if operations else None)


def fast_fraction_cap(ordinary, extra_veto):
    """Union upper for expected FAST time; does not estimate either input."""
    ordinary,extra_veto=map(exact,(ordinary,extra_veto))
    if not 0 <= ordinary <= 1 or not 0 <= extra_veto <= 1:
        raise ValueError("fractions must be in [0,1]")
    return min(F(1),ordinary+extra_veto)


def periodic_starts(first_ns, step_ns, horizon_ns):
    first, step, H = map(exact, (first_ns, step_ns, horizon_ns))
    if first < 0 or step <= 0 or H < 0:
        raise ValueError("invalid time")
    length = H-first
    return max(0, -(-length.numerator*step.denominator // (length.denominator*step.numerator)))


def clipped_busy(intervals, horizon_ns):
    """Exact test oracle for serial non-overlapping bus reservations."""
    H = exact(horizon_ns)
    if H < 0:
        raise ValueError("negative horizon")
    result, previous = F(0), F(0)
    for start, end in sorted((exact(a),exact(b)) for a,b in intervals):
        if start < previous or end < start:
            raise ValueError("overlapping or invalid serial reservations")
        result += max(F(0), min(H,end)-min(H,start))
        previous = end
    return result


def per_bit_moment_caps(config):
    """T187 (6) / rare-rate envelope, only for the proposed singleton class.

    Supplies exact algebra for later agreed calculations. No n or W is
    hidden in r(t); array-rate cannot be held constant across the codes.
    """
    env = config["environment"]
    if env["kind"] not in ("conditional_independent_singleton_per_code_bit", "conditional_word_parent_48_positions"):
        raise ValueError("a compound parent law needs separate moments")
    den = env["reference_words"]*env["reference_bits"]
    T = exact(config["mission_s"])
    b, B, FS = (exact(env[name])/den for name in
                ("reference_background_per_s", "reference_peak_per_s", "reference_solar_mass"))
    if not 0 <= b <= B or FS < 0 or T <= 0:
        raise ValueError("invalid rate envelope")
    M1 = min(B*T, b*T+FS)
    M2 = min(B*B*T, B*M1, b*b*T+(B+b)*FS)
    M3 = min(B**3*T, B*B*M1, b**3*T+(B*B+B*b+b*b)*FS)
    return dict(M1=M1, M2=M2, M3=M3, peak_per_bit=B)

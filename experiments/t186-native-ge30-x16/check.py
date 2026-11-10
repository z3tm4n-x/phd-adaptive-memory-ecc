"""Reproduce the native x16 calendar and bank coverage bounds (Python standard library)."""

import argparse
import hashlib
import json
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent


def decimal(value):
    return format(Decimal(value.numerator) / Decimal(value.denominator), "f")


def check_pair_examples():
    # Small logical examples only. No die mapping is inferred.
    payload = range(4)
    for mates in ([1, 0, 3, 2, 5, 4, 7, 6], [2, 3, 0, 1, 6, 7, 4, 5],
                  [4, 5, 3, 2, 0, 1, 7, 6], [4, 5, 6, 7, 0, 1, 2, 3]):
        assert all(a != b and mates[b] == a for a, b in enumerate(mates))
        words = {min(a, mates[a]) for a in payload}
        outside = sum(mates[a] not in payload for a in payload)
        assert 2 * len(words) == len(payload) + outside
        if not outside:
            representatives = [a for a in payload if a < mates[a]]
            assert set(representatives) == words
        # One isolated old hit, repaired at its first sampled ERR, including
        # a hit initially in the mate of the very first address.
        dirty_word = min(payload[0], mates[payload[0]])
        reports = []
        for a in payload:
            if min(a, mates[a]) == dirty_word:
                reports.append(a)
                dirty_word = None
        assert reports == [payload[0]]
    # In (0,2),(1,3) scanning the even addresses misses the second pair.
    assert {min(a, a ^ 2) for a in (0, 2)} < {min(a, a ^ 2) for a in payload}


def calculate(cal):
    prior = json.loads((HERE / cal["sources"]["previous_port"]).read_text(encoding="utf-8"))
    tick, frame = cal["tick_ns"], cal["frame_ns"]
    slots = cal["visit_offsets_ns"]
    app, management = cal["application_ns"], cal["management_ns"]
    assert (tick, frame, app, management) == (
        prior["tick_ns"], prior["frame_ns"], prior["app_grant_ns"], prior["management_ns"]
    )
    xm, xp = F(cal["xi_min"]), F(cal["xi_max"])
    jitter = F(cal["edge_jitter_ns"])
    edge = 2 * jitter
    times = cal["operation_ns"]
    start = times["address_select_oe_low"]
    sample, oe_high = times["sample_dq_and_err"], times["oe_high"]
    drive, we_low = times["read_release_or_drive_write"], times["we_low"]
    we_high, dq_off, release = times["we_high"], times["fpga_dq_off"], times["write_release"]
    assert start == 0 and all(t % tick == 0 for t in [*times.values(), *slots])
    assert start < sample < oe_high < drive < we_low < we_high < dq_off < release
    read, extra = drive - start, release - drive

    # Available slack for board and FPGA paths, relative to the chip AC limits.
    def slack(duration, chip_limit):
        return duration * xm - edge - chip_limit

    margins = {
        "read_address_ce_dq_capture_or_address_ce_err_capture": slack(sample, 45),
        "read_oe_capture": slack(sample, 22),
        "sample_to_control_change": slack(oe_high - sample, 0),
        "oe_high_to_fpga_drive": slack(drive - oe_high, 18),
        "read_cycle": slack(oe_high - start, 45),
        "write_cycle": slack(dq_off - drive, 45),
        "address_setup_to_write_start": slack(we_low - drive, 0),
        "write_enable_low": slack(we_high - we_low, 35),
        "address_select_byte_setup_to_write_end": slack(we_high - drive, 35),
        "write_data_setup": slack(we_high - drive, 25),
        "data_address_hold": slack(dq_off - we_high, 0),
        "fpga_drive_off_to_release": slack(release - dq_off, 0),
    }
    assert min(margins.values()) > 0
    aperture = release * xp + 3 * jitter
    assert all(start1 < start2 and (start2 - start1) * xm - edge > aperture
               for start1, start2 in zip(slots, slots[1:] + [app[0]]))
    assert app[1] <= management[0] < management[1] <= frame
    result = {
        "read_port_ns": read, "repair_additional_port_ns": extra,
        "repaired_visit_port_ns": read + extra,
        "read_or_additional_write_lower_upper_ns": [decimal(read * xm - edge), decimal(read * xp + edge)],
        "maximum_physical_aperture_ns": decimal(aperture),
        "timing_margins_ns": {name: decimal(val) for name, val in margins.items()},
        "banks": [],
    }
    assert read == extra  # Both have the same tariff on this calendar.
    for size in cal["protected_payload_bytes"]:
        addresses = size // 2
        assert size % 4 == 0 and cal["first_x16_address"] + addresses <= cal["die_x16_addresses"]
        for scheme, count in (("all_half_addresses", addresses), ("verified_representatives", addresses // 2)):
            assert count % len(slots) == 0
            period = count // len(slots) * frame
            last = (count - 1) // len(slots) * frame + slots[(count - 1) % len(slots)]
            cut = period - cal["report_cut_ns_before_next_pass"]
            assert (cut - last) * xm - edge > aperture
            assert (period - cut - cal["command_install_ns"]) * xm - edge > 0
            result["banks"].append({
                "payload_bytes": size, "scan": scheme, "read_count": count,
                "internal_words_lower_upper": [addresses // 2, min(addresses, cal["die_x16_addresses"] // 2)]
                    if scheme == "all_half_addresses" else [count, count],
                "period_ns": period, "last_start_ns": last, "report_cut_ns": cut,
                "period_physical_lower_upper_ns": [decimal(period * xm - edge), decimal(period * xp + edge)],
                "port_clean_ns": count * read, "port_one_isolated_repair_ns": count * read + extra,
                "port_all_writes_ns": count * (read + extra),
            })
    check_pair_examples()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--source-pdfs", type=Path, nargs=2, metavar=("DATASHEET", "AN88889"))
    args = parser.parse_args()
    cal = json.loads((HERE / "calendar.json").read_text(encoding="utf-8"))
    for name, path in zip(("datasheet", "application_note"), args.source_pdfs or []):
        if hashlib.sha256(path.read_bytes()).hexdigest() != cal["sources"][name]["sha256"]:
            parser.error(f"PDF hash mismatch: {name}")
    contents = json.dumps(calculate(cal), indent=2) + "\n"
    out = HERE / "service.json"
    if args.check:
        if out.read_text(encoding="utf-8") != contents:
            parser.exit(1, "Published service values differ from recalculation\n")
        print("OK: four bank rows, phase and AC margins, coverage examples, price of one repair")
    else:
        out.write_text(contents, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

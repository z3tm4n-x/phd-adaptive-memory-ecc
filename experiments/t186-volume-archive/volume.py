"""Test the same four physical SRAM pin constraints in both registered byte projections."""
import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXP = HERE.parent
MAP = EXP / "RE-CY62167-ADDRESS-MAPPING-01/address_mapping_coefficients.json"
PINS = EXP / "RE-CY62167-EXECUTOR-TIMING-GATE-01/reference-continuation-01/pinmap.json"


def raw_address(x, y, masks):
    features = 1 | (x << 1) | (y << 13)
    return sum(((features & m).bit_count() % 2) << i for i, m in enumerate(masks))


def project(raw, shift):
    return (raw >> shift) & ((1 << 20) - 1)


def nibble(address, pins):
    return sum(((address >> p) & 1) << j for j, p in enumerate(pins))


def assess(masks, shift):
    # At any Y the image of the complete X row is its Y offset XOR the X image.
    base = project(raw_address(0, 0, masks), shift)
    x_changes = [base ^ project(raw_address(1 << i, 0, masks), shift) for i in range(12)]
    x_axis = [base ^ project(raw_address(x, 0, masks), shift) for x in range(4096)]
    y_axis = [project(raw_address(0, y, masks), shift) for y in range(4096)]
    pure = [p for p in range(10) if all(not (v >> p & 1) for v in x_changes)]
    winners = []
    for fixed in combinations(range(10), 4):
        xs = {nibble(v, fixed) for v in x_axis}
        assert (len(xs) == 1) == set(fixed).issubset(pure)
        # Verify all 16 fixed levels without enumerating the 2^24 coordinates.
        counts = [0] * 16
        for v in y_axis:
            counts[nibble(v, fixed)] += 1
        selected_rows = [sum(counts[c ^ dx] for dx in xs) for c in range(16)]
        per_row = 4096 // len(xs)
        assert all(rows * per_row == 1 << 20 for rows in selected_rows)
        if per_row == 4096:
            winners.append(list(fixed))
    # Find the translation between the two raw byte lanes of a halfword.
    lane = 1 if shift else 1 << 20
    x_deltas = [x for x in range(4096) if raw_address(x, 0, masks) ^ raw_address(0, 0, masks) == lane]
    y_deltas = [y for y in range(4096) if raw_address(0, y, masks) ^ raw_address(0, 0, masks) == lane]
    assert bool(x_deltas) != bool(y_deltas)
    # A byte has eight physical data positions. Keep all feasible X deltas.
    return dict(pure_pins=pure, whole_row_choices=winners, sets_checked=210,
                rows_per_winning_block=256, information_cells_per_row=4096,
                lane_raw_xor=lane, lane_example_xy_xor=[min(x_deltas,default=0), min(y_deltas,default=0)],
                byte_kernel_x=[x for x in range(4096) if raw_address(x,0,masks)==raw_address(0,0,masks)])


def calculate():
    source = json.loads(MAP.read_bytes())
    masks = source["coefficient_masks_lsb_feature_order"]
    pins = json.loads(PINS.read_bytes())
    low, pin = assess(masks, 1), assess(masks, 0)
    common = [f for f in low["whole_row_choices"] if f in pin["whole_row_choices"]]
    # For the H_low winning block, H_pin admits a same-Y perfect matching
    # of halves by flipping x8 in every cell (commutes with its byte-lane XOR).
    selected = low["whole_row_choices"][0]
    partner_x = 1 << 8
    partner = project(raw_address(partner_x, 0, masks) ^ raw_address(0, 0, masks), 0)
    assert partner and nibble(partner, selected)
    inside = [b for b in range(1 << 20) if nibble(b, selected) == 0]
    pairs = sum(nibble(b ^ partner, selected) == 0 for b in inside) // 2
    translations = {k ^ lane ^ half for k in pin["byte_kernel_x"]
                    for lane in (0,pin["lane_example_xy_xor"][0]) for half in (0,partner_x)}
    assert len(translations) == 32
    assert min(inside) == 0 and len(inside) == 65536 and pairs == 0
    signals = {s["port"] for s in pins["signals"]}
    assert {p for p in signals if p.startswith("addr[")} == {f"addr[{i}]" for i in range(19)}
    assert pins["straps_each_sram"]["A19_pin9"] == "GND"
    return dict(v21_sha256=sha256(MAP.read_bytes()).hexdigest(), H_pin=pin, H_low=low,
                common=common, counterexample=dict(fixed_pins=selected, fixed_value=0,
                projection="H_pin", x_xor=partner_x, y_xor=0, partner_halfword_xor=partner,
                distinct_halfwords=len(inside), full_pairs=pairs, data_cells_per_word=len(translations)),
                board=dict(controlled="A0..A18", A19="GND", BYTE=pins["straps_each_sram"]["BYTE_pin47"],
                           same_block_halfwords_available=sum(b < 1 << 19 for b in inside)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    out = calculate()
    path = HERE / "volume.json"
    if args.check:
        assert json.loads(path.read_bytes()) == out
    else:
        path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, ensure_ascii=False))

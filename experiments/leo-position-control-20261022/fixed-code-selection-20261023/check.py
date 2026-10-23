"""Reproduce source identity, storage arithmetic and one beam normalization.

No radiation transport, time model, probability bound or performance simulation.
Python 3 standard library only. PDF interpretation is manual, page-addressed.
"""

import argparse
import hashlib
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact(value):
    value = Fraction(value)
    return f"{value.numerator}/{value.denominator}"


def calculate(inp):
    req, rt, ku = inp["requirements"], inp["rtg4"], inp["xqrku060"]
    w = req["useful_words_32"]
    bits = w * req["useful_bits_per_word"]
    require((w, bits // 8, req["mission_s"], req["epsilon"]) ==
            (131072, 524288, 315576000, "0.001"), "Requirement changed")
    require(bits == req["useful_bytes"] * 8, "Payload mismatch")
    require(req["physical_Q"] is None, "This selection does not compute Q")
    require((rt["native_code"]["n"], rt["native_code"]["k"],
             ku["native_code"]["n"], ku["native_code"]["k"]) ==
            (24, 18, 72, 64), "Native code changed")
    rr, kr = rt["source_resources"], ku["source_resources"]
    rn, kn = rt["native_code"]["n"], ku["native_code"]["n"]
    rk = rt["native_code"]["k"]
    rdepth, kdepth = rr["lsram_codewords_per_block"], kr["codewords_per_block"]
    require(bits % rt["payload_bits_per_codeword"] == 0 and
            bits % ku["payload_bits_per_codeword"] == 0, "Packing remainder")
    rwords = bits // rt["payload_bits_per_codeword"]
    kwords = bits // ku["payload_bits_per_codeword"]
    require((rwords, kwords) == (2 * w, w // 2), "Declared packing differs")
    require(rwords % (rt["chips"] * rdepth) == 0, "RT blocks incomplete")
    require(kwords % kdepth == 0, "KU blocks incomplete")
    rblocks_each = rwords // (rt["chips"] * rdepth)
    kblocks = kwords // kdepth
    require(rblocks_each <= rr["lsram_blocks_per_chip"], "RT capacity exceeded")
    require(kblocks <= ku["chips"] * kr["bram36_blocks_per_chip"], "KU capacity exceeded")

    # Check actual address/half mappings, not just total byte counts.
    rseen, kseen = set(), set()
    for word in range(w):
        for half in (0, 1):
            slot = (half, word // rdepth, word % rdepth)
            require(slot[0] < rt["chips"] and slot[1] < rblocks_each,
                    "RT mapping outside allocated storage")
            require(slot not in rseen, "RT alias")
            rseen.add(slot)
        codeword, half = divmod(word, 2)
        slot = (codeword // kdepth, codeword % kdepth, half)
        require(slot[0] < kblocks and slot not in kseen, "KU alias or overflow")
        kseen.add(slot)
    require(len(rseen) == rwords and len(kseen) == 2 * kwords,
            "Incomplete mapping")

    one_chip_data = (rr["lsram_blocks_per_chip"] * rdepth +
                     rr["usram_blocks_per_chip"] * rr["usram_codewords_per_block"]) * rk
    require(one_chip_data < bits, "Single-chip exclusion no longer holds")
    beam = rt["source_proton_test"]
    beam_bits = beam["lsram_blocks"] * rdepth * beam["tested_positions_per_address"]
    sigma = Fraction(beam["errors"], beam_bits) / Fraction(beam["fluence_protons_cm2"])
    reported = Fraction(beam["reported_sigma_cm2_per_bit"])
    # Published 8.5024e-15 is rounded to five significant figures.
    require(abs(sigma - reported) <= Fraction("0.00005e-15"),
            "Beam normalization does not round to reported cross section")
    with localcontext() as ctx:
        ctx.prec = 24
        sigma_decimal = str(Decimal(sigma.numerator) / Decimal(sigma.denominator))

    return {
        "kind": "OWN_RESULT: storage arithmetic and beam normalization only",
        "useful_bytes_each_candidate": bits // 8,
        "rtg4": {
            "native_codewords": rwords,
            "lsram_blocks_each_chip": rblocks_each,
            "allocated_physical_bytes_including_ECC": rwords * rn // 8,
            "allocated_padding_bytes": rwords * (rk - rt["payload_bits_per_codeword"]) // 8,
            "allocated_ECC_bytes": rwords * (rn - rk) // 8,
            "installed_LSRAM_bytes_including_ECC": rt["chips"] * rr["lsram_blocks_per_chip"] * rdepth * rn // 8,
            "unused_LSRAM_fraction_per_chip": exact(Fraction(rr["lsram_blocks_per_chip"] - rblocks_each, rr["lsram_blocks_per_chip"])),
            "one_chip_all_SRAM_max_native_ECC_data_bytes": one_chip_data // 8,
            "one_chip_payload_deficit_bytes_even_without_padding": (bits - one_chip_data) // 8,
            "beam_tested_bits": beam_bits,
            "beam_sigma_cm2_per_tested_bit_exact": exact(sigma),
            "beam_sigma_cm2_per_tested_bit_decimal": sigma_decimal
        },
        "xqrku060": {
            "native_codewords": kwords,
            "bram36_blocks_allocated": kblocks,
            "allocated_physical_bytes_including_ECC": kwords * kn // 8,
            "allocated_padding_bytes": 0,
            "allocated_ECC_bytes": kwords * (kn - ku["native_code"]["k"]) // 8,
            "installed_BRAM_bytes_including_ECC": ku["chips"] * kr["bram36_blocks_per_chip"] * kdepth * kn // 8,
            "unused_BRAM_fraction": exact(Fraction(ku["chips"] * kr["bram36_blocks_per_chip"] - kblocks, ku["chips"] * kr["bram36_blocks_per_chip"])),
            "source_shield_Al_mm": exact(Fraction(ku["source_environment_rate"]["shield_Al_mil"] * 254, 10000))
        },
        "physical_Q": None,
        "time_and_controller_resource_margins": None
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--write", action="store_true")
    args = parser.parse_args()
    sources = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
    for source in sources["pdfs"]:
        raw = (args.pdf_dir / source["file"]).read_bytes()
        require(raw.startswith(b"%PDF-"), f"Not PDF: {source['file']}")
        require(len(raw) == source["bytes"], f"Size mismatch: {source['file']}")
        require(hashlib.sha256(raw).hexdigest() == source["sha256"],
                f"SHA256 mismatch: {source['file']}")
    inp = json.loads((HERE / "input.json").read_text(encoding="utf-8"))
    result = calculate(inp)
    serialized = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    target = HERE / "results.json"
    if args.write:
        target.write_text(serialized, encoding="utf-8", newline="\n")
    else:
        require(target.read_text(encoding="utf-8") == serialized, "Results differ")
    print(f"Verified {len(sources['pdfs'])} PDF hashes; both complete payload mappings; "
          "capacity exclusion; one beam normalization. No Q calculated.")
    print("results.json SHA256 (UTF-8/LF):", hashlib.sha256(serialized.encode()).hexdigest())


if __name__ == "__main__":
    main()

"""Check which GENEPI observations survive and project model address groups on v21."""

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
MAP = EXP / "RE-CY62167-ADDRESS-MAPPING-01"
sys.path.insert(0, str(MAP))
sys.path.insert(0, str(EXP / "RE-CY62167-PROTON-01"))
from address_mapping_gf2 import predict_address, solve_gf2_unique
from parse_zenodo_protons import parse_cluster_file


def genepi_fields(path):
    if hashlib.md5(path.read_bytes()).hexdigest() != "642ac181a45c53f192e8471c5387173a":
        raise ValueError("Different 2018 GENEPI archive")
    result = {}
    with zipfile.ZipFile(path) as archive:
        for member in sorted(archive.namelist()):
            if "/65-nm/" not in member or not member.endswith(".csv"):
                continue
            with io.TextIOWrapper(archive.open(member), encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                assert reader.fieldnames == ["Address", "Content", "Pattern"]
                addresses = set()
                rows = matching = flips = 0
                for row in reader:
                    address, value, pattern = (int(row[key], 0) for key in reader.fieldnames)
                    assert 0 <= address < 2**21 and 0 <= value <= 255 and 0 <= pattern <= 255
                    rows += 1
                    addresses.add(address)
                    matching += value == pattern
                    flips += (value ^ pattern).bit_count()
            result[Path(member).name] = {"rows": rows, "unique_addresses": len(addresses),
                                         "matching_DQ": matching, "DQ_pattern_bit_differences": flips}
    return result


# Only the supplied grid's 32 data sites. No syndrome bits are placed here.
FREE = {"one_y": (0x1F0, 0), "two_y": (0x0F0, 0x10), "four_y": (0x070, 0x30)}


def preimages(address, coefficients):
    # Fix free x4,x5,x6 to zero to obtain exactly one representative.
    equations = [mask >> 1 for mask in coefficients] + [1 << b for b in (4, 5, 6)]
    rhs = [((address >> i) & 1) ^ (mask & 1) for i, mask in enumerate(coefficients)] + [0, 0, 0]
    base = solve_gf2_unique(equations, rhs, 24)
    sites = {((base & 4095) ^ (k << 4), base >> 12) for k in range(8)}
    assert all(predict_address(x, y, coefficients) == address for x, y in sites)
    return sites


def model_groups(coefficients):
    groups = {}
    for name, (free_x, free_y) in FREE.items():
        # A synthetic absolute origin. All unfixed choices at this origin are enumerated.
        sites = {(x, y) for x in range(free_x + 1) if not x & ~free_x
                 for y in range(free_y + 1) if not y & ~free_y}
        addresses = sorted({predict_address(x, y, coefficients) for x, y in sites})
        assert len(addresses) == 4 and len(sites) == 32
        assert set.union(*(preimages(address, coefficients) for address in addresses)) == sites
        groups[name] = {"synthetic_x8_raw_addresses": [hex(a) for a in addresses],
                        "distinct_y": sorted({y for x, y in sites})}
    return groups


def cluster_intersections(path):
    manifest = json.loads((MAP / "input_manifest.json").read_bytes())["raw_members"]
    previous = json.loads((EXP / "t186-native-direct-1-4" / "result.json").read_bytes())["populations"]
    totals = {"p": Counter(), "HI": Counter()}
    witnesses = {"p": {}, "HI": {}}
    with zipfile.ZipFile(path) as archive:
        for entry in manifest:
            name = entry["source_file"]
            source = "p" if name.startswith("clust_p") else "HI"
            member, = [p for p in archive.namelist() if Path(p).name == name]
            data = zipfile.Path(archive, member)
            assert hashlib.sha256(data.read_bytes()).hexdigest() == entry["sha256"]
            count = totals[source]
            for index, record in enumerate(parse_cluster_file(data), 1):
                sites = sorted({(c.x, c.y) for c in record.cells})
                if sites == [(0, 0)]:
                    continue
                count["records"] += 1
                if len(sites) < 2:
                    continue
                for layout, (free_x, free_y) in FREE.items():
                    words = {}
                    for x, y in sites:
                        word = (x & ~free_x, y & ~free_y)
                        if word in words:
                            count[layout] += 1
                            witnesses[source].setdefault(layout, {"file": name, "record_1_based": index,
                                                                  "xy": [list(words[word]), [x, y]]})
                            break
                        words[word] = (x, y)
                # Previously published ideal Y-axis placement differs from two/four rows of octets.
                count["axis_y_step16"] += len({(x, y // 512, y % 16) for x, y in sites}) < len(sites)
    for source, count in totals.items():
        assert count["records"] == previous[source]["clusters"]
        assert count["one_y"] == previous[source]["X"]["counts_from_step_1"][15]
        assert count["axis_y_step16"] == previous[source]["Y"]["counts_from_step_1"][15]
    return {s: {k: v[k] for k in ("records", *FREE, "axis_y_step16")} for s, v in totals.items()}, witnesses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--genepi", required=True, type=Path)
    parser.add_argument("--clusters", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    coefficients = json.loads((MAP / "address_mapping_coefficients.json").read_bytes())["coefficient_masks_lsb_feature_order"]
    counts, examples = cluster_intersections(args.clusters)
    results = {"GENEPI_65nm": genepi_fields(args.genepi), "synthetic_groups": model_groups(coefficients),
               "recorded_data_cell_intersections": counts, "first_examples": examples}
    path = HERE / "result.json"
    if args.check:
        if results != json.loads(path.read_bytes()):
            raise SystemExit("Result differs")
        print("Verified GENEPI fields, three synthetic groups, 28 files and both axis controls.")
    else:
        path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

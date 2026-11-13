"""Project distinct recorded data sites onto the two candidate x16 interfaces."""

import argparse
import csv
import hashlib
import json
import sys
import zipfile
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

from check import EXP, HERE, MAP, model_groups, parse_cluster_file, predict_address, preimages

T68 = EXP / "t68-v21-inputs"
sys.path.insert(0, str(T68))
from run import function_namespace

PIN_MASK = (1 << 20) - 1
BLOCK_MASK = sum(1 << bit for bit in (0, 1, 5, 7))
SEAM = ((2047, 1024), (2048, 1024))
FIELDS = ("records", "low", "pin", "row_candidates", "block_candidates")


def hits(addresses):
    """The input has one entry per DISTINCT XY, including sites in the same byte."""
    return (len({a >> 1 for a in addresses}) < len(addresses),
            len({a & PIN_MASK for a in addresses}) < len(addresses))


def calculate(raw):
    coeff = json.loads((MAP / "address_mapping_coefficients.json").read_bytes())[
        "coefficient_masks_lsb_feature_order"]
    manifest = json.loads((MAP / "input_manifest.json").read_bytes())["raw_members"]
    with (T68 / "outputs/raw_x16_hypotheses.csv").open() as stream:
        t68 = {(r["run"], int(r["assumed_raw_byte_selector_bit"])): r for r in csv.DictReader(stream)}
    with (T68 / "outputs/clusters.csv").open() as stream:
        merged_totals = {r["run"]: int(r["merged_objects"]) for r in csv.DictReader(stream)}
    bundle = T68 / "inputs/calc_v18.zip"
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == "14ac38ff24c1bf1a199278f08a7c807176b8b613f434719309050248b8929b83"
    with zipfile.ZipFile(bundle) as z:
        scripts = sorted(n for n in z.namelist() if n.endswith(".py"))
        merge = function_namespace(zipfile.Path(z, "merged.py"))["merge_events"]

    seam_addresses = [predict_address(x, y, coeff) for x, y in SEAM]
    assert [a ^ seam_addresses[0] for a in seam_addresses] == [0, 1 << 20]
    assert not any(a & BLOCK_MASK for a in seam_addresses)
    for (x, y), a in zip(SEAM, seam_addresses):
        assert (x, y) in preimages(a, coeff)

    totals = {"p": Counter(), "HI": Counter()}
    rows, low_examples = {}, {}
    pair_records = defaultdict(list)
    # Each free-bit layout in #489 fixes x11, hence fixes the H_pin byte lane.
    for layout in model_groups(coeff).values():
        group = [int(s, 16) for s in layout["synthetic_x8_raw_addresses"]]
        assert len({a >> 20 for a in group}) == 1
    seam_records = 0
    with zipfile.ZipFile(raw) as z:
        members = {Path(f).name: f for f in z.namelist() if not f.endswith("/")}
        assert len(members) == 28 and set(members) == {m["source_file"] for m in manifest}
        for item in sorted(manifest, key=lambda m: m["source_file"]):
            filename = item["source_file"]
            name = filename.removeprefix("clust_").removesuffix(".txt")
            family = "p" if name.startswith("p") else "HI"
            source = zipfile.Path(z, members[filename])
            data = source.read_bytes()
            assert hashlib.sha256(data).hexdigest() == item["sha256"]
            assert hashlib.md5(data).hexdigest() == item["md5"]
            counts, arities, events = Counter(), set(), []
            for record in parse_cluster_file(source):
                xy = sorted({(c.x, c.y) for c in record.cells})
                if xy == [(0, 0)]:
                    continue
                aa = {site: predict_address(*site, coeff) for site in xy}
                for c in record.cells:
                    arities.add(2 if c.field0_raw is None else 3)
                    assert c.field0_raw is None or c.field0_raw == aa[c.x, c.y]
                addresses = list(aa.values())
                low, pin = hits(addresses)
                counts.update(records=1, low=low, pin=pin)
                seam_records += all(site in aa for site in SEAM)
                if low:
                    left, right = next((u, v) for u, v in combinations(xy, 2) if aa[u] >> 1 == aa[v] >> 1)
                    assert aa[left] ^ aa[right] == 1
                    low_examples.setdefault(name, []).append(dict(
                        line=record.line_start, xy=[left, right], a=[aa[left], aa[right]]))
                if family == "HI":
                    xs, ys = np.array(xy).T
                    events.append(dict(xs=xs, ys=ys, a=np.array(addresses)))
                # Record-wise superset over allowed same-row partnerships. Count each record once.
                by_y = defaultdict(dict)
                for (x, y), a in aa.items():
                    by_y[y][a & PIN_MASK] = (x, y)
                counts["row_candidates"] += any(len(halves) >= 2 for halves in by_y.values())
                block_pairs = {}
                for halves in by_y.values():
                    for left, right in combinations(sorted(h for h in halves if not h & BLOCK_MASK), 2):
                        block_pairs[left, right] = [halves[left], halves[right]]
                counts["block_candidates"] += bool(block_pairs)
                for pair, sites in block_pairs.items():
                    pair_records[pair].append(dict(file=filename, line=record.line_start,
                                                   cluster=record.cluster_id, xy=sites))

            row = {k: counts[k] for k in FIELDS}
            row["fields"] = sorted(arities)
            if family == "HI":
                merged = merge(events)
                mlow = mpin = 0
                for e in merged:
                    low, pin = hits(e["a"].tolist())
                    mlow += low
                    mpin += pin
                assert len(merged) == merged_totals[name]
                for selector, registered, regrouped in [(0, row["low"], mlow), (20, row["pin"], mpin)]:
                    old = t68[name, selector]
                    assert (registered, regrouped) == (int(old["raw_same_x16_registered_objects"]),
                                                        int(old["raw_same_x16_merged_objects"]))
                counts.update(merged=len(merged), merged_low=mlow, merged_pin=mpin)
                row.update(merged=len(merged), merged_low=mlow, merged_pin=mpin)
            totals[family].update(counts)
            rows[name] = row

    prev = json.loads((HERE / "result.json").read_bytes())["recorded_data_cell_intersections"]
    assert all(prev[k]["records"] == v["records"] for k, v in totals.items())
    best_pair = min(pair_records, key=lambda pair: (-len(pair_records[pair]), pair))
    for sample in pair_records[best_pair]:
        for (x, y), h in zip(sample["xy"], best_pair):
            byte = predict_address(x, y, coeff)
            assert byte & PIN_MASK == h
            assert {sy for a in (h, h | (1 << 20)) for _, sy in preimages(a, coeff)} == {y}
    return dict(synthetic_seam=dict(xy=SEAM, a=seam_addresses, xor=seam_addresses[0] ^ seam_addresses[1],
                                    x16_pin=seam_addresses[0] & PIN_MASK, registered_together=seam_records),
                totals=totals, rows=rows, low_examples=low_examples,
                fixed_block_pair=dict(x16=best_pair, matching_records=len(pair_records[best_pair]),
                                      witnesses=pair_records[best_pair]),
                t68_scripts=scripts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clusters", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = HERE / "pin45.json"
    text = json.dumps(calculate(args.clusters), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if json.loads(text) != json.loads(output.read_bytes()):
            raise SystemExit("Different pin45 results")
        print("Verified 28 archive files, both byte selectors, the v21 seam and the fixed pair.")
    else:
        output.write_text(text, encoding="utf-8", newline="\n")

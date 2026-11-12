"""Registered XY footprints and prospective direct-event requirements, task 1.4."""
import argparse
import hashlib
import json
import sys
import zipfile
from collections import Counter
from decimal import Decimal as D, localcontext, ROUND_CEILING
from fractions import Fraction as F
from itertools import combinations
from math import isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
MAP = EXP / "RE-CY62167-ADDRESS-MAPPING-01"
sys.path.insert(0, str(MAP))
sys.path.insert(0, str(EXP / "RE-CY62167-PROTON-01"))
from address_mapping_gf2 import predict_address
from parse_zenodo_protons import parse_cluster_file

TILE_STEPS = (1, 2, 4, 8, 16, 32, 64, 128)


def read(path):
    return json.loads(path.read_bytes())


def divisors(d):
    small = [s for s in range(1, isqrt(d) + 1) if d % s == 0]
    return set(small) | {d // s for s in small}


def collision_steps(sites, factors):
    found = [set(), set()]
    for (x, y), (xx, yy) in combinations(sites, 2):
        if y == yy:
            i, a, b = 0, x, xx
        elif x == xx:
            i, a, b = 1, y, yy
        else:
            continue
        d = abs(a - b)
        for s in factors[d]:
            if a // (32 * s) == b // (32 * s):
                found[i].add(s)
    return found


def map_count(sites, step, axis):
    # Independent full-word projection for the exact finite tilings.
    keys = {(p[1-axis], p[axis] // (32 * step), p[axis] % step) for p in sites}
    return len(keys) < len(sites)


def inspect(source, factors, coeff):
    counts = [Counter(), Counter()]
    clusters = cell_rows = unique = reserved = ambiguous = a4 = diameter = 0
    for rec in parse_cluster_file(source):
        sites = {(c.x, c.y) for c in rec.cells}
        if sites == {(0, 0)}:
            reserved += 1
            ambiguous += rec.is_ambiguous_zero_record
            continue
        assert sites and all(0 <= x < 4096 and 0 <= y < 4096 for x, y in sites)
        clusters += 1
        cell_rows += rec.k
        unique += len(sites)
        if len(sites) < 2:
            continue
        diameter = max(diameter, *(max(p[i] for p in sites) - min(p[i] for p in sites) for i in (0, 1)))
        found = collision_steps(sites, factors)
        for axis in (0, 1):
            counts[axis].update(found[axis])
            for s in TILE_STEPS:
                assert map_count(sites, s, axis) == (s in found[axis])
        words = {predict_address(x, y, coeff) // 4 for x, y in sites}
        a4 += len(words) < len(sites)
    return dict(clusters=clusters, cell_rows=cell_rows, unique_occurrences=unique,
                excluded_origin=reserved, ambiguous_zero=ambiguous, max_dinf=diameter,
                A_div_4=a4, X=dict(sorted(counts[0].items())), Y=dict(sorted(counts[1].items())))


def collect(archive):
    manifest = read(MAP / "input_manifest.json")["raw_members"]
    coeff = read(MAP / "address_mapping_coefficients.json")["coefficient_masks_lsb_feature_order"]
    factors = [()] + [divisors(n) for n in range(1, 4096)]
    series = {}
    with zipfile.ZipFile(archive) as raw:
        for entry in manifest:
            name = entry["source_file"]
            matches = [p for p in raw.namelist() if p.split("/")[-1] == name]
            if len(matches) != 1:
                raise ValueError(f"Expected a single source member {name}")
            path = zipfile.Path(raw, matches[0])
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError(f"Unexpected SHA-256 for {name}")
            series[name] = inspect(path, factors, coeff)
    assert len(series) == 28
    populations = {}
    for species in ("p", "HI", "all"):
        rows = [r for name, r in series.items() if species == "all" or (name.startswith("clust_p") == (species == "p"))]
        assert len(rows) == (28 if species == "all" else 14)
        totals = {k: sum(r[k] for r in rows) for k in ("clusters", "cell_rows", "unique_occurrences", "excluded_origin", "ambiguous_zero", "A_div_4")}
        largest = max(r["max_dinf"] for r in rows)
        totals["max_dinf"] = largest
        for axis in ("X", "Y"):
            counts = [sum(r[axis].get(s, 0) for r in rows) for s in range(1, largest + 2)]
            totals[axis] = dict(counts_from_step_1=counts, first_zero=counts.index(0) + 1,
                                all_zero_from=max((s for s, k in enumerate(counts, 1) if k), default=0) + 1)
        populations[species] = totals
    t68 = read(EXP / "t68-v21-inputs/outputs/summary.json")["clusters"]
    assert populations["all"]["clusters"] == t68["ordinary_clusters"] == 173802
    assert populations["all"]["unique_occurrences"] == t68["cell_occurrences"] == 299026, populations["all"]
    assert populations["HI"]["clusters"] == t68["HI_registered_clusters"]
    return {"series": series, "populations": populations}


def number(f):
    return D(f.numerator) / D(f.denominator)


def zero_design(f):
    with localcontext() as ctx:
        ctx.prec = 60
        log_miss = (1 - number(f)).ln()
        log_alpha = D("0.05").ln()
        n = int((log_alpha / log_miss).to_integral_value(rounding=ROUND_CEILING))
        assert n * log_miss <= log_alpha < (n - 1) * log_miss
        return n


def budgets():
    data = []
    for m in (F(6, 5), F(2), F(4), F(5), F(8)):
        for w, issued in ((32768, F("1.70e-8")), (44529, F("1.25e-8"))):
            parents = F(w * 187464, 524288) / m
            target = F(1, 10000) / parents
            row = dict(mean_bits=str(m), W=w, N_plus=str(parents), exact_target=str(target),
                       N_for_exact_target=zero_design(target))
            if m == 2:
                assert issued <= target
                row.update(issued_target=str(issued), N_for_issued_target=zero_design(issued))
            data.append(row)
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    out = collect(args.archive)
    out["parent_budgets"] = budgets()
    # JSON object keys for integral steps become canonical strings on disk.
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    path = HERE / "result.json"
    if args.check:
        assert json.loads(text) == read(path)
        print("All 28 member hashes, two independent geometric counts and saved results agree.")
    else:
        path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

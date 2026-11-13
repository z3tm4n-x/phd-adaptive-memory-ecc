"""Recount recorded heavy-ion clusters and their conditional bank projections."""
import argparse
import csv
import hashlib
import json
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXP = HERE.parent
MAP = EXP / "RE-CY62167-ADDRESS-MAPPING-01"
sys.path.insert(0, str(MAP))
sys.path.insert(0, str(EXP / "RE-CY62167-PROTON-01"))
from address_mapping_gf2 import predict_address
from parse_zenodo_protons import parse_cluster_file


def read(path):
    return json.loads(path.read_bytes())


@dataclass
class Counts:
    sizes: Counter = field(default_factory=Counter)
    small_same_word: int = 0
    any_same_word: int = 0

    def observe(self, size, words=None):
        if size:
            self.sizes[size] += 1
            if words is not None and len(set(words)) < size:
                self.any_same_word += 1
                self.small_same_word += size == 2

    def summary(self, bank=False):
        n = self.sizes.total()
        cells = sum(k * count for k, count in self.sizes.items())
        result = dict(nonempty=n, unique_cells=cells, singles=self.sizes[1], doubles=self.sizes[2],
                      large_records=n-self.sizes[1]-self.sizes[2],
                      cells_in_large=cells-self.sizes[1]-2*self.sizes[2], max_size=max(self.sizes, default=0))
        if bank:
            result.update(two_cell_same_word=self.small_same_word, any_same_word=self.any_same_word)
        return result

    def merge(self, other):
        self.sizes.update(other.sizes)
        self.small_same_word += other.small_same_word
        self.any_same_word += other.any_same_word


def count_file(member, coefficients, word_count):
    counts = {key: Counts() for key in ("die", "low", "pin")}
    excluded = timed = 0
    for record in parse_cluster_file(member):
        sites = {(v.x, v.y) for v in record.cells}
        if sites == {(0, 0)}:
            excluded += 1
            continue
        timed += record.timestamp_sod is not None
        counts["die"].observe(len(sites))
        addresses = {xy: predict_address(*xy, coefficients) for xy in sites}
        for cell in record.cells:
            if cell.field0_raw is not None:
                assert addresses[(cell.x, cell.y)] == cell.field0_raw
        for key in ("low", "pin"):
            halves = [a // 2 if key == "low" else a % 2**20 for a in addresses.values()]
            words = [half % word_count for half in halves if 0 <= half < 2 * word_count]
            counts[key].observe(len(words), words)
    return counts, excluded, timed


def rounded_down(frac, places):
    n = (frac * 10**places).__floor__()
    whole, remainder = divmod(n, 10**places)
    return f"{whole}.{remainder:0{places}d}"


def calculate(archive):
    previous = read(EXP / "t186-native-direct-1-4/result.json")
    reference = read(EXP / "t196-cluster-main-20261112/result.json")
    word_count = reference["word_count"]
    assert word_count == 32768
    manifest = {e["source_file"]: e["sha256"] for e in read(MAP / "input_manifest.json")["raw_members"]}
    coefficients = read(MAP / "address_mapping_coefficients.json")["coefficient_masks_lsb_feature_order"]
    with (EXP / "t68-v21-inputs/outputs/clusters.csv").open(encoding="utf-8") as fp:
        ion_metadata = list(csv.DictReader(fp))
    assert len(ion_metadata) == 14
    series = {}
    totals = {key: Counts() for key in ("die", "low", "pin")}
    with zipfile.ZipFile(archive) as raw:
        for meta in ion_metadata:
            run = meta["run"]
            name = f"clust_{run}.txt"
            paths = [p for p in raw.namelist() if p.rsplit("/", 1)[-1] == name]
            if len(paths) != 1:
                raise ValueError(f"Expected one archive member for {name}")
            member = zipfile.Path(raw, paths[0])
            digest = hashlib.sha256(member.read_bytes()).hexdigest()
            if digest != manifest[name]:
                raise ValueError(f"Archive checksum mismatch: {name}")
            counts, excluded, timed = count_file(member, coefficients, word_count)
            data = {k: v.summary(k != "die") for k, v in counts.items()}
            old = previous["series"][name]
            assert (data["die"]["nonempty"], data["die"]["unique_cells"], excluded) == (
                old["clusters"], old["unique_occurrences"], old["excluded_origin"])
            assert int(meta["registered_clusters"]) == data["die"]["nonempty"]
            for k in totals:
                totals[k].merge(counts[k])
            series[run] = {"LET_from_T68": meta["LET"], "readout_timed_records": timed, **data}
    total = {k: v.summary(k != "die") for k, v in totals.items()}
    assert total["die"]["nonempty"] == previous["populations"]["HI"]["clusters"]
    assert sum(v["readout_timed_records"] > 0 for v in series.values()) == 6
    assert all(v["readout_timed_records"] in (0, v["die"]["nonempty"]) for v in series.values())
    service = read(EXP / "t186-native-ge30-x16/calendar.json")
    word_bits = service["inner_data_bits"] + service["inner_check_bits"]
    reference_bits = read(EXP / "c1-common-geo-20261109/coverage.json")["D"]
    bank_fraction = Fraction(word_count * word_bits, reference_bits)
    assert bank_fraction == Fraction(1, 16)
    thresholds = {}
    for target, row in reference["thresholds"].items():
        eta = Fraction(row["eta_sufficient"])
        bank_exposure = Fraction(reference["profiles"][target]["S1"]) * bank_fraction
        thresholds[target] = {"eta": str(eta),
                              "min_visible_fraction_of_small_parents_if_no_large_and_m2": str(2*eta),
                              "max_large_inversion_fraction_if_all_small_visible_and_m2": str(1-2*eta),
                              "lifetime_large_inversions_upper_from_total": str(bank_exposure),
                              "lifetime_large_parents_upper_from_total": str(bank_exposure/3)}
    direct = {q["mean_bits"]: {"parent_cap": q["N_plus"], "direct_fraction_exact": q["exact_target"],
                               "direct_fraction_sufficient_12_places": rounded_down(Fraction(q["exact_target"]), 12)}
              for q in previous["parent_budgets"] if q["W"] == word_count}
    return {"series": series, "total": total, "visibility": thresholds,
            "illustrative_direct_allocation": "1/10000", "direct": direct}


def table_line(label, part, let):
    die = part["die"]

    def pair(row):
        return f"{row['large_records']}/{row['nonempty']} · {row['cells_in_large']}/{row['unique_cells']}"

    link = f"[{label}](https://zenodo.org/records/8314389/files/clust_{label}.txt?download=1)" if let else label
    display_let = let.replace(".", ",") if let else "—"
    return (f"| {link} | {display_let} | {pair(die)} | {die['max_size']} | {pair(part['low'])} | "
            f"{pair(part['pin'])} | Z |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", required=True, type=Path)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--table", action="store_true")
    args = ap.parse_args()
    result = calculate(args.archive)
    lines = [table_line(k, v, v["LET_from_T68"]) for k, v in result["series"].items()]
    lines.append(table_line("**14 ионных серий**", result["total"], None))
    if args.check:
        assert result == read(HERE / "result.json")
        report = (HERE / "README.md").read_text(encoding="utf-8").splitlines()
        assert all(report.count(line) == 1 for line in lines)
        print("Verified 14 member hashes, full-die and both bank counts, 15 printed rows and the issued thresholds.")
    elif args.table:
        print("\n".join(lines))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

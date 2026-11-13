"""Inventory the released cluster records. No ZIP contents are extracted to disk."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
MAPPING = HERE.parent / "RE-CY62167-ADDRESS-MAPPING-01"
sys.path.insert(0, str(MAPPING))
from address_mapping_data import inspect_archive_before_member_read, read_archive_members_and_hash
from address_mapping_parser import parse_cluster_text


def inventory(path):
    manifest = json.loads((MAPPING / "input_manifest.json").read_text(encoding="utf-8"))
    _, infos = inspect_archive_before_member_read(path)
    texts, members = read_archive_members_and_hash(path, infos)
    keys = ("source_file", "size", "sha256", "md5")
    expected = sorted(tuple(row[k] for k in keys) for row in manifest["raw_members"])
    actual = sorted(tuple(row[k] for k in keys) for row in members)
    if actual != expected or not all(row["zenodo_md5_match"] for row in members):
        raise ValueError("ZIP members differ from the registered Zenodo files")

    totals = Counter()
    for name, contents in texts.items():
        records, stats = parse_cluster_text(name, contents)
        # line_start distinguishes blocks even when cluster IDs restart in a file.
        blocks = {r.line_start for r in records}
        timed = {r.line_start for r in records if r.timestamp_raw is not None}
        if len(blocks) != stats.cluster_count:
            raise ValueError(f"{name}: empty block; inspect its time header directly")
        totals.update({
            "proton_files" if name.startswith("clust_p") else "heavy_ion_files": 1,
            "raw_cluster_blocks": stats.cluster_count,
            "blocks_with_clock_label": len(timed),
            "blocks_without_clock_label": len(blocks) - len(timed),
            "cell_rows_xy": stats.two_field_count,
            "cell_rows_external_field_xy": stats.three_field_count,
            "raw_cell_rows": stats.cell_record_count,
        })
    return dict(totals)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--check", action="store_true", help="compare with the recorded inventory")
    args = parser.parse_args()
    result = inventory(args.archive)
    if args.check and result != json.loads((HERE / "archive.json").read_text(encoding="utf-8")):
        raise SystemExit("archive inventory differs")
    print(json.dumps(result, indent=2, sort_keys=True))

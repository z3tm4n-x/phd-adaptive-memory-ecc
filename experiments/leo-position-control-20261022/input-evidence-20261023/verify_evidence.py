"""Offline evidence replay only: no CDF validation, Q, or physical acceptance."""

import argparse
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_bytes(path, record):
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == record["sha256"],
            f"SHA256 mismatch: {path}")
    if "bytes" in record:
        require(len(data) == record["bytes"], f"Size mismatch: {path}")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path,
                        help="Directory holding the three external files in evidence.json")
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    manifest = json.loads((here / "evidence.json").read_text(encoding="utf-8"))
    for record in manifest["unchanged_repo_inputs"]:
        checked_bytes(root / record["path"], record)

    for record in manifest["external_files"]:
        data = checked_bytes(args.data_dir / record["file"], record)
        if record["file"].endswith(".pdf"):
            require(data.startswith(b"%PDF-"), f"Not PDF: {record['file']}")
        else:
            catalog = json.loads(data)
            require(catalog["status"]["code"] == record["hapi_status"], "HAPI status")
            rows = catalog["catalog"]
            needles = record["case_insensitive_substrings_over_each_record"]
            matches = [row for row in rows if any(
                term in json.dumps(row, ensure_ascii=False).lower() for term in needles)]
            require(len(rows) == record["records"], "Catalog record count")
            require(len(matches) == record["matching_records"], "Catalog matches")
            print(f"Catalog replay: {len(rows)} records; {len(matches)} matching records")

    print("Evidence hashes checked: 3 external files; 3 unchanged repository inputs")
    print("Scope: metadata and document provenance only; no measurements or numeric word response")


if __name__ == "__main__":
    main()

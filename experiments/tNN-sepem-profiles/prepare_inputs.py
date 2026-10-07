"""Extract the numerical NIST table from a separately downloaded public response.

Download request: POST https://physics.nist.gov/cgi-bin/Star/ap_table-t.pl
prog=PSTAR&matno=013&Energies=&ShowDefault=on
Raw SEPEM and website responses remain outside Git.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def parse_pstar(text):
    if "ALUMINUM" not in text or "PROTON STOPPING" not in text:
        raise ValueError("Not the expected NIST proton/aluminium table")
    rows = []
    for line in re.split(r"<br\s*/?>|\n", text, flags=re.I):
        items = line.split()
        if len(items) != 7:
            continue
        try:
            row = list(map(float, items))
        except ValueError:
            continue
        rows.append(row)
    if len(rows) < 100 or any(b[0] <= a[0] for a, b in zip(rows, rows[1:])):
        raise ValueError("Missing or unsorted range table")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html", type=Path)
    args = ap.parse_args()
    raw = args.html.read_bytes()
    rows = parse_pstar(raw.decode("utf-8"))
    out = HERE / "inputs"
    out.mkdir(exist_ok=True)
    target = out / "nist_pstar_al.csv"
    with target.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["energy_mev", "electronic_stopping_mev_cm2_g", "nuclear_stopping_mev_cm2_g",
                    "total_stopping_mev_cm2_g", "csda_range_g_cm2", "projected_range_g_cm2", "detour"])
        w.writerows(rows)
    metadata = {"source": "NIST PSTAR, aluminium (013)", "retrieved": "2026-10-07",
                "url": "https://physics.nist.gov/cgi-bin/Star/ap_table-t.pl",
                "post": {"prog": "PSTAR", "matno": "013", "Energies": "", "ShowDefault": "on"},
                "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
                "derived_csv_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "rows": len(rows), "scope": "CSDA; not straggling or nuclear-secondary transport"}
    (out / "nist_manifest.json").write_text(json.dumps(metadata, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(metadata))


if __name__ == "__main__":
    main()

"""Recover only the requested 3 g/cm2 Al column from the verified amendment-2 PDF."""

import argparse
import csv
import hashlib
import io
import logging
import re
from pathlib import Path

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
SHA256 = "232c84bf7fb6c2d3aec11c44827bcf01a6b6964366a8d0059ff36cd5b143a9e1"
# PDF page is one-based. Printed page = PDF page - 6.
PAGES = {
    "Л.3.1.2": [(214, 24), (215, 17)],
    "Л.3.1.4": [(218, 24), (219, 21)],
    "Л.3.2.2": [(223, 24), (224, 24)],
    "Л.3.2.4": [(228, 24), (229, 24), (230, 2)],
}
SHIELDS = "0,01 0,1 0,3 0,5 1,0 1,5 2,0 3,0 10,0".split()
SCIENTIFIC = re.compile(r"\d+,\d+E[+-]\d+")


def selected_column(pdf):
    with pdf.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != SHA256:
            raise ValueError("Source differs from the registered amendment-2 PDF")
    reader = PdfReader(pdf)
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["table", "printed_page", "coordinate", "density_at_3g_cm2"])
    for table, pages in PAGES.items():
        for page, expected in pages:
            lines = [s.split() for s in reader.pages[page - 1].extract_text(
                extraction_mode="layout").splitlines() if s.strip()]
            if table not in "".join(lines[0]) or lines[2][-9:] != SHIELDS:
                raise ValueError(f"Unexpected caption or shielding on PDF page {page}")
            count = 0
            for row in lines[3:]:
                if not SCIENTIFIC.fullmatch(row[0]):
                    continue
                if len(row) != 10 or not all(SCIENTIFIC.fullmatch(v) for v in row):
                    raise ValueError(f"Malformed spectral row on PDF page {page}: {row}")
                writer.writerow([table, page - 6, row[0].replace(",", "."), row[8].replace(",", ".")])
                count += 1
            if count != expected:
                raise ValueError(f"Expected {expected} spectral rows on PDF page {page}, got {count}")
    return output.getvalue()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    # Only the running page labels are rotated; all spectral rows and headers are checked.
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    data = selected_column(args.pdf)
    path = HERE / "ost_3g.csv"
    if args.check:
        if path.read_text(encoding="utf-8") != data:
            parser.exit(1, "Selected column differs from source\n")
        print("OK: four captions, nine pages, all 184 coordinates and densities")
    else:
        path.write_text(data, encoding="utf-8", newline="\n")

#!/usr/bin/env python3
"""Reproduce the controlled Fig. 3 digitization for the Cypress FLUKA/RPP curve.

Source: A. Coronetti et al., IEEE TNS 68(5), 937-948 (2021),
DOI 10.1109/TNS.2021.3061209, Fig. 3, printed p. 939 (PDF p. 3).

The source PDF is intentionally not redistributed.  The calibration and marker
centres below are recorded in pixels of a 400-dpi rendering of PDF page 3,
followed by a crop whose top-left corner is (1700, 1500) in page pixels and size
1550 x 900.  Log10 axes are fitted from visible major grid-line crossings.

Green FLUKA star centres were extracted from a colour mask; the two overlapping
peak markers have a wider centre-location allowance.  This script converts the
recorded pixels to (E, sigma) and writes the machine-readable comparator table.
It does not claim the FLUKA curve is experimental data.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np

SOURCE_DOI = "10.1109/TNS.2021.3061209"
SOURCE_FIGURE = "Fig. 3"
SOURCE_PDF_PAGE = 3
SOURCE_PRINTED_PAGE = 939
RENDER_DPI = 400
CROP_ORIGIN_PAGE_PX = (1700, 1500)
CROP_SIZE_PX = (1550, 900)

# Major ticks: (pixel coordinate in crop, log10 physical coordinate).
X_CAL = ((366.5, 0.0), (796.5, 1.0), (1224.5, 2.0))  # E = 1, 10, 100 MeV
Y_CAL = (
    (61.5, -9.0),
    (176.0, -10.0),
    (289.5, -11.0),
    (403.5, -12.0),
    (518.5, -13.0),
    (631.5, -14.0),
)

# (point_id, x_px, y_px, centre-location uncertainty px).
# The two near-peak markers overlap visibly and therefore receive +/-5 px;
# all other centres receive +/-3 px.
MARKERS = (
    ("curve_01", 326.4, 76.7, 3.0),
    ("curve_02", 347.5, 50.0, 5.0),
    ("curve_03", 362.0, 55.0, 5.0),
    ("curve_04", 384.4, 77.3, 3.0),
    ("curve_05", 443.0, 238.3, 3.0),
    ("curve_06", 496.8, 370.3, 3.0),
    ("curve_07", 537.3, 448.0, 3.0),
    ("curve_08", 570.9, 503.7, 3.0),
    ("curve_09", 625.3, 605.7, 3.0),
    ("curve_10", 665.9, 661.9, 3.0),
    ("curve_11", 1053.5, 517.8, 3.0),
    ("curve_12", 1182.5, 522.4, 3.0),
    ("curve_13", 1339.5, 539.4, 3.0),
)

# Publication-level MC uncertainty stated in the text near Table III/Figs. 1-3.
SOURCE_MODEL_RELATIVE_UNCERTAINTY = 0.35


def _fit(cal):
    px = np.array([p for p, _ in cal], float)
    val = np.array([v for _, v in cal], float)
    return tuple(np.polyfit(px, val, 1))


def digitized_rows():
    ax, bx = _fit(X_CAL)
    ay, by = _fit(Y_CAL)
    rows = []
    for point_id, x, y, pxerr in MARKERS:
        energy = 10.0 ** (ax * x + bx)
        sigma = 10.0 ** (ay * y + by)
        # Symmetric pixel errors become multiplicative errors on logarithmic axes.
        energy_rel = math.exp(math.log(10.0) * abs(ax) * pxerr) - 1.0
        sigma_rel = 10.0 ** (abs(ay) * pxerr) - 1.0
        rows.append(
            {
                "comparator": "published_rpp_fluka_digitized",
                "point_id": point_id,
                "energy_mev": energy,
                "sigma_cm2_per_bit": sigma,
                "x_pixel_crop": x,
                "y_pixel_crop": y,
                "pixel_center_uncertainty_px": pxerr,
                "energy_digitization_rel_error": energy_rel,
                "sigma_digitization_rel_error": sigma_rel,
                "source_model_relative_uncertainty": SOURCE_MODEL_RELATIVE_UNCERTAINTY,
                "source_doi": SOURCE_DOI,
                "source_figure": SOURCE_FIGURE,
                "source_pdf_page": SOURCE_PDF_PAGE,
                "source_printed_page": SOURCE_PRINTED_PAGE,
                "curve_semantics": "FLUKA/nested-RPP simulated proton cross section; not experimental",
            }
        )
    return rows


def write_csv(path: Path):
    rows = digitized_rows()
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            r = dict(row)
            r["energy_mev"] = f"{row['energy_mev']:.9g}"
            r["sigma_cm2_per_bit"] = f"{row['sigma_cm2_per_bit']:.9e}"
            r["energy_digitization_rel_error"] = f"{row['energy_digitization_rel_error']:.6g}"
            r["sigma_digitization_rel_error"] = f"{row['sigma_digitization_rel_error']:.6g}"
            w.writerow(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path("published_physics_sigma.csv"))
    a = ap.parse_args()
    write_csv(a.output)


if __name__ == "__main__":
    main()

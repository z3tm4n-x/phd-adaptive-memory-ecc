"""Convolve the four post-Al columns with the accepted T141 response. Python 3.11+."""

import argparse
import csv
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

from archive_check import compare_histories

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
T141 = EXP / "t141-radiation-chain"
sys.path.insert(0, str(T141))
import chain

TABLES = {
    "Л.3.1.2": "sp_x.txt", "Л.3.1.4": "sl_x.txt",
    "Л.3.2.2": "gp_x.txt", "Л.3.2.4": "gl_x.txt",
}


def read_ost(tid, rows, export):
    selected = [r for r in rows if r["table"] == tid]
    return chain.Spectrum(
        np.array([float(r["coordinate"]) for r in selected]),
        np.array([float(r["density_at_3g_cm2"]) for r in selected]),
        export.variable, "flux", "omni", "after_Al_before_BEOL", export.species, tid,
    )


def integrate(spectrum, left, right, solar):
    if not spectrum.coordinate[0] <= left <= right <= spectrum.coordinate[-1]:
        raise ValueError(f"Unsupported interval for {spectrum.source}: {left}, {right}")
    if left == right:
        return 0.0
    if spectrum.variable == "E_MeV":
        sigma = chain.proton_sigma
        knots = np.r_[chain.transport.SIGMA_E, chain.transport.sigma_module.zero_crossing_low(
            chain.transport.POINTS), chain.OLD["Epdi"], 5.0, 10.0]
    else:
        cutoff = chain.CFG["nominal_solar_LET_cutoff_MeV_cm2_mg"]

        def sigma(x):
            values = chain.OLD["sb"](x)
            return np.where(x <= cutoff, values, 0.0) if solar else values

        knots = np.r_[0.15, chain.OLD["LETpts"], cutoff]
    # Integrate on the original interpolant. Endpoints subdivide the quadrature,
    # including intervals that intersect a response breakpoint.
    return chain.fold(spectrum, lambda x: np.where((left <= x) & (x <= right), sigma(x), 0.0),
                      knots=np.r_[knots, left, right], order=chain.CFG["quadrature_order"])


def spectral_row(spectrum, common, solar):
    lo, hi = map(float, (spectrum.coordinate[0], spectrum.coordinate[-1]))
    left, right = common
    full = integrate(spectrum, lo, hi, solar)
    shared = integrate(spectrum, left, right, solar)
    lower = integrate(spectrum, lo, left, solar)
    higher = integrate(spectrum, right, hi, solar)
    assert math.isclose(full, math.fsum([lower, shared, higher]), rel_tol=1e-10)
    row = {"nodes": len(spectrum.coordinate), "native_range": [lo, hi],
           "native_s_inv": full, "common_s_inv": shared,
           "native_below_common_s_inv": lower if lo < left else None,
           "native_above_common_s_inv": higher if hi > right else None}
    if spectrum.variable == "E_MeV":
        assert left == 1.0 and hi == right
        row["H_1_to_5_MeV_s_inv"] = integrate(spectrum, left, 5, solar)
        row["H_5_to_max_MeV_s_inv"] = integrate(spectrum, 5, right, solar)
        assert math.isclose(sum((row["H_1_to_5_MeV_s_inv"], row["H_5_to_max_MeV_s_inv"])),
                            shared, rel_tol=1e-10)
    return row


def totals(rows, source, key):
    background = math.fsum(rows[t][source][key] for t in ("Л.3.2.2", "Л.3.2.4"))
    solar_h = rows["Л.3.1.2"][source][key]
    solar_let = rows["Л.3.1.4"][source][key]
    return {"b": background, "solar_H": solar_h, "solar_LET": solar_let,
            "solar_excess_peak": solar_h + solar_let, "B": math.fsum([background, solar_h, solar_let])}


def calculate():
    with (HERE / "ost_3g.csv").open(encoding="utf-8", newline="") as stream:
        source_rows = list(csv.DictReader(stream))
    manifest = json.loads((chain.LEGACY / "source_inputs.json").read_text(encoding="utf-8"))
    for name, item in manifest["main"]["members"].items():
        if chain.digest(chain.LEGACY / name) != item["sha256"]:
            raise ValueError(f"Different COSRAD main archive member: {name}")
    rows = {}
    for tid, name in TABLES.items():
        export = chain.cosrad(name, 3.0)
        norm = read_ost(tid, source_rows, export)
        common = (float(max(norm.coordinate[0], export.coordinate[0])),
                  float(min(norm.coordinate[-1], export.coordinate[-1])))
        solar = name.startswith("s")
        rows[tid] = {"export": name, "variable": export.variable, "common_range": common,
                     "ost": spectral_row(norm, common, solar),
                     "cosrad": spectral_row(export, common, solar)}

    tab = totals(rows, "ost", "native_s_inv")
    full = totals(rows, "cosrad", "native_s_inv")
    shared = totals(rows, "cosrad", "common_s_inv")
    frozen = json.loads((EXP / "c1-common-geo-20261109/coverage.json").read_text(encoding="utf-8"))
    assert chain.BITS == frozen["D"] and chain.T == frozen["T_s"]
    for key in ("b", "B"):
        assert math.isclose(full[key], float(Fraction(frozen[key + "_s_inv"])), rel_tol=2e-13)
    with (T141 / "outputs/components.csv").open(encoding="utf-8") as stream:
        accepted = {(r["phase"], r["component"]): float(r["lambda_s_inv"])
                    for r in csv.DictReader(stream) if float(r["shield_g_cm2"]) == 3}
    for phase, h, ions in (("solar", "Л.3.1.2", "Л.3.1.4"), ("background", "Л.3.2.2", "Л.3.2.4")):
        protons = rows[h]["cosrad"]
        parts = {"H_low": protons["native_below_common_s_inv"] + protons["H_1_to_5_MeV_s_inv"],
                 "H_high": protons["H_5_to_max_MeV_s_inv"], "LET_exclusive": rows[ions]["cosrad"]["native_s_inv"]}
        assert all(math.isclose(v, accepted[phase, k], rel_tol=2e-12) for k, v in parts.items())
    solar_tail = rows["Л.3.1.2"]["cosrad"]["native_below_common_s_inv"]
    galactic_tail = rows["Л.3.2.2"]["cosrad"]["native_below_common_s_inv"]
    assert tab == totals(rows, "ost", "common_s_inv")
    return {
        "base": "34a6875ee0803e46a47e520d6f4bd5e2008ecb80",
        "reference_bits": chain.BITS, "shield_g_cm2": 3, "table_rows": rows,
        "ost_tabulated": tab, "cosrad_common": shared, "cosrad_full_export": full,
        "ost_plus_cosrad_sub1_scenario": {"b": tab["b"] + galactic_tail,
            "B": tab["B"] + solar_tail + galactic_tail},
        "unknown": {"ost_sub1_solar_and_galactic_physical_spectra": None,
                    "trapped_proton_post_Al_GEO_rate_history": None, "physical_joint_quantile": None},
        "bank_inversions_per_s_conditional": {
            str(w): {source: {key: rate[key] * w / chain.CFG["words"] for key in ("b", "B")}
                     for source, rate in (("ost_tabulated", tab), ("cosrad_full_export", full))}
            for w in (32768, 44529)},
        "archive": compare_histories(EXP, tab, full, frozen),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = calculate()
    output = HERE / "result.json"
    if args.check:
        # Different supported BLAS/libm builds can differ by units in the last place.
        from verify_result import compare
        compare(data, json.loads(output.read_text(encoding="utf-8")))
        print("OK: four folds, disjoint energy bands, accepted COSRAD anchor, archive and residual budgets")
    else:
        output.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                          encoding="utf-8", newline="\n")

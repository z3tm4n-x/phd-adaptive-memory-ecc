"""Component inversion budgets for the geometric visibility test of PR 479."""

import argparse
import csv
import json
from fractions import Fraction as F
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent
BANDS = ("H_low", "H_high", "LET_exclusive")
PHASES = ("background", "solar")
PROJECTIONS = ("low", "pin")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def component_rates():
    folder = EXPERIMENTS / "t141-radiation-chain" / "outputs"
    rates = {phase: {} for phase in PHASES}
    with (folder / "components.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if F(row["shield_g_cm2"]) != 3:
                continue
            phase, band = row["phase"], row["component"]
            if band in rates[phase] or band not in BANDS:
                raise ValueError(f"Unexpected component {phase}/{band}")
            rates[phase][band] = F(row["lambda_s_inv"])
    for phase in PHASES:
        assert set(rates[phase]) == set(BANDS) and min(rates[phase].values()) > 0
    rates["storm_peak"] = {band: sum(rates[p][band] for p in PHASES) for band in BANDS}
    contract = read_json(folder / "contract.json")
    scenario, = [s for s in contract["scenarios"] if s["shield_g_cm2"] == 3
                 and s["scenario"] == "conservative_shape1_geometry1_exclusive1"]
    for phase, key in (("background", "background_s_inv"), ("storm_peak", "peak_upper_s_inv")):
        assert abs(sum(rates[phase].values()) - F(str(scenario[key]))) < F(1, 10**15)
    return rates, contract["words"]


def ion_projections():
    data = read_json(EXPERIMENTS / "t186-heavy-ion-transfer-1-5" / "result.json")
    assert len(data["series"]) == 14
    result = {}
    for address in PROJECTIONS:
        row = data["total"][address]
        for key in ("unique_cells", "cells_in_large", "two_cell_same_word", "singles", "doubles"):
            assert sum(s[address][key] for s in data["series"].values()) == row[key]
        total = row["unique_cells"]
        assert total == row["singles"] + 2 * row["doubles"] + row["cells_in_large"]
        assert row["two_cell_same_word"] <= row["doubles"]
        result[address] = {
            "cells": total,
            "large": F(row["cells_in_large"], total),
            "small_direct": F(2 * row["two_cell_same_word"], total),
        }
    return result


def admissible_fraction(room, charge):
    """Cap a one-parameter allowance at one. None means even zero fails."""
    if room < 0:
        return None
    return min(F(1), room / charge) if charge else F(1)


def budget(shares, projection, limit):
    ion = shares["LET_exclusive"]
    hydrogen = shares["H_low"] + shares["H_high"]
    q = projection["large"] + projection["small_direct"]
    large = ion * projection["large"]
    direct = ion * projection["small_direct"]
    known = large + direct
    room = limit - known
    assert 0 <= known <= ion and ion + hydrogen == 1
    row = {
        "ion_large_share_of_total": large,
        "ion_small_direct_share_of_total": direct,
        "room_after_large": limit - large,
        "ion_large_plus_small_direct_share_of_total": known,
        "room_after_large_and_small_direct": room,
        "max_bad_fraction_of_all_H_if_only_extra": admissible_fraction(room, hydrogen),
        "max_unclassified_fraction_of_true_ions_if_H_safe": admissible_fraction(room, ion * (1-q)),
        "max_unclassified_fraction_of_true_total_if_rest_keeps_table_mix": admissible_fraction(room, 1-known),
    }
    row["max_bad_fraction_within_one_H_band_if_only_extra"] = {
        band: admissible_fraction(room, shares[band]) for band in ("H_low", "H_high")
    }
    return row


def first_solar_weight(background, solar, limit):
    """First admissible solar share for these inputs; includes the all-background endpoint."""
    if background <= limit and solar <= limit:
        return F(0)
    if solar > limit or background <= limit:
        raise ValueError("Expected an all-admissible or decreasing crossing for these projections")
    return (background - limit) / (background - solar)


def calculate():
    rates, reference_words = component_rates()
    projections = ion_projections()
    theory = read_json(EXPERIMENTS / "t196-small-ion-visibility-20261113" / "result.json")
    words = theory["W"]
    geo = theory["domains"]["geo"]
    limit = F(geo["geometric_max_large_plus_small_direct_inversion_share"])
    assert limit == 1 - F(1, words) - 2 * F(geo["required_visible_parents_per_inversion"])
    assert limit == F(8715, 32768) and F(words, reference_words) == F(1, 16)
    totals = {phase: sum(by_band.values()) for phase, by_band in rates.items()}
    phases = {}
    for phase, by_band in rates.items():
        shares = {band: rate / totals[phase] for band, rate in by_band.items()}
        ion = shares["LET_exclusive"]
        phases[phase] = {
            "reference_s_inv": totals[phase],
            "bank_s_inv": totals[phase] * F(words, reference_words),
            "component_fractions": shares,
            "max_bad_fraction_of_ions_if_H_safe": admissible_fraction(limit, ion),
            "max_bad_fraction_of_ions_if_all_H_bad": admissible_fraction(limit - (1 - ion), ion),
            "room_if_all_ions_bad": limit - ion,
            "max_bad_H_if_all_ions_bad": admissible_fraction(limit - ion, 1 - ion),
            "by_address": {key: budget(shares, p, limit) for key, p in projections.items()},
        }
    peak_weight = totals["solar"] / totals["storm_peak"]
    mixed = {}
    for key, projection in projections.items():
        q = projection["large"] + projection["small_direct"]
        bad_key = "ion_large_plus_small_direct_share_of_total"
        background, solar, peak = [phases[p]["by_address"][key][bad_key] for p in (*PHASES, "storm_peak")]
        weight = first_solar_weight(background, solar, limit)
        mixed[key] = {
            "max_ion_fraction_if_H_safe_and_projected_ion_shares_hold": admissible_fraction(limit, q),
            "first_admissible_solar_exposure_fraction_if_no_extra": weight,
            "first_admissible_solar_to_background_exposure_ratio_if_no_extra": weight / (1 - weight),
        }
        assert peak == (1 - peak_weight) * background + peak_weight * solar
        assert (1 - weight) * background + weight * solar <= limit
        if weight:
            assert (1 - weight) * background + weight * solar == limit
        for phase in phases.values():
            row = phase["by_address"][key]
            hydrogen = 1 - phase["component_fractions"]["LET_exclusive"]
            h = row["max_bad_fraction_of_all_H_if_only_extra"]
            u = row["max_unclassified_fraction_of_true_total_if_rest_keeps_table_mix"]
            bad = row[bad_key]
            if u is None:
                assert h is None and bad > limit
            else:
                assert (1 - u) * bad + u == limit
                assert bad + h * hydrogen <= limit
                assert h == 1 or bad + h * hydrogen == limit
    return {"fraction_limit": limit, "ion_projection": projections, "phases": phases,
            "solar_fraction_of_peak_exposure": peak_weight, "mixed_windows": mixed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare with the committed exact fractions")
    args = parser.parse_args()
    result = calculate()
    path = HERE / "result.json"
    encoded = json.dumps(result, default=str, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if encoded != path.read_text(encoding="utf-8"):
            raise SystemExit("result.json differs from the calculation")
        print("OK: six T141 components, both 14-run projections, four rows and mixed windows")
    else:
        path.write_text(encoded, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

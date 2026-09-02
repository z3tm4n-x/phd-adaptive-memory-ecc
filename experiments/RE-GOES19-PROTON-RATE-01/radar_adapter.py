"""Thin adapter around pinned RADAR proton-Al transport.

This module imports RADAR at runtime from a separately checked-out repository.
It does not vendor RADAR code or data. It only normalizes representational
TENDL duplicate-energy rows that the pinned CSV loader cannot ingest and builds
linear response matrices by calling pinned RADAR functions.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

RADAR_SHA = "b032505d4d1b15403b8ad06aef578339f6d1c6b4"
SHIELDS_MM = (0.0, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0)
AL_DENSITY = 2.70


def _git_sha(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def _normalize_rows(src: Path, dst: Path, key_cols: tuple[str, ...], value_cols: tuple[str, ...], extend_mt5_zero: bool = False):
    """Normalize duplicate interpolation coordinates without altering source values.

    Exact duplicates are deduplicated. If equal coordinates carry conflicting
    values, all but the final row are moved to the immediately preceding float,
    preserving an explicit left/right discontinuity while retaining both values.
    """
    with src.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys())
    groups = {}
    for i, row in enumerate(rows):
        key = tuple(row[c] for c in key_cols)
        groups.setdefault(key, []).append((i, row))
    keep = []
    actions = []
    for key, items in groups.items():
        if len(items) == 1:
            keep.append(items[0][1])
            continue
        vals = [tuple(row[c] for c in value_cols) for _, row in items]
        if len(set(vals)) == 1:
            keep.append(items[-1][1])
            actions.append({"kind": "exact_duplicate_dedup", "key": key, "n": len(items)})
        else:
            for j, (_, row0) in enumerate(items):
                row = dict(row0)
                if j < len(items) - 1:
                    c = key_cols[-1]
                    x = float(row[c])
                    row[c] = repr(float(np.nextafter(x, -np.inf)))
                keep.append(row)
            actions.append({"kind": "conflicting_duplicate_left_limit", "key": key, "values": vals})

    if extend_mt5_zero:
        mt5 = [row for row in keep if int(row["mt"]) == 5]
        minr = min(mt5, key=lambda row: float(row["energy_mev"]))
        if float(minr["energy_mev"]) > 0.1 and float(minr["sigma_barn"]) == 0.0:
            row = dict(minr)
            row["energy_mev"] = "0.1"
            keep.append(row)
            actions.append({"kind": "zero_threshold_extension", "mt": 5, "from_mev": float(minr["energy_mev"]), "to_mev": 0.1, "sigma_barn": 0.0})
        maxr = max(mt5, key=lambda row: float(row["energy_mev"]))
        if float(maxr["energy_mev"]) < 390.0:
            # The pinned compact TENDL file ends at 200 MeV. Keep its final supported
            # value at 200 MeV, then set only the nonelastic-survival correction to
            # zero immediately above support. CSDA primary transport remains active.
            emax = float(maxr["energy_mev"])
            row0 = dict(maxr)
            row0["energy_mev"] = repr(float(np.nextafter(emax, np.inf)))
            row0["sigma_barn"] = "0.0"
            row1 = dict(maxr)
            row1["energy_mev"] = "390.0"
            row1["sigma_barn"] = "0.0"
            keep.extend([row0, row1])
            actions.append({"kind": "zero_nonelastic_above_tendl_support", "mt": 5, "support_max_mev": emax, "extended_to_mev": 390.0})

    def sort_key(row):
        return tuple(int(row[c]) if c in {"mt", "product_index"} else float(row[c]) for c in key_cols)

    keep.sort(key=sort_key)
    with dst.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(keep)
    return actions


def _load_radar(root: Path):
    sys.path.insert(0, str(root / "src"))
    from radar.core.spectra import Spectrum1D
    from radar.core.types import Particle, RadiationSource, SpectrumQuantity
    from radar.core.units import Unit
    from radar.shielding.proton_al import ProtonAlRangeEnergyTable, load_proton_al_range_energy_table
    from radar.shielding.proton_al_survival import apply_proton_nonelastic_survival_to_primary_spectrum, load_al27_nonelastic_cross_section_table
    from radar.shielding.proton_al_secondary import calculate_secondary_proton_spectrum_through_al, load_secondary_proton_kernel
    return locals()


def _make_spectrum(rad, energy, y):
    return rad["Spectrum1D"](
        x=tuple(map(float, energy)),
        y=tuple(map(float, y)),
        x_unit=rad["Unit"].MEV,
        y_unit=rad["Unit"].DIFFERENTIAL_FLUX,
        quantity=rad["SpectrumQuantity"].MEAN_DIFFERENTIAL_FLUX,
        particle=rad["Particle"].PROTON,
        source=rad["RadiationSource"].SEP,
        model="RE-GOES19-PROTON-RATE-01-adapter",
    )


def _grid(n: int) -> np.ndarray:
    # Covers the measured SGPS differential range after correction; P11 >500 MeV is
    # handled separately as an energetic-coverage bound, not assigned a spectral shape.
    return np.geomspace(0.11, 390.0, n)


def _extend_stopping_table_to_zero_range(rad, base):
    """Add the physical R->0 endpoint needed by the pinned secondary integrator.

    The pinned table begins at 0.1 MeV with a small positive range. During midpoint
    depth quadrature a nearly stopped proton can have 0 < residual_range < R(0.1 MeV),
    for which the pinned strict inverse interpolator raises. We prepend an asymptotic
    point at tiny positive energy and exactly zero range. No tabulated point is changed.
    Secondary production at these sub-tabular energies remains zero because the TENDL
    kernel itself is zero outside support.
    """
    tiny_energy = 1.0e-9
    return rad["ProtonAlRangeEnergyTable"](
        energy_mev=(tiny_energy,) + tuple(base.energy_mev),
        range_g_cm2=(0.0,) + tuple(base.range_g_cm2),
        stopping_mev_cm2_g=(base.stopping_mev_cm2_g[0],) + tuple(base.stopping_mev_cm2_g),
    )


def _load_normalized_physics(root: Path, temp: Path):
    rad = _load_radar(root)
    data = root / "src/radar/data/normative"
    base_stopping = rad["load_proton_al_range_energy_table"](data / "stopping/proton_al_range.csv")
    stopping = _extend_stopping_table_to_zero_range(rad, base_stopping)
    xs = temp / "xs.csv"
    yy = temp / "yield.csv"
    pp = temp / "pdf.csv"
    actions = [{"kind": "stopping_zero_range_endpoint", "energy_mev": 1.0e-9, "range_g_cm2": 0.0, "original_first_energy_mev": float(base_stopping.energy_mev[0]), "original_first_range_g_cm2": float(base_stopping.range_g_cm2[0])}]
    actions += _normalize_rows(data / "tendl/p_al27_mf3_xs.csv", xs, ("mt", "energy_mev"), ("sigma_barn",), extend_mt5_zero=True)
    actions += _normalize_rows(data / "tendl/p_al27_mf6_proton_yield.csv", yy, ("mt", "product_index", "incident_energy_mev"), ("yield",))
    actions += _normalize_rows(data / "tendl/p_al27_mf6_proton_pdf.csv", pp, ("mt", "product_index", "incident_energy_mev", "emitted_energy_mev"), ("pdf_per_mev",))
    nonelastic = rad["load_al27_nonelastic_cross_section_table"](xs, mt=5)
    kernel = rad["load_secondary_proton_kernel"](xs_path=xs, yield_path=yy, pdf_path=pp)
    return rad, stopping, nonelastic, kernel, actions


def build_matrices(root: Path, n: int, depth_steps: int, survival_steps: int):
    with tempfile.TemporaryDirectory() as td:
        rad, stopping, nonelastic, kernel, actions = _load_normalized_physics(root, Path(td))
        energy = _grid(n)
        identity = np.eye(n)
        primary = np.zeros((len(SHIELDS_MM), n, n))
        secondary = np.zeros_like(primary)
        for di, mm in enumerate(SHIELDS_MM):
            thickness_g_cm2 = mm / 10.0 * AL_DENSITY
            for j in range(n):
                spectrum = _make_spectrum(rad, energy, identity[j])
                p = rad["apply_proton_nonelastic_survival_to_primary_spectrum"](
                    spectrum=spectrum,
                    stopping_table=stopping,
                    cross_section_table=nonelastic,
                    thickness_g_cm2=thickness_g_cm2,
                    integration_steps=survival_steps,
                )
                s = rad["calculate_secondary_proton_spectrum_through_al"](
                    incident_spectrum=spectrum,
                    stopping_table=stopping,
                    kernel=kernel,
                    thickness_g_cm2=thickness_g_cm2,
                    depth_steps=depth_steps,
                )
                primary[di, :, j] = p.y
                secondary[di, :, j] = s.y
        return energy, primary, secondary, actions


def representative_validation(root: Path, sigma_csv: Path):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from sigma_model import load_experimental_points, sigma_hat

    points = load_experimental_points(sigma_csv)
    cases = []
    matrices = {}
    actions = []
    for n in (72, 96):
        energy, primary, secondary, actions = build_matrices(root, n, depth_steps=24, survival_steps=64)
        matrices[n] = (energy, primary, secondary)

    ef, pf, sf = matrices[96]
    sigf = sigma_hat(ef, points, "main_loglog")
    for power in (0.0, 1.5, 3.0):
        jf = (ef / 10.0) ** (-power) * np.exp(-ef / 350.0)
        ec, pc, sc = matrices[72]
        jc = (ec / 10.0) ** (-power) * np.exp(-ec / 350.0)
        for di, mm in enumerate(SHIELDS_MM):
            yf = (pf[di] + sf[di]) @ jf
            yc = (pc[di] + sc[di]) @ jc
            yc_interp = np.interp(np.log(ef), np.log(ec), yc, left=0.0, right=0.0)
            lf = float(np.trapezoid(yf * sigf, ef))
            lc = float(np.trapezoid(yc_interp * sigf, ef))
            cases.append({"kind": "energy_grid", "power": power, "shield_mm": mm, "coarse_n": 72, "fine_n": 96, "relative_change": abs(lf - lc) / max(abs(lf), 1e-300)})

    with tempfile.TemporaryDirectory() as td:
        rad, stopping, nonelastic, kernel, _ = _load_normalized_physics(root, Path(td))
        incident = (ef / 10.0) ** (-1.5) * np.exp(-ef / 350.0)
        spectrum = _make_spectrum(rad, ef, incident)
        for mm in SHIELDS_MM[1:]:
            thickness_g_cm2 = mm / 10.0 * AL_DENSITY
            p = rad["apply_proton_nonelastic_survival_to_primary_spectrum"](
                spectrum=spectrum,
                stopping_table=stopping,
                cross_section_table=nonelastic,
                thickness_g_cm2=thickness_g_cm2,
                integration_steps=64,
            )
            values = []
            for depth_steps in (24, 48):
                s = rad["calculate_secondary_proton_spectrum_through_al"](
                    incident_spectrum=spectrum,
                    stopping_table=stopping,
                    kernel=kernel,
                    thickness_g_cm2=thickness_g_cm2,
                    depth_steps=depth_steps,
                )
                y = np.asarray(p.y) + np.asarray(s.y)
                values.append(float(np.trapezoid(y * sigf, ef)))
            cases.append({"kind": "secondary_depth", "shield_mm": mm, "coarse_steps": 24, "fine_steps": 48, "relative_change": abs(values[1] - values[0]) / max(abs(values[1]), 1e-300)})

    d0_primary_err = float(np.max(np.abs(pf[0] - np.eye(len(ef)))))
    d0_secondary_max = float(np.max(np.abs(sf[0])))
    return matrices[96], actions, cases, d0_primary_err, d0_secondary_max


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--radar-root", type=Path, required=True)
    parser.add_argument("--sigma-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    sha = _git_sha(args.radar_root)
    if sha != RADAR_SHA:
        raise SystemExit(f"RADAR SHA mismatch: {sha}")

    (_, _, _), _, cases, d0p, d0s = representative_validation(args.radar_root, args.sigma_csv)
    energy, primary, secondary, actions = build_matrices(args.radar_root, 96, depth_steps=48, survival_steps=128)
    np.savez_compressed(
        args.out / "radar_transport.npz",
        energy_mev=energy,
        shield_mm=np.array(SHIELDS_MM),
        primary=primary,
        secondary=secondary,
    )
    report = {
        "radar_sha": sha,
        "grid_points": len(energy),
        "energy_min_mev": float(energy[0]),
        "energy_max_mev": float(energy[-1]),
        "production_depth_steps": 48,
        "production_survival_steps": 128,
        "d0_primary_identity_max_abs": d0p,
        "d0_secondary_max_abs": d0s,
        "secondary_nonnegative": bool(np.all(secondary >= -1e-15)),
        "primary_nonnegative": bool(np.all(primary >= -1e-15)),
        "normalization_actions": actions,
        "convergence_cases": cases,
        "max_energy_grid_relative_change": max(x["relative_change"] for x in cases if x["kind"] == "energy_grid"),
        "max_secondary_depth_relative_change": max(x["relative_change"] for x in cases if x["kind"] == "secondary_depth"),
        "high_energy_nuclear_domain_note": "TENDL compact nonelastic/secondary data end at 200 MeV; production adapter leaves CSDA active and applies no nonelastic correction above support. Contribution is quantified separately in task validation.",
    }
    (args.out / "radar_validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

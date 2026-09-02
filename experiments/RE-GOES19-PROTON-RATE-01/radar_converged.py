"""Direct-convolution convergence selector for the pinned RADAR adapter.

The transport operator is linear.  Comparing response matrices assembled on
incommensurate grids adds an avoidable basis/interpolation error to the
physical quadrature test.  This module therefore selects the production grid
from direct RADAR transports of representative spectra and then delegates the
actual production-matrix build to ``radar_adapter.main``.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import radar_adapter as r
from sigma_model import load_experimental_points, sigma_hat

GRID_CANDIDATES = (96, 144, 192, 256, 320, 384)
CONVERGENCE_LIMIT = 0.005
POWERS = (0.0, 1.5, 3.0)


def _direct_rates(root: Path, n: int, points, *, depth_steps: int, survival_steps: int):
    energy = r._grid(n)
    sigma = sigma_hat(energy, points, "main_loglog")
    rates: dict[tuple[float, float], float] = {}
    with tempfile.TemporaryDirectory() as td:
        rad, stopping, nonelastic, kernel, actions = r._prepare_physics(root, Path(td))
        for power in POWERS:
            incident = (energy / 10.0) ** (-power) * np.exp(-energy / 350.0)
            spectrum = r._make_spectrum(rad, energy, incident)
            for mm in r.SHIELDS_MM:
                thickness = mm / 10.0 * r.AL_DENSITY
                primary = rad["apply_proton_nonelastic_survival_to_primary_spectrum"](
                    spectrum=spectrum,
                    stopping_table=stopping,
                    cross_section_table=nonelastic,
                    thickness_g_cm2=thickness,
                    integration_steps=survival_steps,
                )
                secondary = rad["calculate_secondary_proton_spectrum_through_al"](
                    incident_spectrum=spectrum,
                    stopping_table=stopping,
                    kernel=kernel,
                    thickness_g_cm2=thickness,
                    depth_steps=depth_steps,
                )
                y = np.asarray(primary.y, dtype=float) + np.asarray(secondary.y, dtype=float)
                rates[(power, mm)] = float(np.trapezoid(y * sigma, energy))
    return energy, rates, actions


def _compare_rates(coarse_n: int, coarse, fine_n: int, fine):
    cases = []
    for power in POWERS:
        for mm in r.SHIELDS_MM:
            a = coarse[(power, mm)]
            b = fine[(power, mm)]
            rel = abs(b - a) / max(abs(b), 1.0e-300)
            cases.append(
                {
                    "kind": "energy_grid_direct",
                    "power": power,
                    "shield_mm": mm,
                    "coarse_n": coarse_n,
                    "fine_n": fine_n,
                    "relative_change": rel,
                }
            )
    return cases


def validate_and_choose_grid(root: Path, sigma_csv: Path):
    points = load_experimental_points(sigma_csv)
    grid_cases = []
    previous_n = None
    previous_rates = None
    selected_n = None
    actions = None

    for n in GRID_CANDIDATES:
        _, rates, actions = _direct_rates(root, n, points, depth_steps=24, survival_steps=64)
        if previous_rates is not None:
            pair = _compare_rates(previous_n, previous_rates, n, rates)
            grid_cases.extend(pair)
            if max(x["relative_change"] for x in pair) <= CONVERGENCE_LIMIT:
                selected_n = n
                break
        previous_n = n
        previous_rates = rates

    if selected_n is None:
        raise RuntimeError(
            f"direct energy-grid convergence did not reach {CONVERGENCE_LIMIT:.3%} "
            f"by n={GRID_CANDIDATES[-1]}"
        )

    # Independent depth-quadrature check at the selected energy grid.
    energy = r._grid(selected_n)
    sigma = sigma_hat(energy, points, "main_loglog")
    depth_cases = []
    with tempfile.TemporaryDirectory() as td:
        rad, stopping, nonelastic, kernel, _ = r._prepare_physics(root, Path(td))
        incident = (energy / 10.0) ** (-1.5) * np.exp(-energy / 350.0)
        spectrum = r._make_spectrum(rad, energy, incident)
        for mm in r.SHIELDS_MM[1:]:
            thickness = mm / 10.0 * r.AL_DENSITY
            primary = rad["apply_proton_nonelastic_survival_to_primary_spectrum"](
                spectrum=spectrum,
                stopping_table=stopping,
                cross_section_table=nonelastic,
                thickness_g_cm2=thickness,
                integration_steps=64,
            )
            vals = []
            for steps in (24, 48):
                secondary = rad["calculate_secondary_proton_spectrum_through_al"](
                    incident_spectrum=spectrum,
                    stopping_table=stopping,
                    kernel=kernel,
                    thickness_g_cm2=thickness,
                    depth_steps=steps,
                )
                y = np.asarray(primary.y, dtype=float) + np.asarray(secondary.y, dtype=float)
                vals.append(float(np.trapezoid(y * sigma, energy)))
            depth_cases.append(
                {
                    "kind": "secondary_depth",
                    "shield_mm": mm,
                    "coarse_steps": 24,
                    "fine_steps": 48,
                    "relative_change": abs(vals[1] - vals[0]) / max(abs(vals[1]), 1.0e-300),
                }
            )

    if max(x["relative_change"] for x in depth_cases) > CONVERGENCE_LIMIT:
        raise RuntimeError(
            "secondary-depth convergence did not reach "
            f"{CONVERGENCE_LIMIT:.3%} at n={selected_n}"
        )

    return selected_n, grid_cases, depth_cases, actions


def main():
    r.validate_and_choose_grid = validate_and_choose_grid
    r.main()


if __name__ == "__main__":
    main()

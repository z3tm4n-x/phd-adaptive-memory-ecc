"""Conditional GOST R 25645.165-2025 proton spectra at Pi=0.1.

Published equations (1)--(4), printed p. 3; selected cells of tables 1--8,
printed pp. 4--7. The log2(nbar) interpolation is our declared numerical
choice under section 5.9, not a uniquely prescribed interpolation rule.
No S2 quantile, joint exceedance guarantee, or calendar forecast is inferred.
"""
import csv
import math
from pathlib import Path

import numpy as np
from scipy.integrate import quad

from transport import BITS


HERE = Path(__file__).resolve().parent
COEFFICIENTS = HERE / "inputs/gost_selected_coefficients.csv"
PARAMETERS = ("log10_c", "break_energy_mev", "gamma1", "gamma2")
PRODUCTS = ("fluence", "peak_flux")
PROBABILITY = 0.1
REST_ENERGY_MEV = 938.0


def expected_event_count(monthly_wolf, version="1.0"):
    """Equations (3)/(4); input is the monthly smoothed Wolf-number series.

    The event population has omnidirectional Phi(>=30 MeV)>=1e5 cm^-2.
    This function neither forecasts Wolf numbers nor chooses a mission epoch.
    """
    coefficients = {"1.0": 0.0130, "2.0": 0.00925}
    if version not in coefficients:
        raise ValueError("Wolf version must be '1.0' or '2.0'")
    values = np.asarray(monthly_wolf, dtype=float)
    if values.ndim != 1 or not values.size or not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("A nonempty finite nonnegative monthly Wolf series is required")
    return float(coefficients[version] * math.fsum(values.tolist()))


def spectral_parameters(nbar, product):
    """Return the four interpolated parameters for 64 <= nbar <= 128."""
    nbar = float(nbar)
    if product not in PRODUCTS:
        raise ValueError("Product must be 'fluence' or 'peak_flux'")
    if not math.isfinite(nbar) or not 64 <= nbar <= 128:
        raise ValueError("Selected verified cells cover only 64 <= nbar <= 128")
    with COEFFICIENTS.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    values = {}
    for row in rows:
        if float(row["probability"]) != PROBABILITY:
            raise ValueError("Only the declared Pi=0.1 coefficient slice is supported")
        key = (row["product"], row["parameter"], int(row["n"]))
        if key in values:
            raise ValueError("Duplicate coefficient cell")
        values[key] = float(row["value"])
    required = {(p, k, n) for p in PRODUCTS for k in PARAMETERS for n in (64, 128)}
    if set(values) != required or not all(math.isfinite(x) for x in values.values()):
        raise ValueError("Incomplete or invalid selected coefficient cells")
    fraction = math.log2(nbar / 64)
    return {key: float(values[product, key, 64] + fraction *
                       (values[product, key, 128] - values[product, key, 64]))
            for key in PARAMETERS}


def spectrum(energy_mev, nbar, product):
    """Differential incident spectrum, Eq. (1), valid here for E >= 1 MeV.

    Fluence: cm^-2 MeV^-1 (already omnidirectional).
    Peak flux: cm^-2 s^-1 sr^-1 MeV^-1 (directional intensity).
    """
    e = np.asarray(energy_mev, dtype=float)
    if not np.isfinite(e).all() or np.any(e < 1):
        raise ValueError("GOST proton spectrum requires finite energy >=1 MeV")
    par = spectral_parameters(nbar, product)
    ek = par["break_energy_mev"]
    c = 10 ** par["log10_c"]
    # Squared momentum ratio avoids a redundant square root and retains -2*g2.
    value = c * np.where(e < ek, (e / ek) ** -par["gamma1"],
                        (e * (e + 2 * REST_ENERGY_MEV) /
                         (ek * (ek + 2 * REST_ENERGY_MEV))) ** -par["gamma2"])
    return float(value) if value.ndim == 0 else value


def _integral_above(threshold, par):
    """Separate scalar adaptive quadrature, no Response energy-grid cutoff.

    The scalar expression is independent of the vectorized spectrum evaluator,
    but shares the four source parameters. Its quadrature error is diagnostic,
    not a rigorous rounding/error certificate.
    """
    c, ek = 10 ** par["log10_c"], par["break_energy_mev"]
    p_k = math.sqrt(ek * (ek + 2 * REST_ENERGY_MEV))

    def scalar(e):
        if e < ek:
            return c * math.exp(-par["gamma1"] * math.log(e / ek))
        momentum = math.sqrt(e * (e + 2 * REST_ENERGY_MEV))
        return c * math.exp(-2 * par["gamma2"] * math.log(momentum / p_k))

    cuts = [float(threshold)]
    if threshold < ek:
        cuts.append(ek)
    cuts.append(math.inf)
    results = [quad(scalar, a, b, epsabs=1e-5, epsrel=2e-12, limit=200)
               for a, b in zip(cuts[:-1], cuts[1:])]
    return float(math.fsum(x[0] for x in results)), float(math.fsum(x[1] for x in results))


def summary(response, nbar):
    """Convolve GOST spectra with supplied sigma*dE quadratures.

    A response quadrature contains incident energies and weights already
    including the transported per-bit cross-section and dE, but neither the
    memory bit count nor a solid-angle factor. No response-tail extrapolation
    is invented here: the full spectrum integrals are separately to infinity.
    """
    parameters = {p: spectral_parameters(nbar, p) for p in PRODUCTS}
    integral = {p: {} for p in PRODUCTS}
    for product in PRODUCTS:
        for threshold in (10, 30, 60, 100):
            value, error = _integral_above(threshold, parameters[product])
            integral[product][str(threshold)] = {
                "value": value, "quad_estimated_absolute_error": error}
    fluence30 = integral["fluence"]["30"]["value"]
    variants = {}
    for name, (incident, weights) in response.quadratures.items():
        e, w = np.asarray(incident, dtype=float), np.asarray(weights, dtype=float)
        if (e.ndim != 1 or not e.size or e.shape != w.shape or not np.isfinite(w).all()
                or np.any(w < 0)):
            raise ValueError("Response needs equal nonempty 1D energies and nonnegative finite weights")
        f = spectrum(e, nbar, "peak_flux")
        phi = spectrum(e, nbar, "fluence")
        peak = float(4 * math.pi * BITS * np.dot(w, f))
        total = float(BITS * np.dot(w, phi))
        if not math.isfinite(peak) or not math.isfinite(total):
            raise ValueError("Nonfinite GOST convolution")
        variants[str(name)] = {
            "peak_lambda_s-1": peak,
            "N_expected_upsets": total,
            "fluence_gt30_omni_cm-2": fluence30,
            "incident_quadrature_min_MeV": float(e.min()),
            "incident_quadrature_max_MeV": float(e.max()),
            "value_type": "calculated_conditional_scenario",
        }
    return {
        "status": "conditional_mean_cycle_scenario_not_calendar_forecast",
        "mission_mean_events": float(nbar),
        "exceedance_probability": PROBABILITY,
        "interpolation": "linear coefficients in log2(nbar); declared numerical choice under section 5.9",
        "parameters": parameters,
        "normalization": {
            "protected_bits": int(BITS),
            "fluence_solid_angle_factor": 1.0,
            "peak_flux_solid_angle_factor": float(4 * math.pi),
            "fluence_units": "cm-2 MeV-1",
            "peak_flux_units": "cm-2 s-1 sr-1 MeV-1",
        },
        "incident_integrals_to_infinity": integral,
        "integral_units": {"fluence": "cm-2", "peak_flux": "cm-2 s-1 sr-1"},
        "gost": variants,
        "limitations": [
            "Separate marginal peak and fluence levels do not establish a joint S2 quantile",
            "Response convolution uses only supplied finite incident-energy quadrature support",
            "Quadrature error estimates are diagnostics, not rigorous interval certificates",
            "The chosen mean-cycle input is not a forecast under GOST 25645.302",
        ],
    }

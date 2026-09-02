"""Compute 5-minute CY62167GE30 proton-induced bit-flip rates.

The pipeline preserves East/West chains separately, applies the explicit 4pi
isotropy-equivalent conversion immediately before transport, never fills
missing timestamps from neighboring observations, and distinguishes measured
GOES support from explicit low-energy spectral extrapolation scenarios.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from goes19_adapter import load_directory, reconstruct_on_grid
from sigma_model import MODEL_NAMES, load_experimental_points, sigma_hat, zero_crossing_low

N_BITS = 16_777_216
FOUR_PI = 4.0 * math.pi
SHIELDS_MM = (0.0, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0)
SIGMA_SENSITIVITY_MODELS = ("linear_energy", "gap_linear_5_40", "low_hold")
LOW_EXTRAP_GAMMAS = (0.0, 2.0, 4.0)
LOW_EXTRAP_REFERENCE_GAMMA = 2.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def trap_weights(x):
    x = np.asarray(x, float)
    w = np.zeros_like(x)
    w[0] = (x[1] - x[0]) / 2
    w[-1] = (x[-1] - x[-2]) / 2
    w[1:-1] = (x[2:] - x[:-2]) / 2
    return w


def reconstruct_goes(goes, grid):
    """Reconstruct only inside the measured differential-channel support."""
    T = len(goes.times)
    n = len(grid)
    J = np.full((T, 2, n), np.nan)
    U = np.full_like(J, np.nan)
    for d in range(2):
        lo = float(goes.lower[d, 0])
        hi = float(goes.upper[d, -1])
        for t in range(T):
            if not goes.valid[t, d]:
                continue
            jr = reconstruct_on_grid(goes.effective[d], goes.flux[t, d], lo, hi, grid)
            ur = reconstruct_on_grid(goes.effective[d], goes.uncert[t, d], lo, hi, grid)
            # Unsupported energies are zero only inside the transport call. Their
            # absence is explicitly tracked and never described as measured zero.
            J[t, d] = np.where(np.isfinite(jr), jr, 0.0)
            U[t, d] = np.where(np.isfinite(ur), ur, 0.0)
    return J, U


def low_energy_extension(goes, grid, e_zero: float, gamma: float):
    """Power-law extension anchored at the lower P1 support edge.

    J(E) = J_P1 * (E / E_P1,low)^(-gamma), E_zero <= E < E_P1,low.
    No claim is made that gamma is measured. gamma={0,2,4} are transparent
    sensitivity scenarios; gamma=2 is the reference reporting scenario.
    """
    grid = np.asarray(grid, float)
    T = len(goes.times)
    out = np.zeros((T, 2, len(grid)), float)
    unc = np.zeros_like(out)
    for d in range(2):
        lo = float(goes.lower[d, 0])
        mask = (grid >= e_zero) & (grid < lo)
        if not np.any(mask):
            continue
        shape = (grid[mask] / lo) ** (-gamma)
        valid = goes.valid[:, d] & np.isfinite(goes.flux[:, d, 0])
        out[np.ix_(valid, [d], mask)] = goes.flux[valid, d, 0][:, None, None] * shape[None, None, :]
        uvalid = valid & np.isfinite(goes.uncert[:, d, 0])
        unc[np.ix_(uvalid, [d], mask)] = goes.uncert[uvalid, d, 0][:, None, None] * shape[None, None, :]
    return out, unc


def _p11_rate(goes, sigma_high):
    # P11 is integral intensity >500 MeV. Above 186 MeV sigma is explicitly
    # held constant, so the rate can be evaluated without inventing a spectrum.
    return N_BITS * FOUR_PI * goes.p11 * sigma_high


def _p11_uncert_rate(goes, sigma_high):
    return N_BITS * FOUR_PI * goes.p11_uncert * sigma_high


def _central(a):
    return np.where(np.all(np.isfinite(a), axis=1), np.mean(a, axis=1), np.nan)


def _transport_component(inp4, primary, secondary, w):
    po = inp4 @ primary.T
    so = inp4 @ secondary.T
    return po, so, N_BITS * (po @ w), N_BITS * (so @ w)


def _raw_low_slope_diagnostic(goes):
    """Uncapped local P1/P2A spectral-index diagnostic; never used as model."""
    out = {}
    for d, name in enumerate(("E", "W")):
        e1 = float(goes.effective[d, 0])
        e2 = float(goes.effective[d, 1])
        j1 = goes.flux[:, d, 0]
        j2 = goes.flux[:, d, 1]
        m = goes.valid[:, d] & np.isfinite(j1) & np.isfinite(j2) & (j1 > 0) & (j2 > 0)
        gamma = -np.log(j2[m] / j1[m]) / math.log(e2 / e1)
        out[name] = {
            "n": int(gamma.size),
            "p05": float(np.quantile(gamma, 0.05)),
            "median": float(np.quantile(gamma, 0.50)),
            "p95": float(np.quantile(gamma, 0.95)),
            "note": "diagnostic only; not used because provisional low-energy channel ratios are too unstable/background-sensitive for unconstrained extrapolation",
        }
    return out


def _solve_high_gamma(j390: float, p11: float) -> float | None:
    """Solve a power-law index from P10 differential and P11 integral data.

    For J(E)=J390*(E/390)^(-gamma), gamma>1, require
    integral_500^inf J(E)dE == P11. The root is unique for positive inputs.
    """
    if not (np.isfinite(j390) and np.isfinite(p11) and j390 > 0 and p11 > 0):
        return None
    ratio = p11 / (j390 * 500.0)
    lo, hi = 1.0 + 1e-8, 100.0
    def fn(g):
        return (390.0 / 500.0) ** g / (g - 1.0) - ratio
    while fn(hi) > 0 and hi < 1e6:
        hi *= 2.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if fn(mid) > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _gap_integral_from_anchor(j390: float, gamma: float) -> float:
    if not (np.isfinite(j390) and j390 >= 0 and gamma > 1):
        return float("nan")
    a = 500.0 / 390.0
    return j390 * 390.0 * ((a ** (1.0 - gamma) - 1.0) / (1.0 - gamma))


def _gap_integral_from_p11(p11: float, gamma: float) -> float:
    """Infer 390-500 integral from P11 when P10 is unusable, at fixed gamma."""
    if not (np.isfinite(p11) and p11 >= 0 and gamma > 1):
        return float("nan")
    # Ratio of power-law integrals [390,500] / [500,inf].
    return p11 * ((500.0 / 390.0) ** (gamma - 1.0) - 1.0)


def high_energy_gap_bridge(goes):
    """Data-constrained 390-500 MeV bridge using P10 and integral P11.

    Positive P10/P11 pairs determine gamma independently at each timestamp and
    direction. Where P10 is nonpositive/unusable, the direction-specific median
    fitted gamma is used with P11 alone. This is still an extrapolation model,
    but it is constrained by both neighboring GOES measurements rather than a
    free flat continuation.
    """
    T = len(goes.times)
    gamma = np.full((T, 2), np.nan)
    used_fallback = np.zeros((T, 2), bool)
    med = np.full(2, np.nan)
    for d in range(2):
        fitted = []
        for t in range(T):
            if not goes.valid[t, d]:
                continue
            g = _solve_high_gamma(float(goes.flux[t, d, -1]), float(goes.p11[t, d]))
            if g is not None:
                gamma[t, d] = g
                fitted.append(g)
        med[d] = float(np.median(fitted)) if fitted else 1.2
        for t in range(T):
            if goes.valid[t, d] and not np.isfinite(gamma[t, d]):
                gamma[t, d] = med[d]
                used_fallback[t, d] = True

    integ = np.full((T, 2), np.nan)
    integ_lo = np.full((T, 2), np.nan)
    integ_hi = np.full((T, 2), np.nan)
    for d in range(2):
        for t in range(T):
            if not goes.valid[t, d]:
                continue
            g = gamma[t, d]
            j = float(goes.flux[t, d, -1])
            p11 = float(goes.p11[t, d])
            uj = float(goes.uncert[t, d, -1]) if np.isfinite(goes.uncert[t, d, -1]) else 0.0
            up = float(goes.p11_uncert[t, d]) if np.isfinite(goes.p11_uncert[t, d]) else 0.0
            if j > 0 and not used_fallback[t, d]:
                integ[t, d] = _gap_integral_from_anchor(j, g)
                # Envelope at fixed fitted gamma; spectral-index model uncertainty
                # is handled separately from the L2 measurement uncertainty.
                integ_lo[t, d] = _gap_integral_from_anchor(max(0.0, j - uj), g)
                integ_hi[t, d] = _gap_integral_from_anchor(j + uj, g)
            else:
                integ[t, d] = _gap_integral_from_p11(max(0.0, p11), g)
                integ_lo[t, d] = _gap_integral_from_p11(max(0.0, p11 - up), g)
                integ_hi[t, d] = _gap_integral_from_p11(max(0.0, p11 + up), g)
    diag = {
        "direction_median_gamma": {"E": float(med[0]), "W": float(med[1])},
        "fallback_rows": {"E": int(np.sum(used_fallback[:, 0])), "W": int(np.sum(used_fallback[:, 1]))},
        "gamma_quantiles": {},
    }
    for d, name in enumerate(("E", "W")):
        x = gamma[goes.valid[:, d], d]
        diag["gamma_quantiles"][name] = {
            "p05": float(np.quantile(x, 0.05)),
            "median": float(np.quantile(x, 0.50)),
            "p95": float(np.quantile(x, 0.95)),
        }
    return integ, integ_lo, integ_hi, gamma, diag


def calculate(goes, transport_npz: Path, sigma_csv: Path):
    z = np.load(transport_npz)
    energy = np.asarray(z["energy_mev"], float)
    shields = np.asarray(z["shield_mm"], float)
    primary_m = np.asarray(z["primary"], float)
    secondary_m = np.asarray(z["secondary"], float)
    if tuple(shields.tolist()) != SHIELDS_MM:
        raise ValueError(f"shield grid mismatch {shields}")
    if primary_m.shape != (len(shields), len(energy), len(energy)):
        raise ValueError("transport shape")

    points = load_experimental_points(sigma_csv)
    sig_main = sigma_hat(energy, points, "main_loglog")
    w_main = trap_weights(energy) * sig_main
    e_zero = zero_crossing_low(points)

    J, U = reconstruct_goes(goes, energy)
    J4 = FOUR_PI * J
    U4 = FOUR_PI * U
    extensions = {}
    for gamma in LOW_EXTRAP_GAMMAS:
        L, LU = low_energy_extension(goes, energy, e_zero, gamma)
        extensions[gamma] = (FOUR_PI * L, FOUR_PI * LU)

    T = len(goes.times)
    D = len(shields)
    shape = (T, D, 2)
    measured_p = np.full(shape, np.nan)
    measured_s = np.full(shape, np.nan)
    measured_t = np.full(shape, np.nan)
    scenario_p = {g: np.full(shape, np.nan) for g in LOW_EXTRAP_GAMMAS}
    scenario_s = {g: np.full(shape, np.nan) for g in LOW_EXTRAP_GAMMAS}
    scenario_t = {g: np.full(shape, np.nan) for g in LOW_EXTRAP_GAMMAS}
    rate_lo_ref = np.full(shape, np.nan)
    rate_hi_ref = np.full(shape, np.nan)
    sensitive_band_ref = np.full(shape, np.nan)
    input_gt200 = np.full(shape, np.nan)
    alt = {m: np.full(shape, np.nan) for m in SIGMA_SENSITIVITY_MODELS}

    high_sigma_main = float(sigma_hat(np.array([600.0]), points, "main_loglog")[0])
    p11_main = _p11_rate(goes, high_sigma_main)
    p11_u = _p11_uncert_rate(goes, high_sigma_main)
    gap_integral, gap_integral_lo, gap_integral_hi, gap_gamma, gap_bridge_diag = high_energy_gap_bridge(goes)
    gap_bridge_main = N_BITS * FOUR_PI * gap_integral * high_sigma_main
    gap_bridge_lo = N_BITS * FOUR_PI * gap_integral_lo * high_sigma_main
    gap_bridge_hi = N_BITS * FOUR_PI * gap_integral_hi * high_sigma_main
    band = (energy >= 0.8) & (energy <= 1.2)
    highin = energy > 200.0
    ref_gamma = LOW_EXTRAP_REFERENCE_GAMMA

    for di in range(D):
        for direction in range(2):
            valid = goes.valid[:, direction]
            if not np.any(valid):
                continue
            inp = J4[valid, direction]
            po, so, rp, rs = _transport_component(inp, primary_m[di], secondary_m[di], w_main)
            rp = rp + p11_main[valid, direction]
            measured_p[valid, di, direction] = rp
            measured_s[valid, di, direction] = rs
            measured_t[valid, di, direction] = rp + rs

            # Explicit low-energy extrapolation scenarios.
            scenario_outputs = {}
            for gamma in LOW_EXTRAP_GAMMAS:
                low_inp = extensions[gamma][0][valid, direction]
                lpo, lso, lrp, lrs = _transport_component(low_inp, primary_m[di], secondary_m[di], w_main)
                scenario_p[gamma][valid, di, direction] = rp + lrp + gap_bridge_main[valid, direction]
                scenario_s[gamma][valid, di, direction] = rs + lrs
                scenario_t[gamma][valid, di, direction] = rp + rs + lrp + lrs + gap_bridge_main[valid, direction]
                if gamma == ref_gamma:
                    scenario_outputs[gamma] = (po + lpo, so + lso)

            # L2 envelope for the reference extrapolation scenario. P1 uncertainty
            # is propagated with the same assumed power-law shape in the added band.
            low_meas = np.maximum(0.0, inp - U4[valid, direction])
            high_meas = inp + U4[valid, direction]
            low_ext, low_ext_u = extensions[ref_gamma]
            low_e = low_ext[valid, direction]
            low_eu = low_ext_u[valid, direction]
            low_total_inp = low_meas + np.maximum(0.0, low_e - low_eu)
            high_total_inp = high_meas + low_e + low_eu
            lowout = (low_total_inp @ primary_m[di].T) + (low_total_inp @ secondary_m[di].T)
            highout = (high_total_inp @ primary_m[di].T) + (high_total_inp @ secondary_m[di].T)
            rate_lo_ref[valid, di, direction] = N_BITS * (lowout @ w_main) + np.maximum(
                0, p11_main[valid, direction] - p11_u[valid, direction]
            ) + gap_bridge_lo[valid, direction]
            rate_hi_ref[valid, di, direction] = N_BITS * (highout @ w_main) + p11_main[valid, direction] + p11_u[valid, direction] + gap_bridge_hi[valid, direction]

            # Diagnostics use the reference scenario where relevant.
            total_ref_output = scenario_outputs[ref_gamma][0] + scenario_outputs[ref_gamma][1]
            wb = w_main.copy()
            wb[~band] = 0.0
            sensitive_band_ref[valid, di, direction] = N_BITS * (total_ref_output @ wb)
            inp_hi = np.zeros_like(inp)
            inp_hi[:, highin] = inp[:, highin]
            out_hi = (inp_hi @ primary_m[di].T) + (inp_hi @ secondary_m[di].T)
            input_gt200[valid, di, direction] = N_BITS * (out_hi @ w_main) + gap_bridge_main[valid, direction] + p11_main[valid, direction]

            # Sigma interpolation sensitivity at the fixed reference spectrum.
            ref_inp = inp + extensions[ref_gamma][0][valid, direction]
            refout = (ref_inp @ primary_m[di].T) + (ref_inp @ secondary_m[di].T)
            for model in SIGMA_SENSITIVITY_MODELS:
                sig = sigma_hat(energy, points, model)
                w = trap_weights(energy) * sig
                high_sigma = float(sigma_hat(np.array([600.0]), points, model)[0])
                p11_alt = N_BITS * FOUR_PI * goes.p11[valid, direction] * high_sigma
                gap_alt = N_BITS * FOUR_PI * gap_integral[valid, direction] * high_sigma
                alt[model][valid, di, direction] = N_BITS * (refout @ w) + p11_alt + gap_alt

    # Alternative 390-500 MeV diagnostic. The reference rate already includes the
    # P10/P11-constrained power-law bridge above; this flat-P10 continuation is
    # retained only as a deliberately simple stress test.
    sig_gap = float(sigma_hat(np.array([445.0]), points, "main_loglog")[0])
    gap_diag = N_BITS * FOUR_PI * goes.flux[:, :, -1] * (500.0 - 390.0) * sig_gap

    return {
        "energy": energy,
        "shields": shields,
        "measured_primary": measured_p,
        "measured_secondary": measured_s,
        "measured_total": measured_t,
        "scenario_primary": scenario_p,
        "scenario_secondary": scenario_s,
        "scenario_total": scenario_t,
        "reference_gamma": ref_gamma,
        "reference_total": scenario_t[ref_gamma],
        "reference_primary": scenario_p[ref_gamma],
        "reference_secondary": scenario_s[ref_gamma],
        "uncert_low_ref": rate_lo_ref,
        "uncert_high_ref": rate_hi_ref,
        "sensitive_band_ref": sensitive_band_ref,
        "input_gt200": input_gt200,
        "alt": alt,
        "p11_rate": p11_main,
        "gap390_500_diag": gap_diag,
        "gap_bridge_rate": gap_bridge_main,
        "gap_bridge_gamma": gap_gamma,
        "gap_bridge_diagnostic": gap_bridge_diag,
        "low_sigma_zero_crossing": e_zero,
        "points": points,
        "raw_low_slope_diagnostic": _raw_low_slope_diagnostic(goes),
    }


def q(v, p):
    v = np.asarray(v, float)
    return float(np.nanquantile(v, p)) if np.any(np.isfinite(v)) else float("nan")


def summarize(goes, R):
    rows = []
    total = R["reference_total"]
    primary = R["reference_primary"]
    secondary = R["reference_secondary"]
    measured = R["measured_total"]
    for di, mm in enumerate(R["shields"]):
        e = total[:, di, 0]
        w = total[:, di, 1]
        c = np.where(np.isfinite(e) & np.isfinite(w), (e + w) / 2, np.nan)
        mc = np.where(
            np.isfinite(measured[:, di, 0]) & np.isfinite(measured[:, di, 1]),
            np.mean(measured[:, di, :], axis=1),
            np.nan,
        )
        cp = np.where(np.all(np.isfinite(primary[:, di, :]), axis=1), np.mean(primary[:, di, :], axis=1), np.nan)
        cs = np.where(np.all(np.isfinite(secondary[:, di, :]), axis=1), np.mean(secondary[:, di, :], axis=1), np.nan)
        band = np.where(np.all(np.isfinite(R["sensitive_band_ref"][:, di, :]), axis=1), np.mean(R["sensitive_band_ref"][:, di, :], axis=1), np.nan)
        hiin = np.where(np.all(np.isfinite(R["input_gt200"][:, di, :]), axis=1), np.mean(R["input_gt200"][:, di, :], axis=1), np.nan)
        lo = np.where(np.all(np.isfinite(R["uncert_low_ref"][:, di, :]), axis=1), np.mean(R["uncert_low_ref"][:, di, :], axis=1), np.nan)
        hi = np.where(np.all(np.isfinite(R["uncert_high_ref"][:, di, :]), axis=1), np.mean(R["uncert_high_ref"][:, di, :], axis=1), np.nan)
        idx = int(np.nanargmax(c))
        med = float(np.nanmedian(c))
        mean = float(np.nanmean(c))
        mx = float(c[idx])
        alts = []
        for _, a in R["alt"].items():
            ac = np.where(np.all(np.isfinite(a[:, di, :]), axis=1), np.mean(a[:, di, :], axis=1), np.nan)
            alts.append(ac)
        astack = np.stack(alts)
        rel_spread = np.full(astack.shape[1], np.nan)
        finite_any = np.any(np.isfinite(astack), axis=0)
        if np.any(finite_any):
            aa = astack[:, finite_any]
            rel_spread[finite_any] = (np.nanmax(aa, axis=0) - np.nanmin(aa, axis=0)) / np.maximum(c[finite_any], 1e-300)
        ew = abs(e - w) / np.maximum((e + w) / 2, 1e-300)
        gapc = np.where(np.all(np.isfinite(R["gap390_500_diag"]), axis=1), np.mean(R["gap390_500_diag"], axis=1), np.nan)
        gapbridge = np.where(np.all(np.isfinite(R["gap_bridge_rate"]), axis=1), np.mean(R["gap_bridge_rate"], axis=1), np.nan)
        low_frac = (c - mc - gapbridge) / np.maximum(c, 1e-300)
        p11c = np.where(np.all(np.isfinite(R["p11_rate"]), axis=1), np.mean(R["p11_rate"], axis=1), np.nan)

        row = {
            "shield_mm": float(mm),
            "absolute_status": "PARTIAL_LOW_SPECTRUM_AND_SIGMA_EXTRAPOLATION" if mm == 0 else "PARTIAL_SIGMA_EXTRAPOLATION",
            "reference_low_spectrum_gamma": R["reference_gamma"],
            "valid_5min_intervals": int(np.sum(np.isfinite(c))),
            "coverage_fraction": float(np.mean(np.isfinite(c))),
            "median_s-1": med,
            "mean_s-1": mean,
            "p90_s-1": q(c, 0.90),
            "p95_s-1": q(c, 0.95),
            "p99_s-1": q(c, 0.99),
            "p99_9_s-1": q(c, 0.999),
            "max_s-1": mx,
            "max_timestamp_utc": goes.times[idx].isoformat(),
            "dynamic_range_max_over_median": mx / med if med > 0 else float("inf"),
            "total_expected_flipped_bits_observed_intervals": float(np.nansum(c * 300.0)),
            "measured_support_median_s-1": float(np.nanmedian(mc)),
            "median_fraction_from_low_spectrum_extrapolation": q(low_frac, 0.5),
            "p99_fraction_from_low_spectrum_extrapolation": q(low_frac, 0.99),
            "mean_primary_fraction": float(np.nanmean(cp / np.maximum(c, 1e-300))),
            "mean_secondary_fraction": float(np.nanmean(cs / np.maximum(c, 1e-300))),
            "p99_secondary_fraction": q(cs / np.maximum(c, 1e-300), 0.99),
            "max_secondary_fraction": float(np.nanmax(cs / np.maximum(c, 1e-300))),
            "mean_rate_fraction_from_0p8_1p2MeV_output": float(np.nanmean(band / np.maximum(c, 1e-300))),
            "p99_rate_fraction_from_0p8_1p2MeV_output": q(band / np.maximum(c, 1e-300), 0.99),
            "mean_rate_fraction_from_input_gt200MeV": float(np.nanmean(hiin / np.maximum(c, 1e-300))),
            "p99_rate_fraction_from_input_gt200MeV": q(hiin / np.maximum(c, 1e-300), 0.99),
            "median_high_gap_bridge_fraction": q(gapbridge / np.maximum(c, 1e-300), 0.5),
            "p99_high_gap_bridge_fraction": q(gapbridge / np.maximum(c, 1e-300), 0.99),
            "median_flat_P10_390_500_gap_fraction_diagnostic": q(gapc / np.maximum(c, 1e-300), 0.5),
            "p99_flat_P10_390_500_gap_fraction_diagnostic": q(gapc / np.maximum(c, 1e-300), 0.99),
            "median_P11_gt500_fraction": q(p11c / np.maximum(c, 1e-300), 0.5),
            "median_EW_relative_discrepancy": q(ew, 0.5),
            "p95_EW_relative_discrepancy": q(ew, 0.95),
            "p99_EW_relative_discrepancy": q(ew, 0.99),
            "median_L2_uncertainty_envelope_relative_halfwidth": q((hi - lo) / (2 * np.maximum(c, 1e-300)), 0.5),
            "p95_L2_uncertainty_envelope_relative_halfwidth": q((hi - lo) / (2 * np.maximum(c, 1e-300)), 0.95),
            "median_sigma_model_range_relative_to_main": q(rel_spread, 0.5),
            "p95_sigma_model_range_relative_to_main": q(rel_spread, 0.95),
        }
        for gamma in LOW_EXTRAP_GAMMAS:
            a = R["scenario_total"][gamma]
            ac = np.where(np.all(np.isfinite(a[:, di, :]), axis=1), np.mean(a[:, di, :], axis=1), np.nan)
            tag = str(int(gamma)) if float(gamma).is_integer() else str(gamma).replace(".", "p")
            row[f"low_gamma{tag}_median_s-1"] = q(ac, 0.5)
            row[f"low_gamma{tag}_p99_s-1"] = q(ac, 0.99)
        rows.append(row)
    return rows


def write_summary(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def _shield_tag(mm: float) -> str:
    return str(int(mm)) if float(mm).is_integer() else str(mm).replace(".", "p")


def write_rate_csv(path: Path, goes, R):
    """Compact wide 5-min interface.

    East/West total chains remain separate. Primary/secondary are reported for
    the E/W-average reference scenario. The d=0 measured-support and alternate
    low-energy extrapolation scenarios are explicit additional columns.
    """
    fields = [
        "timestamp_utc", "algorithm_version", "east_valid", "west_valid",
        "east_quality_flag", "west_quality_flag",
    ]
    for mm in R["shields"]:
        tag = _shield_tag(float(mm))
        fields += [
            f"d{tag}_lambda_E_s-1", f"d{tag}_lambda_W_s-1", f"d{tag}_lambda_central_s-1",
            f"d{tag}_lambda_central_h-1", f"d{tag}_m5_central_bits",
            f"d{tag}_primary_central_s-1", f"d{tag}_secondary_central_s-1",
        ]
    fields += [
        "d0_measured_support_central_s-1",
        "d0_low_gamma0_central_s-1",
        "d0_low_gamma4_central_s-1",
    ]

    def fmt(x):
        return "" if not np.isfinite(x) else f"{x:.7e}"

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for t, time in enumerate(goes.times):
            row = {
                "timestamp_utc": time.isoformat(),
                "algorithm_version": goes.version[t],
                "east_valid": int(goes.valid[t, 0]),
                "west_valid": int(goes.valid[t, 1]),
                "east_quality_flag": int(goes.quality_any[t, 0]),
                "west_quality_flag": int(goes.quality_any[t, 1]),
            }
            for di, mm in enumerate(R["shields"]):
                tag = _shield_tag(float(mm))
                e = R["reference_total"][t, di, 0]
                ww = R["reference_total"][t, di, 1]
                central = np.mean(R["reference_total"][t, di]) if np.all(np.isfinite(R["reference_total"][t, di])) else np.nan
                pc = np.mean(R["reference_primary"][t, di]) if np.all(np.isfinite(R["reference_primary"][t, di])) else np.nan
                sc = np.mean(R["reference_secondary"][t, di]) if np.all(np.isfinite(R["reference_secondary"][t, di])) else np.nan
                row[f"d{tag}_lambda_E_s-1"] = fmt(e)
                row[f"d{tag}_lambda_W_s-1"] = fmt(ww)
                row[f"d{tag}_lambda_central_s-1"] = fmt(central)
                row[f"d{tag}_lambda_central_h-1"] = fmt(3600.0 * central)
                row[f"d{tag}_m5_central_bits"] = fmt(300.0 * central)
                row[f"d{tag}_primary_central_s-1"] = fmt(pc)
                row[f"d{tag}_secondary_central_s-1"] = fmt(sc)
            meas = R["measured_total"][t, 0]
            g0 = R["scenario_total"][0.0][t, 0]
            g4 = R["scenario_total"][4.0][t, 0]
            row["d0_measured_support_central_s-1"] = fmt(np.mean(meas) if np.all(np.isfinite(meas)) else np.nan)
            row["d0_low_gamma0_central_s-1"] = fmt(np.mean(g0) if np.all(np.isfinite(g0)) else np.nan)
            row["d0_low_gamma4_central_s-1"] = fmt(np.mean(g4) if np.all(np.isfinite(g4)) else np.nan)
            w.writerow(row)

def write_sigma_model(path: Path, R):
    points = R["points"]
    grid = np.unique(np.r_[np.geomspace(0.11, 500, 350), [p.energy_mev for p in points], 29.0, R["low_sigma_zero_crossing"]])
    fields = ["energy_mev"] + list(MODEL_NAMES) + ["experimental_sigma_cm2_per_bit", "experimental_value_type", "experimental_source"]
    by = {p.energy_mev: p for p in points}
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        vals = {m: sigma_hat(grid, points, m) for m in MODEL_NAMES}
        for i, e in enumerate(grid):
            p = by.get(float(e))
            row = {"energy_mev": f"{e:.9g}"}
            for m in MODEL_NAMES:
                row[m] = f"{vals[m][i]:.9e}"
            row["experimental_sigma_cm2_per_bit"] = "" if p is None else f"{p.sigma_cm2_bit:.9e}"
            row["experimental_value_type"] = "" if p is None else p.value_type
            row["experimental_source"] = "" if p is None else p.source
            w.writerow(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--goes-dir", type=Path, required=True)
    ap.add_argument("--transport", type=Path, required=True)
    ap.add_argument("--sigma-csv", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    goes = load_directory(a.goes_dir)
    R = calculate(goes, a.transport, a.sigma_csv)
    rows = summarize(goes, R)
    write_summary(a.out / "summary_by_shielding.csv", rows)
    write_rate_csv(a.out / "goes19_proton_rate.csv", goes, R)
    write_sigma_model(a.out / "sigma_bit_model.csv", R)
    (a.out / "goes19_audit.json").write_text(json.dumps(goes.audit, indent=2), encoding="utf-8")
    diagnostics = {
        "low_sigma_zero_crossing_mev": R["low_sigma_zero_crossing"],
        "low_spectrum_extrapolation": {
            "status": "explicit scenario, not measured GOES spectrum",
            "formula": "J(E)=J_P1*(E/E_P1_low)^(-gamma) for E_zero<=E<E_P1_low",
            "P1_lower_support_mev": 0.92,
            "gamma_scenarios": list(LOW_EXTRAP_GAMMAS),
            "reference_gamma": LOW_EXTRAP_REFERENCE_GAMMA,
            "interpretation": "gamma=0/2/4 are sensitivity scenarios rather than confidence bounds; gamma=2 is only a reproducible reference scenario",
            "raw_P1_P2A_slope_diagnostic": R["raw_low_slope_diagnostic"],
        },
        "d0_status": "Scenario absolute rate is reported using gamma=2; measured-support-only and gamma=0/4 alternatives are retained separately.",
        "high_energy_gap_bridge": {
            "status": "included extrapolated bridge constrained by P10 differential and P11 integral measurements",
            "formula": "power law J(E)=J390*(E/390)^(-gamma); gamma chosen so integral_500^inf J dE equals measured P11",
            "diagnostic": R["gap_bridge_diagnostic"],
            "fallback": "where P10 is nonpositive, use direction-median fitted gamma with measured P11 normalization",
        },
        "gap390_500_diagnostic_note": "Reference rate includes the P10/P11-constrained power-law bridge. A flat-P10 bridge is retained only as an alternative stress-test diagnostic.",
        "p11_note": "Measured P11 >500 MeV is included analytically because sigma is held constant above 186 MeV; its integral value also constrains the 390-500 MeV bridge slope.",
    }
    (a.out / "rate_diagnostics.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()

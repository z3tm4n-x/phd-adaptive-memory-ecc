"""Addressed regression against the retained T67/RADAR numerical chain.

Loads only existing matrices, never builds a transport model or fetches data.
Agreement of two matrix-folding orders checks arithmetic, not physical validity.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np

from transport import RangeTable, quadrature, sigma

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LEGACY_MATRIX = REPO / "experiments/RE-CY62167-COVERAGE-THRESHOLD-01/recovery/outputs/radar_transport.npz"
LEGACY_RESPONSE = REPO / "experiments/t67-goes-growth/response.py"
LEGACY_EVENTS = REPO / "experiments/t67-goes-growth/outputs/reference_events.csv"
PINNED_EVENTS = ("sep_20170910_1645", "sep_20241009_0505", "sep_20260118_2255")
DATA32_BITS = 2**19 * 32
FULL38_BITS = 2**19 * 38


def matrix_fold(energy, matrix, incident, sigma_bit, bits=FULL38_BITS):
    """Direct output-spectrum trapezoid, independently of T67 kernel order."""
    energy = np.asarray(energy, dtype=float)
    matrix = np.asarray(matrix, dtype=float)
    incident, sigma_bit = np.asarray(incident), np.asarray(sigma_bit)
    if (matrix.shape != (len(energy), len(energy)) or incident.shape != energy.shape
            or sigma_bit.shape != energy.shape or np.any(np.diff(energy) <= 0)):
        raise ValueError("unaligned ordered matrix/spectrum inputs")
    if any(not np.isfinite(a).all() or np.any(a < 0) for a in (matrix, incident, sigma_bit)) or bits <= 0:
        raise ValueError("nonnegative finite response required")
    return float(4*math.pi*bits*np.trapezoid((matrix@incident)*sigma_bit, energy))


def load_legacy_response():
    spec = importlib.util.spec_from_file_location("sepem_checked_t67_response", LEGACY_RESPONSE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _table_with_cut(table, energy):
    """Add an exactly interpolated cut without changing log-log range law."""
    new = copy.copy(table)
    value = table.range(np.array([energy]))[0]
    stopping = np.exp(np.interp(np.log(energy), np.log(table.energy), np.log(table.stopping)))
    k = int(np.searchsorted(table.energy, energy))
    if k < len(table.energy) and table.energy[k] == energy:
        return new
    new.energy = np.insert(table.energy, k, energy)
    new.ranges = np.insert(table.ranges, k, value)
    new.stopping = np.insert(table.stopping, k, stopping)
    return new


def csda_common_fold(table, power, rho=2.7, bits=FULL38_BITS, order=24):
    """Incident [5,390] MeV support, matching the retained matrix's upper end."""
    table = _table_with_cut(table, 390.)
    energy, kernel, _, _ = quadrature(table, rho, order=order)
    use = (energy >= 5.) & (energy < 390.)
    incident = (energy[use]/10.)**(-power)*np.exp(-energy[use]/350.)
    return float(4*math.pi*bits*np.dot(incident, kernel[use]))


def legacy_event_rows(path=LEGACY_EVENTS):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        source = list(csv.DictReader(stream))
    result = []
    for event_id in PINNED_EVENTS:
        matches = [r for r in source if r["event_id"] == event_id and int(r["cadence_s"]) == 300]
        if len(matches) != 1:
            raise ValueError(f"expected one preselected 5-minute event row: {event_id}")
        row = matches[0]
        peak = float(row["peak_s-1"])
        result.append({
            "event_id": event_id, "peak_start_utc": row["peak_start_utc"],
            "satellite": row["peak_satellite"], "direction": row["peak_direction"],
            "cadence_s": 300, "shield_mm_al": 10., "shield_g_cm2_al": 2.7,
            "T67_peak_data32_s-1": peak,
            "same_chain_scaled_full38_s-1": peak*38/32,
            "full38_over_data32": 38/32, "value_type": "calculated_legacy_and_normalization",
            "scope": "directional screened maximum; not E/W mean; same-chain scaling assumes equal sensitivity of all 38 positions",
        })
    return result


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(out, events=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    old = load_legacy_response()
    with np.load(LEGACY_MATRIX, allow_pickle=False) as data:
        energy = data["energy_mev"]
        shields = data["shield_mm"]
        index = list(shields).index(10.)
        primary, secondary = data["primary"][index], data["secondary"][index]
        identity_error = float(np.max(np.abs(data["primary"][0]-np.eye(len(energy)))))
        zero_secondary_error = float(np.max(np.abs(data["secondary"][0])))
    if energy[-1] != 390.:
        raise ValueError("retained matrix endpoint changed")
    old_points = old.sigma.load_experimental_points(old.SIGMA_CSV)
    sigma_old = old.sigma.sigma_hat(energy, old_points, "main_loglog")
    sigma_new = sigma(energy)
    if not np.allclose(sigma_old, sigma_new, rtol=2e-15, atol=0):
        raise AssertionError("new response does not reuse the old main_loglog interpolant")
    weighted_sigma = old.NS["trap_weights"](energy)*sigma_old
    table = RangeTable()
    rows = []
    for power in (0., 1.5, 3.):
        incident = (energy/10.)**(-power)*np.exp(-energy/350.)
        # Match the new quadrature's lower support. Retain native old support
        # separately to reveal, rather than assume away, any below-5 effect.
        common = np.where(energy >= 5., incident, 0.)
        p = matrix_fold(energy, primary, common, sigma_old)
        s = matrix_fold(energy, secondary, common, sigma_old)
        kernel_order = float(4*math.pi*FULL38_BITS*common@(primary+secondary).T@weighted_sigma)
        relative = abs(kernel_order-p-s)/max(abs(p+s), 1e-300)
        if relative > 2e-13:
            raise AssertionError("independent matrix/trapezoid order failed arithmetic check")
        native = matrix_fold(energy, primary+secondary, incident, sigma_old)
        new = csda_common_fold(table, power)
        refine = csda_common_fold(table, power, order=48)
        old32 = matrix_fold(energy, primary+secondary, common, sigma_old, DATA32_BITS)
        ratio = (p+s)/old32
        if not np.isclose(ratio, 38/32, rtol=2e-15):
            raise AssertionError("data32/full38 normalization changed")
        rows.append({"spectral_power": power, "incident_model": "(E/10 MeV)^(-power) exp(-E/350 MeV)",
            "shield_g_cm2_al": 2.7, "protected_bits": FULL38_BITS,
            "angular_factor": 4*math.pi, "incident_support_MeV": "5..390",
            "legacy_primary_s-1": p, "legacy_secondary_s-1": s, "legacy_total_s-1": p+s,
            "legacy_native_0p11_390_total_s-1": native,
            "new_CSDA_primary_only_s-1": new,
            "new_over_legacy_primary": new/p,
            "new_over_legacy_total": new/(p+s),
            "matrix_order_relative_difference": relative,
            "new_quadrature_24_48_relative_difference": abs(refine-new)/max(abs(refine),1e-300),
            "full38_over_data32": ratio, "value_type": "calculated_diagnostic_not_physical_equivalence"})
    reference = legacy_event_rows()
    report = {
        "status": "arithmetic_regression_and_model_difference_recorded",
        "inputs": {str(p.relative_to(REPO)).replace("\\", "/"): _sha(p) for p in (
            LEGACY_MATRIX, LEGACY_RESPONSE, LEGACY_EVENTS, old.SIGMA_CSV, HERE/"transport.py", HERE/"inputs/nist_pstar_al.csv")},
        "matrix_energy_points": len(energy), "matrix_thicknesses_mm_al": list(map(float, shields)),
        "d0_primary_identity_max_abs": identity_error, "d0_secondary_max_abs": zero_secondary_error,
        "response_points_identical": True,
        "synthetic_spectra": rows, "preselected_T67_event_peaks": reference,
        "limitations": [
            "Legacy primary includes the retained nuclear survival treatment and a different range table/discretization; new CSDA is primary only with NIST PSTAR ranges.",
            "These differences are documented candidates for the observed discrepancy, not a quantified causal decomposition or a proof of accuracy.",
            "Legacy matrices have only seven retained thicknesses, up to 10 mm Al = 2.7 g/cm2; no matrix for 3 g/cm2 is constructed or interpolated here.",
            "Synthetic common-support folding excludes the legacy >390 MeV bridge/tail; retained real T67 peaks include their declared full historical chain.",
            "T67 peaks are maxima over screened direction/satellite records, not a central E/W average, and have no common events with the 1974-2015 RDS archive.",
            "Scaling T67 by 38/32 changes only the declared bit count, not shielding, instruments, event profile or confidence in the physical model.",
            "No numerical agreement threshold between physical transport models is imposed; only arithmetic and unit normalization are tested.",
        ],
    }
    if events is not None:
        with Path(events).open(encoding="utf-8", newline="") as stream:
            rds = list(csv.DictReader(stream))
        # Predetermined years; choose the largest N in each for a descriptive
        # severity comparison, not a match of the same physical event.
        selected = []
        for year in (1989, 2003, 2005):
            options = [r for r in rds if r["peak_utc"].startswith(str(year))]
            if options:
                pick = max(options, key=lambda r: float(r["N_expected_upsets"]))
                selected.append({k: pick[k] for k in ("event_id", "peak_utc", "peak_lambda_s-1", "N_expected_upsets", "S2_s-1")})
        report["RDS_noncoincident_examples"] = selected
        report["RDS_events_input_sha256"] = _sha(events)
    for name, data in (("legacy_transport_comparison.csv", rows), ("legacy_T67_reference_events.csv", reference)):
        with (out/name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(data[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(data)
    (out/"legacy_transport_comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE/"outputs")
    parser.add_argument("--events", type=Path)
    args = parser.parse_args()
    result = run(args.out, args.events)
    print(json.dumps({"status": result["status"], "synthetic_cases": len(result["synthetic_spectra"]),
                      "preselected_T67_events": len(result["preselected_T67_event_peaks"])}, indent=2))

"""SGPS L2 data/quality adapter; no time filling or implicit sensor averaging."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import numpy as np
from nc_reader import open_nc

CHANNELS = ("P1", "P2A", "P2B", "P3", "P4", "P5", "P6", "P7", "P8A", "P8B", "P8C", "P9", "P10", "P11")
OLD_LO = np.array([1.02, 1.90, 2.31, 3.40, 5.84, 11.64])
OLD_HI = np.array([1.86, 2.30, 3.34, 6.48, 11.00, 23.27])
CORR_LO = np.array([0.92, 1.80, 2.20, 3.30, 6.30, 12.4])
CORR_HI = np.array([1.80, 2.20, 3.20, 6.20, 11.7, 23.3])
CORR = np.array([0.656, 0.688, 0.708, 0.625, 0.618, 0.753])
EPOCH = datetime(2000, 1, 1, 12, tzinfo=timezone.utc).timestamp()


def clean(a, attrs):
    out = np.asarray(a, float).copy()
    valid = np.isfinite(out)
    if "_FillValue" in attrs:
        valid &= out != attrs["_FillValue"]
    if "valid_min" in attrs:
        valid &= out >= attrs["valid_min"]
    if "valid_max" in attrs:
        valid &= out <= attrs["valid_max"]
    out[~valid] = np.nan
    return out


def directions(a, yaw):
    """Index 0 East / 1 West; invalid yaw is missing, never an assumed attitude."""
    out = np.full(a.shape, np.nan)
    for y, order in ((0, [1, 0]), (2, [0, 1])):
        mask = yaw == y
        out[mask] = a[mask][:, order]
    return out


def lut_matches(value, attrs):
    """NOAA reversed this variable's documented polarity; never infer from name."""
    meaning = attrs.get("long_name", "")
    for good in (0, 1):
        if f"{good} if all input files' specified lookup tables matched" in meaning:
            return value == good
    raise ValueError("Unknown ExpectedLUTNotFound polarity")


def corrected_energy(lo, hi, effective):
    lo, hi, effective = (x.copy() for x in (lo, hi, effective))
    factors = np.ones(13)
    if np.allclose(lo[:, :6], OLD_LO, atol=.011, rtol=0) and np.allclose(hi[:, :6], OLD_HI, atol=.011, rtol=0):
        lo[:, :6], hi[:, :6] = CORR_LO, CORR_HI
        factors[:6] = CORR
        effective[:, :6] = np.sqrt(CORR_LO * CORR_HI)
        action = "published_2024_P1_P5_correction_once"
    elif np.allclose(lo[:, :6], CORR_LO, atol=.011, rtol=0) and np.allclose(hi[:, :6], CORR_HI, atol=.011, rtol=0):
        action = "already_corrected_no_repeat"
    else:
        raise ValueError("Unqualified P1-P5 energy calibration; do not silently extrapolate")
    unavailable = (~np.isfinite(effective)) | (effective <= 0)
    effective[unavailable] = np.sqrt(lo * hi)[unavailable]
    return lo, hi, effective, factors, action, bool(np.any(unavailable))


@dataclass
class Source:
    time: np.ndarray
    flux: np.ndarray
    corrected: np.ndarray
    uncertainty: np.ndarray
    screened: np.ndarray
    strict: np.ndarray
    yaw: np.ndarray
    lower: np.ndarray  # sensor order -X,+X, not fixed East/West
    upper: np.ndarray
    energy: np.ndarray
    cadence: int
    signature: str
    audit: dict


def read(path):
    path = Path(path)
    with open_nc(path) as f:
        attrs, names = f.attrs(), f.names()
        if attrs.get("processing_level") != "Level 2" or "SGPS" not in attrs.get("instrument", ""):
            raise ValueError("Not an SGPS Level 2 product")
        sat = int(attrs["platform"][1:])
        cadence = {"PT1M": 60, "PT5M": 300}[attrs["time_coverage_resolution"]]
        time_name = "time" if "time" in names else "L2_SciData_TimeStamp"
        ta = f.attrs(time_name)
        if "seconds since 2000-01-01 12:00:00" not in ta["units"] or "start" not in ta["long_name"].lower():
            raise ValueError("Unknown timestamp epoch or averaging convention")
        t = clean(f.array(time_name), ta) + EPOCH
        if not np.all(np.isfinite(t)) or np.any(np.diff(t) <= 0):
            raise ValueError("Invalid or non-increasing timestamps")
        yaw_name = "yaw_flip_flag" if "yaw_flip_flag" in names else "YawFlipFlag"
        yaw = clean(f.array(yaw_name), f.attrs(yaw_name))
        # Earlier YawFlipFlag is an aggregate without a documented 2=inverted
        # contract. Only an all-zero aggregate unambiguously means upright.
        if yaw_name == "YawFlipFlag":
            yaw[yaw != 0] = np.nan
        def val(name):
            return clean(f.array(name), f.attrs(name))
        fa = f.attrs("AvgDiffProtonFlux")
        if fa["units"] != "protons/(cm^2 sr keV s)":
            raise ValueError("Unqualified differential flux units")
        if f.attrs("AvgIntProtonFlux")["units"] != "protons/(cm^2 sr s)":
            raise ValueError("Unqualified integral flux units")
        raw = np.concatenate((val("AvgDiffProtonFlux") * 1000, val("AvgIntProtonFlux")[..., None]), axis=2)
        unc = np.concatenate((val("AvgDiffProtonFluxUncert") * 1000, val("AvgIntProtonFluxUncert")[..., None]), axis=2)
        counts = np.concatenate((val("DiffValidL1bSamplesInAvg"), val("IntValidL1bSamplesInAvg")[..., None]), axis=2)
        # A reported numeric flux with zero contributing samples is not a zero
        # observation (this occurs in the special September 2017 product).
        raw[counts <= 0] = np.nan
        screened = np.isfinite(raw) & (counts >= .9 * cadence)
        strict = screened.copy()
        flags = {}
        for prefix in ("Diff", "Int"):
            for suffix in ("DQFdtcSum", "DQFerrSum", "DQFoobSum", "ProtonIgnoredL1bDQFs"):
                name = prefix + suffix
                if name not in names:
                    continue
                a = val(name)
                flags[name] = {"flagged": int(np.count_nonzero(a > 0)), "missing": int(np.count_nonzero(~np.isfinite(a))), "sum": float(np.nansum(a)), "meaning": f.attrs(name).get("long_name")}
                if prefix == "Diff":
                    strict[:, :, :13] &= np.isfinite(a) & (a == 0)
                    if suffix != "DQFerrSum":
                        screened[:, :, :13] &= np.isfinite(a) & (a == 0)
                else:
                    strict[:, :, 13] &= np.isfinite(a) & (a == 0)
                    if suffix != "DQFerrSum":
                        screened[:, :, 13] &= np.isfinite(a) & (a == 0)
        energies = []
        for name in ("DiffProtonLowerEnergy", "DiffProtonUpperEnergy", "DiffProtonEffectiveEnergy"):
            if f.attrs(name)["units"] != "keV":
                raise ValueError("Unqualified energy units")
            energies.append(val(name) / 1000)
        lo, hi, ef, factors, action, substitute = corrected_energy(*energies)
        corrected = raw.copy()
        corrected[:, :, :13] *= factors
        unc[:, :, :13] *= factors
        # Preserve warnings: testing / thermal caveats are not hidden corrections.
        contamination_test = bool(sat == 19 and t[0] < datetime(2025, 4, 3, tzinfo=timezone.utc).timestamp())
        if contamination_test:
            strict[:, :, [7, 10]] = False
            screened[:, :, [7, 10]] = False
        lut_missing = float(np.asarray(f.array("ExpectedLUTNotFound"))) if "ExpectedLUTNotFound" in names else None
        lut_description = f.attrs("ExpectedLUTNotFound") if lut_missing is not None else {}
        lut_ok = lut_matches(lut_missing, lut_description) if lut_missing is not None else False
        if not lut_ok:
            strict[:] = False
            screened[:] = False
        signature_fields = {k: attrs.get(k) for k in ("platform", "algorithm_version", "L1b_LUT_Filenames", "processing_parameters_file", "sgps_mx_instrument_id", "sgps_px_instrument_id")}
        signature_fields["product_version"] = re.search(r"_v([^/]+)\.nc$", path.name)[1]
        signature_fields.update({"lower": lo.tolist(), "upper": hi.tolist(), "energy": ef.tolist(), "correction": action, "cadence_s": cadence})
        signature = hashlib.sha256(json.dumps(signature_fields, sort_keys=True, default=str).encode()).hexdigest()
        flux, corrected, unc = [directions(x, yaw) for x in (raw, corrected, unc)]
        strict = directions(strict.astype(float), yaw) == 1
        screened = directions(screened.astype(float), yaw) == 1
        audit = {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                 "bytes": path.stat().st_size, "satellite": sat, "cadence_s": cadence,
                 "records": len(t), "first_start_utc": datetime.fromtimestamp(t[0], timezone.utc).isoformat(),
                 "last_end_utc": datetime.fromtimestamp(t[-1] + cadence, timezone.utc).isoformat(),
                 "date_created": attrs.get("date_created"), "algorithm_date": attrs.get("algorithm_date"),
                 "signature": signature, "processing": signature_fields,
                 "effective_energy_geometric_mean_substitution": substitute,
                 "yaw_ambiguous_rows": int(np.count_nonzero(~np.isin(yaw, [0, 2]))),
                 "noncadence_steps": int(np.count_nonzero(np.diff(t) != cadence)),
                 "valid_values_by_direction_channel": np.sum(np.isfinite(flux), axis=0).tolist(),
                 "strict_values_by_direction_channel": np.sum(strict, axis=0).tolist(),
                 "screened_values_by_direction_channel": np.sum(screened, axis=0).tolist(),
                 "quality": flags, "expected_lut_not_found": lut_missing,
                 "lut_flag_metadata": lut_description, "lut_match": lut_ok,
                 "g19_P7_P8C_test_period": contamination_test,
                 "g18_temperature_dependence_caveat": sat == 18,
                 "flux_units": ["protons/(cm2 sr s MeV)"] * 13 + ["protons/(cm2 sr s)"]}
        return Source(t, flux, corrected, unc, screened, strict, yaw, lo, hi, ef, cadence, signature, audit)

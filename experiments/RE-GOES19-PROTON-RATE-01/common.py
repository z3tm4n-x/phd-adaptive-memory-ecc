"""Shared constants and typed records for RE-GOES19-PROTON-RATE-01."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

N_BITS = 16_777_216
AL_DENSITY_G_CM3 = 2.70
SHIELD_MM = (0.0, 1.0, 2.0, 5.0, 10.0)
CHANNELS = ("P1", "P2A", "P2B", "P3", "P4", "P5", "P6", "P7", "P8A", "P8B", "P8C", "P9", "P10")
P1_P5_CORR = np.array([0.656, 0.688, 0.708, 0.625, 0.618, 0.753], dtype=float)
P1_P5_LO = np.array([0.92, 1.80, 2.20, 3.30, 6.30, 12.4], dtype=float)
P1_P5_HI = np.array([1.80, 2.20, 3.20, 6.20, 11.7, 23.3], dtype=float)
P1_P5_EFF = np.sqrt(P1_P5_LO * P1_P5_HI)
GOES_CAL_URL = (
    "https://www.ospo.noaa.gov/operations/goes/product-quality-overview/"
    "ps-pvr/goes-19/SEISS/SGPS/Provisional/GOES-19_SEISS_SGPS_Provisional_ReadMe.pdf"
)
RD174_FORMULA = "RD 134-0174-2009 sec.6.4 eq.(6.6)"
RADAR_SHA = "b032505d4d1b15403b8ad06aef578339f6d1c6b4"
EPOCH = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _decode(value):
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def trapezoid_weights(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    w = np.zeros_like(x)
    w[0] = 0.5 * (x[1] - x[0])
    w[-1] = 0.5 * (x[-1] - x[-2])
    if len(x) > 2:
        w[1:-1] = 0.5 * (x[2:] - x[:-2])
    return w


@dataclass
class GoesData:
    times: list[datetime]
    versions: np.ndarray
    yaw: np.ndarray
    flux_sensor: np.ndarray       # [time, sensor, channel], p cm^-2 sr^-1 MeV^-1
    flux_uncert_sensor: np.ndarray
    integral_p11: np.ndarray      # [time, sensor], p cm^-2 sr^-1 s^-1, >500 MeV
    effective_mev: np.ndarray     # [sensor, channel]
    lower_mev: np.ndarray
    upper_mev: np.ndarray
    valid_sensor: np.ndarray      # [time, sensor]
    quality_any_dqf: np.ndarray   # [time, sensor]
    files: list[dict]
    calibration_applied: bool

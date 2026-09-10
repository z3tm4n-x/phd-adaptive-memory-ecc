"""Transparent sigma_bit(E) models for RE-GOES19-PROTON-RATE-01.

The source CSV remains the primary object.  No Weibull/FLUKA curves are used.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import numpy as np

MODEL_NAMES = (
    "main_loglog",
    "linear_energy",
    "gap_linear_5_40",
    "low_hold",
    "supported_only_diagnostic",
)

@dataclass(frozen=True)
class SigmaPoint:
    energy_mev: float
    sigma_cm2_bit: float
    source: str
    value_type: str


def load_experimental_points(path: str | Path) -> tuple[SigmaPoint, ...]:
    pts=[]
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            raw=(row.get("sigma_bit_cm2_per_bit") or "").strip()
            if not raw:
                continue
            e=float(row["energy_mev"])
            # Keep the exact 184-MeV anchor and the 186-MeV raw-aligned digitization as separate points.
            pts.append(SigmaPoint(e,float(raw),row.get("source","").strip(),row.get("value_type","").strip()))
    pts.sort(key=lambda p:p.energy_mev)
    # Defensive exact-energy uniqueness.
    out=[]
    for p in pts:
        if out and p.energy_mev == out[-1].energy_mev:
            raise ValueError(f"duplicate sigma energy {p.energy_mev}")
        out.append(p)
    return tuple(out)


def _interp_loglog(x: np.ndarray, xp: np.ndarray, fp: np.ndarray) -> np.ndarray:
    return np.exp(np.interp(np.log(x), np.log(xp), np.log(fp)))


def _inside_model(e: np.ndarray, xp: np.ndarray, fp: np.ndarray, model: str) -> np.ndarray:
    if model == "linear_energy":
        return np.interp(e, xp, fp)
    if model == "gap_linear_5_40":
        y=_interp_loglog(e,xp,fp)
        mask=(e>=5.0)&(e<=40.0)
        if np.any(mask):
            f5=float(fp[np.where(xp==5.0)[0][0]])
            f40=float(fp[np.where(xp==40.0)[0][0]])
            y[mask]=f5+(f40-f5)*(e[mask]-5.0)/35.0
        return y
    # main_loglog, low_hold, supported-only all use log-log inside support.
    return _interp_loglog(e,xp,fp)


def sigma_hat(energy_mev, points: tuple[SigmaPoint,...], model: str="main_loglog") -> np.ndarray:
    """Return sigma_bit in cm^2/bit.

    Main boundary rules are explicit, not silent zeros:
    - below 0.9 MeV: linear continuation of the first two experimental points,
      clipped at zero (zero crossing is data-determined by that local linear continuation);
    - above 186 MeV: constant hold at the 186-MeV experimental value;
    - inside support: log-log interpolation, ignoring unresolved 29 MeV.

    Sensitivity models alter one transparent choice at a time.
    """
    if model not in MODEL_NAMES:
        raise ValueError(model)
    e=np.asarray(energy_mev,dtype=float)
    if np.any(e<=0):
        raise ValueError("energy must be positive")
    xp=np.array([p.energy_mev for p in points],float)
    fp=np.array([p.sigma_cm2_bit for p in points],float)
    emin,emax=xp[0],xp[-1]
    y=np.empty_like(e)
    inside=(e>=emin)&(e<=emax)
    y[inside]=_inside_model(e[inside],xp,fp,model)
    low=e<emin
    high=e>emax
    if model == "supported_only_diagnostic":
        y[low]=0.0
        y[high]=0.0
    else:
        if model == "low_hold":
            y[low]=fp[0]
        else:
            # data-local linear continuation through 0.9 and 1.0 MeV.
            slope=(fp[1]-fp[0])/(xp[1]-xp[0])
            y[low]=np.maximum(0.0, fp[0] + slope*(e[low]-xp[0]))
        y[high]=fp[-1]
    return y


def zero_crossing_low(points: tuple[SigmaPoint,...]) -> float:
    p0,p1=points[0],points[1]
    slope=(p1.sigma_cm2_bit-p0.sigma_cm2_bit)/(p1.energy_mev-p0.energy_mev)
    return p0.energy_mev-p0.sigma_cm2_bit/slope

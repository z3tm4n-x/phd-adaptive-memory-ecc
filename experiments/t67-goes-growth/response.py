"""Reuse the existing CY62167/RADAR chain, without rerunning transport.

Only pure numerical functions are loaded from the pinned repository sources by
AST selection: this avoids importing the unavailable h5py dependency of the
old, hard-coded 59-file GOES-19 reader. No source statements are rewritten.
"""
from __future__ import annotations
import ast
import importlib.util
import hashlib
import math
from pathlib import Path
from types import SimpleNamespace
import sys
import numpy as np

REPO = Path(__file__).resolve().parents[2]
UPSTREAM = REPO / "experiments/RE-GOES19-PROTON-RATE-01"
TRANSPORT = REPO / "experiments/RE-CY62167-COVERAGE-THRESHOLD-01/recovery/outputs/radar_transport.npz"
SIGMA_CSV = REPO / "experiments/RE-CY62167-PROTON-01/sigma_bit_experimental.csv"
BITS = 16777216
PINNED = {
    UPSTREAM / "goes19_adapter.py": "042eedfb3cee28e567c433850fbbc832c7c1704b953ab4b7d709d049398f0abb",
    UPSTREAM / "rate_pipeline.py": "d3a1a577922a02d1d498146f2c6a6fa3888478b36a823d8d0a89f921d4ad1b52",
    UPSTREAM / "sigma_model.py": "a43de56e3939c868cbe4ed8ab43cbbc4e9b1262cd437e82da7ecce85e5497a12",
    TRANSPORT: "7f006d49c4e469b624db62b84925571c40f0602cfbd0f3b333211521dad60f9e",
    SIGMA_CSV: "841c0b4c708816a5e75867d1c49b7734c1b596b3ff793ccd1726357104e69972",
}
for path, expected in PINNED.items():
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("Pinned upstream changed: " + str(path))


def pure_functions(path, names, namespace):
    tree = ast.parse(path.read_text())
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in selected} != set(names):
        raise ValueError("upstream numerical interface changed")
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)


NS = {"np": np, "math": math}
pure_functions(UPSTREAM / "goes19_adapter.py", ["reconstruct_on_grid"], NS)
pure_functions(UPSTREAM / "rate_pipeline.py",
               ["trap_weights", "_solve_high_gamma", "_gap_integral_from_anchor",
                "_gap_integral_from_p11", "high_energy_gap_bridge"], NS)
spec = importlib.util.spec_from_file_location("t67_existing_sigma", UPSTREAM / "sigma_model.py")
sigma = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sigma
spec.loader.exec_module(sigma)


def gap_bridge(f, valid):
    """Vectorized existing 390–500 model; same daily median fallback, no new fit.

    Unlike the upstream report helper, empty directions have a defined missing
    result. Fallback is retrospective, not a causal observation estimator.
    """
    j, p = f[:, :, 12], f[:, :, 13]
    fit = valid & (j > 0) & (p > 0)
    gamma = np.full(j.shape, np.nan)
    ratio = p[fit] / (j[fit] * 500)
    lo, hi = np.full(len(ratio), 1+1e-8), np.full(len(ratio), 100.)
    while np.any((390/500)**hi/(hi-1) > ratio):
        hi[(390/500)**hi/(hi-1) > ratio] *= 2
        if np.max(hi) > 1e6:
            raise ValueError("Unqualified spectral index")
    for _ in range(80):
        mid = .5*(lo+hi)
        above = (390/500)**mid/(mid-1) > ratio
        lo[above], hi[~above] = mid[above], mid[~above]
    gamma[fit] = .5*(lo+hi)
    fallback = valid & ~fit
    med = []
    for d in range(2):
        g = float(np.median(gamma[fit[:, d], d])) if np.any(fit[:, d]) else 1.2
        gamma[fallback[:, d], d] = g
        med.append(g)
    gap = np.full(j.shape, np.nan)
    g = gamma[fit]
    gap[fit] = j[fit]*390*np.expm1((1-g)*math.log(500/390))/(1-g)
    gap[fallback] = p[fallback]*np.expm1((gamma[fallback]-1)*math.log(500/390))
    diag = {"direction_median_gamma": dict(zip(("E", "W"), med)),
            "fallback_rows": {name:int(np.sum(fallback[:,d])) for d,name in enumerate(("E", "W"))}}
    return gap, fallback, diag


class Response:
    def __init__(self):
        z = np.load(TRANSPORT)
        self.energy = z["energy_mev"]
        idx = list(z["shield_mm"]).index(10.0)
        self.primary, self.secondary = z["primary"][idx], z["secondary"][idx]
        self.points = sigma.load_experimental_points(SIGMA_CSV)
        self.weights = NS["trap_weights"](self.energy)
        self.models = ["main_loglog", "linear_energy", "gap_linear_5_40", "low_hold"]
        self.kernels = {}

    def channel_kernel(self, src, sensor, model):
        key = (src.signature, sensor, model)
        if key in self.kernels:
            return self.kernels[key]
        columns = []
        for c in range(13):
            basis = np.eye(13)[c]
            j = NS["reconstruct_on_grid"](src.energy[sensor], basis, src.lower[sensor, 0], src.upper[sensor, -1], self.energy)
            j = np.nan_to_num(j, nan=0.0)
            # Existing gamma=2 scenario below P1. At 10 mm it is numerically
            # absent for the pinned transfer; do not silently assume that.
            if c == 0:
                mask = (self.energy >= sigma.zero_crossing_low(self.points)) & (self.energy < src.lower[sensor, 0])
                j[mask] += (self.energy[mask] / src.lower[sensor, 0]) ** -2
            columns.append(j)
        basis = np.asarray(columns).T
        w = self.weights * sigma.sigma_hat(self.energy, self.points, model)
        factor = BITS * 4 * math.pi
        kp = factor * (basis.T @ self.primary.T @ w)
        ks = factor * (basis.T @ self.secondary.T @ w)
        self.kernels[key] = (kp, ks, basis)
        return kp, ks, basis

    def calculate(self, src):
        n = len(src.time)
        f = src.corrected
        valid = np.all(np.isfinite(f), axis=2)
        gap, fallback, diag = gap_bridge(f, valid)
        output = {}
        for model in self.models:
            primary = np.full((n, 2), np.nan)
            secondary = np.full((n, 2), np.nan)
            high_sigma = float(sigma.sigma_hat(np.array([600.]), self.points, model)[0])
            tail = BITS * 4 * math.pi * high_sigma * (gap + f[:, :, 13])
            for d in range(2):
                for yaw in (0, 2):
                    sensor = (1-d) if yaw == 0 else d
                    ok = valid[:, d] & (src.yaw == yaw)
                    kp, ks, _ = self.channel_kernel(src, sensor, model)
                    primary[ok, d] = f[ok, d, :13] @ kp
                    secondary[ok, d] = f[ok, d, :13] @ ks
            output[model] = primary + secondary + tail
            if model == "main_loglog":
                output["core_primary"] = primary
                output["core_secondary"] = secondary
                output["high_energy_model"] = tail
        # Median-gamma fallback depends on the file's spectrum and is descriptive
        # only; exclude from the strict growth view to avoid inferred zero issues.
        output["strict"] = np.all(src.strict, axis=2) & (f[:, :, 12] > 0) & (f[:, :, 13] > 0)
        # Screen only channels actually used by the pinned 10 mm response.
        screened = np.zeros((n, 2), bool)
        core_strict = np.zeros((n, 2), bool)
        for d in range(2):
            for yaw in (0, 2):
                sensor = (1-d) if yaw == 0 else d
                kp, ks, _ = self.channel_kernel(src, sensor, "main_loglog")
                active = np.flatnonzero(kp + ks > 0)
                m = src.yaw == yaw
                screened[m, d] = np.all(src.screened[m, d][:, np.r_[active,13]], axis=1)
                core_strict[m, d] = np.all(src.strict[m, d][:, active], axis=1)
        output["screened"] = screened
        output["core_strict"] = core_strict
        output["core_only"] = output["core_primary"] + output["core_secondary"]
        output["fallback"] = fallback
        output["gap_diagnostics"] = diag
        return output

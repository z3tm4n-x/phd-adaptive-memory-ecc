"""Primary-proton CSDA calculation in a centred spherical Al shell.

The integration variable is incident energy: transmitted particles retain their
weight; stopped particles are removed, never renormalized. No nuclear-secondary
or angular-scattering claim is attached to this primary-only model.
"""
import csv
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np
from numpy.polynomial.legendre import leggauss
from numpy.polynomial.hermite import hermgauss
from scipy.integrate import cumulative_trapezoid
from scipy.special import logsumexp

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
ENERGY = np.array(CFG["proton_energy_MeV"])
BITS = CFG["words"] * CFG["protected_bits_per_word"]
ANGULAR = 4*math.pi
SIGMA_PATH = REPO / "experiments/RE-CY62167-PROTON-01/sigma_bit_experimental.csv"
SIGMA_MODULE = REPO / "experiments/RE-GOES19-PROTON-RATE-01/sigma_model.py"
spec = importlib.util.spec_from_file_location("sepem_existing_sigma", SIGMA_MODULE)
sigma_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sigma_module
spec.loader.exec_module(sigma_module)
POINTS = sigma_module.load_experimental_points(SIGMA_PATH)
SIGMA_E = np.array([p.energy_mev for p in POINTS])
SIGMA_S = np.array([p.sigma_cm2_bit for p in POINTS])


class RangeTable:
    def __init__(self):
        tab = np.genfromtxt(HERE/"inputs/nist_pstar_al.csv", delimiter=",", names=True)
        self.energy = tab["energy_mev"]
        self.ranges = tab["csda_range_g_cm2"]
        self.stopping = tab["total_stopping_mev_cm2_g"]

    def range(self, e):
        e = np.asarray(e)
        if np.any(e <= 0) or np.any(e > self.energy[-1]):
            raise ValueError("Energy outside positive PSTAR table")
        return np.exp(np.interp(np.log(e), np.log(self.energy), np.log(self.ranges)))

    def inverse(self, r):
        r = np.asarray(r)
        return np.where(r > self.ranges[0],
                        np.exp(np.interp(np.log(np.maximum(r, self.ranges[0])),
                                         np.log(self.ranges), np.log(self.energy))), 0.)

    def residual(self, energy, thickness):
        return self.inverse(self.range(energy)-thickness)

    def bohr_range_sd(self, thickness):
        # Thick, nonrelativistic Bohr approximation for z=1, Al Z/A.
        # Var(R) = integral v_E / S(E)^3 dE. Used only to set the width of
        # a near-stopping sensitivity model, not a validated transport kernel.
        e0 = float(self.inverse(thickness))
        e = np.unique(np.r_[np.geomspace(.001, e0, 4001), self.energy[self.energy < e0]])
        stopping = np.exp(np.interp(np.log(e), np.log(self.energy), np.log(self.stopping)))
        bohr = .1569 * 13 / 26.9815385  # MeV^2 per (g/cm^2)
        return float(np.sqrt(np.trapezoid(bohr/stopping**3, e)))


def sigma(energy, model="pdi"):
    e = np.asarray(energy, dtype=float)
    result = np.zeros_like(e)
    keep = e > 0
    if model == "no_pdi":
        # Explicit mechanism-removal diagnostic; not a second measured device.
        result[keep & (e >= 5)] = sigma_module.sigma_hat(e[keep & (e >= 5)], POINTS)
    elif model == "step_envelope":
        # Upper envelope of the declared log-log interpolant, NOT an
        # experimental confidence envelope or device/lot upper bound.
        v = e[keep]
        k = np.clip(np.searchsorted(SIGMA_E, v)-1, 0, len(SIGMA_E)-2)
        r = np.maximum(SIGMA_S[k], SIGMA_S[k+1])
        r[v < SIGMA_E[0]] = SIGMA_S[0]
        r[v > SIGMA_E[-1]] = SIGMA_S[-1]
        result[keep] = r
    else:
        result[keep] = sigma_module.sigma_hat(e[keep], POINTS)
    return result


def quadrature(table, rho, model="pdi", order=12):
    # Splits resolve all range and sigma knots, including the very narrow
    # incident band mapped onto the measured 0.9--1.1 MeV PDI peak.
    residual_knots = np.r_[.001, sigma_module.zero_crossing_low(POINTS), SIGMA_E,
                           table.energy]
    incident_knots = table.inverse(rho + table.range(residual_knots))
    cuts = np.unique(np.r_[5., ENERGY, 289.2, 500., 1000., 3000., 10000.,
                           table.energy, incident_knots, table.inverse(rho)])
    cuts = cuts[(cuts >= 5) & (cuts <= 10000)]
    z, w = leggauss(order)
    lo, hi = cuts[:-1], cuts[1:]
    e = ((lo[:,None]+hi[:,None])/2+(hi-lo)[:,None]/2*z).ravel()
    weights = ((hi-lo)[:,None]/2*w).ravel()
    residual = table.residual(e, rho)
    return e, weights*sigma(residual, model), weights, residual


class Response:
    """Fast piecewise-power-law convolution using positive moment tables.

    Lookup uses linear interpolation of log M(s), M(s)=int w(E)(E/Ei)^s dE.
    Log-M curvature is Var(log(E/Ei)) <= log(hi/lo)^2/4. Thus lookup relative
    error <= exp(ds^2 log(hi/lo)^2/32)-1, independently of the data's slopes.
    Quadrature discretization is checked separately, not included in that bound.
    """
    def __init__(self, order=12, slope_step=.02, hermite_order=15):
        self.table = RangeTable()
        self.slope_grid = np.arange(-80, 40+slope_step/2, slope_step)
        self.slope_step = slope_step
        self.bands = np.r_[5., ENERGY, 289.2, 500., 1000., 3000., 10000.]
        self.kernels = {}
        self.quadratures = {}
        definitions = [("csda_3_pdi",3.,"pdi",False),
                       ("csda_2p5_pdi",2.5,"pdi",False),
                       ("csda_3_no_pdi",3.,"no_pdi",False),
                       ("csda_3_interpolant_upper",3.,"step_envelope",False),
                       ("bohr_3_pdi",3.,"pdi",True),
                       ("bohr_2p5_pdi",2.5,"pdi",True)]
        for name,rho,model,straggle in definitions:
            if straggle:
                h, w = hermgauss(hermite_order)
                sd = self.table.bohr_range_sd(rho)
                shifts = rho+np.sqrt(2)*sd*h
                if np.any(shifts <= 0):
                    raise ValueError("Straggling quadrature crosses nonpositive shell")
                quads = [quadrature(self.table, float(x), model, order) for x in shifts]
                e = np.concatenate([q[0] for q in quads])
                weights = np.concatenate([q[1]*a/math.sqrt(math.pi) for q,a in zip(quads,w)])
            else:
                e,weights,_,_ = quadrature(self.table,rho,model,order)
            self.quadratures[name] = (e,weights)
            moments=[]
            for lo,hi in zip(self.bands[:-1],self.bands[1:]):
                idx = (e >= lo)&(e < hi)&(weights > 0)
                if not np.any(idx):
                    moments.append(None)
                    continue
                anchor = self._anchor(lo,hi)
                logx = np.log(e[idx]/ENERGY[anchor])
                # Chunk keeps Bohr sensitivity's precomputation bounded.
                val = np.empty(len(self.slope_grid))
                for first in range(0,len(val),200):
                    a = self.slope_grid[first:first+200]
                    val[first:first+len(a)] = logsumexp(a[:,None]*logx+np.log(weights[idx]),axis=1)
                moments.append(val)
            self.kernels[name] = moments

    @staticmethod
    def _anchor(lo,hi):
        return int(np.clip(np.searchsorted(ENERGY,(lo+hi)/2)-1,0,len(ENERGY)-2))

    def calculate(self, flux):
        f = np.asarray(flux)
        if f.ndim != 2 or f.shape[1] != 11 or not np.all(np.isfinite(f)) or np.any(f <= 0):
            raise ValueError("H spectra must contain 11 finite strictly positive channels")
        slopes = np.diff(np.log(f),axis=1)/np.diff(np.log(ENERGY))
        if np.any(slopes < self.slope_grid[0]) or np.any(slopes > self.slope_grid[-1]):
            raise ValueError("Moment lookup slope range exceeded; no silent clipping")
        output={name:np.zeros(len(f)) for name in self.kernels}
        output.update({"csda_3_cut289":np.zeros(len(f)),"csda_3_cut1000":np.zeros(len(f)),
                       "csda_3_jlinear_logE":np.zeros(len(f))})
        integrals=np.zeros((len(f),4))
        for band,(lo,hi) in enumerate(zip(self.bands[:-1],self.bands[1:])):
            k = self._anchor(lo,hi)
            s = slopes[:,k].copy()
            amp = f[:,k].copy()
            if lo >= ENERGY[-1]:
                # Anchor high extension to the last measured centre.
                s = np.minimum(slopes[:,-1],-2.)
                amp = f[:,-1]*np.exp(s*np.log(ENERGY[k]/ENERGY[-1]))
            for name,moments in self.kernels.items():
                if moments[band] is None:
                    continue
                part = amp*np.exp(np.interp(s,self.slope_grid,moments[band]))*BITS*ANGULAR
                output[name] += part
                if name == "csda_3_pdi":
                    if hi <= 289.2:
                        output["csda_3_cut289"] += part
                    if hi <= 1000:
                        output["csda_3_cut1000"] += part
                    if lo < ENERGY[0] or lo >= ENERGY[-1]:
                        output["csda_3_jlinear_logE"] += part
                    else:
                        e,w = self.quadratures[name]
                        idx=(e>=lo)&(e<hi)
                        x=np.log(e[idx]/ENERGY[k])/np.log(ENERGY[k+1]/ENERGY[k])
                        output["csda_3_jlinear_logE"] += BITS*ANGULAR*(
                            f[:,k]*np.sum(w[idx]*(1-x))+f[:,k+1]*np.sum(w[idx]*x))
            for j,threshold in enumerate((10,30,60,100)):
                low=max(lo,threshold)
                if low < hi:
                    v=s+1
                    # Stable analytic integral of the reconstructed power law.
                    t=np.log(hi/low)
                    ratio=np.empty_like(v)
                    near=np.abs(v)<1e-10
                    ratio[near]=t
                    ratio[~near]=np.expm1(v[~near]*t)/v[~near]
                    integrals[:,j] += amp*low*np.exp(s*np.log(low/ENERGY[k]))*ratio
        return output,integrals, {"slope_min":float(slopes.min()),"slope_max":float(slopes.max()),
                                  "tail_slope_limited_rows":int(np.sum(slopes[:,-1]>-2))}

    def metadata(self):
        width=float(np.max(np.log(self.bands[1:]/self.bands[:-1])))
        return {"bits":BITS,"angular_factor":ANGULAR,
                "pdi_incident_energy_MeV_rho3":float(self.table.inverse(3+self.table.range(1))),
                "stopping_threshold_MeV_rho3":float(self.table.inverse(3)),
                "bohr_near_stopping_range_sd_g_cm2":{str(r):self.table.bohr_range_sd(r) for r in (2.5,3)},
                "lookup_relative_error_bound":math.expm1(self.slope_step**2*width**2/32),
                "lookup_scope":"positive discrete quadrature, excluding quadrature/model error",
                "variants":list(self.kernels),"nuclear_secondaries":"not included; not assumed absent",
                "physical_sigma_upper_bound":None,"helium_and_heavy_ion_rate":None}

"""Conditional helium sensitivity, not a measured CY62167 alpha response.

Assumptions: primary alpha particles, straight CSDA rays to the centre of a
spherical Al shell, isotropic flux, and species/angle-independent application
of the historical CY62167 LET Weibull to silicon electronic stopping power.
The LET Weibull is reproduced from t68-v21-inputs/inputs/calc_v18.zip,
orbital.py:sb; it is NOT an alpha-particle calibration or upper bound.
Nuclear reactions, secondaries, range straggling and Z>=3 ions are not covered.

RDS flux is per MeV/nucleon. E_alpha=4 E_nuc and j_alpha=j_nuc/4. Integration
below is in E_nuc, so the Jacobian cancels: there is no extra factor of four.
CSV extraction uses only standard-library numeric source extraction. The CSV
files are computational inputs, not formatted spreadsheet artifacts.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import re
import numpy as np
from numpy.polynomial.legendre import leggauss

HERE = Path(__file__).resolve().parent
ENERGY = np.array([6.01, 8.70, 12.58, 18.18, 26.30, 38.03, 54.99, 79.53])
NOMINAL_MAX = 95.64
ALPHA_MASS_NUMBER = 4
FIELDS = ["energy_mev", "electronic_stopping_mev_cm2_g",
          "nuclear_stopping_mev_cm2_g", "total_stopping_mev_cm2_g",
          "csda_range_g_cm2", "projected_range_g_cm2", "detour"]


def parse_astar(text, material):
    text = html.unescape(text)
    if material.upper() not in text.upper() or "ALPHA" not in text.upper():
        raise ValueError("Not the expected ASTAR material/particle table")
    rows = []
    for line in re.split(r"<br\s*/?>|\n", text, flags=re.I):
        fields = line.split()
        if len(fields) != 7:
            continue
        try:
            rows.append(list(map(float, fields)))
        except ValueError:
            pass
    a = np.asarray(rows)
    if (len(a) < 100 or a.shape[1] != 7 or not np.all(np.isfinite(a))
            or np.any(a <= 0) or np.any(np.diff(a[:, 0]) <= 0)
            or np.any(np.diff(a[:, 4]) <= 0)):
        raise ValueError("Missing, invalid or unsorted ASTAR table")
    return rows


def extract_astar(al_html, si_html, target=HERE / "inputs"):
    """Reproduce the two derived CSV inputs; raw HTML remains outside Git."""
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    meta = {"retrieved": "2026-10-07", "energy_convention": "total kinetic MeV per alpha particle",
            "url": "https://physics.nist.gov/cgi-bin/Star/ap_table-t.pl",
            "documentation": "https://physics.nist.gov/PhysRefData/Star/Text/programs.html",
            "scope": "ASTAR CSDA and stopping powers; not a secondary transport calculation",
            "tables": []}
    for src, label, symbol, number in [(al_html, "ALUMINUM", "al", "013"),
                                        (si_html, "SILICON", "si", "014")]:
        raw = Path(src).read_bytes()
        rows = parse_astar(raw.decode("utf-8"), label)
        out = target / f"nist_astar_{symbol}.csv"
        with out.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(FIELDS)
            writer.writerows(rows)
        meta["tables"].append({"material": label, "post": {"prog": "ASTAR", "matno": number,
                                    "Energies": "", "ShowDefault": "on"},
            "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
            "derived_csv": out.name, "derived_csv_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
            "rows": len(rows), "total_energy_MeV": [rows[0][0], rows[-1][0]],
            "energy_MeV_per_nucleon": [rows[0][0]/4, rows[-1][0]/4]})
    (target / "astar_manifest.json").write_text(json.dumps(meta, indent=2)+"\n", encoding="utf-8")
    return meta


def sigma_let(let):
    """Historical cm^2/bit Weibull; LET in MeV cm^2/mg."""
    l = np.asarray(let, dtype=float)
    return 2.6e-7 * (-np.expm1(-(np.maximum(l - .15, 0.) / 70.)**1.2))


class AlphaTable:
    def __init__(self, material):
        a = np.genfromtxt(HERE / f"inputs/nist_astar_{material}.csv", delimiter=",", names=True)
        self.energy = a["energy_mev"]
        self.ranges = a["csda_range_g_cm2"]
        self.electronic = a["electronic_stopping_mev_cm2_g"]

    def range(self, total_energy):
        e = np.asarray(total_energy, dtype=float)
        if np.any(e < self.energy[0]) or np.any(e > self.energy[-1]):
            raise ValueError("Total alpha energy outside ASTAR support")
        return np.exp(np.interp(np.log(e), np.log(self.energy), np.log(self.ranges)))

    def inverse(self, r):
        r = np.asarray(r, dtype=float)
        if np.any(r > self.ranges[-1]):
            raise ValueError("Range outside ASTAR support")
        # Explicit computational cutoff: residual total energy <1 keV is
        # discarded. This cutoff is a model approximation, not exact stopping.
        return np.where(r >= self.ranges[0],
                        np.exp(np.interp(np.log(np.maximum(r, self.ranges[0])),
                                         np.log(self.ranges), np.log(self.energy))), 0.)

    def residual(self, energy_nuc, density):
        return self.inverse(self.range(ALPHA_MASS_NUMBER*np.asarray(energy_nuc))-density)

    def let(self, total_energy):
        e = np.asarray(total_energy, dtype=float)
        if np.any(e < 0) or np.any(e > self.energy[-1]):
            raise ValueError("Residual total alpha energy outside ASTAR support")
        result = np.zeros_like(e)
        use = e >= self.energy[0]
        result[use] = np.exp(np.interp(np.log(e[use]), np.log(self.energy),
                                       np.log(self.electronic))) / 1000.
        return result


def interpolate_spectrum(flux, energy):
    """Independent eight-channel interpolation, including legitimate zeros.

    Log-log for two positive endpoints. Otherwise linear flux in log energy,
    clipped at zero on the two edge extrapolations. No missing value becomes 0.
    """
    f = np.atleast_2d(np.asarray(flux, dtype=float))
    if f.shape[1] != 8 or np.any(~np.isfinite(f)) or np.any(f < 0):
        raise ValueError("Helium requires eight finite nonnegative channels")
    e = np.asarray(energy, dtype=float)
    if np.any(e < 5) or np.any(e > NOMINAL_MAX):
        raise ValueError("Spectrum lookup outside nominal measured channel bounds")
    k = np.clip(np.searchsorted(ENERGY, e)-1, 0, 6)
    x = np.log(e/ENERGY[k]) / np.log(ENERGY[k+1]/ENERGY[k])
    a, b = f[:, k], f[:, k+1]
    result = np.maximum(a*(1-x)+b*x, 0.)
    pos = (a > 0) & (b > 0)
    safe_a, safe_b = np.maximum(a, 1e-300), np.maximum(b, 1e-300)
    return np.where(pos, np.exp(np.log(safe_a)*(1-x)+np.log(safe_b)*x), result)


class HeliumResponse:
    def __init__(self, bits=19922944, order=16, slope_step=.02):
        self.al, self.si = AlphaTable("al"), AlphaTable("si")
        self.bits = int(bits)
        self.angular = 4*math.pi
        self.slope_step = slope_step
        self.slopes = np.arange(-200., 200.+slope_step/2, slope_step)
        self.tail_max = min(self.al.energy[-1], self.si.energy[-1])/4
        self.bands = np.r_[5., ENERGY, NOMINAL_MAX, self.tail_max]
        self.kernels, self.quadratures = {}, {}
        for label, rho in [("helium_3", 3.), ("helium_2p5", 2.5)]:
            if self.al.range(4*5.) >= rho:
                raise ValueError("Below-5 exclusion is not justified by CSDA stopping")
            # Split at material knots and at mapped residual knots, resolving
            # the low-energy LET peak and the Weibull threshold numerically.
            # Add the two LET threshold crossings explicitly, so the onset
            # of the Weibull is not left inside an unsplit quadrature band.
            roots = []
            y = self.si.electronic/1000.
            for i in np.flatnonzero((y[:-1]-.15)*(y[1:]-.15) < 0):
                a = np.log(.15/y[i])/np.log(y[i+1]/y[i])
                roots.append(self.si.energy[i]*(self.si.energy[i+1]/self.si.energy[i])**a)
            residual_knots = np.unique(np.r_[self.al.energy, self.si.energy, roots])
            incident = self.al.inverse(np.minimum(rho+self.al.range(residual_knots), self.al.ranges[-1]))/4
            cuts = np.unique(np.r_[self.bands, self.al.energy/4, incident, self.al.inverse(rho)/4])
            cuts = cuts[(cuts >= 5) & (cuts <= self.tail_max)]
            z, w = leggauss(order)
            lo, hi = cuts[:-1], cuts[1:]
            e = ((lo[:, None]+hi[:, None])/2+(hi-lo)[:, None]*z/2).ravel()
            weights = ((hi-lo)[:, None]*w/2).ravel()
            residual = self.al.residual(e, rho)
            weights *= sigma_let(self.si.let(residual))
            self.quadratures[label] = (e, weights)
            moments = []
            for low, high in zip(self.bands[:-1], self.bands[1:]):
                k = int(np.clip(np.searchsorted(ENERGY, (low+high)/2)-1, 0, 6))
                idx = (e >= low) & (e < high) & (weights > 0)
                if not np.any(idx):
                    moments.append(None)
                    continue
                anchor = NOMINAL_MAX if low >= NOMINAL_MAX else ENERGY[k]
                logx = np.log(e[idx]/anchor)
                lookup = np.empty(len(self.slopes))
                for first in range(0, len(lookup), 256):
                    s = self.slopes[first:first+256]
                    values = s[:, None]*logx+np.log(weights[idx])
                    maximum = values.max(axis=1)
                    lookup[first:first+len(s)] = maximum+np.log(np.exp(values-maximum[:, None]).sum(axis=1))
                x = np.log(e[idx]/ENERGY[k])/np.log(ENERGY[k+1]/ENERGY[k])
                moments.append((k, lookup, float(np.sum(weights[idx]*(1-x))), float(np.sum(weights[idx]*x))))
            self.kernels[label] = moments

    def calculate(self, flux):
        f = np.atleast_2d(np.asarray(flux, dtype=float))
        if f.shape[1] != 8 or np.any(~np.isfinite(f)) or np.any(f < 0):
            raise ValueError("Helium requires eight finite nonnegative channels")
        result = {key: np.zeros(len(f)) for name in self.kernels for key in (name, name+"_tail250")}
        for name, moments in self.kernels.items():
            for band, moment in enumerate(moments):
                if moment is None:
                    continue
                k, lookup, left, right = moment
                a, b = f[:, k], f[:, k+1]
                positive = (a > 0) & (b > 0)
                s = np.zeros(len(f))
                s[positive] = np.log(b[positive]/a[positive])/np.log(ENERGY[k+1]/ENERGY[k])
                if np.any(s[positive] < self.slopes[0]) or np.any(s[positive] > self.slopes[-1]):
                    raise ValueError("Helium moment slope range exceeded; no silent clipping")
                if self.bands[band] >= NOMINAL_MAX:
                    s = np.minimum(s, -2.)
                    # Last zero channel gives zero only for this declared tail
                    # reconstruction, not a physical upper bound beyond RDS.
                    amp = interpolate_spectrum(f, np.array([NOMINAL_MAX]))[:, 0]
                    part = amp*np.exp(np.interp(s, self.slopes, lookup))
                    result[name+"_tail250"] += part*self.bits*self.angular
                    continue
                part = a*left+b*right
                if self.bands[band] < ENERGY[0]:
                    part[a == 0] = 0.
                if self.bands[band] >= ENERGY[-1]:
                    part[b == 0] = 0.
                part[positive] = a[positive]*np.exp(np.interp(s[positive], self.slopes, lookup))
                part = np.maximum(part, 0.)*self.bits*self.angular
                result[name] += part
                result[name+"_tail250"] += part
        return result

    def metadata(self):
        return {"status": "conditional model sensitivity only; not measured helium response or upper bound",
            "bits": self.bits, "angular_factor": self.angular, "alpha_mass_number": 4,
            "flux_units": "cm^-2 s^-1 sr^-1 (MeV/nucleon)^-1",
            "integration_variable": "incident MeV/nucleon; j_alpha dE_alpha = j_nuc dE_nuc",
            "nominal_cutoff_MeV_per_nucleon": NOMINAL_MAX,
            "tail_sensitivity": "last pair slope limited to <= -2, continuous at 95.64, cutoff 250 MeV/nucleon",
            "astar_max_total_energy_MeV": float(self.al.energy[-1]),
            "requested_tail_to_1000_MeV_per_nucleon": "unsupported by the saved ASTAR tables; not extrapolated",
            "tail_above_250": None,
            "interpolation": "log-log positive endpoints; linear j/logE for zero endpoint, clipped at zero at edges",
            "response": "sigma_bit=2.6e-7*(1-exp(-((LET-0.15)/70)^1.2)) for LET>0.15; cm^2/bit",
            "let_units": "MeV cm^2/mg; ASTAR Si electronic stopping divided by 1000",
            "response_provenance": "experiments/t68-v21-inputs/inputs/calc_v18.zip: orbital.py sb",
            "response_transfer_assumption": "species and incidence-angle invariance of historical LET Weibull",
            "check_bit_sensitivity": "same as data bits, user-declared assumption",
            "minimum_residual_energy_keV": 1.,
            "sub_keV_rule": "discarded as explicit computational cutoff, not proven zero physical response",
            "stopping_threshold_MeV_per_nucleon": {str(x): float(self.al.inverse(x)/4) for x in (2.5, 3.)},
            "below_5_range_g_cm2": float(self.al.range(20.)),
            "moment_lookup_relative_error_bound": math.expm1(self.slope_step**2*max(np.log(self.bands[1:]/self.bands[:-1]))**2/32),
            "lookup_bound_scope": "positive discrete quadrature only; excludes quadrature and model errors",
            "helium_nuclear_response": None, "Z_ge_3_rate": None,
            "shared_dependencies": ["audit.input_files", "audit.digest", "numpy"],
            "production_proton_mapping_or_response_helpers_reused": False}


def compute_helium(path, cache, n):
    """Return {'arrays': {key: memmap}, 'metadata': ...}; never launch implicitly.

    Reads audited reference identity and verifies exact row/time alignment.
    Raw source remains external. Call after audit.py, from the parent pipeline.
    """
    import pandas as pd
    from audit import input_files, digest
    path, cache = Path(path), Path(cache)
    if HERE in cache.resolve().parents or cache.resolve() == HERE:
        raise ValueError("Derived full-row helium cache must remain outside Git package")
    audit = json.loads((HERE/"outputs/input_audit.json").read_text())
    ref = audit["reference_series"]["SEPEM_He_reference.txt"]
    h_ref = audit["reference_series"]["SEPEM_H_reference.txt"]
    if not ref["numerically_complete"] or ref["records"] != n:
        raise ValueError("Helium reference count/completeness mismatch")
    if any(ref[k] != h_ref[k] for k in ("records", "first_bin_start", "end_exclusive")):
        raise ValueError("Hydrogen and helium time axes differ")
    cfg = json.loads((HERE/"config.json").read_text())
    response = HeliumResponse(bits=cfg["words"]*cfg["protected_bits_per_word"])
    cache.mkdir(parents=True, exist_ok=True)
    keys = [key for name in response.kernels for key in (name, name+"_tail250")]
    arrays = {key: np.lib.format.open_memmap(cache/(key+".npy"), mode="w+", dtype="float64", shape=(n,)) for key in keys}
    offset, zeros = 0, np.zeros(8, dtype=np.int64)
    first = np.datetime64(ref["first_bin_start"], "s")
    with input_files(path) as files:
        candidates = [v for v in files if Path(v[0]).name == "SEPEM_He_reference.txt"]
        if len(candidates) != 1:
            raise ValueError("Exactly one helium reference required")
        with candidates[0][2]() as stream:
            if digest(stream) != ref["sha256"]:
                raise ValueError("Helium bytes differ from audited source")
        with candidates[0][2]() as stream:
            for chunk in pd.read_csv(stream, skiprows=1, header=None, chunksize=50000):
                if chunk.shape[1] != 9:
                    raise ValueError("Helium CSV must contain timestamp and eight channels")
                flux = chunk.iloc[:, 1:].to_numpy(dtype=float)
                stop = offset+len(flux)
                times = chunk.iloc[:, 0].to_numpy(dtype="datetime64[s]")
                expected = first+np.arange(offset, stop)*np.timedelta64(300, "s")
                if stop > n or not np.array_equal(times, expected):
                    raise ValueError("Helium timestamps changed from audited grid")
                rates = response.calculate(flux)
                for key, values in rates.items():
                    arrays[key][offset:stop] = values
                zeros += np.sum(flux == 0, axis=0)
                offset = stop
    if offset != n:
        raise ValueError("Helium reference row count changed")
    for arr in arrays.values():
        arr.flush()
    meta = response.metadata()
    meta.update({"reference_sha256": ref["sha256"], "n": n, "rate_keys": keys,
                 "zeros_by_channel": zeros.tolist(), "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 "astar_manifest": json.loads((HERE/"inputs/astar_manifest.json").read_text())})
    return {"arrays": arrays, "metadata": meta}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract ASTAR source tables only; does not process RDS")
    parser.add_argument("--extract-astar", nargs=2, type=Path, metavar=("AL_HTML", "SI_HTML"), required=True)
    args = parser.parse_args()
    print(json.dumps(extract_astar(*args.extract_astar), indent=2))

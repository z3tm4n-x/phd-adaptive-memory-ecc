"""Pinned profiles and exogenous marked parents shared by all port policies."""
import hashlib
import json
from pathlib import Path

import numpy as np

from engine import CFG, HERE, W

EXP = HERE.parent
NS = 10**9
BITS = CFG["bits_per_word"]
SCALE = W * BITS / CFG["reference_bits"]


def load(path):
    return json.loads((EXP / path).read_bytes())


class Profile:
    def __init__(self, spec, cache=None):
        self.spec = spec
        self.name = spec["id"]
        self.horizon = spec["T_s"] * NS
        ost = load("t186-ost-geo-3g/result.json")
        if self.name == "stress":
            self.duration = spec["pulse_duration_ns"]
            self.starts = np.asarray(spec["pulse_start_s"], dtype="int64") * NS
            self.mass = (len(self.starts) * self.duration / NS
                         * spec["bank_inversions_per_s_during_pulse"])
            self.notes = {"bank_inversions_expected": self.mass}
        elif self.name == "class_plateau":
            env = ost["archive"]["old_limits"]
            b, B = env["b"], env["B"]
            # Nearest integer nanosecond for a single deterministic edge.
            self.split = round(NS * (env["S1"] - b * spec["T_s"]) / (B - b))
            high_mass = B * (self.split / NS)
            low_mass = b * ((self.horizon - self.split) / NS)
            self.high_fraction = high_mass / (high_mass + low_mass)
            self.mass = (high_mass + low_mass) * SCALE
            self.notes = {"plateau_duration_ns": self.split, "S1_reference": high_mass + low_mass,
                          "S2_reference_per_s": B * high_mass + b * low_mass,
                          "bank_inversions_expected": self.mass}
        else:
            if cache is None:
                raise ValueError("SEPEM requires --cache pointing to the T141 cache (bands.npy)")
            path = Path(cache) / "bands.npy"
            provenance = load("t141-radiation-chain/outputs/profile-provenance.json")
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            assert digest == provenance["input"]["arrays_sha256"]["bands.npy"]
            sepem = load("c1-geo-fixed-20261109/sepem.json")
            witness = load("t196-archive-same-map-20261110/result.json")["archive"]
            bins, i = witness["number_bins"], spec["start_bin"]
            assert i == witness["start_bin"] == sepem["maxima"]["S2"]["start_bin"]
            data = np.load(path, mmap_mode="r")[i - 1:i + bins, 1]
            raw = data[:, 0] + data[:, 1]
            total = (ost["ost_tabulated"]["b"] + (1 + ost["archive"]["beta_ost_tabulated"])
                     * np.maximum(raw - sepem["H_p10"], 0))
            self.mean = total[1:]
            self.low = np.minimum(total[:-1], self.mean)
            self.slope = 2 * (self.mean - self.low)  # change across one full bin
            high = self.low + self.slope
            dt = spec["bin_s"]
            self.bin_ns = dt * NS
            assert bins * self.bin_ns == self.horizon
            self.cdf = np.cumsum(self.mean)
            s1 = float(dt * np.sum(self.mean))
            s2 = float(dt / 3 * np.sum(self.low**2 + self.low * high + high**2))
            assert abs(s1 - witness["S1_witness_approx"]) < 1e-6
            assert abs(s2 - witness["S2_reconstruction_approx"]) < 1e-6
            self.mass = s1 * SCALE
            self.notes = {"start_utc": witness["start"], "end_utc": witness["stop"],
                          "bands_sha256": digest, "S1_reference": s1, "S2_reference_per_s": s2,
                          "bank_inversions_expected": self.mass}

    def times(self, rng, n):
        if self.name == "stress":
            return self.starts[rng.integers(len(self.starts), size=n)] + rng.integers(self.duration, size=n)
        if self.name == "class_plateau":
            high = rng.random(n) < self.high_fraction
            times = np.empty(n, dtype=np.int64)
            times[high] = rng.integers(self.split, size=int(high.sum()))
            times[~high] = rng.integers(self.split, self.horizon, size=int((~high).sum()))
            return times
        which = self.cdf.searchsorted(rng.random(n) * self.cdf[-1], side="right")
        a, d = self.low[which], self.slope[which]
        u_mean = rng.random(n) * self.mean[which]
        # Solve a*x + d*x^2/2 = U*mean without subtracting two near-equal roots.
        x = 2 * u_mean / (a + np.sqrt(a * a + 2 * d * u_mean))
        return which * self.bin_ns + np.minimum((x * self.bin_ns).astype(np.int64), self.bin_ns - 1)


def generate(profile, profile_id, law_id, batch, size):
    rng = np.random.Generator(np.random.PCG64([CFG["seed"], profile_id, law_id, batch]))
    law = CFG["laws"][law_id]
    numerator, denominator = law["mean"]
    counts = rng.poisson(profile.mass * denominator / numerator, size=size)
    owner = np.repeat(np.arange(size), counts)
    n = len(owner)
    time = profile.times(rng, n)
    order = np.lexsort((time, owner))
    time = time[order]
    # Arrival times sorted within replica. Assign independent marks in that order.
    start = rng.integers(W, size=n)
    kind = law["id"]
    if kind == "two_uniform":
        other = rng.integers(W - 1, size=n)
        words = np.column_stack((start, other + (other >= start))).ravel()
        multiplicity = np.full(n, 2, dtype="int64")
    elif kind == "compact_5":
        words = ((start[:, None] + np.arange(5)) % W).ravel()
        multiplicity = np.full(n, 5, dtype="int64")
    elif kind == "compact_1p2":
        pair = rng.integers(5, size=n) == 0
        multiplicity = 1 + pair
        pos = np.cumsum(multiplicity) - multiplicity
        words = np.empty(int(multiplicity.sum()), dtype="int64")
        words[pos] = start
        words[pos[pair] + 1] = (start[pair] + 1) % W
    else:
        assert kind == "single"
        multiplicity = np.ones(n, dtype="int64")
        words = start
    bits = rng.integers(BITS, size=len(words), dtype="int64")
    # Ownership is already ordered and is unchanged by sorting within a replica.
    parent_edges = np.r_[np.int64(0), np.cumsum(counts)]
    hit_edges = np.r_[np.int64(0), np.cumsum(multiplicity)][parent_edges]
    return np.repeat(time, multiplicity), words, bits, hit_edges, counts, multiplicity

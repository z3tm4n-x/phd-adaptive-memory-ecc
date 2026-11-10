"""Frozen C1 archive reconstructions and paired marked Poisson inputs."""
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import gzip
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXP = HERE.parent
sys.path.insert(0, str(EXP / "c1-repeat-quota-20261109"))
from observations import G_MAIN, T, WIDTH, setup

DT = 300
W = 65536
D = 38 * 524288
K = 39 * W / (2 * D)
NAMES = ("SEPEM", "East", "West")
GROUPS = ("event", "outside", "gap", "tail")


def catalogue_file(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


@dataclass
class Profile:
    name: str
    utc: str
    edges: np.ndarray
    lo: np.ndarray
    hi: np.ndarray
    group: np.ndarray
    summary: dict

    def __post_init__(self):
        self.duration = np.diff(self.edges)
        assert (self.duration > 0).all() and self.edges[0] == 0 and self.edges[-1] == T
        self.area = self.duration * (self.lo + self.hi) / 2
        self.slope = (self.hi - self.lo) / self.duration
        assert np.all(self.lo > 0) and np.all(self.hi >= self.lo - 1e-15)
        self.mass = float(np.sum(self.area))
        self.summary.update(S1=self.mass,
            S2_per_s=float(np.sum(self.duration * (self.lo**2 + self.hi*self.lo + self.hi**2) / 3)),
            peak_per_s=float(np.max(self.hi)), expected_parents=K*self.mass,
            group_seconds=dict(zip(GROUPS, np.bincount(self.group, weights=self.duration, minlength=4))),
            profile_sha256=sha256(b"".join(a.astype(dtype).tobytes() for a, dtype in
                [(self.edges,"<f8"),(self.lo,"<f8"),(self.hi,"<f8"),(self.group,"u1")])).hexdigest())

    def draw(self, rep):
        seed = [436, 20261110, NAMES.index(self.name), rep]
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed)))
        # Independent Poisson counts on disjoint affine pieces. Given a count,
        # use the inverse of x*(lo+slope*x/2); avoid subtraction of close roots.
        counts = rng.poisson(K*self.area)
        idx = np.repeat(np.arange(len(counts)), counts)
        size = len(idx)
        y = rng.random(size) * self.area[idx]
        x = 2*y/(self.lo[idx] + np.sqrt(self.lo[idx]**2 + 2*self.slope[idx]*y))
        order = np.lexsort((x, idx))
        idx, x = idx[order], x[order]
        left = self.edges[idx].astype(np.int64)
        ns = left*10**9 + np.floor((self.edges[idx]-left+x)*1e9).astype(np.int64)
        # Each integer timestamp labels the ns immediately after its left edge.
        u = rng.integers(0, W, size=size)
        v = rng.integers(0, W-1, size=size)
        v += v >= u
        bits = rng.integers(0, 39, size=(size, 2))
        marks = np.column_stack((ns, u, bits[:,0], v, bits[:,1])).astype("<i8")
        assert np.all(u != v) and np.all(np.diff(ns) >= 0) and np.all(ns < T*10**9)
        marks.setflags(write=False)
        return marks, sha256(marks.tobytes()).hexdigest()


def build(name, rates, background, origin, events, calendar_bins, previous_mean, meta):
    """Apply the PR423/426 reconstruction before clipping to the catalogue."""
    observed = np.flatnonzero(np.isfinite(rates))
    mean = rates[observed] - background
    gap = np.diff(np.r_[-1, observed]) * DT - DT
    prior = np.r_[previous_mean, mean[:-1]]
    z = np.minimum(mean, prior + G_MAIN*gap)
    endpoint = 2*mean-z
    # Every missing interval is at least 300 s and the C1 peak is below g*300.
    # Its required rising part therefore fits in its last missing bin.
    ramps = (gap > 0) & (z > 0)
    ramp_len = z[ramps] / G_MAIN
    assert np.all(ramp_len < DT)
    observed_starts = observed.astype(float)*DT
    ramp_end = observed_starts[ramps]
    ramp_start = ramp_end-ramp_len
    base_edges = np.arange(WIDTH+1, dtype=float)*DT
    event_edges = [max(0., min(float(T), t)) for span in events for t in span]
    edges = np.unique(np.r_[base_edges, ramp_start, event_edges])
    left, right = edges[:-1], edges[1:]
    bins = (left//DT).astype(int)
    low = np.full(WIDTH, background)
    slope = np.zeros(WIDTH)
    low[observed] += z
    slope[observed] = (endpoint-z)/DT
    lo = low[bins] + slope[bins]*(left-bins*DT)
    hi = low[bins] + slope[bins]*(right-bins*DT)
    if len(ramp_end):
        r = np.searchsorted(ramp_end, left, side="right")
        ix = np.flatnonzero(r < len(ramp_end))
        ix = ix[left[ix] >= ramp_start[r[ix]]]
        # Anchor at the bin's known endpoint, avoiding accumulated clock error.
        lo[ix] = np.maximum(background, background + z[ramps][r[ix]] - G_MAIN*(ramp_end[r[ix]]-left[ix]))
        hi[ix] = background + z[ramps][r[ix]] - G_MAIN*(ramp_end[r[ix]]-right[ix])
    group = np.full(len(left), 1, dtype=np.uint8)
    for start, stop in events:
        if start < stop:
            a, b = np.searchsorted(left, [start,stop])
            group[a:b] = 0
    valid = np.zeros(WIDTH, dtype=bool)
    valid[observed] = True
    group[~valid[bins]] = 2
    group[bins >= calendar_bins] = 3
    # Check every measured bin even if a catalogue transition splits it.
    area = (right-left)*(lo+hi)/2
    by_bin = np.bincount(bins, weights=area, minlength=WIDTH)
    assert np.allclose(by_bin[observed], DT*rates[observed], rtol=8e-14, atol=1e-15)
    gap_excess = float(np.sum((z[ramps]**2)/(2*G_MAIN)))
    assert np.isclose(np.sum(by_bin[~valid]-DT*background), gap_excess, rtol=1e-9, atol=2e-9)
    variation = z[0] - (z[0] if gap[0] else 0) + np.sum(2*(mean-z)) + np.sum(z[ramps])
    assert variation <= 28.855 and np.max(endpoint+background) <= .9813008496992158
    assert np.max(slope) <= G_MAIN+1e-15
    meta.update(covered_s=int(len(observed)*DT), calendar_gap_s=(calendar_bins-len(observed))*DT,
                tail_s=(WIDTH-calendar_bins)*DT, S1_measured=float(np.sum(rates[observed])*DT),
                gap_excess=gap_excess, J_per_s=float(variation), bins_with_data=len(observed))
    return Profile(name, origin, edges, lo, hi, group, meta)


def load_profiles(cache, names):
    common, old = setup(ROOT, ROOT)
    from coverage import goes_observed, sepem_series
    if "SEPEM" in names:
        series, _, _, _, info = sepem_series(cache/"t141-cache", old)
        window = info["maxima"]["S2"]
        i = window["start_bin"]
        assert window["start_utc"] == "1996-12-16T07:20:00Z"
        event_times = [((e["start_bin"]-i)*DT, (e["stop_bin"]-i)*DT)
                       for e in catalogue_file(old/"sepem-events.json.gz")
                       if e["stop_bin"] > i and e["start_bin"] < i+WIDTH]
        b = info["background_per_s"]
        meta = dict(start_bin=i, stop_utc=window["stop_utc_exclusive"], binned_S2=window["S2_s_inv"])
        yield build("SEPEM",series[i:i+WIDTH],b,window["start_utc"],event_times,WIDTH,series[i-1]-b,meta)
    if any(name != "SEPEM" for name in names):
        gc = cache/"c1-goes"
        manifest = catalogue_file(old/"goes-sources.json.gz")["receipt"]["folded"]
        receipt = json.loads((gc/"receipt.json").read_text(encoding="utf-8"))["folded"]
        expected = {row["name"]:row for row in manifest}
        assert len(receipt) == len(manifest) == len(expected) == 4761
        assert {row["name"]:row for row in receipt} == expected
        rates, _, _, info = goes_observed(gc,old)
        events = catalogue_file(old/"goes-events.json.gz")
        origin = "2017-01-01T00:00:00Z"
        epoch = timestamp(origin)
        published = json.loads((common/"growth.json").read_text(encoding="utf-8"))["profiles"]
        for k,name in enumerate(("East","West")):
            if name not in names:
                continue
            rate = rates[:,k]
            b = info["background_s_inv"]
            spans = [(timestamp(e["onset"])-epoch,timestamp(e["end"])-epoch) for e in events[name]]
            profile = build(name,rate,b,origin,spans,len(rate),rate[np.isfinite(rate)][0]-b,
                            dict(folded_files=len(manifest), cutoff_utc="2026-11-09T00:00:00Z",
                                 stop_utc=datetime.fromtimestamp(epoch+T, timezone.utc).isoformat()))
            assert np.isclose(profile.summary["S1_measured"], info["directions"][name]["S1_observed"],rtol=3e-15)
            ref = published["GOES_composite_5min_"+name]
            assert np.isclose(profile.mass,ref["constructed_full_S1"],rtol=3e-15)
            assert np.isclose(profile.summary["gap_excess"],ref["witness_excess_on_gaps"],rtol=3e-15)
            yield profile

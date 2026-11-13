"""Read the local folded inputs and reconstruct the nine histories used in #459."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
from pathlib import Path
from runpy import run_path
import sys

import numpy as np

from replay import EXP, OLD, T, W


DIRECTIONS = ("East","West")
NAMES = ("SEPEM","GOES_composite_5min_East","GOES_composite_5min_West",
         *(f"G{sat}_1min_{d}" for sat in (16,18,19) for d in DIRECTIONS))
PERIOD = T//10**9
ORIGIN = datetime(2017,1,1,tzinfo=timezone.utc)
TRANSFER = json.loads((EXP/"t186-ost-geo-3g/result.json").read_bytes())
TAB = TRANSFER["ost_tabulated"]
TRANSFER = TRANSFER["archive"]
OLD_B = TRANSFER["old_limits"]["b"]
K = TRANSFER["excess_multiplier"]
G = TRANSFER["old_limits"]["g"]


def utc(seconds):
    return (ORIGIN+timedelta(seconds=int(seconds))).isoformat().replace("+00:00","Z")


@dataclass
class History:
    name: str
    edges: np.ndarray
    left: np.ndarray
    right: np.ndarray
    meta: dict

    def __post_init__(self):
        self.length = np.diff(self.edges)
        assert self.edges[0]==0 and self.edges[-1]==PERIOD and np.all(self.length>0)
        assert self.left.min() >= TAB["b"]-1e-15 and self.right.min() >= TAB["b"]-1e-15
        areas = self.length*(self.left+self.right)/2
        self.mass = np.cumsum(areas,dtype=np.float64)
        s1 = float(areas.sum())
        assert abs(self.mass[-1]-s1) < 4e-5
        s2 = float(np.sum(self.length*(self.left**2+self.left*self.right+self.right**2)/3))
        positive = np.maximum(self.right-self.left,0).sum()+np.maximum(self.left[1:]-self.right[:-1],0).sum()
        j = float(self.left[0]-OLD_B+positive)
        peak = float(max(self.left.max(),self.right.max()))
        ref_key = "SEPEM_archive" if self.name=="SEPEM" else self.name
        source = TRANSFER["archives_on_transferred_profiles"][ref_key]
        assert abs(s1-source["S1_on_accepted_windows_or_gap_completion"]) < 2e-6
        assert j <= source["J_in_old_background_coordinates"]+2e-8
        assert peak <= source["peak_of_transferred_construction"]+2e-12
        h = hashlib.sha256()
        for a in (self.edges,self.left,self.right):
            h.update(a.astype("<f8",copy=False).tobytes())
        self.meta.update(S1=round(s1,9), S2_per_s=round(s2,9),peak_per_s=round(peak,12),
                         J_old_floor_per_s=round(j,10), piece_count=len(self.length),
                         profile_sha256=h.hexdigest())

    def draw(self, idx, rep):
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([186,34,idx,rep])))
        n = rng.poisson(self.mass[-1]*W/(524288*1.2))
        target = np.sort(rng.random(n)*self.mass[-1])
        pieces = np.searchsorted(self.mass,target,side="right")
        previous = np.where(pieces>0,self.mass[pieces-1],0.)
        y = (target-previous)/self.length[pieces]
        lo,hi = self.left[pieces],self.right[pieces]
        # Invert lo*f + (hi-lo)*f²/2 and avoid loss of fractional ns against a decade.
        fraction = 2*y/(lo+np.sqrt(lo**2+2*(hi-lo)*y))
        assert np.all((fraction>=0)&(fraction<1))
        edge = self.edges[pieces]
        whole_s = edge.astype(np.int64)
        offset_ns = np.floor((edge-whole_s+fraction*self.length[pieces])*1.e9).astype(np.int64)
        ts = whole_s*10**9+offset_ns
        assert np.all(np.diff(ts)>0) and ts[-1]<T
        first = rng.integers(W,size=n)
        double = rng.integers(5,size=n)==4
        counts = 1+double.astype(np.int64)
        words = np.repeat(first,counts)
        second_at = np.cumsum(counts)[double]-1
        words[second_at] = (words[second_at]+1)%W
        bits = rng.integers(38,size=len(words))
        return np.repeat(ts,counts),words,bits,n


def sepem(cache):
    left,right,_ = OLD["profile"](cache/"t141-cache")
    receipt = OLD["ARCH"]["histories"]()
    edges = np.arange(len(left)+1,dtype=np.int64)*300
    meta = dict(start_utc=receipt["start"],stop_utc=receipt["stop"],dt_s=300,
                measured_first_utc=receipt["start"],measured_last_end_utc=receipt["stop"],
                measured_s=PERIOD,unobserved_s=0,terminal_gap_s=0,bins=len(left),
                S1_measured=round(receipt["S1_witness_approx"],9),start_bin=receipt["start_bin"])
    return History("SEPEM",edges,left,right,meta)


def completed(name, times, values, dt, ref, nfiles):
    # The #423/#426 witness drops to background in holes, then rises at g to z.
    ok = np.isfinite(values)
    t = times[ok].astype(np.float64)
    excess = np.maximum(0.,values[ok]-OLD_B)
    gap = np.r_[t[0],np.diff(t)-dt]
    assert len(t)==ref["bins"] and np.all(gap>=0)
    z = np.minimum(excess,np.r_[excess[0],excess[:-1]+G*gap[1:]])
    endpoint = 2*excess-z
    ramp_height = np.minimum(z,G*gap)
    start_level = z-ramp_height
    # All real gaps are longer than a full ramp on these inputs.
    assert np.all(start_level[gap>0]==0)
    ramp_len = ramp_height/G
    edges = np.unique(np.r_[0.,t-ramp_len,t,t+dt,PERIOD])
    left,right = np.zeros(len(edges)-1),np.zeros(len(edges)-1)
    i = np.searchsorted(edges,t)
    assert np.array_equal(edges[i+1],t+dt)
    left[i],right[i] = z,endpoint
    ramp = ramp_len>0
    before = i[ramp]-1
    assert np.allclose(edges[before],t[ramp]-ramp_len[ramp],atol=1e-8,rtol=0)
    right[before] = z[ramp]
    length = np.diff(edges)
    if not np.isclose(np.sum(length[before]*z[ramp]/2),ref["witness_excess_on_gaps"],rtol=1e-7,atol=1e-8):
        raise ValueError(f"Different gap completion for {name}")
    measured = int(len(t)*dt)
    meta = dict(start_utc=utc(0),stop_utc=utc(PERIOD),cutoff_utc="2026-11-09T00:00:00Z",
                measured_first_utc=utc(t[0]),measured_last_end_utc=utc(t[-1]+dt),
                bins=len(t),dt_s=dt,source_files=nfiles,measured_s=measured,
                unobserved_s=PERIOD-measured,terminal_gap_s=int(PERIOD-t[-1]-dt),
                S1_measured=round(float(dt*np.sum(TAB["b"]+K*excess)),9))
    assert meta["terminal_gap_s"]==ref["terminal_gap_s"]
    return History(name,edges,TAB["b"]+K*left,TAB["b"]+K*right,meta)


def goes(cache):
    obs = run_path(str(EXP/"c1-repeat-quota-20261109/observations.py"))
    common, previous = obs["setup"](EXP.parent,EXP.parent)
    # Load the project-local readers, independent of an installed coverage.py package.
    local = run_path(str(common/"coverage.py"))
    from cadence import samples
    from minute_sources import selected
    growth = json.loads((common/"growth.json").read_bytes())["profiles"]
    gc = cache/"c1-goes"
    with gzip.open(previous/"goes-sources.json.gz","rt",encoding="utf-8") as f:
        manifest = json.load(f)["receipt"]["folded"]
    saved = json.loads((gc/"receipt.json").read_bytes())["folded"]
    assert len(saved)==len(manifest)==4761 and {r["name"]:r for r in saved}=={r["name"]:r for r in manifest}
    rates,_,_,info = local["goes_observed"](gc,previous)
    for d,name in enumerate(NAMES[1:3]):
        yield completed(name,np.arange(len(rates))*300,rates[:,d],300,growth[name],len(manifest))
    mc = cache/"c1-common-minutes"
    chosen = selected()
    receipt = json.loads((mc/"receipt.json").read_bytes())
    assert not receipt["errors"] and set(receipt["ok"])=={r["name"] for r in chosen} and len(chosen)==548
    for sat in (16,18,19):
        files = [r for r in chosen if r["satellite"]==sat]
        # The signature is only consumed by pairwise slope selection, not the retained means.
        t,value,_,_ = samples(files,mc/"folded",60,sat,{r["name"]:0 for r in files},info)
        for d,direction in enumerate(DIRECTIONS):
            name = f"G{sat}_1min_{direction}"
            yield completed(name,t,value[:,d],60,growth[name],len(files))

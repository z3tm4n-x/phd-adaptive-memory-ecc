"""Nominal bus use for the native ERR ladder on one transferred SEPEM decade."""
import argparse
import hashlib
import json
from math import ceil
from pathlib import Path
from runpy import run_path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
ARCH = run_path(str(EXP / "t196-archive-same-map-20261110/calculate.py"))
A, W = 65536, 32768
L = 22_937_600  # nanoseconds, 4 x16 addresses per 1400 ns
T = 315_576_000 * 10**9
CAP = 256
THRESHOLDS = np.array(ARCH["base"]["thresholds"](ARCH["scan"], 8), dtype=np.int64)
PHASE = np.array([0, 240, 520, 760], dtype=np.int64)


def profile(cache):
    receipt = json.loads((EXP / "t141-radiation-chain/outputs/profile-provenance.json").read_bytes())["input"]
    path = cache / "bands.npy"
    with path.open("rb") as f:
        assert hashlib.file_digest(f, "sha256").hexdigest() == receipt["arrays_sha256"][path.name]
    bands = np.load(path, mmap_mode="r")
    inputs = ARCH["histories"]()
    source = ARCH["read_json"](EXP / "c1-geo-fixed-20261109/sepem.json")
    ost = ARCH["read_json"](EXP / "t186-ost-geo-3g/result.json")
    start, count = inputs["start_bin"], inputs["number_bins"]
    part = bands[start-1:start+count, 1, :]
    raw = part[:, 0] + part[:, 1]
    means = float(ost["ost_tabulated"]["b"]) + (1 + float(ost["archive"]["beta_ost_tabulated"])) * np.maximum(raw - float(source["H_p10"]), 0)
    left = np.minimum(means[:-1], means[1:])
    right = 2*means[1:] - left
    assert abs(300*means[1:].sum() - inputs["S1_witness_approx"]) < 1.e-6
    assert abs(100*np.sum(left**2+left*right+right**2) - inputs["S2_reconstruction_approx"]) < 1.e-6
    return left, right, 300*np.cumsum(means[1:])


def draw(rng, left, right, mass):
    # Integrate the rate per parent, not the bit inversion rate.
    n = rng.poisson(mass[-1] * W / (2 * 524288))
    target = np.sort(rng.random(n)*mass[-1])
    bins = np.searchsorted(mass, target, side="right")
    previous = np.zeros(n)
    after_first = bins > 0
    previous[after_first] = mass[bins[after_first]-1]
    area = (target-previous)/300
    # Stable inverse of area = left*x + (right-left)*x^2/2 inside each bin.
    x = 2*area / (left[bins] + np.sqrt(left[bins]**2 + 2*(right[bins]-left[bins])*area))
    ticks = bins.astype(np.int64)*300_000_000_000 + np.floor(x*300_000_000_000).astype(np.int64)
    first = rng.integers(W, size=n)
    second = rng.integers(W-1, size=n)
    second += second >= first
    words = np.column_stack((first, second)).ravel()
    assert np.all(np.diff(ticks) > 0)
    return np.repeat(ticks, 2), words, rng.integers(38, size=2*n)


@njit
def read_ns_until(length):
    if length >= L:
        return A*100
    frames = length//1400
    total = frames*400
    for phase in PHASE:
        total += min(100, max(0, length%1400-phase))
    return total


@njit
def replay(ticks, words, bits, horizon, skip=True):
    # Paths remain exact until the first simultaneous double error or an
    # impact in the aperture of a visit to the same word. Stop before the
    # ambiguous scan: no chip semantics past that point are postulated.
    masks = np.zeros(W, dtype=np.int64)
    flagged = np.zeros(W, dtype=np.bool_)
    touched = np.empty(W, dtype=np.int64)
    carry = np.empty(W, dtype=np.int64)
    ncarry = 0
    scans = 0
    read_ns = 0
    write_ns = 0
    rnd = 0
    step = 1
    last_bad = 0
    pos = 0
    while rnd*L < horizon:
        start = rnd*L
        end = min(start+L, horizon)
        nxt = pos
        while nxt < len(ticks) and ticks[nxt] < end:
            nxt += 1
        empty = pos == nxt and ncarry == 0
        touched_count = ncarry
        for j in range(ncarry):
            touched[j] = carry[j]
            flagged[carry[j]] = True
        ncarry = 0
        for p in range(pos, nxt):
            w = words[p]
            if not flagged[w]:
                touched[touched_count] = w
                touched_count += 1
                flagged[w] = True
        writes = 0
        detected = False
        for j in range(touched_count):
            w = touched[j]
            p = pos
            mask = masks[w]
            # Concrete adjacent pairing, conditional on a fully closed region.
            for half in range(3):
                addr = 2*w+half
                visit = start+(addr//4)*1400+PHASE[addr%4] if half<2 else end
                boundary = min(visit, end)
                while p < nxt and ticks[p] < boundary:
                    if words[p] == w:
                        mask ^= np.int64(1)<<bits[p]
                        if mask & (mask-1):
                            return read_ns+write_ns, horizon-start, scans, 1
                    p += 1
                if half==2 or visit>=end:
                    continue
                occupied = 200 if mask else 100
                while p < nxt and ticks[p] < min(visit+occupied, end):
                    if words[p] == w:
                        return read_ns+write_ns, horizon-start, scans, 2
                    p += 1
                if mask:
                    writes += max(0,min(100,end-visit-100))
                    if visit+200 <= end:
                        mask = 0
                        detected = True
            masks[w] = mask
            flagged[w] = False
            if mask:
                carry[ncarry] = w
                ncarry += 1
        pos = nxt
        if detected and rnd>0:
            last_bad = (rnd+CAP-1)//CAP
        if rnd%CAP==0:
            step = 1
            for threshold in THRESHOLDS:
                if rnd//CAP-last_bad >= threshold:
                    step *= 2
        elif detected:
            step = 1
        groups = 1
        if skip and empty and end-start==L:
            hit_time = ticks[pos] if pos<len(ticks) else horizon
            groups += (hit_time-end)//(step*L)
            if step<CAP:
                level = 0
                while 2**level!=step:
                    level += 1
                target = (last_bad+THRESHOLDS[level])*CAP
                groups = min(groups, max(1,(target-rnd+step-1)//step))
        read_ns += (groups-1)*A*100 + read_ns_until(end-start)
        write_ns += writes
        scans += groups
        rnd += groups*step
    return read_ns+write_ns, 0, scans, 0


def selftest():
    no_events = np.array([],dtype=np.int64)
    assert read_ns_until(30)==30 and read_ns_until(300)==160 and read_ns_until(L)==A*100
    horizon = 4000*L+280
    times = np.array([L//2,L//2,1500*L+201,1500*L+201],dtype=np.int64)
    ws = np.array([2,3,14,15],dtype=np.int64)
    bits=np.array([5,7,32,37],dtype=np.int64)
    for ts, ww, bb in [(times,ws,bits),(no_events,no_events,no_events)]:
        literal = replay(ts,ww,bb,horizon,False)
        assert literal==replay(ts,ww,bb,horizon,True) and literal[3]==0
    # A late hit after both word visits is repaired once at the next scan.
    assert replay(times[:2],ws[:2],bits[:2],2*L,False)[0] == 2*A*100+200
    double = np.array([7000,7010],dtype=np.int64)
    assert replay(double,np.array([100,100]),np.array([1,2]),L)[3]==1
    assert replay(double,np.array([100,100]),np.array([1,1]),L)[0]==A*100
    assert replay(np.array([60]),np.array([0]),np.array([37]),L)[3]==2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sepem-cache",type=Path,required=True)
    args=parser.parse_args()
    selftest()
    data=profile(args.sepem_cache)
    rows=[]
    for child in np.random.SeedSequence(462).spawn(128):
        draws=draw(np.random.default_rng(child),*data)
        a,tail,scans,stop=replay(*draws,T)
        rows.append((a/1.e9,(a+tail)/1.e9,scans,stop))
    sample=np.array(rows)
    print(json.dumps(dict(trials=len(rows), words=W, seed=462,
        stopped=sum(int(r[3]!=0) for r in rows),
        mean_lower_s=round(float(sample[:,0].mean()),3),
        mean_upper_s=round(float(sample[:,1].mean()),3),
        sample_se_lower_s=round(float(sample[:,0].std(ddof=1)/np.sqrt(len(rows))),3),
        sample_se_upper_s=round(float(sample[:,1].std(ddof=1)/np.sqrt(len(rows))),3),
        average_scans_before_stop=float(sample[:,2].mean())),indent=2))


if __name__=="__main__":
    main()

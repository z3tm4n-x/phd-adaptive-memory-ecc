"""Small, independent Package-A oracles. Not the production RES-003 controller.

All times in the executor are integer nanoseconds. No hidden physical state is
returned as a controller observation. E_cap is an audit-only first-passage flag.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Sequence
import math
import numpy as np

ACTIVE_BITS = 39 * 2**20
PARITY_POSITIONS = (1, 2, 4, 8, 16, 32)
DATA_POSITIONS = tuple(p for p in range(1, 39) if p not in PARITY_POSITIONS)

def encode(data: int) -> int:
    """32 data bits -> shortened extended Hamming (39,32), even parity."""
    if not isinstance(data, int) or not 0 <= data < 2**32:
        raise ValueError('data must be a 32-bit unsigned integer')
    word = sum(((data >> i) & 1) << (p - 1) for i, p in enumerate(DATA_POSITIONS))
    for p in PARITY_POSITIONS:
        parity = sum((word >> (j - 1)) & 1 for j in range(1, 39) if j & p) & 1
        word |= parity << (p - 1)
    return word | ((word.bit_count() & 1) << 38)

def decode(word: int) -> tuple[str, int]:
    """Return status and decoded/repaired codeword, not an oracle error count.

Only <=2 corrupt bits have the SECDED guarantee. Some >=3 corruptions can be
miscorrected. The separate audit process detects E_cap when the true distance
first exceeds one, and does not expose that flag to this decoder.
"""
    if not isinstance(word, int) or not 0 <= word < 2**39:
        raise ValueError('word must have 39 bits')
    syndrome = 0
    for p in range(1, 39):
        if (word >> (p - 1)) & 1:
            syndrome ^= p
    odd = word.bit_count() & 1
    if syndrome == 0 and not odd:
        return 'clean', word
    if syndrome == 0 and odd:
        return 'corrected', word ^ (1 << 38)
    if odd and 1 <= syndrome <= 38:
        return 'corrected', word ^ (1 << (syndrome - 1))
    return 'uncorrectable', word

def per_bit_to_active(rate: float, *, normalization: str = 'per_bit', bits: int = ACTIVE_BITS) -> float:
    if normalization != 'per_bit':
        raise ValueError('refuse to rescale a rate already normalized to an array')
    if bits != ACTIVE_BITS:
        raise ValueError('wrong region: active region is 39 * 2^20, not data-only or padding')
    if not math.isfinite(rate) or rate < 0:
        raise ValueError('invalid rate')
    return bits * rate

def convert_let_density(L_g: Sequence[float], phi_per_L_g: Sequence[float]):
    L = np.asarray(L_g, float); phi = np.asarray(phi_per_L_g, float)
    if L.shape != phi.shape or np.any(~np.isfinite(L)) or np.any(~np.isfinite(phi)):
        raise ValueError('incompatible or non-finite arrays')
    if np.any(L < 0) or np.any(phi < 0):
        raise ValueError('negative input')
    return L / 1000, phi * 1000

def differential_to_omni(flux: Sequence[float], *, per_keV: bool, per_sr: bool):
    """Both factors explicit; never call with per_sr=True on native COSRAD total flux."""
    a = np.asarray(flux, float)
    if np.any(~np.isfinite(a)) or np.any(a < 0):
        raise ValueError('invalid flux is not a measured zero')
    return a * (1000 if per_keV else 1) * (4 * np.pi if per_sr else 1)

def pair_bound_constant(rate: float, horizon: float, period: float,
                        words: int, bits: int, scan_time: float) -> float:
    """Sufficient pair-count bound, homogeneous singleton reference only.

Checks of word j: k*period - scan_time*(words-1-j)/words. Clean initial state;
all terminal intervals retained. Not a delayed-executor or grouped bound.
No COSRAD rate is hard-coded here.
"""
    if rate < 0 or horizon <= 0 or not 0 < scan_time <= period or words < 1 or bits < 2:
        raise ValueError('invalid reference parameters')
    d = scan_time * np.arange(words - 1, -1, -1, dtype=float) / words
    m = np.floor((horizon + d) / period).astype(np.int64)
    last = horizon - (m * period - d)
    sum_sq = np.where(m >= 1, (period-d)**2 + (m-1)*period**2 + last**2, horizon**2)
    value = (bits-1)/(2*bits) * (rate/words)**2 * float(np.sum(sum_sq))
    return min(1.0, value)

@dataclass(frozen=True)
class Upset:
    time_ns: int
    cells: tuple[tuple[int, int], ...]  # (word, Hamming bit index 0..38)

@dataclass
class Execution:
    completed_counts: list[tuple[int, int]]
    final_words: list[int]
    first_ecap_ns: int | None
    reads: int
    writes: int
    reservation_ns: int
    committed_counts_by_pass: list[int]

def run_fixed(*, words: int, horizon_ns: int, period_ns: int,
              upsets: Iterable[Upset], slot_ns: int = 300,
              latch_ns: int = 100) -> Execution:
    """Independent small-W delayed-write oracle, zero encoded payload.

A pass occupies the final W*slot_ns of each period. It is scheduled only
from its own period, not the input profile. All streams must be immutable.
No stop/abort on hidden E_cap. No controller implementation is tested here.
"""
    if words < 1 or horizon_ns <= 0 or not 0 < latch_ns < slot_ns or period_ns < words*slot_ns:
        raise ValueError('invalid executor timing')
    events = []; P = words*slot_ns; reservations = 0; pass_starts=[]
    end = period_ns
    while end-P < horizon_ns:
        start = end-P; idx = len(pass_starts); pass_starts.append(start)
        reservations += max(0, min(P, horizon_ns-start))
        for w in range(words):
            latch = start+w*slot_ns+latch_ns; commit=start+(w+1)*slot_ns
            if latch < horizon_ns:
                events.append((latch,2,'latch',idx,w))
            if commit <= horizon_ns:
                events.append((commit,0,'commit',idx,w))
        if end <= horizon_ns:
            events.append((end,3,'observation',idx,0))
        end += period_ns
    for event_index, u in enumerate(upsets):
        if not isinstance(u.time_ns,int) or u.time_ns < 0:
            raise ValueError('upset time must be a nonnegative integer ns')
        if len(set(u.cells)) != len(u.cells):
            raise ValueError('a physical group lists each affected cell once')
        if any(not 0 <= w < words or not 0 <= bit < 39 for w,bit in u.cells):
            raise ValueError('cell outside active region')
        if u.time_ns < horizon_ns:
            events.append((u.time_ns,1,'upset',event_index,u.cells))
    events.sort(key=lambda x:(x[0],x[1],x[3]))
    state=[0]*words; pending={}; counts=[0]*len(pass_starts); observations=[]
    first=None; reads=writes=0
    for time,_,kind,idx,arg in events:
        if kind == 'upset':
            for w,bit in arg: state[w] ^= 1 << bit
            if first is None and any(state[w].bit_count()>1 for w,_ in arg): first=time
        elif kind == 'latch':
            reads += 1; status,corrected=decode(state[arg])
            pending[(idx,arg)] = (status,corrected)
        elif kind == 'commit':
            status,corrected=pending.pop((idx,arg),('no_latch',0))
            if status == 'corrected':
                state[arg]=corrected; writes+=1; counts[idx]+=1
        else:
            observations.append((time,counts[idx]))
    return Execution(observations,state,first,reads,writes,reservations,counts)

from __future__ import annotations

import bisect
import math
import random
from dataclasses import dataclass
from typing import Iterable, Sequence

# Frozen synthetic arithmetic-regression constants. The external Stage-5 proof
# needed to interpret the resulting pair as a probabilistic reference bracket is
# not available in the controlled evidence package. Keep these values only to
# detect arithmetic/code drift; do not use them for scientific tightness,
# optimality, or reference-relative resource claims.
BENCH_T = 315_576_000.0
BENCH_Q = 1e-3
BENCH_N_WORDS = 131_072
BENCH_N_BITS = 5_111_808
BENCH_N = 39
BENCH_B = 2048
BENCH_M1 = 2.5557299843014127
BENCH_LAMBDA_PER_DAY = 2.000136176904177
BENCH_EXPECTED_EVENTS = 7305.497386142507
BENCH_PAIR_P = 0.0767585412924521
BENCH_PAIR_E = 0.099441794311289
BENCH_PHASE_FACTOR = 1.000961072684732


def synthetic_tau_upper() -> float:
    """Frozen sufficient-formula arithmetic regression value; not an accepted optimum."""
    alpha = (BENCH_N - 1) / (2 * (BENCH_N_BITS - 1))
    nu = BENCH_LAMBDA_PER_DAY * BENCH_M1 / 86400.0
    s2 = nu * nu * BENCH_T
    return BENCH_Q / (alpha * s2)


def _mu_base(tau: float) -> float:
    # Frozen Stage-5 arithmetic expression. Its external probabilistic proof is
    # not part of the controlled evidence available to this task.
    return (BENCH_EXPECTED_EVENTS**2 / (2.0 * BENCH_B)) * BENCH_PAIR_P * (tau / BENCH_T)


def synthetic_reference_risk_bounds(tau: float):
    """Legacy-named frozen Stage-5 formula outputs for arithmetic regression.

    The function name is retained for compatibility. The two returned values are
    NOT treated by the current project as verified probabilistic lower/upper risk
    bounds because the external Stage-5 derivation/proof is unavailable. They may
    only be used to reproduce the historical numerical regression benchmark.
    """
    tau = float(tau)
    mu = _mu_base(tau)
    q_upper = min(1.0, mu * BENCH_PHASE_FACTOR)
    shared = (BENCH_EXPECTED_EVENTS**3 / (2.0 * BENCH_B**2)) * (2.0 * tau / BENCH_T) ** 2
    q_lower = max(0.0, mu - 0.5 * mu * mu - shared)
    return q_lower, q_upper


def bisect_monotone_root(func, target: float, lo: float, hi: float, tol: float = 1e-9, max_iter: int = 200):
    flo = func(lo) - target
    fhi = func(hi) - target
    if flo > 0 or fhi < 0:
        raise ValueError("root is not bracketed")
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        fm = func(mid) - target
        if hi - lo <= tol:
            return mid
        if fm >= 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def synthetic_reference_tau_bracket():
    """Legacy-named frozen arithmetic root pair; not a verified reference bracket."""
    lower_period = bisect_monotone_root(lambda t: synthetic_reference_risk_bounds(t)[1], BENCH_Q, 1.0, 1000.0)
    upper_period = bisect_monotone_root(lambda t: synthetic_reference_risk_bounds(t)[0], BENCH_Q, 1.0, 1000.0)
    return lower_period, upper_period


def combined_reference_risk(nu_direct: float, T: float, residual_survival: float) -> float:
    """Exact risk only for the declared absorbing-direct surrogate product model.

    This product formula requires an independent thinned direct process and the
    residual process under a fixed, state-independent event partition and the
    same fixed restoration action. It is not an exact physical-toggle risk and
    is not automatically valid for state-dependent partitioning, shared random
    environments, or adaptive policies.
    """
    if not (0.0 <= residual_survival <= 1.0):
        raise ValueError("residual_survival outside [0,1]")
    return 1.0 - math.exp(-nu_direct * T) * residual_survival


@dataclass(frozen=True)
class ResidualMark:
    """One residual registered-event mark after a declared W partition.

    bit_ids are stable data-bit identifiers. word_positions give the cyclic scrub phase rank for each bit's word.
    A residual mark must not itself contain two distinct bits of the same word; that is enforced by caller/model build.
    """
    bit_ids: tuple[int, ...]
    word_ids: tuple[int, ...]
    word_positions: tuple[int, ...]


def simulate_residual_first_passage(
    marks: Sequence[ResidualMark],
    mark_weights: Sequence[float],
    lambda_registered_s: float,
    T: float,
    tau: float,
    n_words: int,
    rng: random.Random,
) -> bool:
    """Event-level residual reference kernel with toggles and cyclic sequential scrub.

    This kernel is deliberately generic and is not run for GEO in Phase A. It is used for semantics tests
    and is ready to consume a PI-supplied registered-event mixture in Phase B. Direct marks are excluded
    because the declared comparison surrogate treats them as absorbing; that surrogate is conservative
    relative to the corresponding toggle path under the stated coupling, not identical to it.
    Returns True on first passage to >=2 erroneous distinct data bits in any word.
    """
    if lambda_registered_s < 0 or T < 0 or tau <= 0 or n_words <= 0:
        raise ValueError("invalid process parameters")
    if not marks:
        return False
    for mark in marks:
        if not (len(mark.bit_ids) == len(mark.word_ids) == len(mark.word_positions)):
            raise ValueError("malformed residual mark")
        if len(set(mark.word_ids)) != len(mark.word_ids):
            raise ValueError("residual mark contains same-word multiplicity and belongs in absorbing direct surrogate branch")
    if len(marks) != len(mark_weights) or any(w < 0 for w in mark_weights) or sum(mark_weights) <= 0:
        raise ValueError("invalid mark law")
    weights = [w / sum(mark_weights) for w in mark_weights]
    cumulative = []
    s = 0.0
    for w in weights:
        s += w
        cumulative.append(s)

    state: dict[int, set[int]] = {}
    last_scrub_index: dict[int, int] = {}

    def scrub_before(time_s: float, word_id: int, position: int):
        phase = tau * (position / n_words)
        idx = math.floor((time_s - phase) / tau)
        prev = last_scrub_index.get(word_id, -1)
        if idx > prev:
            state.pop(word_id, None)
            last_scrub_index[word_id] = idx

    t = 0.0
    if lambda_registered_s == 0:
        return False
    while True:
        t += rng.expovariate(lambda_registered_s)
        if t > T:
            return False
        u = rng.random()
        mark_idx = bisect.bisect_left(cumulative, u)
        mark = marks[min(mark_idx, len(marks) - 1)]
        for bit, word, pos in zip(mark.bit_ids, mark.word_ids, mark.word_positions):
            scrub_before(t, word, pos)
            st = state.setdefault(word, set())
            if bit in st:
                st.remove(bit)
                if not st:
                    state.pop(word, None)
            else:
                st.add(bit)
                if len(st) >= 2:
                    return True

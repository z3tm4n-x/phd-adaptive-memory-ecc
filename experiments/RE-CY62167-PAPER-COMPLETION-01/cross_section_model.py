from __future__ import annotations

import math

SIGMA_SAT = 2.6e-7
L0 = 0.15
W = 70.0
H = 1.2
N_BITS = 2**24


def sigma_bit(let_value: float) -> float:
    L = float(let_value)
    if L <= L0:
        return 0.0
    return SIGMA_SAT * (1.0 - math.exp(-(((L - L0) / W) ** H)))


def article_effective_fluence(S_cells: int, let_value: float) -> float:
    sb = sigma_bit(let_value)
    if sb <= 0:
        raise ValueError("sigma_b is zero at/below threshold")
    return float(S_cells) / (N_BITS * sb)


def point_cross_sections(*, N_events: int, S_cells_used: int, N_direct: int, S_accumulation: int, let_value: float):
    F = article_effective_fluence(S_cells_used, let_value)
    sigma_event = N_events / F
    sigma_direct = N_direct / F
    sigma_acc = S_accumulation / F
    p_direct = N_direct / N_events if N_events else math.nan
    mbar_acc = S_accumulation / N_events if N_events else math.nan
    # Equivalent reconstruction identities.
    if N_events:
        if not math.isclose(sigma_direct, p_direct * sigma_event, rel_tol=2e-15, abs_tol=1e-18):
            raise AssertionError("direct cross-section identity failed")
        if not math.isclose(sigma_acc, mbar_acc * sigma_event, rel_tol=2e-15, abs_tol=1e-18):
            raise AssertionError("accumulation cross-section identity failed")
    return {
        "F_art_cm-2": F,
        "sigma_event_cm2": sigma_event,
        "sigma_direct_point_cm2": sigma_direct,
        "sigma_accumulation_point_cm2": sigma_acc,
        "p_D_reg": p_direct,
        "mbar_C": mbar_acc,
    }

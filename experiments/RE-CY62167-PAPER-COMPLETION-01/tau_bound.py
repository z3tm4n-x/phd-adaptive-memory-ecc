from __future__ import annotations

import math

T_DEFAULT = 3.156e8
Q_DEFAULT = 1e-3
N_BITS = 2**24
N_WORDS = 2**19
N_DATA = 32
BETA = (N_DATA - 1) / (2 * N_BITS)


def q_upper(T: float, tau: float, nu_direct: float, nu_accumulation_bit: float) -> float:
    return T * (nu_direct + BETA * tau * nu_accumulation_bit**2)


def tau_max_upper(nu_direct: float, nu_accumulation_bit: float, T: float = T_DEFAULT, q_dop: float = Q_DEFAULT):
    threshold = q_dop / T
    if nu_direct >= threshold:
        return None, "DIRECT-BOUND-EXHAUSTED"
    if nu_accumulation_bit <= 0:
        return math.inf, "CERTIFIED-POSITIVE-PERIOD"
    tau = (threshold - nu_direct) / (BETA * nu_accumulation_bit**2)
    return tau, "CERTIFIED-POSITIVE-PERIOD"


def direct_budget_fraction(nu_direct: float, T: float = T_DEFAULT, q_dop: float = Q_DEFAULT) -> float:
    return T * nu_direct / q_dop


def direct_log_sensitivity(f_D: float):
    if f_D >= 1:
        return None, "DIRECT BUDGET EXHAUSTED"
    if f_D == 0:
        return -0.0, "DEFINED"
    return -f_D / (1.0 - f_D), "DEFINED"

"""Small author checks for T196 stage A; no policy/MC/old-campaign replay.

Usage: python check.py --input /path/to/PR268-a8c27f8-inputs.json
The engineer's file is the only input; its exact bytes are pinned.
"""
import argparse
from decimal import Decimal, localcontext
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

INPUT_COMMIT = "a8c27f891ecfcfb568e4b6d62c9f35478fa877b6"
INPUT_SHA256 = "550fd820bf1d53161da01ab7924eddb71e1ef4152a0c05e133f0303fbc5acf04"


def decimal(x):
    with localcontext() as ctx:
        ctx.prec = 45
        return str(Decimal(x.numerator) / Decimal(x.denominator))


def exponential_upper(x, n=80):
    """Exact rational series and geometric upper tail for exp(x), x>=0."""
    assert x >= 0 and n + 2 > x
    term = F(1)
    total = term
    for k in range(1, n + 1):
        term *= x / k
        total += term
    next_term = term * x / (n + 1)
    return total + next_term / (1 - x / (n + 2))


def free_lengths(length, windows):
    """Clipped union of service apertures inside a deterministic interval."""
    clipped = sorted((max(F(0), a), min(length, b))
                     for a, b in windows if b > 0 and a < length)
    cursor = F(0)
    lengths = []
    for a, b in clipped:
        if a > cursor:
            lengths.append(a - cursor)
        cursor = max(cursor, b)
    if cursor < length:
        lengths.append(length - cursor)
    return lengths


def run(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA256:
        raise ValueError("Input differs from agreed PR268 a8c27f8; no silent rebase")
    cfg = json.loads(raw)
    env = cfg["proposed_environment"]
    p, r, fixed = env["p"], env["residual"], cfg["fixed"]
    W, T = fixed["words"], F(fixed["mission_s"])
    B, b = F(env["total_peak"]), F(env["background"])
    A = F(p["amplitude_above_background"])
    R, g, Fr = F(r["cap_R"]), F(r["growth_g"]), F(r["mass_F_r"])
    Fs, H, width = F(env["total_solar_mass"]), F(p["cycle_s"]), F(p["width_s"])
    passed = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        passed.append(name)

    check("whole_58440_cycles", T / H == 58440)
    check("all_triangles_inside_horizon", 0 <= F(p["left_s"])
          and F(p["left_s"]) + width <= H)
    check("known_mass_half", (T / H) * A * width / 2 == Fs / 2)
    check("peak_partition", b + A + R == B)
    check("residual_mass_half", Fr == Fs / 2)
    check("total_growth_partition", g + A / (width / 2)
          == F(env["old_growth_rho_per_s"]) * F(env["old_growth_threshold"]))
    check("strictly_positive_components", min(b, A, R, g, Fr) > 0)
    check("full39_singleton", fixed["code"] == [39, 32, 1]
          and F(env["spatial"]["q"]) == F(1, W)
          and F(env["spatial"]["chi"]) == F(1, W)
          and env["spatial"]["d"] == 0 and env["spatial"]["m"] == 1)

    rise = R / g
    rise_mass = R * rise / 2
    plateau = (Fr - rise_mass) / R
    duration = rise + plateau
    check("positive_plateau_and_shift_range", plateau > 0 and duration < T)
    check("witness_exact_mass", rise_mass + plateau * R == Fr)
    check("old_B_plateau_not_in_new_class", B - b > R)

    diag = cfg["diagnostic"]
    alpha, zeta = F(diag["alpha_star"]), F(diag["zeta_star"])
    eps, delta0 = F(fixed["epsilon"]), F(fixed["lifetime_other_budget"])
    e0 = delta0 + alpha + zeta
    gamma_max = (eps - e0) / 2
    check("agreed_T36_budget", alpha == F(1, 10000) and zeta == alpha
          and gamma_max == F(397, 1000000))
    check("risk_square_root_below_10_21", 2 * W * gamma_max < F(1021, 100)**2)
    check("log_30000_above_10_3", exponential_upper(F(103, 10)) < 3 / alpha)
    check("statistic_barrier_margin", F(103, 10) > F(1021, 100))
    check("background_K1_reserve_floor", b * T / W > eps / 2)

    # Geometry cases include OFF, equal gaps (equality), and boundary-clipped
    # service windows. These target common endpoint mistakes in the new lemma.
    length, d = F(100), F(1)
    eqgap = (length - 2 * d) / 3
    cases = {
        "OFF": [],
        "equal_gaps": [(eqgap, eqgap + d),
                       (2 * eqgap + d, 2 * eqgap + 2 * d)],
        "both_edges": [(F(-1, 2), F(1, 2)), (F(999, 10), F(1009, 10))],
        "unequal_with_overlap": [(F(20), F(21)), (F(41, 2), F(43, 2)),
                                (F(70), F(71))],
    }
    for name, windows in cases.items():
        n = len(windows)
        sq = sum((x * x for x in free_lengths(length, windows)), F(0))
        lower = max(length - n * d, 0)**2 / (n + 1)
        check("free_gap_lower_" + name, sq >= lower)
        if name in ("OFF", "equal_gaps"):
            check("free_gap_equality_" + name, sq == lower)

    # Fubini factor L+d, including both extremes of the allowed shift domain.
    Tsmall, rise_small, Lsmall = F(1000), F(10), F(100)
    shift_end = Tsmall - rise_small - Lsmall
    apertures = [(F(0), F(1)), (F(500), F(501)), (F(999), F(1000))]
    shift_measures = []
    for a, end in apertures:
        measure = max(F(0), min(shift_end, end - rise_small)
                      - max(F(0), a - rise_small - Lsmall))
        shift_measures.append(measure)
        check("translated_aperture_" + str(a), measure <= Lsmall + (end - a))
    check("interior_fubini_equality", shift_measures[1] == Lsmall + 1)

    return {
        "scope": "author semantic checks only; no hybrid Q, resource result or independent acceptance",
        "input_commit": INPUT_COMMIT,
        "input_sha256": INPUT_SHA256,
        "checks": passed,
        "checks_passed": len(passed),
        "exact": {
            "known_extra_mass": str(Fs / 2),
            "residual_mass": str(Fr),
            "ramp_time_s": str(rise),
            "ramp_mass": str(rise_mass),
            "plateau_time_s": str(plateau),
            "witness_duration_s": str(duration),
            "T36_e0": str(e0),
            "T36_gamma_max": str(gamma_max),
            "twice_W_gamma": str(2 * W * gamma_max),
            "background_K1_reserve_floor": str(b * T / W),
        },
        "display_only": {
            "ramp_time_s": decimal(rise),
            "plateau_time_s": decimal(plateau),
            "witness_duration_s": decimal(duration),
            "background_K1_reserve_floor": decimal(b * T / W),
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.input), ensure_ascii=False, indent=2, sort_keys=True))

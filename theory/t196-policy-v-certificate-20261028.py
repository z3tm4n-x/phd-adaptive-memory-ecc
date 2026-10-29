"""Exact checks for the analytical V certificate; no mission simulation.

Only the already registered first_probe is read. Timing and delta_C have
no defaults: optional numerical evaluation requires explicit bindings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("experiments/regime-map-methodology-20261019/"
              "predictability-volume-20261028/inputs.json")
SOURCE_SHA = "5f62171e4706854f6419345d7eaed1f2103c06bc4989976fde03942db091c6cd"
RESULT = Path(__file__).with_name("t196-policy-v-certificate-20261028-result.json")


def ceil(x: F) -> int:
    return -(-x.numerator // x.denominator)


def record(x: F) -> dict:
    """Exact fraction plus an upward decimal, including for negative inputs."""
    scale = 10**18
    n = ceil(x * scale)
    sign = "-" if n < 0 else ""
    n = abs(n)
    return {"exact": str(x), "decimal_up": f"{sign}{n // scale}.{n % scale:018d}"}


def dual_bound(edges, weights, R, Fr, g, y, beta, gamma):
    """Check (14) exactly; return (15). No assumed optimum or solver trust."""
    n = len(weights)
    if n == 0 or len(edges) != n + 1 or len(beta) != n or len(gamma) != n - 1:
        raise ValueError("Invalid dual dimensions")
    ds = [edges[j + 1] - edges[j] for j in range(n)]
    cs = [(edges[j] + edges[j + 1]) / 2 for j in range(n)]
    if min(ds) <= 0 or min([R, Fr, g, y] + list(beta) + list(gamma)) < 0:
        raise ValueError("Nonpositive cell or negative bound/multiplier")
    for j in range(n):
        left = gamma[j - 1] if j else F(0)
        right = gamma[j] if j < n - 1 else F(0)
        if ds[j] * y + beta[j] + left - right < ds[j] * weights[j]:
            raise ValueError(f"Invalid dual inequality in cell {j}")
    return Fr * y + R * sum(beta) + g * sum(
        gamma[j] * (cs[j + 1] - cs[j]) for j in range(n - 1))


def profile_max(env, lo, hi):
    """Exact maximum of the pinned triangular profile on a closed cell."""
    if not F(0) <= lo < hi <= env["T"]:
        raise ValueError("Cell lies outside the fixed mission")
    peak = env["left"] + env["rise"]
    first = max(0, ceil((lo - peak) / env["cycle"]))
    last = min(env["count"] - 1, (hi - peak) // env["cycle"])
    if first <= last:
        return env["pmax"]

    def at(t):
        j = t // env["cycle"]
        phase = t - j * env["cycle"]
        if j >= env["count"]:
            return env["b"]
        triangle = max(F(0), 1 - abs(phase - peak) / env["rise"])
        return env["b"] + env["amplitude"] * triangle

    return max(at(lo), at(hi))


def geometry(T, L, Dobs, install, xi_minus, xi_plus, J):
    if min(T, L, Dobs, xi_minus) <= 0 or min(install, J) < 0 or xi_plus < xi_minus:
        raise ValueError("Invalid timing input")
    k = max(1, ceil((Dobs + install) / L))
    H = (k + 1) * xi_plus * L + 2 * J
    P = xi_plus * Dobs + 2 * J
    d = k * xi_minus * L
    if d <= 2 * J or P > H:
        raise ValueError("Timing does not satisfy certificate preconditions")
    M = H // d + 1
    N = ceil((T + 2 * J) / d) + 2
    return {"k": k, "H": H, "P": P, "d": d, "M": M, "N": N}


def finite_v(T, L, Dobs, install, xi, J, W, integral):
    """(4)-(6) for supplied deterministic word-rate integrals.

    This routine is deliberately used only on short algebraic examples.
    Formula (1), not a billion-node allocation, is the mission-level check.
    """
    geo = geometry(T, L, Dobs, install, xi, xi, J)
    k = geo["k"]
    last = ceil((T + J - xi * Dobs) / (xi * L)) - 1

    def clip(a, b):
        return max(F(0), a), min(T, b)

    def mass(ab):
        a, b = ab
        return integral(a, b) if a < b else F(0)

    A, C, nodes = {}, {}, {}
    for m in range(last, -1, -1):
        choices = []
        for u in (0, 1):
            nxt = m + k + u
            I = clip(xi * (m * L + Dobs) - J, xi * (nxt * L + Dobs) + J)
            S = clip(xi * nxt * L - J, xi * (nxt * L + Dobs) + J)
            mu, s = mass(I), mass(S)
            local = F(W, 2) * mu**2 + W * s * A.get(nxt, F(0))
            choices.append({"next": nxt, "I": I, "S": S, "mu": mu,
                            "s": s, "local": local,
                            "D": local + C.get(nxt, F(0))})
        nodes[m] = choices
        A[m] = max(x["mu"] for x in choices)
        C[m] = max(x["D"] for x in choices)
    start_I = clip(F(0), xi * Dobs + J)
    mu = mass(start_I)
    start_local = F(W, 2) * mu**2 + W * mu * A.get(0, F(0))
    return {"A": A, "C": C, "nodes": nodes, "start_I": start_I,
            "start_local": start_local, "V0": start_local + C.get(0, F(0)),
            "geo": geo}


def algebra_checks():
    checks = []
    # A sharp primal/dual pair: growth improves the same mass-only bound.
    edges = [F(i) for i in range(4)]
    weights = [F(1), F(1), F(3)]
    beta = [F(0)] * 3
    gamma = [F(2, 3), F(4, 3)]
    ub = dual_bound(edges, weights, F(1), F(1), F(1, 4), F(5, 3), beta, gamma)
    x = [F(1, 12), F(1, 3), F(7, 12)]
    assert sum(x) == 1 and max(x) <= 1
    assert all(x[j + 1] - x[j] <= F(1, 4) for j in range(2))
    assert sum(w * v for w, v in zip(weights, x)) == ub == F(13, 6) < 3
    checks.append("growth_dual_matches_independent_primal_witness_13_over_6")
    for y, gm in [(F(5, 3) - F(1, 100), gamma), (F(5, 3), [F(-1), F(4, 3)])]:
        try:
            dual_bound(edges, weights, F(1), F(1), F(1, 4), y, beta, gm)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid dual was accepted")
    checks.append("invalid_dual_and_negative_multiplier_rejected")
    assert dual_bound([F(0), F(5)], [F(3)], F(1), F(0), F(1),
                      F(3), [F(0)], []) == 0
    checks.append("zero_total_residual_mass_gives_zero_even_with_positive_cap")

    # Increasing affine word rate. Integrals and squared integrals are separate
    # polynomial identities; neither is a sampled simulator trace.
    T, L, Dobs, install, xi, J, W = F(29, 5), F(1, 2), F(3, 5), F(1, 10), F(1), F(1, 100), 3
    b, a = F(1, 50), F(1, 100)

    def mass(lo, hi):
        return b * (hi - lo) + a * (hi**2 - lo**2) / 2

    def square(lo, hi):
        return b*b*(hi-lo) + b*a*(hi**2-lo**2) + a*a*(hi**3-lo**3)/3

    f = finite_v(T, L, Dobs, install, xi, J, W, mass)

    def paths(m):
        if m not in f["nodes"]:
            return [([], F(0))]
        out = []
        for choice in f["nodes"][m]:
            for tail, cost in paths(choice["next"]):
                out.append(([choice] + tail, choice["local"] + cost))
        return out

    all_paths = paths(0)
    assert f["V0"] == f["start_local"] + max(cost for _, cost in all_paths)
    checks.append("backward_recursion_equals_exhaustive_finite_path_maximum")
    g = f["geo"]
    cap = b + a * T
    compressed = W * ((g["H"] + g["M"] * g["P"] / 2) * square(F(0), T)
                      + g["H"] * cap**2 * 2 * J * g["N"])
    for path, cost in all_paths:
        assert f["start_local"] + cost <= compressed
        Is = [f["start_I"]] + [v["I"] for v in path]
        Ss = [f["start_I"]] + [v["S"] for v in path]
        Js = [f["nodes"][0][1]["I"]] if 0 in f["nodes"] else []
        Js += [f["nodes"][v["next"]][1]["I"] for v in path if v["next"] in f["nodes"]]
        cuts = sorted({F(0), T, *(p for ab in Is + Ss + Js for p in ab if 0 <= p <= T)})
        for left, right in zip(cuts, cuts[1:]):
            mid = (left + right) / 2
            count = lambda ivs: sum(lo <= mid < hi for lo, hi in ivs)
            assert count(Is) <= 2 and count(Ss) <= count(Is) and count(Js) <= g["M"]
        energy_I = sum(square(lo, hi) for lo, hi in Is if lo < hi)
        assert energy_I <= square(F(0), T) + cap**2 * 2 * J * g["N"]
    checks.append("every_finite_path_obeys_window_multiplicity_and_halo_bound")
    assert f["V0"] > 0 and f["V0"] <= compressed
    checks.append("compressed_energy_bound_dominates_exact_finite_recursion")
    # Two hidden residuals with the same chosen public branch cannot have
    # the same potential merely because the observed C was zero.
    ch = f["nodes"][0][1]
    assert (ch["mu"] + ch["D"]) - ch["D"] == ch["mu"] > 0
    checks.append("zero_observation_does_not_remove_hidden_residual_term")
    short = F(1, 5)
    tail = finite_v(short, L, Dobs, install, xi, J, W, mass)
    assert tail["nodes"] == {}
    assert tail["V0"] == F(W, 2) * mass(F(0), short)**2 > 0
    checks.append("partial_startup_terminal_interval_is_charged_without_fake_count")
    return checks


def load_environment():
    source_text = (ROOT / SOURCE).read_text(encoding="utf-8")
    digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    if digest != SOURCE_SHA:
        raise ValueError("Pinned inputs changed; inspect before reusing this certificate")
    data = json.loads(source_text)
    e, first, bank, service = data["environment"], data["first_probe"], data["bank"], data["service"]
    T = F(bank["mission_s"])
    W, alpha, eps = first["words"], F(first["alpha"]), F(first["epsilon"])
    assert (W, alpha, eps) == (1048576, F(1, 10), F(1, 1000))
    b, B, Fs = F(e["b"]), F(e["B"]), F(e["Fs"])
    tpl = e["template"]
    n, width, rise = tpl["count"], F(tpl["width_s"]), F(tpl["rise_s"])
    assert width == 2 * rise and n * tpl["cycle_s"] == T
    amp = (1 - alpha) * 2 * Fs / (n * width)
    R, Fr, growth = B - b - amp, alpha * Fs, F(e["rho"]) * F(e["ell"]) - amp / rise
    Ip = b*b*T + 2*b*(1-alpha)*Fs + n*width*amp*amp/3
    # Independent exact integration of each linear segment from its endpoints.
    linear_square = lambda lo, hi, length: length * (lo*lo + lo*hi + hi*hi) / 3
    Ip_direct = b*b*(T-n*width) + n*(linear_square(b, b+amp, rise)
                                          + linear_square(b+amp, b, rise))
    assert Ip_direct == Ip and R > 0 and growth > 0
    Ur = dual_bound([F(0), T], [2*(b+amp)+R], R, Fr, growth,
                    2*(b+amp)+R, [F(0)], [])
    c = F(39, e["reference_positions"])
    return {"W": W, "T": T, "alpha": alpha, "epsilon": eps, "b": b, "B": B,
            "Fs": Fs, "pmax": b+amp, "R": R, "Fr": Fr, "g": growth,
            "Ip": Ip, "Ur": Ur, "c": c, "L": F(service["calendar"]["g_ticks"]*W, 10**9),
            "xi_minus": F(service["xi_minus"]), "xi_plus": F(service["xi_plus"]),
            "J": F(service["J_ns"])/10**9,
            "delta_exec": F(data["information"]["lifetime_delta_exec"]),
            "amplitude": amp, "left": F(tpl["left_s"]), "rise": rise,
            "cycle": F(tpl["cycle_s"]), "count": n}


def manifest(env, checks):
    assert profile_max(env, F(0), env["left"] / 2) == env["b"]
    assert profile_max(env, env["left"], env["left"] + env["rise"]) == env["pmax"]
    assert profile_max(env, F(0), env["T"]) == env["pmax"]
    witness_duration = env["Fr"] / env["R"]
    assert F(0) < witness_duration < env["T"]
    # r=R until Fr/R, then zero is nonincreasing, hence satisfies the
    # one-sided growth constraint. This bounds the CERTIFICATE, not Q.
    energy_floor = env["Ip"] + (2*env["b"]+env["R"])*env["Fr"]
    test_floor = env["W"]*env["c"]**2 * (2*env["xi_plus"]*env["L"]) * energy_floor
    assert test_floor > env["epsilon"]
    down = test_floor * 10**18
    down_int = down.numerator // down.denominator
    return {
        "task": 196, "base_main": "29a37708145fbabfb51ce5dda6d5001962973ec2",
        "policy": "later_iff_complete_valid_zero_healthy_and_installed_in_time_else_nearest",
        "status": "PROCEDURE_CHECKED_COMPRESSED_TEST_INSUFFICIENT_FULL_V_UNINSTANTIATED",
        "source": SOURCE.as_posix(), "source_sha256_lf": SOURCE_SHA,
        "script_sha256_lf": hashlib.sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),
        "fixed_probe": {"words": env["W"], "alpha": str(env["alpha"]),
                        "epsilon": str(env["epsilon"]), "mission_s": str(env["T"])},
        "environment": {k: record(env[k]) for k in ["pmax", "R", "Fr", "g", "Ip", "Ur"]},
        "squared_rate_integral_upper": record(env["Ip"] + env["Ur"]),
        "mass_only_risk_coefficient_per_s": record(env["W"]*env["c"]**2*(env["Ip"]+env["Ur"])),
        "residual_cap_all_T_exposure_over_quota": record(env["R"]*env["T"]/env["Fr"]),
        "compressed_test_diagnostic": {
            "witness": "r=R on [0,Fr/R), then 0; nonincreasing, same original class",
            "witness_duration_s": record(witness_duration),
            "test_value_lower_bound_not_Q": {
                "exact": str(test_floor),
                "decimal_down": f"{down_int // 10**18}.{down_int % 10**18:018d}"},
            "strictly_above_epsilon": True,
            "holds_for_every_valid_environment_dual_and_regular_timing_binding": True,
            "implication": "Only the compressed test fails; not a lower bound on Q or on the sharper V."
        },
        "missing_bindings": ["certified decision offset for own count at 4 MiB",
                             "certified installation guard for these templates",
                             "nonoverlapping lifetime exceptions and delta_C"],
        "numeric_Q_upper": None,
        "checks": checks + ["canonical_profile_integral_matches_independent_linear_segment_identity",
                            "cell_maximum_uses_actual_profile_and_peak_locations",
                            "admissible_mass_witness_forces_compressed_test_above_fixed_epsilon"],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    ap.add_argument("--decision-offset-ns")
    ap.add_argument("--install-guard-ns")
    ap.add_argument("--delta-total", help="Other nonoverlapping lifetime exceptions, excluding delta_C")
    ap.add_argument("--delta-C", dest="delta_c")
    ap.add_argument("--dual-json", type=Path,
                    help="Exact rational edges/y/beta/gamma; profile weights are recomputed")
    args = ap.parse_args()
    env = load_environment()
    result = manifest(env, algebra_checks())
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        RESULT.write_text(output, encoding="utf-8", newline="\n")
    else:
        if RESULT.read_text(encoding="utf-8") != output:
            raise AssertionError("Saved result differs from exact replay")
    print(f"Exact algebra checks: {len(result['checks'])}; saved result matches.")
    print("Compressed test insufficient at the unchanged first_probe; this is not Q > epsilon.")
    Ur = env["Ur"]
    if args.dual_json:
        cert = json.loads(args.dual_json.read_text(encoding="utf-8"))
        edges = [F(v) for v in cert["edges"]]
        if edges[0] != 0 or edges[-1] != env["T"]:
            raise ValueError("Dual cells must cover the full fixed mission")
        weights = [2*profile_max(env, lo, hi)+env["R"] for lo, hi in zip(edges, edges[1:])]
        Ur = dual_bound(edges, weights, env["R"], env["Fr"], env["g"], F(cert["y"]),
                        [F(v) for v in cert["beta"]], [F(v) for v in cert["gamma"]])
        print(json.dumps({"verified_dual_Ur": record(Ur), "cells": len(weights)}, indent=2))
    vals = [args.decision_offset_ns, args.install_guard_ns, args.delta_total, args.delta_c]
    if any(v is not None for v in vals):
        if not all(v is not None for v in vals):
            ap.error("All four explicit timing/exception bindings are required")
        Dobs, install, delta, delta_c = [F(v) for v in vals]
        if delta < env["delta_exec"] or delta_c < 0 or delta + delta_c > 1:
            raise ValueError("Invalid lifetime exception allowance")
        geo = geometry(env["T"], env["L"], Dobs/10**9, install/10**9,
                       env["xi_minus"], env["xi_plus"], env["J"])
        future = env["W"]*env["c"]**2 * (
            (geo["H"]+geo["M"]*geo["P"]/2)*(env["Ip"]+Ur)
            + geo["H"]*env["B"]**2*2*env["J"]*geo["N"])
        q = delta + delta_c + future
        print(json.dumps({"conditional_on_supplied_contract": True,
                          "policy_unchanged": True,
                          "geometry": {k: str(v) for k, v in geo.items()},
                          "V_upper": record(future), "delta_plus_V": record(q),
                          "test_passes": q <= env["epsilon"],
                          "meaning_of_false": "This certificate is insufficient; no violation proved."},
                         ensure_ascii=False, indent=2))
    else:
        print("Numeric Q not instantiated: timing and delta_C bindings remain explicit.")


if __name__ == "__main__":
    main()

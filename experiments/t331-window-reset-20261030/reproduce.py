"""One registered c01 calculation for #331; exact fractions, no search/grid."""

import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def lf_bytes(path):
    return path.read_bytes().replace(b"\r\n", b"\n")


def digest(path):
    return hashlib.sha256(lf_bytes(path)).hexdigest()


def directed(value, places=20):
    """Exact rational and outward decimal display; no floating point."""
    value = F(value)
    scale = 10 ** places
    lo = value.numerator * scale // value.denominator
    hi = -((-value.numerator * scale) // value.denominator)

    def decimal(integer):
        sign = "-" if integer < 0 else ""
        whole, part = divmod(abs(integer), scale)
        return f"{sign}{whole}.{part:0{places}d}"

    return {
        "exact": str(value),
        "lower": decimal(lo),
        "upper": decimal(hi),
    }


def calculate():
    registration = json.loads(lf_bytes(HERE / "registration.json"))
    assert registration["task"] == 331
    assert registration["rule_id"] == "L_cut_c01_m8_H0"
    assert registration["declared_before_numerical_check"] is True
    assert registration["numerical_cases"] == 1
    assert registration["cell_id"] == "c01"
    assert registration["ratio"] == 8 and registration["hold"] == 0
    sources = registration["source_sha256_LF"]
    assert sources, "Registration must pin sources before the calculation"
    for relative, expected in sources.items():
        assert digest(ROOT / relative) == expected, f"Source changed: {relative}"

    inputs = json.loads(lf_bytes(ROOT / registration["inputs_path"]))
    cells = json.loads(lf_bytes(ROOT / registration["cells_path"]))
    matches = [cell for cell in cells["cells"] if cell["id"] == "c01"]
    assert len(matches) == 1
    cell = matches[0]
    env, bank = inputs["environment"], inputs["bank"]
    svc, info = inputs["service"], inputs["information"]
    template = env["template"]

    W = cell["words"]
    T = bank["mission_s"]
    epsilon, alpha = F(cell["epsilon"]), F(cell["alpha"])
    assert (W, cell["useful_bytes"], T, epsilon, alpha) == (
        1048576, 4194304, 315576000, F(1, 1000), F(0)
    )
    assert bank["code"] == [39, 32, 1] and bank["physical_word_bits"] == 48
    assert bank["clean_initial_conditional"] and bank["initial_K0"] == 0
    assert bank["pending_initial"] is False and bank["useful_writes"] == 0
    assert not bank["ordinary_app_read_repairs"]
    assert svc["calendar"]["g_ticks"] == 196
    assert svc["N0_hold_override"]["hold_ticks"] == 0

    D = env["reference_positions"]
    b, B, Fs = F(env["b"]), F(env["B"]), F(env["Fs"])
    N, width, rise = template["count"], template["width_s"], template["rise_s"]
    assert (N, width, rise, template["cycle_s"], template["left_s"]) == (
        58440, 600, 300, 5400, 1800
    )
    assert T == N * template["cycle_s"] and width == 2 * rise
    assert D == env["reference_words"] * env["reference_bits"] == 19922944
    a = 2 * Fs / (N * width)
    IH = N * width * (b * b + b * a + a * a / 3)
    IL = (T - N * width) * b * b
    K = F(W * 39 * 38, 2 * D * D)
    M1 = b * T + Fs
    xi = F(svc["xi_plus"])
    ns = F(1, 10 ** 9)
    J = F(svc["J_ns"]) * ns
    dE = 124 * xi * ns + 3 * J
    XE = 2 * B * dE * M1
    delta = F(info["lifetime_delta_exec"]) + F(info["lifetime_delta_calendar"])
    hplus = F(info["healthy_poll_nominal_s"]) * xi + J
    delay = F(info["command_delay_upper_s"])
    et = F(info["mission_time_error_upper_s"])
    freeze = svc["calendar"]["freeze_ticks"] * xi * ns + J
    C0 = hplus + delay + freeze + 2 * et
    L = svc["calendar"]["g_ticks"] * W * ns
    ratio = registration["ratio"]

    numerator = epsilon - delta - K * ((J + dE) * (IH + IL) + XE)
    denominator = K * L * xi * (IH + ratio * IL)
    assert denominator > 0
    kH = numerator // denominator
    kL = ratio * kH
    result = {
        "schema": 1,
        "task": 331,
        "rule_id": registration["rule_id"],
        "base_main": registration["base_main"],
        "registration_sha256_LF": digest(HERE / "registration.json"),
        "reproduce_sha256_LF": digest(Path(__file__)),
        "source_sha256_LF": sources,
        "arithmetic": "exact fractions; outward decimal display with 20 places",
        "numerical_cases": 1,
        "cell_id": "c01",
        "kH": kH,
        "kL": kL,
        "hold": 0,
        "quantifier": "fixed p at alpha=0; every execution/channel law under the accepted contract",
    }
    cap = inputs["comparison"]["period_menu"]["max_kL"]
    if kH < 1 or kL > cap:
        result["status"] = "local_rule_rejects"
        return result

    assert kH * denominator <= numerator < (kH + 1) * denominator
    PH = L * kH * xi + J
    PL = L * kL * xi + J
    AH, AL = PH + dE, PL + dE
    local = delta + K * (AH * IH + AL * IL + XE)
    slack = epsilon - local
    assert slack >= 0
    sigma = AH + 2 * C0
    values = {
        "epsilon": epsilon,
        "Delta": delta,
        "a_reference_per_s": a,
        "IH_reference_squared_integral": IH,
        "IL_reference_squared_integral": IL,
        "K": K,
        "dE_s": dE,
        "C0_s": C0,
        "PH_plus_s": PH,
        "PL_plus_s": PL,
        "sigma_s": sigma,
        "XE": XE,
        "L_cut_fictitious_upper": local,
        "rounding_slack": slack,
    }
    result["geometric_domain"] = 0 < sigma < rise
    if not result["geometric_domain"]:
        result["status"] = "not_established"
        result["gap"] = "PR303 boundary polynomial requires 0<sigma<300"
    else:
        Jsigma = 2 * N * (
            b * b * sigma + b * a * sigma ** 2 / rise
            + a * a * sigma ** 3 / (3 * rise ** 2)
        )
        boundary = K * (AL - AH) * Jsigma
        physical = local + boundary
        assert boundary >= 0 and Jsigma <= IH
        values.update({
            "Jsigma_reference_squared_integral": Jsigma,
            "D_boundary_upper_correction": boundary,
            "physical_Q_upper_unclipped": physical,
            "physical_Q_upper": min(F(1), physical),
            "physical_margin": epsilon - physical,
        })
        result["boundary_covered_by_rounding"] = boundary <= slack
        result["status"] = (
            "sufficient_admissibility" if boundary <= slack else "not_established"
        )
        if boundary > slack:
            result["gap"] = "A lower witness or sharper physical estimate is required; no second case authorized"
    result["values"] = {key: directed(value) for key, value in values.items()}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="save the single registered result")
    group.add_argument("--check", action="store_true", help="replay and compare the same result (default)")
    args = parser.parse_args()
    result = calculate()
    target = HERE / "result.json"
    if args.write:
        if target.exists():
            parser.error("result.json already exists; use --check to replay the registered case")
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        stored = json.loads(lf_bytes(target))
        assert result == stored, "The stored result differs from the exact replay"
    print(json.dumps({
        "status": result["status"], "kH": result["kH"], "kL": result["kL"],
        "values": result.get("values", {}),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

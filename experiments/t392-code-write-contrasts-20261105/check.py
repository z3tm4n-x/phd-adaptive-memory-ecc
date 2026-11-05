"""One rational compatibility check of c01 for T392; no grid or old replay.

The formula/selection rule is in theory/t392-code-write-contrasts-20261105.md.
Accepted models are not imported or executed. Only geometry is printed at 1/2/4 MiB.
"""
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction as F
from hashlib import sha256
from math import comb
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = "0df2a56e178fd7e79af9799d1b111d3dfdc57c70"
MAP = "experiments/regime-map-methodology-20261019/predictability-volume-20261028/"
COMMON = "experiments/t186-method-comparison/code-strength/common-input.json"
PINNED = {
    MAP + "inputs.json": "5f62171e4706854f6419345d7eaed1f2103c06bc4989976fde03942db091c6cd",
    MAP + "map-14/inputs.json": "bbd6e84d1ab646e16577b01519d21d339100ced74cda34f6c503a77a590bafd4",
    COMMON: "e635327d07e74742247c5ad56cbf865c1bf05c362910dad5e56ce94b8d4c550e",
}
NS = 10**9


def read(name):
    text = (ROOT / name).read_text(encoding="utf-8").replace("\r\n", "\n")
    if sha256(text.encode()).hexdigest() != PINNED[name]:
        raise ValueError("Pinned input changed: " + name)
    return json.loads(text)


def ceil(x):
    return -(-x.numerator // x.denominator)


def encode(value):
    if isinstance(value, F):
        with localcontext() as ctx:
            ctx.prec = 40
            ctx.rounding = ROUND_FLOOR
            lo = str(Decimal(value.numerator) / Decimal(value.denominator))
            ctx.rounding = ROUND_CEILING
            hi = str(Decimal(value.numerator) / Decimal(value.denominator))
        return {"exact": str(value), "decimal_down": lo, "decimal_up": hi}
    if isinstance(value, dict):
        return {key: encode(v) for key, v in value.items()}
    if isinstance(value, list):
        return [encode(v) for v in value]
    return value


def calculate():
    cfg, cells, common = read(MAP + "inputs.json"), read(MAP + "map-14/inputs.json"), read(COMMON)
    cell = next(row for row in cells["cells"] if row["id"] == "c01")
    W, eps = cell["words"], F(cell["epsilon"])
    assert W == 1048576 and F(cell["alpha"]) == 0 and eps == F(1, 1000)
    assert cfg["bank"]["initial_K0"] == 0 and not cfg["bank"]["pending_initial"]
    e, svc, app = cfg["environment"], cfg["service"], common["application"]
    D, T = e["reference_positions"], F(cfg["bank"]["mission_s"])
    b, Fs = F(e["b"]), F(e["Fs"])
    pulses, width = e["template"]["count"], e["template"]["width_s"]
    a = 2 * Fs / (pulses * width)
    peak = b + a  # alpha=0: r=0, the known profile's actual cap
    S1 = b * T + Fs
    S2 = b*b*T + 2*b*Fs + F(pulses*width, 3)*a*a
    S3 = b**3*T + 3*b*b*Fs + pulses*width*b*a*a + F(pulses*width, 4)*a**3
    M1, M2, M3, bit_peak = S1/D, S2/D**2, S3/D**3, peak/D
    xp, xm, J = F(svc["xi_plus"]), F(svc["xi_minus"]), F(svc["J_ns"])
    delta = F(cfg["information"]["lifetime_delta_exec"])
    h, arrival0 = app["epoch_ns"], app["first_ns"] + app["write_offset_ns"]
    deadline = F(svc["app_deadline_ns"], NS)
    k = h // svc["calendar"]["g_ticks"]  # declared before evaluation, no selection by Q
    Pnom = F(196*k*W, NS)
    Pplus = Pnom*xp + J/NS
    dE44 = (128*xp + 3*J)/NS
    L = Pplus + dE44
    U44 = delta + W*comb(44, 3)*(L*L*M3 + 3*bit_peak*dE44*L*M2
                                + 3*bit_peak**2*dE44**2*M1)
    Pwrite = F(W*h, NS)
    Uwrite39 = delta + W*comb(39, 2)*(Pwrite*M2 + 2*bit_peak*deadline*M1)

    # T187/T196 lower on complete repair-free gaps; first/last partial gaps omitted.
    gaps = int(T // Pwrite) - 1
    gap = Pwrite - deadline
    mu_max = 39*bit_peak*gap
    assert 0 < mu_max < 1 and gaps > 0
    Z_lower = W*gaps*comb(39, 2)*(b/D)**2*gap*gap*(1-mu_max)
    # exp(-mu)>=1-mu and 1-exp(-Z)>=Z/(1+Z); no floating exponentials.
    Qwrite_lower = Z_lower/(1+Z_lower) - delta

    total_ns = int(T)*NS
    last_write_index = (total_ns - 1 - arrival0) // h
    tail_min = total_ns - (arrival0 + last_write_index*h)
    Nar = (total_ns - 1 - app["first_ns"] - app["read_offset_ns"]) // h + 1
    Naw = last_write_index + 1

    # Accepted serial/aperture formulas with each code's own conditional latency.
    resources = {}
    for n in (39, 44):
        dec = common["service"][f"decode{n}_ns"]
        enc = common["service"][f"encode{n}_ns"]
        R, E, Aw = (48+dec)*xp+J, (104+dec)*xp+J, (104+dec+enc)*xp+J
        frames = 2 + ceil((F(10**6) + max(E, Aw) + J)/(1568*xm))
        apps = 1 + ceil(F(10**6 + svc["app_deadline_ns"], h))
        peak_serial = (8*frames*E + apps*(R+Aw) + frames*(64*xp+J))/10**6
        resources[str(n)] = {
            "control_margin_ns": 164*xm-J-E,
            "full_write_to_management_margin_ns": 160*xm-J-Aw,
            "response_envelope_ns": 820+1568*xp+J+Aw,
            "all_slot_peak_with_full_management": peak_serial,
            "frames": frames, "app_operations_each": apps,
        }
        assert 164*xm-J-E > 0 and 160*xm-J-Aw > 0
        assert peak_serial < F(4, 5) and 820+1568*xp+J+Aw < 3000

    assert U44 < eps and Qwrite_lower > eps
    assert arrival0 + (W-1)*h + int(deadline*NS) < W*h
    assert tail_min > deadline*NS  # incidental at this T; not used in the risk proof
    return {
        "base_main": BASE, "pinned_sha256_LF": PINNED,
        "scope": "c01 only; conditional singleton/clean p+r; no physical calibration",
        "reference_moments": {"peak": peak, "S1": S1, "S2": S2, "S3": S3},
        "constant44": {"k": k, "P_nominal_s": Pnom, "P_plus_s": Pplus,
                       "dE_s": dE44, "Q_upper": U44, "slack": eps-U44},
        "write_only39": {"P_s": Pwrite, "Q_upper": Uwrite39,
                         "complete_gaps_per_word": gaps, "mu_max_gap": mu_max,
                         "Z_rational_lower": Z_lower, "Q_rational_lower": Qwrite_lower,
                         "first_deadline_max_ns": arrival0+(W-1)*h+int(deadline*NS),
                         "min_terminal_gap_ns": tail_min,
                         "max_terminal_gap_ns": tail_min+(W-1)*h},
        "geometry_only_no_other_risk_cells": [
            {"W": w, "P_write_s": F(w*h, NS)} for w in (262144, 524288, 1048576)
        ],
        "application_counts_all_started": {"read": Nar, "write": Naw},
        "conditional_resource_substitutions": resources,
    }


if __name__ == "__main__":
    print(json.dumps(encode(calculate()), ensure_ascii=False, indent=2))

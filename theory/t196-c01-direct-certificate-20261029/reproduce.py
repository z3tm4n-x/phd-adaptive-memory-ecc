"""Exact initial test for the direct physical-pair certificate of fixed c01 M.

No policy search, simulation, changed timing, or change to an accepted result.
The stopped functional and its connection to M are proved in the sibling note.
Default checks result.json; --write updates only this directory's result.json.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "db35c1ec64a99487e28106b326f3d21fc42a4f54"
MAP = "experiments/regime-map-methodology-20261019/predictability-volume-20261028/"
PINS = {
    MAP + "THEORY.md": "a2d4da37e9cc685e638bd620bae3d3622bee3dabe445e90c90abcdfb5c95eaf1",
    MAP + "RESOURCE.md": "8d55e3732ba88ae0ee18d0c8c312226a0311e14712d4d9c3a2332b2feb51665a",
    MAP + "inputs.json": "5f62171e4706854f6419345d7eaed1f2103c06bc4989976fde03942db091c6cd",
    MAP + "map-14/result.json": "ef8b56daf67fbc3b48804129ba7ddde27dab33346aee9c24254f8c20584274e0",
    "experiments/t186-method-comparison/code-strength/SERVICE.md": "b6a93bf0722358619a5c54f4a5587be7852b79bba8a2d4160e313a4b69e9906c",
    "theory/t196-causal-e-transition-20261028.md": "813bcd06f2619b82d8ac3f5d1c4690f36ed0e1b002042da2ab84318b948ffb77",
    "theory/t196-theorem31-assembly-20261029.md": "a48a526f0e67c28983bcd503c65c038544ff5a9eac294dc07aa159ab6eab0142",
    "theory/t196-window-application-20261029.md": "bd07cdd340185cb14f9105f810dfa4725cc571f4851a2e9e0e71e99d17e1d453",
    "theory/REVIEW_T196_WINDOW_APPLICATION_20261029.md": "b3970589dcb5bee62e0b7d62ed6d8b97f8cd90c6198da71df41a88cbdedb0399",
}


def sha(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def calculate():
    for name, expected in PINS.items():
        assert sha(ROOT / name) == expected, f"Changed accepted source: {name}"
    x = json.loads((ROOT / (MAP + "inputs.json")).read_text("utf-8"))
    accepted = json.loads((ROOT / (MAP + "map-14/result.json")).read_text("utf-8"))
    cell = accepted["cells"]["c01"]
    W, T = cell["cell"]["words"], F(cell["mission_s"])
    eps, alpha = F(cell["cell"]["epsilon"]), F(cell["cell"]["alpha"])
    method = cell["methods"]["M"]
    assert (W, T, eps, alpha, method["pair"]) == (1048576, F(315576000), F(1, 1000), F(0), [26, 208])
    e, s, info = (x[k] for k in ("environment", "service", "information"))
    xm, xp, J = (F(s[k]) for k in ("xi_minus", "xi_plus", "J_ns"))
    N, width = e["template"]["count"], F(e["template"]["width_s"])
    b, B, Fs = (F(e[k]) for k in ("b", "B", "Fs"))
    D = e["reference_positions"]
    a = 2 * Fs / (N * width)
    IH = N * width * (b*b + b*a + a*a/3)
    IL = (T - N*width) * b*b
    c, chi = F(39, D), F(38, 39)
    K = W * chi * c*c / 2
    L = F(196 * W, 10**9)
    dE = (124*xp + 3*J) / 10**9
    PH, PL = (k*L*xp + J/10**9 for k in (26, 208))
    assert W % 8 == 0
    q_last = 1568*((W-1)//8) + 164*((W-1) % 8)
    assert 196*W - q_last == 420
    clearance = 420*xm - 124*xp - 3*J
    assert clearance > 0
    assert 26*L*xm > dE
    hold = cell["price_bounds"][method["price"]]["price"]["hold"]
    assert F(hold["lower_s"]) >= PH + dE
    assert F(e["template"]["left_s"]) > PH + dE
    assert T - (F(e["template"]["left_s"]) + (N-1)*F(e["template"]["cycle_s"]) + width) > PH + dE
    assert IH == F(cell["environment"]["IH"])
    assert IL == F(cell["environment"]["IL"])
    assert K == F(cell["environment"]["K"])

    # Derived from the explicit marked-pair functional, not from the
    # probability of the unmodified PR308 auxiliary first break.
    ordinary = K * ((PH+dE)*IH + (PL+dE)*IL)
    cross = W * chi * c*c * B*dE*(b*T+Fs)
    v0_upper = ordinary + cross
    delta = F(info["lifetime_delta_exec"]) + F(info["lifetime_delta_calendar"])
    q_upper = delta + v0_upper
    assert ordinary == F(method["Q_terms"]["known"])
    assert cross == F(method["Q_terms"]["E_cross"])
    assert F(method["Q_terms"]["residual"]) == 0
    assert q_upper == F(method["Q_upper"]) < eps
    diagnostic = delta + v0_upper / chi
    assert diagnostic > eps  # diagnostic only; neither a lower bound nor a certificate
    return dict(
        status="OWN RESULT pending acceptance: narrow causal transition plus direct physical certificate",
        base_main=BASE, source_sha256_LF=PINS,
        cell="c01", words=W, mission_s=T, alpha=alpha, epsilon=eps, periods=[26, 208],
        stopped_event="first physical uncorrectable state or first physical execution exception",
        certificate_law="own physical M process; raw marked Poisson parents; deterministic guaranteed support",
        proof_slice_pending_clearance_lower_ns=clearance,
        round_nominal_s=L, ordinary_block_upper_s=208*L*xp+2*J/10**9,
        dE_s=dE, PH_upper_s=PH, PL_upper_s=PL,
        pair_mark_probability=chi, K=K,
        ordinary_pair_expectation_upper=ordinary, aperture_cross_expectation_upper=cross,
        EV0_upper=v0_upper, delta=delta, Q_upper=q_upper, initial_margin=eps-q_upper,
        initial_test_passed=True,
        unproved_auxiliary_coefficient_substitution=diagnostic,
        original_PR308_break_certificate_established=False,
        PR314_scope_changed=False, future_action_admission_established=False,
        complete_price_established=False, new_policy_search=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    out = calculate()
    raw = (json.dumps(out, default=str, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    path = HERE / "result.json"
    if args.write:
        path.write_bytes(raw)
    else:
        assert path.read_bytes().replace(b"\r\n", b"\n") == raw, "Saved result differs from exact replay"
    print("PASS: nine pinned sources, pending-free proof slices, exact initial test and replay")
    # Display only. All scientific comparisons above use exact fractions.
    for key in ("EV0_upper", "Q_upper", "initial_margin", "proof_slice_pending_clearance_lower_ns"):
        print(key, format(float(out[key]), ".16g"))


if __name__ == "__main__":
    main()

"""Independent exact lower bound on the PR310 certificate, not on Q(T)."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/regime-map-methodology-20261019/predictability-volume-20261028/inputs.json"
EXPECTED = "5f62171e4706854f6419345d7eaed1f2103c06bc4989976fde03942db091c6cd"


def down(value, digits=18):
    scale = 10**digits
    v = value * scale
    n = v.numerator // v.denominator
    return f"{n // scale}.{n % scale:0{digits}d}"


def main():
    source = SOURCE.read_text(encoding="utf-8")
    assert hashlib.sha256(source.encode("utf-8")).hexdigest() == EXPECTED
    data = json.loads(source)
    e, s, probe = data["environment"], data["service"], data["first_probe"]
    W, alpha, epsilon = probe["words"], F(probe["alpha"]), F(probe["epsilon"])
    assert (W, alpha, epsilon) == (1048576, F(1, 10), F(1, 1000))
    T = F(data["bank"]["mission_s"])
    b, B, Fs = F(e["b"]), F(e["B"]), F(e["Fs"])
    tpl = e["template"]
    amplitude = (1-alpha)*2*Fs/(tpl["count"]*F(tpl["width_s"]))
    R, Fr = B-b-amplitude, alpha*Fs
    growth = F(e["rho"])*F(e["ell"])-amplitude/F(tpl["rise_s"])
    tau = Fr/R
    assert 0 < tau < T and growth >= 0 and b+amplitude+R == B
    assert R*tau == Fr  # The nonincreasing witness respects the same quota.
    assert W % 8 == 0 and s["calendar"]["g_ticks"] == 196
    last_slot_ns = 1568*((W-1)//8)+164*((W-1) % 8)
    assert last_slot_ns == 196*W-420
    L, J = F(196*W, 10**9), F(s["J_ns"])/10**9
    xi_minus, xi_plus = F(s["xi_minus"]), F(s["xi_plus"])
    Lminus, Lplus = xi_minus*L, xi_plus*L
    d0 = xi_minus*F(last_slot_ns, 10**9)-2*J
    lam0 = F(39, e["reference_positions"])*(b+R)
    assert d0 > 0 and tau > 5*Lplus and 0 < xi_minus <= xi_plus
    lower12 = W*lam0**2*(Lminus*tau**2/(tau+4*Lminus)+d0*(tau-5*Lplus))
    lower3 = W*lam0**2*(2*Lminus*tau**2/(tau+8*Lminus))
    assert min(lower12, lower3) > epsilon
    result = {
        "meaning": "Lower bound on PR310 V_star, NOT on Q(T)",
        "source_sha256_lf": EXPECTED,
        "fixed_probe": {"W": W, "alpha": str(alpha), "epsilon": str(epsilon)},
        "witness_duration_s": str(tau),
        "necessary_physical_decision_offset_lower_s": str(d0),
        "k_1_or_2": {"exact": str(lower12), "decimal_down": down(lower12)},
        "k_at_least_3": {"exact": str(lower3), "decimal_down": down(lower3)},
        "all_regular_timing_bindings_insufficient_for_this_uniform_certificate": True,
        "lifetime_exceptions_not_set_to_zero": True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

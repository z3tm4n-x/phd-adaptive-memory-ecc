"""Audit existing inputs, not a new transport or replacement certificate."""
from decimal import Decimal as D, localcontext
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def load(path):
    p = REPO / path
    data = p.read_bytes()
    return json.loads(data), {"path": path, "sha256_checkout_bytes": hashlib.sha256(data).hexdigest()}


def calculate():
    old, source = load("experiments/t68-v21-inputs/outputs/v21_reconstructed.json")
    t73, source73 = load("theory/t73-burst-mode-count-inputs.json")
    row = next(r for r in old["rows"] if r["rho"] == 3)
    fixed = next(r for r in t73["environments"] if r["shield_g_cm2"] == "3")
    with localcontext() as context:
        context.prec = 50
        b, s, sp = (D(str(row[k])) for k in ("nuG", "nuS", "nuSp"))
        T, duration = D(315576000), D(115776)
        coef = D(37) / D(76 * 524288) * D("0.108")
        components = {"quiet": T*b*b, "solar": duration*s*s,
                      "mixed": 2*duration*b*s}
        return {
            "type": "calculated from existing serialized model inputs; not measured",
            "source_files": [source, source73],
            "protected_bits": 524288*38,
            "historical_nu_G_per_s": str(b), "historical_nu_S_per_s": str(s),
            "historical_nu_S_PDI_per_s": str(sp),
            "historical_solar_exposure_upper": str(duration*s),
            "historical_S2_components_per_s": {k: str(v) for k, v in components.items()},
            "historical_S2_sum_per_s": str(sum(components.values())),
            "accepted_rounded_S2_per_s": fixed["S2_rational_upper_per_s"],
            "accepted_rounded_B_per_s": str(D(fixed["bbar_per_s"]) + D(fixed["solar_peak_per_s"])),
            "PDI_formula_diagnostic_per_s": str(T*b*b+duration*sp*sp+2*duration*b*sp),
            "PDI_note": "Alternate historical response; not a new estimate of S2 or a replacement of 6940",
            "requested_fixed_period_s": "0.108",
            "requested_accumulation_multiplier_s": str(coef),
            "requested_old_accumulation_bound": str(coef*D(6940)),
            "requested_direct_bound": "0.00028024",
            "requested_remaining_probability": str(D("0.001")-D("0.00028024")-coef*D(6940)),
            "new_S2_A_per_s": None, "new_S2_B_per_s": None,
            "freed_probability": None,
            "interpretation_gap": "Historical full LET+HEP envelope differs from the new conditional proton-PDI profile; mission mean is explicitly supplied by the new mean-cycle scenario",
            "no_new_rules_or_certificates": True
        }


def main():
    out = HERE / "outputs"
    out.mkdir(exist_ok=True)
    (out / "baseline_audit.json").write_text(json.dumps(calculate(), ensure_ascii=False, indent=2)
        + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

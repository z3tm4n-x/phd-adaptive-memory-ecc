"""One c01 lower-bound refinement, not a search over policies or environments.

Default: verify the saved exact-fraction/directed-interval result.
--write: write only this directory's result.json. Accepted inputs stay read-only.
The deterministic mass inequality and its quantifiers are proved in ../*.md.
"""
import argparse
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "92d3d33f064acdabd82a4bc4b8e64f0971c29359"
MAP = "experiments/regime-map-methodology-20261019/predictability-volume-20261028/"
PINS = {
    MAP + "inputs.json": "5f62171e4706854f6419345d7eaed1f2103c06bc4989976fde03942db091c6cd",
    MAP + "map-14/inputs.json": "bbd6e84d1ab646e16577b01519d21d339100ced74cda34f6c503a77a590bafd4",
    MAP + "map-14/result.json": "ef8b56daf67fbc3b48804129ba7ddde27dab33346aee9c24254f8c20584274e0",
    MAP + "THEORY.md": "a2d4da37e9cc685e638bd620bae3d3622bee3dabe445e90c90abcdfb5c95eaf1",
    MAP + "RESOURCE.md": "8d55e3732ba88ae0ee18d0c8c312226a0311e14712d4d9c3a2332b2feb51665a",
    MAP + "first_point.py": "2ee8678bc484cb1ca1b02a3542efec52090683baf15b89e61790539f9c790947",
    "experiments/t114-two-stage-err/intervals.py": "817cdad503f8432fe9d57c0b9340921b1af683b8db4b72aa9314ccf0f53b3be2",
}


def sha(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def numeric(value):
    if isinstance(value, dict):
        return {k: numeric(v) for k, v in value.items()}
    if isinstance(value, list):
        return [numeric(v) for v in value]
    if isinstance(value, str):
        try:
            return F(value)
        except ValueError:
            pass
    return value


def floor_decimal(q, places):
    """Display a nonnegative rational lower bound with downward rounding."""
    assert q >= 0
    scale = 10**places
    n = q.numerator * scale // q.denominator
    return f"{n // scale}.{n % scale:0{places}d}"


def calculate():
    for name, expected in PINS.items():
        assert sha(ROOT / name) == expected, f"Changed accepted input: {name}"
    spec = importlib.util.spec_from_file_location(
        "accepted_intervals", ROOT / "experiments/t114-two-stage-err/intervals.py"
    )
    iv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(iv)
    I = iv.I

    inputs = numeric(json.loads((ROOT / (MAP + "inputs.json")).read_text("utf-8")))
    cells = numeric(json.loads((ROOT / (MAP + "map-14/inputs.json")).read_text("utf-8")))
    accepted = numeric(json.loads((ROOT / (MAP + "map-14/result.json")).read_text("utf-8")))
    cell = accepted["cells"]["c01"]
    assert cell["cell"] == next(c for c in cells["cells"] if c["id"] == "c01")
    W, T = cell["cell"]["words"], F(cell["mission_s"])
    assert (W, T, cell["cell"]["alpha"], cell["cell"]["epsilon"]) == (
        1048576, F(315576000), F(0), F(1, 1000)
    )
    env, svc, info = (inputs[k] for k in ("environment", "service", "information"))
    template = env["template"]
    N, width, cycle = (template[k] for k in ("count", "width_s", "cycle_s"))
    assert (N, width, cycle, template["rise_s"]) == (58440, 600, 5400, 300)
    assert T == N * cycle
    b, Fs, D = (env[k] for k in ("b", "Fs", "reference_positions"))
    a = 2 * Fs / (N * width)
    c = F(39, D)
    K = F(W * 39 * 38, 2 * D**2)
    J = svc["J_ns"] / 10**9
    dE = (124 * svc["xi_plus"] + 3 * svc["J_ns"]) / 10**9
    delta = info["lifetime_delta_exec"]
    assert (a, K, b) == tuple(cell["environment"][k] for k in ("a", "K", "b"))
    assert cell["environment"]["Fr"] == 0
    assert F(196 * W, 10**9) * svc["xi_plus"] + J < template["left_s"]

    # One declared cutoff. It excludes every real P >= 14, including OFF;
    # it is neither a candidate period nor a newly searched policy grid.
    P0 = F(14)
    parts = [
        ("whole_triangles", width, width * b + width * a / 2, b + a, N),
        ("interior_background_gaps", cycle - width, (cycle - width) * b, b, N - 1),
    ]
    assert sum(length * multiplicity for _, length, _, _, multiplicity in parts) == T - 4800
    Z = I(0)
    blocks = []
    for name, length, mass, peak, multiplicity in parts:
        M = length / P0 + 2
        retained_mass = max(F(0), mass - peak * M * dE)
        z = I(K * multiplicity * retained_mass**2 / (M + 1)) * I(-c * mass).exp()
        Z = Z + z
        blocks.append(dict(
            name=name, length_s=length, multiplicity=multiplicity,
            mass_reference=mass, peak_reference_per_s=peak,
            apertures_per_word_upper=M, retained_mass_lower=retained_mass,
            exponent_enclosure=[str(z.lo), str(z.hi)],
        ))
    q = I(1) - (I(0) - Z).exp() - I(delta)
    assert F(q.lo) > cell["cell"]["epsilon"]
    assert F(q.hi) - F(q.lo) < F(1, 10**40)

    method = cell["methods"]["M"]
    assert method["pair"] == [26, 208] and method["Q_status"] == "certified"
    assert method["Q_upper"] == sum(method["Q_terms"].values()) <= F(1, 1000)
    bundle = cell["price_bounds"][method["price"]]
    price = bundle["price"]
    assert price["work_after_first_failure_paid"] and price["full_started_tail_paid"]
    assert sum(price["read_terms_upper"].values()) == price["reads_upper"]
    assert sum(price["repair_terms_upper"].values()) == price["repairs_upper"]
    reads = (1 - delta) * W * (T / (P0 + J) - 2)
    costs = {}
    for coord, ticks in (("bus", 48), ("serial", 68)):
        unit_lower = ticks * svc["xi_minus"] / 10**9 - J
        lower = reads * unit_lower
        old = cell["fixed_class_lower_for_price"]["cost"][coord]["lower_s"]
        mc = price["coordinates"][coord]
        common_lower = mc["app_s"]["lower"] + mc["init_s"]["lower"]
        assert mc["all_known_upper_s"] == (
            mc["checks_upper_s"] + mc["repairs_upper_s"]
            + mc["app_s"]["upper"] + mc["init_s"]["upper"]
        )
        margin = lower + common_lower - mc["all_known_upper_s"]
        assert lower > old and margin > 0
        costs[coord] = dict(
            fixed_class_old_protection_lower_s=old,
            fixed_class_new_protection_lower_s=lower,
            fixed_class_with_common_lower_s=lower + common_lower,
            M_accepted_price=mc,
            unknown_M_minus_uniform_unknown_F_lower_budget_s=margin,
            unknown_budget_us_per_s=10**6 * margin / T,
            unknown_actual_price=None,
        )
    return dict(
        status="OWN RESULT pending acceptance; conditional model and price only",
        base_main=BASE, sources_sha256_LF=PINS,
        cell="c01", words=W, mission_s=T, alpha=F(0), epsilon=F(1, 1000),
        fixed_class_cutoff_s=P0, cutoff_optimized=False,
        lower_scope="all real constant periods P >= 14, arbitrary phases, including OFF",
        witness="same p_0, r=0; accepted deterministic execution witness; no conditioning on future success",
        dE_s=dE, delta_fixed=delta, blocks=blocks,
        Z_enclosure=[str(Z.lo), str(Z.hi)], Q_lower_expression_enclosure=[str(q.lo), str(q.hi)],
        fixed_class_reads_lower=reads,
        M_pair=method["pair"], M_accepted_Q_upper=method["Q_upper"],
        M_risk_margin=F(1, 1000) - method["Q_upper"],
        M_reads_upper=price["reads_upper"], M_repairs_upper=price["repairs_upper"],
        M_read_terms_upper=price["read_terms_upper"], M_repair_terms_upper=price["repair_terms_upper"],
        M_calendar_action_counts_upper=bundle["management"]["calendar_action_counts_upper"],
        M_local_selector_checks_upper=bundle["management"]["local_slot_selector_checks_upper"],
        cost_measure="full-horizon expected cost; uniform accepted bounds; started tail included",
        costs=costs,
        theorem31_membership_established=False, complete_price_established=False,
        new_policy_grid=False, new_environment=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = calculate()
    raw = (json.dumps(result, default=str, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    target = HERE / "result.json"
    if args.write:
        target.write_bytes(raw)
    else:
        assert target.read_bytes().replace(b"\r\n", b"\n") == raw, "Saved result differs from exact replay"
    print("c01 only; accepted input hashes and exact replay: PASS")
    print("Q_F lower at 14 s >=", floor_decimal(F(result["Q_lower_expression_enclosure"][0]), 14))
    for coord, row in result["costs"].items():
        print(coord, "F protection lower >=", floor_decimal(row["fixed_class_new_protection_lower_s"], 6),
              "s; unknown-price budget >", floor_decimal(row["unknown_budget_us_per_s"], 6), "us/s")


if __name__ == "__main__":
    main()

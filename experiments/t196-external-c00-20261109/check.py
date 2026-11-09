"""Directed substitutions for the single c00 message rule, issue 196 (09.11)."""
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

MAP = Path(__file__).resolve().parents[1] / "regime-map-methodology-20261019" / "predictability-volume-20261028"
NS = 10**9


def pinned(name, digest):
    contents = (MAP / name).read_text(encoding="utf-8")
    if sha256(contents.encode()).hexdigest() != digest:
        raise ValueError(f"Input changed: {name}")
    return json.loads(contents)


def upper(value, digits):
    scale = 10**digits
    units = -(-value * scale // 1)
    return f"{units // scale}.{units % scale:0{digits}d}" if digits else str(units)


def calculate():
    cfg = pinned("inputs.json", "5f62171e4706854f6419345d7eaed1f2103c06bc4989976fde03942db091c6cd")
    first = pinned("first-point-result.json", "0f727a6bd458c15baf7e46e48ba78d88e161afa8b77e5941a1ea78db12aa4952")
    T, W = F(first["mission_s"]), first["words"]
    assert F(first["alpha"]) == F(1, 10) and W == 1048576 and F(first["epsilon"]) == F(1, 1000)
    env = {k: F(v) for k, v in first["environment"].items()}
    b, a, R, Fr, g = (env[k] for k in ("b", "a", "R", "Fr", "g"))
    N = cfg["environment"]["template"]["count"]
    svc = cfg["service"]
    xp, xm, J = F(svc["xi_plus"]), F(svc["xi_minus"]), F(svc["J_ns"])
    stride = svc["calendar"]["g_ticks"] * W
    d = (124*xp + 3*J) / NS

    def pplus(k):
        return (k*stride*xp + J) / NS

    def pminus(k):
        return (k*stride*xm - J) / NS

    # The whole-period cap in reference units. The current positive-growth
    # contract is one-sided, so it bounds both forward age and high-sample counts.
    cap, error, stamp_error = F("0.015"), F("0.0001"), F("0.001")
    sync_pad, fresh_age = F("1.02"), F("1.25")
    span = pplus(36) + pplus(1) + d
    assert span + 4*sync_pad <= 12
    assert span + 2*sync_pad + fresh_age + 2*stamp_error < 11
    assert pminus(36) - fresh_age > 6
    expiry = (cap-error)/g - stamp_error  # z=0, measured from the reported stamp

    fast, shoulder, quiet = (pplus(k)+d for k in (3, 6, 36))
    pmax = b + a
    residual_coefficient = fast*(2*pmax + R)
    assert quiet*(2*pmax + cap) <= residual_coefficient
    z = F(3, 5)  # the two wings of each triangle have h<z
    wing_integral = N*600*(b*b*z + b*a*z*z + a*a*z**3/3)
    central_integral = env["IH"] - wing_integral
    exceptions = (F(cfg["information"]["lifetime_delta_exec"])
                  + F(cfg["information"]["lifetime_delta_calendar"]) + F("0.000001"))
    U = exceptions + env["K"]*(quiet*env["IL"] + shoulder*wing_integral
                               + fast*central_integral + residual_coefficient*Fr + env["XE"])
    assert U < F(first["epsilon"])

    min_block = pminus(36)
    normal_passes = (T/min_block + 2 + 5*N*((600+12)/min_block + 1)
                     + 6*N*((240+12)/min_block + 1))
    max_reads = W*(T/pminus(1) + 2)
    parents = 39*W*(b*T + F(cfg["environment"]["Fs"])) / cfg["environment"]["reference_positions"]
    read = F(first["per_operation_seconds"]["bus_read"]["upper"])
    repair = F(first["per_operation_seconds"]["repair"]["upper"])
    core = read*(W*normal_passes + exceptions*max_reads) + repair*(2*parents + U*max_reads)
    high_blocks = Fr / (6*(cap - 2*error - (11+6)*g))
    assert cap - 2*error - 17*g > 0
    unavailable_time, interruptions = T/2000, 2002
    affected_blocks = unavailable_time/min_block + (1+12/min_block)*interruptions
    extra_per_block = 11*W*read
    before_source = core + extra_per_block*(3 + high_blocks + affected_blocks)
    target = F("20941612")/5
    assert F(first["fixed_class"]["excluded_from"]["cost"]["bus"]["lower_s"]) >= 5*target
    example_source = F(10000)
    protected = before_source + example_source
    assert protected <= target
    # Same application and preparation on both sides, map-14/TABLE.md.
    common_upper = F("15305.35")
    common_lower = F("14989.40")
    assert 5*(protected + common_upper) <= 5*target + common_lower
    return {
        "growth_per_s2": upper(g, 14), "36_block_s_lower_exact": str(min_block),
        "expiry_z0_s_floor": int(expiry), "risk_upper": upper(U, 12),
        "remaining_risk_floor_1e-9": int((F(first["epsilon"])-U)*10**9),
        "high_blocks_upper": upper(high_blocks, 3),
        "interruption_blocks_upper": upper(affected_blocks, 3),
        "ordinary_cost_upper_s": upper(core, 3),
        "additional_bus_per_block_upper_s": upper(extra_per_block, 9),
        "cost_before_source_upper_s": upper(before_source, 3),
        "source_allowance_s_floor": int(target-before_source),
        "cost_including_10000_s_upper_s": upper(protected, 3),
    }


if __name__ == "__main__":
    print(json.dumps(calculate(), indent=2))

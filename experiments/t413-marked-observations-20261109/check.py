"""T413 D5. One conditional substitution on the frozen PR371 point."""
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]


def pinned(name, digest):
    s = (ROOT/name).read_text(encoding="utf-8")
    if sha256(s.encode("utf-8")).hexdigest() != digest:
        raise ValueError("Frozen input changed: " + name)
    return json.loads(s)


def one_minus_exp_lower(x):
    # A positive partial sum bounds exp(x) from below.
    term = total = F(1)
    for j in range(1, 20):
        term *= F(x, j)
        total += term
    return 1 - 1/total


def directed(x, digits, up=False):
    scale = 10**digits
    units = -(-x*scale // 1) if up else x*scale // 1
    return f"{units//scale}.{units%scale:0{digits}d}"


def check():
    old = pinned("theory/observation-carry-refinement-20261101/result.json",
                 "444c93c12f05160e7ffa50caf3e9f4995fb04ec55b1042d2f6a387315eef9ce5")
    cfg = pinned("experiments/regime-map-methodology-20261019/predictability-volume-20261028/inputs.json",
                 "5f62171e4706854f6419345d7eaed1f2103c06bc4989976fde03942db091c6cd")
    f, a, g = old["frozen"], old["application"], old["geometry"]
    W, T, N = f["words"], F(f["mission_s"]), F(g["attempts_upper"])
    assert (W, f["K"], f["m"], f["c"], a["k_base"], a["k_rare"]) == (1048576, 3001, 6, 32, 6, 11)
    assert (F(f["alpha"]), F(f["epsilon"]), f["eta"]) == (F(1, 2), F(".01"), 2)
    env = cfg["environment"]
    refscale = F(39*W, env["reference_positions"])
    b = refscale*F(env["b"])
    amplitude = refscale*F(env["Fs"])/(env["template"]["count"]*env["template"]["width_s"])
    pmax = b + amplitude
    peak, Fr = refscale*F(env["B"]), refscale*F(env["Fs"])/2
    R = peak - pmax
    mass = b*T + 2*Fr
    assert mass == F(old["refinement"]["parent_mass_upper"])

    # Sensitivity assumptions, as fractions of *bit inversions*; D1 is a count.
    s_max, d = F("0.0001"), F("0.0001")
    v_max = 2*d/mass
    single, pair = one_minus_exp_lower(2), one_minus_exp_lower(4)
    assert single > pair/2
    score = (1-s_max-v_max)*single + s_max*pair/2
    mu_low = F(a["exposure_lower"])
    assert score >= F(".8646") and score*mu_low-2*f["c"] > F(a["log_threshold_upper"])
    zero_exposure = (1-v_max-s_max/2)*mu_low
    assert zero_exposure > 98
    new_upper = F(a["Q_upper"]) + d
    assert new_upper < F(f["epsilon"])
    increment = (f["m"]+1)*s_max*mass/2 + N*d
    D0 = F(a["D0_upper"]) + increment
    phi = F(a["rare_fraction_lower_before_extra_z"]) - increment/N
    assert phi > 0 and f["m"] + D0 < N
    budgets, increments = {}, {}
    ns, nb = a["rare_passes"], a["baseline_passes"]
    Mb = F(a["main_reads_maximum"])
    clockplus = F(cfg["service"]["xi_plus"])
    for x, read, repair in (("bus", 48*clockplus+F(".5"), 56*clockplus+F(".5")),
                            ("serial", 68*clockplus+F(".5"), 56*clockplus)):
        delta_microseconds = (W*(nb-ns)*read*increment + Mb*repair*d)/(1000*T)
        old_budgets = a["costs"][x]["strict_full_cost_budget"]
        budgets[x] = {rival: directed(F(value)*10**6-delta_microseconds, 6)
                      for rival, value in old_budgets.items()}
        increments[x] = directed(delta_microseconds, 6, True)
    rival_Q = F(old["old_rival_bounds_used_verbatim"]["constant_member"]["Q_upper"]) + d
    assert rival_Q < F(f["epsilon"])

    fence = F(a["first_eligible_fence_upper_s"])
    assert R*fence < Fr and R > F(a["u"]) and peak*fence/W < 1
    zero_lower = 1 - peak*fence/W
    Ip = F(old["refinement"]["known_p_squared"])
    blind = (F(f["delta0"]) + F(f["deltaC_design"]) + F(a["aperture_pair_upper"])
             + F(a["a_rare_upper_s"])*(Ip+(2*pmax+R)*Fr)/(2*W))
    base_only = (F(f["delta0"]) + F(f["deltaC_design"]) + F(a["aperture_pair_upper"])
                 + F(a["a_base_upper_s"])*(Ip+(2*pmax+R)*Fr)/(2*W))
    assert blind > F(f["epsilon"]) and zero_lower > F(f["alpha_total"])
    assert base_only + d < F(f["epsilon"])
    return {"conditional_score_lower": directed(score, 10),
            "conditional_log_score_lower": directed(score*mu_low-64, 9),
            "false_valid_zero_exponent_lower": directed(zero_exposure, 9),
            "conditional_Q_upper": directed(new_upper, 12, True),
            "risk_margin_lower": directed(F(f["epsilon"])-new_upper, 12),
            "conditional_D0_upper": directed(D0, 6, True),
            "rare_fraction_before_z_lower": directed(phi, 9),
            "fixed_member_Q_upper": directed(rival_Q, 12, True),
            "extra_known_cost_us_per_s_upper": increments,
            "budgets_us_per_s_lower": budgets,
            "all_words_D1_zero_first_false_permit_lower": directed(zero_lower, 9),
            "unrestricted_D1_zero_blind_Q_upper": directed(blind, 12, True),
            "base_only_Q_upper_with_d": directed(base_only+d, 12, True)}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))

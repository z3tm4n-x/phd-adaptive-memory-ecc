#!/usr/bin/env python3
"""One registered candidate; rational checks, no Monte Carlo or period grid."""
from decimal import Decimal, localcontext, ROUND_CEILING, ROUND_FLOOR
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = ROOT / "experiments/hybrid-p-r-20261026/inputs.json"
EXPECTED = "cc72a44914b0aa5547fe1e2b5a2a654c84573ab1c5fe6e35a4f4122831ec86c6"
COMMON = ROOT / "experiments/t186-method-comparison/code-strength/common-input.json"
raw = INPUT.read_bytes()
assert sha256(raw).hexdigest() == EXPECTED
data = json.loads(raw)
assert sha256(COMMON.read_bytes()).hexdigest() == data["source_sha256"][COMMON.relative_to(ROOT).as_posix()]
common = json.loads(COMMON.read_bytes())
env, fixed = data["proposed_environment"], data["fixed"]
W, T, eps = fixed["words"], F(fixed["mission_s"]), F(fixed["epsilon"])
assert (W, T, eps, fixed["code"]) == (131072, 315576000, F("0.001"), [39, 32, 1])
assert fixed["initial_K0"] == 0 and fixed["useful_writes"] == 0
assert not fixed["ordinary_reads_repair"] and not fixed["ordinary_reads_publish_ERR"]
assert env["residual"]["distribution_over_paths"] is None
assert env["spatial"]["m"] == 1 and env["spatial"]["d"] == 0
assert F(env["spatial"]["q"]) == F(env["spatial"]["chi"]) == F(1, W)
b = F(env["background"])
Ap = F(env["p"]["amplitude_above_background"])
R = F(env["residual"]["cap_R"])
g = F(env["residual"]["growth_g"])
Fr = F(env["residual"]["mass_F_r"])
Fs, B = F(env["total_solar_mass"]), F(env["total_peak"])
pmax = b + Ap
assert B == pmax + R and Fs == 2 * Fr
cycle, width, left = (F(env["p"][k]) for k in ("cycle_s", "width_s", "left_s"))
ncycles = T / cycle
assert ncycles.denominator == 1 and left + width < cycle
assert ncycles * width * Ap / 2 == Fs / 2

# The policy was committed before arithmetic at f352faff (one candidate).
M, kbase, krare, K, eta, threshold = 120000, 2, 12000, 1, 1, 3
slo, shi = F(".025700"), F(".025702")
alo, ahi, P = F(".051400"), F(".051404"), F(".025702")
h, ae = F(".078"), F("308.42")
alpha, zeta, beta = F(".0001"), F(".0001"), F(".00055")
delta0 = F(fixed["lifetime_other_budget"])
deltaC_example_requirement = F(".00005")  # a requirement, NOT measured/assumed evidence
u = R / 2
cal, svc = common["calendar"], common["service"]
block_ticks = W * cal["g_ticks"] + 7 * cal["frame_ticks"]
assert block_ticks == 25701088
block = F(block_ticks, 10**9)
xi_lo, xi_hi = F(svc["clock_lower"]), F(svc["clock_upper"])
J = F(svc["operation_endpoint_span_ns"]) / 10**9
assert slo <= block * xi_lo - J
assert block * xi_hi + J <= shi == P
assert alo <= kbase * block * xi_lo - J
assert kbase * block * xi_hi + J <= ahi
assert krare * block * xi_hi + J <= ae
assert h >= ahi + P
# This only checks the duration envelope, not receiver completeness or WCET.

tau_lo, tau_hi = slo + M * alo, shi + M * ahi
Delta, w = tau_hi - tau_lo, alo - P
assert w > 0 and tau_hi + ae < T

def ceilf(x):
    return -((-x.numerator) // x.denominator)

q = ceilf(Delta / alo) + 1
used = M - q
assert q == 11 and used == 119989
prefix_last_end_upper = shi + (used - 1) * ahi + w
assert prefix_last_end_upper <= tau_lo
# Strictly positive terms have k < (u/g - Delta)/alo.
kfirst = q + 1
klast = min(M, ceilf((u / g - Delta) / alo) - 1)
positive = max(0, klast - kfirst + 1)
sum_r = positive * (u - g * Delta) - g * alo * F(positive * (kfirst + klast), 2)
mu = w * (used * b + sum_r)
# One independent direct sum over this SAME group (not a parameter grid).
direct_mu = w * (used * b + sum(max(F(0), u - g * (Delta + k * alo)) for k in range(q + 1, M + 1)))
assert mu == direct_mu

# Directed transcendental comparisons via exact finite series.
# e > sum_{j=0}^4 1/j! = 65/24 > 100/37 => 1-e^-1 > .63.
assert F(65, 24) > F(100, 37)
x, term, exp_partial = F("9.22"), F(1), F(1)
for j in range(1, 81):
    term *= x / j
    exp_partial += term
assert exp_partial > 10000  # hence log(10000) < 9.22
score_lower = F(".63") * mu - threshold
assert score_lower > x
assert eta == 1 and alpha == F(1, 10000)
# The conservative policy explicitly requires C<=3; we do NOT assert C=4
# would fail the exact exponential test.
def permit(valid, available_by_deadline, total):
    return valid and available_by_deadline and 0 <= total <= threshold
assert permit(True, True, 0) and permit(True, True, 3)
assert not permit(True, True, 4)
assert not permit(False, True, 0) and not permit(True, False, 0)

int_p2 = b*b*T + b*Fs + Ap*Fs/3
S2 = int_p2 + (2*pmax + R) * Fr
Qbase = h * S2 / W
residual_tail_upper = (B * P)**2 / 2
assert K == 1 and residual_tail_upper < zeta
Me_upper = (pmax + u) * ae + g * ae**2 / 2
be_upper = (K * Me_upper + Me_upper**2 / 2) / W
MR_upper = B * ae
bR_upper = (K * MR_upper + MR_upper**2 / 2) / W
assert be_upper <= beta < bR_upper
Q_without_deltaC = delta0 + alpha + zeta + Qbase + beta
deltaC_allow = eps - Q_without_deltaC
Q_example = Q_without_deltaC + deltaC_example_requirement
margin_example = eps - Q_example
assert deltaC_allow > deltaC_example_requirement > 0
assert Q_example < eps

# Nonzero quiet environment only proves mathematical reachability.
# It does not establish full C on the existing wire.
quiet_r = b / 10
assert quiet_r <= R and quiet_r*T < Fr
assert left + width < tau_hi < left + cycle
quiet_mass_upper = (b + quiet_r)*tau_hi + Ap*width/2
quiet_no_parent_prob_lower = 1 - quiet_mass_upper
assert quiet_no_parent_prob_lower > F(".66")
assert F(data["retained_quotas"]["ordinary_outage_fraction"])*T > tau_hi
# Thus the permitted loss budget can invalidate the whole single learning group.
assert krare % kbase == 0
saved_main_passes_on_success = krare // kbase - 1
assert saved_main_passes_on_success == 5999
nominal_base_count = (T-block) // (kbase*block)
nominal_final_tail = T-block-nominal_base_count*kbase*block
assert 0 <= nominal_final_tail < kbase*block

def value(x):
    x = F(x)
    with localcontext() as ctx:
        ctx.prec = 50
        return {"exact": str(x), "decimal": str(Decimal(x.numerator) / Decimal(x.denominator))}

def rounded(x, places=12, up=True):
    with localcontext() as ctx:
        ctx.prec = 80
        y = Decimal(x.numerator) / Decimal(x.denominator)
        return str(y.quantize(Decimal(1).scaleb(-places), rounding=ROUND_CEILING if up else ROUND_FLOOR))

result = {
    "status": "CONDITIONAL_THEORY_CANDIDATE_NOT_SERVICE_SIGNOFF",
    "base_main": "f82de4749dd248dee793dbb9a2b3981fb3ad7378",
    "candidate_commit_before_arithmetic": "f352faff399b29a0f06b94cd16b0a5b8f248e063",
    "input_path": INPUT.relative_to(ROOT).as_posix(),
    "input_sha256": EXPECTED,
    "common_input_sha256": sha256(COMMON.read_bytes()).hexdigest(),
    "checker_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    "candidate": {
        "startup_blocks": 1, "base_blocks": kbase, "training_actions": M,
        "used_actions": used, "uncounted_tail_actions": q,
        "rare_blocks": krare, "eta": eta, "sum_C_at_most": threshold,
        "u": "R/2", "K": K, "alpha": str(alpha), "zeta": str(zeta),
        "rare_risk_allowance": str(beta), "new_queries_after_invalid": 0,
        "rare_actions_at_most": 1,
    },
    "exact_checks": {k: value(v) for k,v in {
        "tau_lower_s": tau_lo, "tau_upper_s": tau_hi, "clock_interval_s": Delta,
        "idle_prefix_s": w, "last_prefix_end_upper_s": prefix_last_end_upper,
        "positive_residual_terms": positive, "exposure_lower": mu,
        "log_test_lower_C3": score_lower, "log_threshold_upper": x,
        "integral_p_squared": int_p2, "S2_upper": S2, "Qbase_upper": Qbase,
        "residual_tail_upper": residual_tail_upper,
        "excursion_mass_upper": Me_upper, "excursion_risk_upper": be_upper,
        "no_information_mass_upper": MR_upper,
        "no_information_same_certificate_upper": bR_upper,
        "Q_upper_excluding_deltaC": Q_without_deltaC,
        "deltaC_allowable_upper": deltaC_allow,
        "deltaC_example_requirement": deltaC_example_requirement,
        "Q_upper_if_example_requirement_met": Q_example,
        "margin_if_example_requirement_met": margin_example,
        "relative_margin_if_requirement_met": margin_example / eps,
        "quiet_r_mass": quiet_r*T,
        "quiet_history_mass_upper": quiet_mass_upper,
        "quiet_no_parent_probability_lower": quiet_no_parent_prob_lower,
        "nominal_last_partial_interval_s": nominal_final_tail,
    }.items()},
    "directed_summary": {
        "Qbase_upper": rounded(Qbase),
        "exposure_lower": rounded(mu, 9, False),
        "log_test_lower_C3": rounded(score_lower, 9, False),
        "residual_tail_upper": rounded(residual_tail_upper),
        "excursion_risk_upper": rounded(be_upper),
        "no_information_certificate_lower_value_NOT_Q_lower": rounded(bR_upper, 12, False),
        "Q_upper_excluding_deltaC": rounded(Q_without_deltaC),
        "sufficient_deltaC_bound": rounded(deltaC_allow, 12, False),
        "Q_upper_if_deltaC_at_most_5e-5": rounded(Q_example),
        "margin_lower_if_deltaC_at_most_5e-5": rounded(margin_example, 12, False),
    },
    "price": {
        "saved_scheduled_main_passes_on_success": saved_main_passes_on_success,
        "full_cost_gain_claimed": False,
        "processing_WCET_cost_energy_and_extra_veto": None,
        "strong_schedule_comparison_claimed": False,
    },
    "remaining_conditions": [
        "Existing full source prefix, pass attribution/deduplication, invalid and current health",
        "Predictable physical timing, preserved main passes and pending completion",
        "Receiver/decision WCET and evidence for delta_C within allowed budget",
        "Actual positive-probability valid history on existing wire; no new heartbeat presumed",
        "Learning-time/success law and costs on all histories for any mean-gain claim",
    ],
    "verification": "Exact rational gates and one direct exposure sum passed; no MC or old period grid",
}
rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
if len(sys.argv) == 2 and sys.argv[1] == "--write":
    (HERE / "result.json").write_text(rendered, encoding="utf-8", newline="\n")
    print("PASS: result.json; one candidate, exact arithmetic, conditional service applicability.")
elif len(sys.argv) == 1:
    print(rendered, end="")
else:
    raise SystemExit("usage: python3 check.py [--write]")

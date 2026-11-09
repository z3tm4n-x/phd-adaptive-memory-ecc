"""Replay the floor review, the first late-onset test and the registered rule certificate."""
from fractions import Fraction as F
from math import ceil, factorial, floor
from pathlib import Path
import argparse
import json
import subprocess


ROOT = Path(__file__).resolve().parents[2]
BASE = "099b3710f4f67b5d7776a29675b6ac984805fc56"
REGISTERED = "8472a0a2f3fc0c5521f49c62fd40dd4e736e8bf9"
W = 65536
EPS = F("0.001")
PAIR = F(38, 78)
XI_LO, XI_HI = F("0.99999"), F("1.00001")
JITTER = F("0.0000000005")
APERTURE = F(124, 10**9) * XI_HI + 3 * JITTER
L = F(196 * W, 10**9)
P = 32 * L
HISTORY = ceil(300 / P)
READ_LO = F(48, 10**9) * XI_LO - JITTER
READ_HI = F(48, 10**9) * XI_HI + JITTER
WRITE_HI = F(56, 10**9) * XI_HI + JITTER


def inputs(name):
    spec = f"{BASE}:experiments/c1-common-geo-20261109/{name}.json"
    return json.loads(subprocess.check_output(["git", "show", spec], cwd=ROOT))


def directed(value, digits, up=False):
    scale = 10**digits
    k = (ceil if up else floor)(value * scale)
    return f"{k//scale}.{k%scale:0{digits}d}"


def review(six, coverage, fixed_row):
    mission = F(six["T"])
    c = F(39, six["D"])
    b, B = F(coverage["b_s_inv"]), F(coverage["B_s_inv"])
    tau = F(six["plateau_s"])
    fixed_lower = F(fixed_row["necessary"]["bus_lower_percent"])

    def cost(reads):
        seconds = reads * READ_LO
        percent = 100 * seconds / mission
        return {"reads_lower":floor(reads), "bus_s_lower":directed(seconds, 6),
                "bus_percent_lower":directed(percent, 12),
                "fraction_of_fixed_lower":directed(percent / fixed_lower, 12)}

    plateau = {}
    for sharp in (False, True):
        num = denominator_correction = block_words = F(0)
        for duration, block, rate in ((tau, F(1), c*B), (mission-tau, F(3600), c*b)):
            mass = W * rate * block
            assert 0 < mass < 1
            empty = (1 - mass/64)**64 if sharp else 1 - mass
            weight = floor(duration/(block + 2*APERTURE)) * (1-EPS) * empty
            num += W * weight * rate * (block + APERTURE)
            denominator_correction += 2*PAIR*W*APERTURE*weight*rate**2*(block + APERTURE)
            block_words += W * weight
        reads = PAIR*num**2/(EPS + denominator_correction) - block_words
        plateau["sharper_empty" if sharp else "PR428"] = cost(reads)

    groups, theta = 900, F(1,2)
    height, hold, g = F(1,32), F(500), F(six["growth_s_inv2"])
    ramp = height/g
    slot = ramp + hold
    slots = floor((mission/groups)/(slot+2*APERTURE))
    added = height * (hold + ramp/2)
    assert slots == 691 and groups*height <= F("28.855") and groups*added <= F(six["F"])
    empty_hot = (1 - W*c*(b*slot + added)/64)**64
    empty_quiet = 1 - W*c*b*slot
    factor = theta/slots * empty_hot * PAIR * (c*(b + height))**2
    k = 47543
    assert factor*groups*slots*(1-EPS)*(W*hold - k*APERTURE)**2/(W+k) > EPS
    original = (1-theta)*empty_quiet*groups*slots*(1-EPS)*k
    shares = [1-theta*F(j,slots) for j in range(1,slots+1)]
    roots = [2*(1-share)*F("0.7071") + 2*share-1 for share in shares]
    assert all(u*u <= share for u, share in zip(roots, shares))
    denom = EPS + 2*factor*W*APERTURE*(hold+APERTURE)*groups*slots
    improved = empty_quiet * (
        factor*W**2*(hold+APERTURE)**2*(groups*(1-EPS)*sum(roots))**2/denom
        - W*groups*sum(shares))
    assert improved > original > 0
    return {"high_start":plateau, "unknown_start_PR428":cost(original),
            "unknown_start_quiet_prefix":cost(improved)}


def ramp_probe(six, coverage):
    b, B = F(coverage["b_s_inv"]), F(coverage["B_s_inv"])
    c, g = F(39, six["D"]), F(six["growth_s_inv2"])
    a = (B-b)/2
    rise = a/g
    assert rise < 300 and a < F("28.855") and a*(rise/2+P+L) <= F(six["F"])
    rows = {}

    def empty_bounds(mean):
        # After the first omitted term all further ratios are at most mean/26.
        assert 0 <= mean < 26
        partial = sum(mean**k / factorial(k) for k in range(25))
        tail = mean**25 / factorial(25) / (1 - mean/26)
        return 1/(partial+tail), 1/partial

    for key, time in (("five_minutes", F(300)), ("first_gate_earliest_envelope", HISTORY*P),
                      ("first_gate_latest_nominal", HISTORY*P + L)):
        mean = W*c*(b*time + a*a/(2*g))
        lo, hi = empty_bounds(mean)
        rows[key] = {"time_s":float(time), "bank_mean":float(mean),
                     "empty_probability_lower":directed(lo,14),
                     "empty_probability_upper":directed(hi,14,True)}
    # A conservative upper for one slow edge in the ramp/hold probe, singleton law.
    hist_lo = XI_LO*(HISTORY*P-L)-2*JITTER
    visible = c*(W-1)*(b*hist_lo + max(F(0),a-g*(L+JITTER))**2/(2*g))
    slow_area = W*c*c/2*(XI_HI*P+APERTURE)**2*(b+a)**2
    pair_upper = slow_area*empty_bounds(visible)[1]
    assert pair_upper < F("1.52e-10")
    rows["probe_single_edge_pair_upper"] = directed(pair_upper,18,True)
    return rows


def certificate(six, coverage):
    T, c = F(six["T"]), F(39, six["D"])
    S1, S2, U = F(six["S1_max"]), F(six["S2_max"]), F("28.855")
    B, delta = F(coverage["B_s_inv"]), F(six["delta_exec"])
    hf, hs = XI_HI*L+APERTURE, XI_HI*P+APERTURE
    hist = XI_LO*(HISTORY*P-L)-2*JITTER
    age = XI_HI*((HISTORY+1)*P+L)+APERTURE+2*JITTER
    nf = ceil((T+2*JITTER+APERTURE)/(XI_LO*L))+3
    ns = ceil((T+2*JITTER+APERTURE)/(XI_LO*P))+3
    na = ceil((age+2*APERTURE+2*JITTER)/(XI_LO*P))+3
    G = age + na*APERTURE
    coefficient = W*c*c/2
    fast = coefficient*hf*(S2+B**2*nf*APERTURE)
    variation = coefficient*hs*B*U*G
    exp_lower = F("2.71828")
    assert sum(F(1,factorial(k)) for k in range(10)) > exp_lower
    visibility = coefficient*hs*(S1+B*ns*APERTURE)/(exp_lower*c*(W-1)*hist)
    subtotal = delta+fast+variation
    intercepts = {}
    for direct in (F(0), F("0.00001"), F("0.0001")):
        intercepts[str(direct)] = directed(visibility/(EPS-subtotal-direct), 9, True)
    cases = {}
    for gamma in (F(1), F(1,2), F(1,3), F(1,4)):
        q = subtotal + visibility/gamma
        cases[str(gamma)] = directed(q, 9, True)
    assert HISTORY == 730 and hist > 300 and APERTURE < XI_LO*F(164,10**9)
    assert subtotal + 2*visibility < EPS < subtotal + 4*visibility
    return {"fast":directed(fast,12,True), "variation":directed(variation,12,True),
            "visibility_over_gamma":directed(visibility,12,True),
            "cases_d0":cases,"min_gamma_rounded_up":intercepts,
            "history_lower_s":float(hist),"age_overlap_upper_s":float(G)}


def conditional_cost(six, row, q):
    T, c = F(six["T"]), F(39,six["D"])
    hard = F(row["necessary"]["maximum_reads_upper"])
    mass = W*c*F(six["S1_max"])
    h_f, h_s = XI_LO*L-2*JITTER, XI_LO*P-2*JITTER
    hold = (HISTORY+1)*(XI_HI*P+2*JITTER)
    fast_pre = min(T, XI_HI*L+JITTER+hold*(1+2*mass))
    reads = W*(2+T/h_s+(1/h_f-1/h_s)*fast_pre) + q*hard
    repairs = 2*mass + q*hard
    base = READ_HI*reads + WRITE_HI*repairs
    extra_per_invalid = READ_HI*W*(1/h_f-1/h_s)*hold
    allowance = F(row["necessary"]["bus_lower_s"])/2
    # The switch cap after the stop requires the cell clock to remain bounded.
    switch_cap = ceil((T+2*JITTER)/(XI_LO*P)) + 2
    peak = row["peak"]
    return {"case":"gamma=1/2, d=0, delta=6e-6, hard caps as in PR423; intercept at I=0",
            "expected_word_hits_upper":directed(mass,6,True),
            "before_stop_fast_s_upper":directed(fast_pre,3,True),
            "bus_read_repair_s_upper":directed(base,3,True),
            "bus_percent_upper":directed(100*base/T,6,True),
            "margin_to_twice_s_lower":directed(allowance-base,3),
            "extra_bus_s_per_invalid_upper":directed(extra_per_invalid,5,True),
            "total_fast_s_upper":directed(fast_pre+q*T,3,True),
            "expected_switches_upper":ceil(1+4*mass+q*switch_cap),
            "bus_peak_one_ms_if_reserved_slots_hold":directed(F(peak["all_slot_bus_upper_percent"]),7,True),
            "serial_peak_one_ms_if_reserved_slots_hold":directed(F(peak["all_slot_serial_upper_percent"]),7,True),
            "full_invalid_nominal_read_percent_before_boundary_terms":directed(100*W*F(48,10**9)/L,9)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-only", action="store_true")
    args = parser.parse_args()
    six, coverage = inputs("six"), inputs("coverage")
    fixed = next(row for row in six["rows"] if row["W"] == W and F(row["epsilon"]) == EPS)
    out = {"frozen_rule":REGISTERED,"review":review(six,coverage,fixed)}
    if not args.review_only:
        out["first_probe"] = ramp_probe(six, coverage)
        out["certificate"] = certificate(six, coverage)
        q = F(out["certificate"]["cases_d0"]["1/2"])
        out["price"] = conditional_cost(six,fixed,q)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()

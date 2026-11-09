"""Compare the frozen repeat-rise class and (A) at the authorized 0.25 MiB point."""
import argparse
import hashlib
import json
import math
import subprocess
from fractions import Fraction as F
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
FREEZE = "5e3b40b46c7cbb2baebd6e2f3bfde32d92abfca0"
C1 = "c0176b4837b5310378fb4218f2d549aeb4c991e9"
C1_DIR = "experiments/c1-common-geo-20261109"
C1_ARCHIVE = "c944c91a2c20a207516824333e02711aaf34898f"
C1_OLD_DIR = "experiments/c1-geo-fixed-20261109"
STRICT_INPUT = "d6c1203a52f84d9d0bf5f0bc5ac689c92751db33"


def data(commit, path):
    raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
    return json.loads(raw)


def rounded(q, digits, upper=False):
    integer = (math.ceil if upper else math.floor)(q * 10**digits)
    return f"{integer//10**digits}.{integer%10**digits:0{digits}d}"


def covered_starts(bad, offset, width, count):
    # A bad left index i describes the included bin(s) i,...,i+offset.
    left = np.maximum(0, bad - width + 1 + offset)
    right = np.minimum(count - 1, bad)
    keep = left <= right
    delta = np.zeros(count+1, dtype=np.int32)
    np.add.at(delta, left[keep], 1)
    np.add.at(delta, right[keep]+1, -1)
    return int(np.count_nonzero(np.cumsum(delta[:-1]) > 0))


def infeasible_bin_windows(means, step_mass, cap, width):
    # The archived means all lie in the linear branch of the required
    # starting ceiling. Verify strict violations with exact binary inputs.
    assert F.from_float(float(means.max())) + step_mass/2 < cap
    count = len(means)-width+1
    window_diff = np.zeros(count+1, dtype=np.int32)
    f = float(step_mass)
    # All true candidates have m_i > step_mass/2. The small outward tolerance
    # only enlarges the floating shortlist; exact comparisons decide inclusion.
    candidates = np.flatnonzero(means >= f/2 - 1e-14)
    for lag in range(1, 2+math.ceil(float(means.max())/f)):
        base = (lag-F(1,2))*step_mass
        high = candidates[(candidates >= lag) & (means[candidates] >= float(base)-1e-14)]
        bad = []
        for i in high:
            need = F.from_float(float(means[i]))-base
            if need <= 0:
                continue
            prior = F.from_float(float(means[i-lag]))
            too_low = (2*step_mass*prior < need**2 if prior <= step_mass/2
                       else prior + step_mass/2 < need)
            if too_low:
                bad.append(i-lag)
        if bad:
            indices = np.asarray(bad)
            left = np.maximum(0, indices+lag-width+1)
            right = np.minimum(count-1, indices)
            ok = left <= right
            np.add.at(window_diff, left[ok], 1)
            np.add.at(window_diff, right[ok]+1, -1)
    return int(np.count_nonzero(np.cumsum(window_diff[:-1]) > 0))


def strict_coverage(cache, mission, cap, quota):
    cadence = data(C1, C1_DIR + "/cadence.json")
    counts = {"1min":0, "5min":0}
    observed = 0.0
    for source in cadence["native"].values():
        for dt, product in source.items():
            if dt not in counts:
                continue
            pair = product.get("strict_nu_slope_s_inv2")
            if pair is not None:
                counts[dt] += pair["pairs"]
                if dt == "5min":
                    observed = max(observed, pair["slope"])
    strict_g = F(math.ceil(2*F.from_float(observed)*10**9), 10**9)
    archive = data(C1_ARCHIVE, C1_OLD_DIR + "/sepem.json")
    bands = cache/"bands.npy"
    with bands.open("rb") as handle:
        assert hashlib.file_digest(handle, "sha256").hexdigest() == archive["source_cache"]["arrays_sha256"][bands.name]
    h = np.load(bands, mmap_mode="r")[:, 1, :].sum(axis=1)
    nu = archive["background_per_s"] + (1+archive["HI_to_H"])*np.maximum(0, h-archive["H_p10"])
    step = 300
    width = mission//step
    windows = len(nu)-width+1
    increments = np.diff(nu)
    violating_pairs = np.flatnonzero(increments > step*float(strict_g))
    excluded = covered_starts(violating_pairs, 1, width, windows)
    exact_bad = infeasible_bin_windows(nu-archive["background_per_s"], strict_g*step, cap, width)
    # The same bin-integral witness as in PR423 has slope 2(Delta m)_+/step.
    steep_bins = 1 + np.flatnonzero(2*increments > step*float(strict_g))
    existing_fit = windows-covered_starts(steep_bins, 0, width, windows)
    witnesses = data(STRICT_INPUT, "experiments/c1-repeat-quota-20261109/strict.json")["strict_joint_witnesses"]
    joint = sum(block["windows"] for block in witnesses)
    assert joint == windows-exact_bad and all(F(block["exact"]) < quota for block in witnesses)
    return {"strict_pairs":counts, "max_five_per_s2":observed, "strict_g_per_s2":str(strict_g),
            "violating_SEPEM_pairs":len(violating_pairs), "excluded_full_starts_necessary":excluded,
            "passing_adjacent_condition":windows-excluded,
            "feasible_bin_integrals_free_start":windows-exact_bad,
            "certified_with_same_bin_fit":existing_fit,
            "certified_with_strict_joint_witnesses":joint,
            "segment_J":[block["exact"] for block in witnesses]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sepem-cache", required=True, type=Path)
    args = parser.parse_args()
    quota = F(data(FREEZE, "experiments/c2-repeat-rise-20261109/quota.json")["quota_per_s"])
    env = data(C1, C1_DIR + "/coverage.json")
    inp = data(C1, C1_DIR + "/six.json")
    b, B = F(env["b_s_inv"]), F(env["B_s_inv"])
    T, D = F(inp["T"]), F(inp["D"])
    R, budget = B-b, F(inp["F"])
    tau = budget/R
    words = 65536
    L = F(196 * words, 10**9)
    rate = 39*B/D
    eps, delta = F(1, 1000), F(inp["delta_exec"])
    xmin, xmax, jitter = F(99999,100000), F(100001,100000), F(1,2*10**9)
    aperture = F(124,10**9)*xmax + 3*jitter
    s2 = b*b*T + (2*b+R)*budget
    assert tau == F(inp["plateau_s"]) and R < quota and s2 == F(inp["S2_max"])

    # A strict difference of classes at the nominal g: a train of minimum-area ramps.
    g, amplitude = F(inp["growth_s_inv2"]), R/2
    teeth = math.floor(quota/amplitude) + 1
    pulse_time = teeth*amplitude/g
    pulse_mass = teeth*amplitude**2/(2*g)
    assert pulse_time < T and pulse_mass < budget and teeth*amplitude > quota

    def physical(block, squares):
        empty = 1-words*rate*block
        assert empty > 0
        z = math.floor(tau/block)*empty*F(38,78)*rate**2*squares
        return z/(1+z)

    q_lower = {}
    for h in range(2,7):
        squares = 13*words*(4*h*L-aperture)**2
        q_lower[str(h)] = physical(64*h*L, squares)
    k = math.ceil((128*L+aperture)/(7*L))
    assert k == 19
    q_lower["h>=7"] = physical(128*L, words*(128*L-k*aperture)**2/(k+1))
    assert min(q_lower.values()) > eps

    # PR420 (3), positive terms of the majorant on the initial plateau.
    complete = math.floor((tau-3*L)/(4*L))-1
    min_scan = L-F(420,10**9)
    v_carry_h1 = complete*words*rate**2*((4*L)**2/2 + 4*L*min_scan)
    v_slow_h2 = F(words,2)*rate**2*tau**2/(4+tau/(8*L))
    false_h_le4 = 1-3*4*words*rate*L
    v_fast_h5 = F(words,2)*rate**2*tau**2/(2+tau/(5*L))
    assert min(v_carry_h1, v_slow_h2, false_h_le4, v_fast_h5) > eps

    row = next(row for row in inp["rows"] if row["W"] == words and F(row["epsilon"]) == eps)
    fixed = row["candidate"]
    hmax = 4*L*xmax+2*jitter
    bus_lo = 100*(1-eps-delta)*words*(T/hmax-2)*(F(48,10**9)*xmin-jitter)/T
    bus_hi = F(fixed["price"]["bus"]["upper_percent"])
    result = {
        "class_commit":FREEZE, "C1_inputs":C1,
        "J_plateau":rounded(R, 12, True), "quota":str(quota), "tau_s":rounded(tau, 9),
        "S2_max_s_inv":rounded(s2,9,True),
        "fragmentation":{"height_per_s":rounded(amplitude,9), "pulses":teeth,
                         "total_rise_per_s":rounded(teeth*amplitude,6),
                         "duration_s":rounded(pulse_time,3,True),
                         "excess_inversions":rounded(pulse_mass,3,True)},
        "stat_false_admission_h1_to_h4_lower":rounded(false_h_le4,9),
        "stat_V_lower_h_ge5":rounded(v_fast_h5,9),
        "unfiltered_V_lower_h1":rounded(v_carry_h1,9),
        "unfiltered_V_lower_h_ge2":rounded(v_slow_h2,9),
        "physical_Q_lower":{key:rounded(q,9) for key,q in q_lower.items()},
        "fixed_Q_upper":rounded(F(fixed["risk"]["total"]),12,True),
        "fixed_class_bus_lower_pct":rounded(F(row["necessary"]["bus_lower_percent"]),7),
        "fixed_candidate_bus_upper_pct":rounded(bus_hi,7,True),
        "h1_if_admissible_bus_lower_pct":rounded(bus_lo,7),
        "max_relative_saving_pct":rounded(100*(1-bus_lo/bus_hi),5,True),
        "max_saved_bus_percentage_points":rounded(bus_hi-bus_lo,7,True),
        "strict_quality":strict_coverage(args.sepem_cache,int(T),R,quota)
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

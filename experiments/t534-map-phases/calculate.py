"""Registered 256 KiB map test. Exact rationals and outward rounding, one GEO row."""
import argparse
import json
from fractions import Fraction as F
from math import ceil, floor
from pathlib import Path
from runpy import run_path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
ref = run_path(str(EXP / "t186-native-cost-map/calculate.py"))
maps = run_path(str(EXP / "native-service-robustness-20261113/check_theory.py"))
large = json.loads((EXP / "t504-large-bank/result.json").read_bytes())
accepted = json.loads((EXP / "t525-two-phases/result.json").read_bytes())
up, down = ref["up"], ref["down"]
W, A, eps = 2**16, 2**17, F(1, 1000)
ladder = maps["AnyPairs"](W, A)
L, xp, xm, edge, J = ladder.scan.L, ref["XP"], ref["XM"], ref["DE"], ref["J"]
T, c, delta, geo = ref["T"], ref["C"], ref["DELTA"], ref["GEO"]
ns = F(1, 10**9)


def phase_lines():
    """Each strip gives q(D) <= intercept - slope*D after taking the maximum."""
    b = ref["B0"]
    pair = W*c**2/2
    s = W*c*ladder.eta
    p = [L, *ladder.levels[1:]]
    ampl = [xp*L/2, *ladder.amplitude]
    durations = [ladder.history[0], *ladder.history]
    def weighted(x):
        return sum(a*ref["weight"](s*h*x) for a, h in zip(ampl, durations))

    omega = ref["aperture"](geo, L)
    other_masks = sum(a*ref["aperture"](geo, period) for a, period in zip(ampl, p))
    mass = geo.peak*xp*ladder.levels[-1]
    kernel = mass/(1-ref["weight"](s*mass)) + geo.peak*xp*ladder.scan.phase_max
    rises = (1+1/F("2.71828")**2)*geo.rise*sum(ampl)*kernel
    h = xp*L+edge
    baseline = T*b*b
    excess = geo.exposure-T*b
    common = baseline*weighted(b) + other_masks + rises
    lines = []
    for lo, hi_b in ref["REVIEW"]["strips"](geo.peak):
        factor = baseline+excess*hi_b+2*omega
        intercept = delta+pair*(h*factor+common+excess*hi_b*weighted(lo))
        lines.append((intercept, pair*xp*factor))
    return lines


def plateau_one_visit(words, blocked):
    """Full fastest lattice, one excluded band per word and per physical scan."""
    block = next(b for b in ref["word_blocks"](words)
                 if b.subset == "all" and b.max_span == F(1, 4))
    period = xp*L
    interior = period-blocked
    visits = floor((block.span+blocked)/period)+1
    squares = interior*(block.span-visits*blocked)-interior**2/2
    z = block.blocks*max(0, block.first_factor*squares-block.intersections)
    return max(0, z/(1+z)-delta)


def archive_fixed():
    # Same fixed clock and same SEPEM decade as the accepted two-parent witness.
    B, U, second = maps["WITNESSES"]["archive"]
    mean, dead = ref["MEAN"], ladder.fast
    overlap = ref["PARENTS"]["overlap_success"]("compact_1p2", W)
    def excluded(k, cubic):
        p = F(k, W)
        x = 2*k*c*B/mean
        free = (1-dead/p)**2*second - dead*(B**2+4*B*U) - (1+4*p)*B**2-p*B*U
        if dead >= p or x >= 1 or free <= 0:
            return F(0)
        survival = 1-x + (x*x/2-x**3/6 if cubic else 0)
        z = survival*c*c*k*overlap*free/(2*mean**2)
        return z/(1+z)-delta

    def issued(cubic):
        hi = ceil(2*W*dead)
        while excluded(hi, cubic) <= eps:
            hi *= 2
            assert 2*hi*c*B < mean
        lo = 0
        while hi-lo > 1:
            mid = (hi+lo)//2
            if excluded(mid, cubic) > eps:
                hi = mid
            else:
                lo = mid
        assert excluded(hi-1, cubic) <= eps < excluded(hi, cubic)
        price = (1-delta)*A*ref["READ_LO"]*(T/(F(hi,W)+2*J)-2)
        return hi, price, excluded(hi, cubic)

    k, cost, q = issued(True)
    old_k, old_cost, _ = issued(False)
    assert maps["common_witness"](ladder, W, W, (B,U,second)) == old_cost
    return {"old_K_word_s": old_k, "old_compulsory_reads_s_lower": down(old_cost,3),
            "K_word_s": k, "forbidden_physical_period_s":str(F(k,W)),
            "exclusion_Q_lower":down(q,15), "compulsory_reads_s_lower":down(cost,3),
            "percent_lower":down(100*cost/T,6)}


def calculate():
    assert [int(p/L) for p in ladder.levels] == [1,2,4,8,16,32,64,128]
    assert ladder.counts == accepted["zero_cell_counts"] and ladder.scan.addresses == A
    lines = phase_lines()
    def bound(d):
        return max(intercept-slope*d for intercept,slope in lines)

    root = max((intercept-eps)/slope for intercept,slope in lines)
    tick = ceil(root/ns)
    assert bound((tick-1)*ns) > eps >= bound(tick*ns)
    offsets = ref["BASE"]["CAL"]["visit_offsets_ns"]
    tight_gaps = [offsets[i+1]-offsets[i] for i in (0,2)]
    assert len(set(tight_gaps)) == 1
    tight = tight_gaps[0]*ns
    one_phase = sum(ladder.risk(ladder.eta,geo))
    close_lower = plateau_one_visit(W, edge+xp*tight)
    outside_lower = plateau_one_visit(A, edge)
    all_outside = maps["AnyPairs"](A,A)
    outside_upper = sum(all_outside.risk(all_outside.eta,geo))
    assert up(one_phase,12) == accepted["old_stop_upper"]
    assert down(outside_lower,12) == large["rows"][1]["fixed"]["common_Q_lower"]
    # Uniform upper for every intermediate W: factor at A and visibility at W_min.
    uniform_upper = delta + F(A,W)*(one_phase-delta)
    p_same = large["rows"][0]["fixed"]["quote"]
    return {
        "base":"582f57e2a3bc27102876d110134e829e13b6f63e",
        "registration":"29762d36bbc045a76111909b3b311c3d9551d585",
        "words_closed":W, "addresses":A, "L_local_s":str(L), "strips":len(lines),
        "common_separation_ns_ceiling":tick, "common_separation_percent_upper":up(100*tick*ns/L,6),
        "certificate_at_previous_ns_lower":down(bound((tick-1)*ns),15),
        "stop_upper_at_issued_ns":up(bound(tick*ns),15),
        "stop_upper_at_3ms":up(bound(F(3,1000)),12),
        "stop_upper_at_L_over_2_general_masks":up(bound(L/2),12),
        "stop_upper_at_L_over_2_exact_masks":accepted["stop_upper_also_bounds_physical_Q"],
        "one_phase_closed_upper":up(one_phase,12), "tight_separation_ns":tight_gaps[0],
        "tight_two_phase_upper":up(bound(tight),12), "tight_physical_lower":down(close_lower,12),
        "closed_worst_Q_lower":down(close_lower,12),
        "all_external_physical_lower":down(outside_lower,12),
        "all_external_one_phase_upper":up(outside_upper,12),
        "all_maps_one_phase_upper":up(uniform_upper,12),
        "registered_fixed_candidate_s":p_same["period_s"], "archive_fixed":archive_fixed(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    path = HERE / "result.json"
    result = calculate()
    if parser.parse_args().check:
        assert result == json.loads(path.read_bytes())
        print("Phase criterion, physical plateau witnesses and SEPEM fixed-price floor agree.")
    else:
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

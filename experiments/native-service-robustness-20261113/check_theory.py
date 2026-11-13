"""Directed checks for the proposed service changes. Run with python -B check_theory.py."""
import json
from dataclasses import dataclass
from fractions import Fraction as F
from functools import cached_property
from math import ceil
from pathlib import Path
from runpy import run_path

EXPERIMENTS = Path(__file__).resolve().parent.parent
M = run_path(str(EXPERIMENTS / "t186-native-cost-map" / "calculate.py"))
BASE = M["BASE"]
PARENTS = M["PARENTS"]
REVIEW = M["REVIEW"]
T, C, DELTA, B0 = (M[k] for k in ("T", "C", "DELTA", "B0"))
XI, J, DE, READ, WRITE, HARD = (M[k] for k in ("XP", "J", "DE", "READ", "WRITE", "HARD"))
EPS = F(1, 1000)
MEAN = F(6, 5)
GEO, ARCHIVE = M["GEO"], M["ARCHIVE"]
UP, DOWN = M["up"], M["down"]
W = 32768
OLD = M["Ladder"](W)
DELTA_WRITE = XI * F(140, 10**9) + 3*J  # qualified capture at 60 ns through release at 200 ns
ARCHIVE_WITNESS = REVIEW["ARCH"]["histories"]()
WITNESSES = {
    "geo": PARENTS["plateau"](),
    "archive": (F(ARCHIVE_WITNESS["B_witness_upper"]), F(ARCHIVE_WITNESS["U_witness_upper"]),
                F(ARCHIVE_WITNESS["S2_witness_lower_used"])),
}


def max_history(ladder):
    # Exact deterministic interval ends are displaced inward by J at each edge
    # in #479 (1). This looser upper also covers outward displacement.
    return XI * (max(ladder.counts)*ladder.levels[-1]-ladder.scan.drain) + 2*J


def background_split(ladder, env, eta):
    assert eta > 0
    x = eta * ladder.words * C * B0 * max_history(ladder)
    assert 0 < x < 1
    q = sum(ladder.risk(eta, env))
    return DELTA + (q-DELTA)/(1-x)


def costs(ladder, w_high, env, q, force):
    # w_high bounds pre-stop contacts, resets and the number of parents.
    hits = (w_high+1)*C*env.exposure
    mask = min(env.exposure, (ladder.fast+2*J)*(
        env.exposure/(M["XM"]*ladder.levels[-1])+2*(env.peak+env.rise)))
    cells = min(hits, w_high*C*(env.exposure+mask)/MEAN)
    start, reset = ladder.fees
    pre_read = start+reset*(1+cells)
    post = (READ+WRITE)*HARD*q
    return (1+WRITE/READ)*pre_read+post if force else pre_read+WRITE*hits+post


@dataclass(frozen=True)
class AnyPairs(M["Ladder"]):
    # Equal W can have different periods and price when A differs.
    addresses: int

    @cached_property
    def scan(self):
        return BASE["Scan"](2*self.addresses)


def common_witness(ladder, lo, hi, witness):
    # #472, eqs. 3-6, uniform in every W and pairing in [lo,hi].
    peak, rise, second = witness
    dead = ladder.fast
    overlap = PARENTS["overlap_success"]("compact_1p2", lo)

    def excluded(cap):
        mass = 2*cap*C*peak/MEAN
        missing = dead*hi/cap
        if missing >= 1 or mass >= 1:
            return F(0)
        p = F(cap, lo)
        error = dead*(peak**2+4*peak*rise)+(1+4*p)*peak**2+p*peak*rise
        clean = max(0, (1-missing)**2*second-error)
        z = (1-mass)*C**2*cap*overlap*clean/(2*MEAN**2)
        return z/(1+z)-DELTA

    left = right = ceil(2*hi*dead)
    while excluded(right) <= EPS:
        left, right = right, 2*right
        assert 2*right*C*peak < MEAN
    while right-left > 1:
        middle = (left+right)//2
        if excluded(middle) > EPS:
            right = middle
        else:
            left = middle
    assert excluded(right) > EPS
    cost = (1-DELTA)*ladder.scan.addresses*M["READ_LO"]*(T*lo/(right+2*J*hi)-2)
    return cost


def check_distinct_calendars():
    # The shared W=32768 occurs at the edge of one map and inside the other.
    for addresses in (32768, 65536):
        ladder = AnyPairs(32768, addresses)
        for env in (GEO, ARCHIVE):
            assert ladder.risk(ladder.eta, env) == M["Ladder"].risk.__wrapped__(
                ladder, ladder.eta, env)


def map_rows(addresses):
    # Analytic grouping for all integer W; these are not sampled maps.
    half = addresses//2
    groups = [(half,half+4096)]+[(lo+1,lo+4096) for lo in range(half+4096,addresses,4096)]
    assert sum(hi-lo+1 for lo,hi in groups) == half+1
    for lo, hi in [*groups, (addresses,addresses)]:
        ladder = AnyPairs(lo,addresses)
        assert ladder.scan.addresses == addresses
        row = {}
        for name, env in (("geo",GEO), ("archive",ARCHIVE)):
            eta = F(5*lo-4, 6*lo)
            q = DELTA + F(hi,lo)*(sum(ladder.risk(eta,env))-DELTA)
            price = costs(ladder,hi,env,q,False)
            fixed = common_witness(ladder,lo,hi,WITNESSES[name])
            candidate_period = F("0.0934444") if addresses==32768 else F("0.0458752")
            cand = M["physical"](ladder.scan, hi, candidate_period,both=False,env=env)
            assert cand <= EPS
            # #481 count of all reads/writes uses the one-phase stop bound.
            # Its returned double-phase probability is unused; cand above is
            # the actual single-phase probability for this unknown pairing.
            fixed_upper, _ = M["fixed_price"](AnyPairs(hi,addresses), candidate_period, env)
            continuous = M["physical"](ladder.scan,hi,ladder.scan.L,both=False,env=env)
            row[name] = {"q":UP(q,12), "fixed_candidate_q":UP(cand,12),
                         "continuous_fraction_upper":UP(continuous/EPS,6),
                         "stairs_s":UP(price,3),"fixed_s_min":DOWN(fixed,3),
                         "fixed_candidate_s_upper":UP(fixed_upper,3),
                         "fixed_over_stairs_lower":DOWN(fixed/price,4)}
        yield [lo, hi, row]


def main():
    check_distinct_calendars()
    h = XI*OLD.levels[-1]+2*J+DE
    cases = {}
    floor_full = F("11527603.947")
    floor_archive = F("1585505.253")
    for name, env, old_floor in (("geo",GEO,floor_full),("archive",ARCHIVE,floor_archive)):
        eta, eta_check = OLD.eta, F(32,38)*OLD.eta
        guard = W*C**2*h
        s1r = env.exposure-B0*T
        q = background_split(OLD,env,F(3,8))
        q_force = sum(OLD.risk(eta_check,env))
        q_force_split = background_split(OLD,env,eta_check)
        cost = costs(OLD,W,env,q_force,True)
        bound_writes = (W+1)*C*env.exposure
        hits = C*env.peak*DELTA_WRITE*bound_writes
        # Sufficient candidate for strongest fixed schedule under the same service
        fixed_q = M["physical"](OLD.scan, W, F("0.0934444"), both=False,env=env)
        assert fixed_q < EPS
        assert q <= EPS and q_force <= EPS and q_force_split <= EPS
        assert 2*cost < 2*old_floor
        assert abs(READ-WRITE)==0
        # For arbitrary dangerous results of a hit during WE#, exhibit one
        # allowed mark-to-failure transition and one admissible fixed clock.
        # A fixed period at or above cutoff fails via the accepted accumulation
        # witness. A shorter period has at least the write density used below.
        if name == "geo":
            cutoff = F(1455,8192)
            assert M["common_floor"](OLD, int(cutoff*W)) > EPS
            total_exposure = F(BASE["S1"])
        else:
            caps = REVIEW["accepted_bounds"]()["laws"]["compact_1p2"]["archives"]
            cutoff = F(caps["K_word_s"],W)
            assert F(caps["Q_lower"]) > EPS
            read = REVIEW["ARCH"]["read_json"]
            transferred = read(EXPERIMENTS / "t186-ost-geo-3g/result.json")
            w = read(EXPERIMENTS / "c1-geo-fixed-20261109/sepem.json")["maxima"]["S2"]
            a = transferred["archive"]
            exact_s1 = a["excess_multiplier"]*w["S1"] + T*(
                transferred["ost_tabulated"]["b"]-a["excess_multiplier"]*a["old_limits"]["b"])
            assert exact_s1 > 164214
            total_exposure = F(164214)
        # Each x16 address has one periodic WE-low mask in physical seconds.
        # Its zero-mean primitive is bounded by the physical vulnerable width.
        # Sum over all A disjoint masks. Edges and integrated variation cost
        # at most width*(B+2U) per mask, plus the 2B allowance for horizon clipping.
        min_exposed_mass = C*OLD.scan.addresses*F(50,10**9)*(
            total_exposure/cutoff-3*env.peak-2*env.rise)
        unsafe_lower = min_exposed_mass/(1+min_exposed_mass)-DELTA
        assert unsafe_lower > F(1,1000) if name == "geo" else unsafe_lower > F(7,10000)
        allowed_danger = min(EPS-q_force,
                             (old_floor-cost)/((READ+WRITE)*HARD))
        cases[name] = {"bb":UP(guard*B0**2*T,12),"br_rb":UP(2*guard*B0*s1r,12),
            "q_excess_only_3_over_8":UP(q,12),"q_force_all":UP(q_force,12),
            "q_force_excess":UP(q_force_split,12),"force_ladder_s":UP(cost,3),
            "force_fixed_s_lower":DOWN(2*old_floor,3),
            "ratio_same_forced_service_lower":DOWN(2*old_floor/cost,4),
            "ratio_fixed_can_omit_writes_lower":DOWN(old_floor/cost,4),
            "collision_post_sample_q_upper":UP(hits,15),
            "residual_budget_failure_and_twofold":DOWN(allowed_danger,12),
            "WE_low_short_fixed_counterexample_lower":DOWN(unsafe_lower,12),
            "force_collision_raw_upper":UP(C*env.exposure,9)}
    print(json.dumps({"closed_0125":cases,
                      "maps_00625":list(map_rows(32768)),
                      "maps_0125":list(map_rows(65536))},indent=2))


if __name__ == "__main__":
    main()

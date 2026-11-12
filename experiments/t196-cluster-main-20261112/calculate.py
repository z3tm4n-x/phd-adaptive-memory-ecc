"""Task 1.3. Directed risk and full-horizon port occupation on one closed map."""
import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from math import ceil, floor
from pathlib import Path
from runpy import run_path


HERE = Path(__file__).resolve().parent
EXP = HERE.parent
ARCH = run_path(str(EXP / "t196-archive-same-map-20261110/calculate.py"))
BASE, SCAN = ARCH["base"], ARCH["scan"]
A, W, W_HI = SCAN.addresses, ARCH["W_LO"], ARCH["W_HI"]
T, C, EPS, DELTA = (BASE[k] for k in ("T", "C", "EPS", "DELTA"))
B0, XI_LO, XI_HI, J, DE = (BASE[k] for k in ("B0", "XI_LO", "XI_HI", "J", "APERTURE"))
LEVELS = [2**i * SCAN.L for i in range(9)]
COMMON = LEVELS[-1]
COUNTS = BASE["thresholds"](SCAN, 8)
HISTORY = [XI_LO * (n * COMMON - SCAN.drain) - 2*J for n in COUNTS]
AMPLITUDE = [XI_HI * p / 2 for p in LEVELS[1:]]
FAST = XI_HI * SCAN.L + DE
MASK_WIDTH = FAST + 2*J
HARD = BASE["max_accesses"]()
READ = XI_HI * BASE["READ"] + 2*J
WRITE = XI_HI * BASE["REPAIR"] + 2*J
FIXED_PERIOD = F("0.0934444")
RESET_FEE = ARCH["COST_PER_RESET"]
START, RESET, _, TAIL = ARCH["fees"]()
ACCEPTED_12 = "b7d6cf91d5bd33df6c313536748be7dda87ed0f8"
BOUNDS_PATH = "experiments/t196-visible-parents-20261112/bounds.json"
assert W == 32768 and A == 2*W
assert COUNTS == [5, 10, 19, 38, 75, 149, 298, 596]
assert RESET <= RESET_FEE and TAIL == (READ + WRITE)*HARD


def up(value, places=9):
    return BASE["emit"](value, places, upward=True)


def down(value, places=9):
    return BASE["emit"](value, places, upward=False)


def accepted_bounds():
    root = EXP.parent
    path = root / BOUNDS_PATH
    expected = "4452cadd61670a5f5705169289f36fa2d436a57f"
    def reviewed_bytes(raw):
        data = raw.replace(b"\r\n", b"\n")
        blob = hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
        return data if blob == expected else None
    if path.is_file():
        data = reviewed_bytes(path.read_bytes())
        if data is not None:
            return json.loads(data)
    # The reviewed scientific version can precede its integration into main.
    ref = subprocess.run(["git", "show", f"{ACCEPTED_12}:{BOUNDS_PATH}"], cwd=root,
                         capture_output=True)
    if ref.returncode:
        raise SystemExit("Missing reviewed #472 input. Run: git fetch origin refs/pull/472/head")
    data = reviewed_bytes(ref.stdout)
    assert data is not None, "Expected the reviewed #472 input"
    return json.loads(data)


@dataclass(frozen=True)
class Profile:
    peak: F
    rise: F
    exposure: F
    second: F


def profiles():
    geo = Profile(BASE["B"], BASE["U"], BASE["S1"], BASE["S2"])
    source = ARCH["read_json"](EXP / "t186-ost-geo-3g/result.json")["archive"]
    rows = source["archives_on_transferred_profiles"]
    receipt = ARCH["histories"]()
    assert source["conditional_class_covers"] and set(rows) == set(receipt["archive_rows"])
    peak = F(ceil(1000 * max(r["peak_of_transferred_construction"] for r in rows.values())), 1000)
    rise = F(ceil(max(r["J_in_old_background_coordinates"] for r in rows.values())))
    exposure = F(receipt["S1_all_upper_used"])
    second = min(geo.second, B0**2*T + (peak+B0)*(exposure-B0*T))
    assert B0 < peak <= geo.peak and rise <= geo.rise and B0*T < exposure <= geo.exposure
    return geo, Profile(peak, rise, exposure, second)


def aperture(profile, period):
    return DE * (profile.second/(XI_LO*period) + profile.peak**2 + 4*profile.peak*profile.rise)


def weight(z):
    """Exact #449 ceiling of (1+z/64)^(-64) on the 10^-18 lattice."""
    base = z.denominator*64
    divisor = (base+z.numerator)**64
    return F((base**64 * 10**18 + divisor-1)//divisor, 10**18)


@lru_cache(maxsize=None)
def strips(peak):
    intervals = []
    left = B0
    while left < peak:
        right = min(peak, 2*left)
        step = (right-left)/32
        for i in range(32):
            lo = left+i*step
            intervals.append((lo, lo+step+B0))
        left = right
    return intervals


@lru_cache(maxsize=18000)
def coefficient(eta, x):
    s = W*C*eta
    return FAST + sum(a*weight(s*h*x) for a,h in zip(AMPLITUDE, HISTORY))


@lru_cache(maxsize=None)
def risk(eta, profile):
    assert eta > 0
    s = W*C*eta
    slope = max(hi_b * coefficient(eta, lo) for lo,hi_b in strips(profile.peak))
    integral = T*B0**2*coefficient(eta, B0) + (profile.exposure-B0*T)*slope
    phases = FAST*aperture(profile, SCAN.L)
    phases += sum(a*aperture(profile,p) for a,p in zip(AMPLITUDE,LEVELS[1:]))
    mass = profile.peak*XI_HI*COMMON
    kernel = mass/(1-weight(s*mass)) + profile.peak*XI_HI*SCAN.phase_max
    rises = (1+1/F("2.71828")**2)*sum(AMPLITUDE)*profile.rise*kernel
    pair = W*C**2/2
    return DELTA, pair*integral, pair*phases, pair*rises


def threshold(profile):
    lo, hi = F(0), F(1)
    assert sum(risk(hi, profile)) <= EPS
    for _ in range(14):
        mid = (lo+hi)/2
        if sum(risk(mid,profile)) <= EPS:
            hi = mid
        else:
            lo = mid
    qlo, qhi = sum(risk(lo,profile)), sum(risk(hi,profile))
    assert hi-lo == F(1,2**14) and qhi <= EPS < qlo
    return lo, hi, {"eta_fail":str(lo), "eta_sufficient":str(hi),
                    "certificate_at_fail_lower":down(qlo,12),
                    "certificate_at_pass_upper":up(qhi,12)}


def block_overlap(k):
    # W times the mean success for the two-parent witness: shift 0 or +/-1,...,+/-(k-1).
    assert 2*k <= W
    return (1-F(1,38**k)) + 2*sum(1-F(1,38**j) for j in range(1,k))


def block_floor(k, witness):
    peak, rise, second_low = witness
    a = block_overlap(k)
    def excluded(cap):
        p = F(cap,W)
        missing = FAST*W_HI/cap
        mass = 2*cap*C*peak/k
        edge = FAST*(peak**2+4*peak*rise)+(1+4*p)*peak**2+p*peak*rise
        profile = (1-missing)**2*second_low-edge
        if missing >= 1 or mass >= 1 or profile <= 0:
            return F(0)
        z = (1-mass)*C**2*cap*a*profile/(2*k*k)
        return z/(1+z)-DELTA
    lo = ceil(2*W_HI*FAST)
    hi = lo
    while excluded(hi) <= EPS:
        lo, hi = hi, 2*hi
        if 2*hi*C*peak >= k:
            raise ValueError("No positive two-parent crossing for this witness")
    while hi-lo > 1:
        mid = (lo+hi)//2
        if excluded(mid) > EPS:
            hi = mid
        else:
            lo = mid
    assert excluded(hi)>EPS and (hi==ceil(2*W_HI*FAST) or excluded(lo)<=EPS)
    return hi, excluded(hi)


def fixed_lower(cap):
    return (1-DELTA)*A*(XI_LO*BASE["READ"]-2*J)*(T*W/(cap+2*J*W_HI)-2)


def fixed_candidate(profile):
    width = XI_HI*FIXED_PERIOD+2*J+DE
    n = BASE["N"]
    q_physical = DELTA + W*C**2*F(n-1,2*n)*(width*profile.second+2*profile.peak*DE*profile.exposure)
    assert q_physical <= EPS
    q_stop = DELTA + W*C**2/2*(XI_HI*FIXED_PERIOD+DE)*(profile.second+aperture(profile,FIXED_PERIOD))
    reads = min(HARD,A*(2+T/(XI_LO*FIXED_PERIOD-2*J))+DELTA*HARD)
    repairs = min(reads,(W+1)*C*profile.exposure+q_stop*HARD)
    return q_physical, q_stop, READ*reads + WRITE*repairs


def compare(profile, mean, eta, cap, floor_q, eta_hi):
    terms = risk(eta,profile)
    q = sum(terms)
    assert q < 1
    hits = (W+1)*C*profile.exposure
    stripe = min(profile.exposure, MASK_WIDTH*(profile.exposure/(XI_LO*COMMON)+2*profile.peak+2*profile.rise))
    parents = W*C*profile.exposure/mean
    cells = min(hits, parents+W*C*stripe/mean)
    before_reads = START+RESET*(1+cells)
    before_writes = WRITE*hits
    bus = before_reads+before_writes+TAIL*q
    ungrouped = bus + RESET*(hits-cells)
    floor_bus = fixed_lower(cap)
    ladder_low = (1-q)*A*(XI_LO*BASE["READ"]-2*J)*(T/(XI_HI*COMMON+2*J)-2)
    q_f, q_fstop, fixed_up = fixed_candidate(profile)
    margin = floor_bus/2-bus
    return {"eta":str(eta), "parent_fraction_sufficient":up(eta_hi*mean,8),
            "stop_Q_upper":up(q,12), "epsilon_minus_Q_lower":down(EPS-q,12),
            "admissible_by_test":q<=EPS, "risk_terms_up":[up(t,15) for t in terms],
            "true_repairs_upper":up(hits,6), "parents_upper":up(parents,6),
            "exposure_in_common_scans_upper":up(stripe,6), "true_reset_cells_upper":up(cells,6),
            "pre_stop_read_s_upper":up(before_reads,6), "pre_stop_repair_s_upper":up(before_writes,6),
            "post_stop_s_upper":up(TAIL*q,6), "ladder_s_upper_I0_X0":up(bus,3),
            "without_grouping_I0_X0_bus_s_upper":up(ungrouped,3),
            "without_grouping_half_margin_s_lower":down(floor_bus/2-ungrouped,3),
            "ladder_percent_upper":up(100*bus/T,6), "ladder_s_lower":down(ladder_low,3),
            "fixed_K_word_s":cap, "fixed_exclusion_Q_lower":down(floor_q,12),
            "fixed_s_lower":down(floor_bus,3), "fixed_percent_lower":down(100*floor_bus/T,6),
            "fixed_candidate_Q_upper":up(q_f,12), "fixed_candidate_stop_upper":up(q_fstop,12),
            "fixed_candidate_s_upper":up(fixed_up,3), "fixed_candidate_percent_upper":up(100*fixed_up/T,6),
            "fixed_over_ladder_lower":down(floor_bus/bus,6),
            "fixed_over_ladder_upper":up(fixed_up/ladder_low,6),
            "half_floor_minus_ladder_s_lower":down(margin,3),
            "whole_resets_for_half_if_X0":floor(margin/RESET_FEE) if margin>=0 else None,
            "twofold_established_at_I0_X0":(q<=EPS and margin>=0)}


def result():
    prior = accepted_bounds()
    geo, archive = profiles()
    index = ARCH["histories"]()
    environments = {"geo":geo, "reconstructions":archive}
    witnesses = {"geo":(geo.peak,geo.peak-B0,prior["geo_witness_S2_lower_per_s"]),
                 "reconstructions":(F(index["B_witness_upper"]),F(index["U_witness_upper"]),index["S2_witness_lower_used"])}
    limit = {key:threshold(profile) for key,profile in environments.items()}
    # Reproduce the historical closed-map control using its own conservative visibility.
    old = sum(risk(F(W-1,2*W),geo))
    assert up(old,9) == "0.000762790"
    for z in (F(0), F(1,3), F(81,5)):
        assert weight(z) == BASE["exp_upper"](z)
    laws = [("compact_1p2",F(6,5),F(5*W-4,6*W)),("compact_5",F(5),F(1,5)),
            ("two_uniform",F(2),F(1,2)),("compact_4",F(4),F(1,4)),("compact_8",F(8),F(1,8))]
    output = {}
    for law,mean,eta in laws:
        output[law] = {}
        for key,profile in environments.items():
            if law in prior["laws"]:
                label = "geo" if key == "geo" else "archives"
                if law == "two_uniform" and key == "reconstructions":
                    label = "archives_word_phase_bound_462"
                row = prior["laws"][law][label]
                cap, floor_q = row["K_word_s"],F(row["Q_lower"])
                assert down(fixed_lower(cap),3) == row["endpoints"][0]["bus_s_lower"]
                if law == "compact_5":
                    repeat_cap, repeat_q = block_floor(5,witnesses[key])
                    assert repeat_cap == cap and down(repeat_q,12) == row["Q_lower"]
            else:
                cap, floor_q = block_floor(int(mean),witnesses[key])
            output[law][key] = compare(profile,mean,eta,cap,floor_q,limit[key][1])
    return {"word_count":W,"addresses":A,"T_s":int(T),"reset_s_upper":str(RESET_FEE),
            "historical_control_Q_upper":up(old,9),
            "profiles":{name:{"B":str(p.peak),"U":str(p.rise),"S1":str(p.exposure),
                              "S2":str(p.second)} for name,p in environments.items()},
            "thresholds":{name:item[2] for name,item in limit.items()},"laws":output}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    args = parser.parse_args()
    out = result()
    if args.check:
        assert out == json.loads((HERE/"result.json").read_bytes())
        print("Five laws, both visibility brackets, price bounds and historical controls match.")
    else:
        print(json.dumps(out,ensure_ascii=False,indent=2))

"""A fixed SEPEM witness and same-map bus comparison for the accepted ERR ladder."""
import argparse
import hashlib
import json
from fractions import Fraction as F
from math import ceil, floor
from pathlib import Path
from runpy import run_path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
NATIVE = EXP / "t196-native-err-20261110"
base = run_path(str(NATIVE / "check.py"))
scan = base["Scan"](131072)
A, L = scan.addresses, scan.L
T, C = base["T"], base["C"]
XI_LO, XI_HI, J, D_E = base["XI_LO"], base["XI_HI"], base["J"], base["APERTURE"]
READ, REPAIR = base["READ"], base["REPAIR"]
EPS, DELTA = base["EPS"], base["DELTA"]
W_LO, W_HI = A//2, 44529
CAP = F(37200)   # P0(W) = CAP/W seconds; one convenient, sufficient cutoff.
COST_PER_RESET = F("34.016758")


def read_json(path):
    return json.loads(path.read_bytes(), parse_float=F)


def show(value, digits, upper):
    return base["emit"](value, digits, upward=upper)


def histories():
    transferred = read_json(EXP / "t186-ost-geo-3g/result.json")
    old = read_json(EXP / "c1-geo-fixed-20261109/sepem.json")
    witness = old["maxima"]["S2"]
    profile = read_json(EXP / "t436-archive-replay/sepem.json")
    assert profile["start_utc"] == witness["start_utc"]
    assert profile["input"]["start_bin"] == witness["start_bin"]
    assert profile["input"]["calendar_gap_s"] == profile["input"]["tail_s"] == 0
    archive = transferred["archive"]
    k = archive["excess_multiplier"]
    b0 = archive["old_limits"]["b"]
    b1 = transferred["ost_tabulated"]["b"]
    intercept = b1-k*b0
    assert k > 0 and intercept > 0
    shift_terms = 2*k*intercept*witness["S1"] + intercept**2*T
    bin_second = k**2*witness["S2_s_inv"] + shift_terms
    reconstructed_second = k**2*profile["input"]["S2_per_s"] + shift_terms
    first = k*witness["S1"] + intercept*T
    rows = archive["archives_on_transferred_profiles"]
    sepem = rows["SEPEM_archive"]
    assert abs(first-sepem["S1_on_accepted_windows_or_gap_completion"]) < F("0.000001")
    # Outward, deliberately coarse inputs; the fractional programs below only
    # use these integers. The binned second moment is a lower by Jensen.
    s2_low, s2_high = F(15624), F(134875)
    assert s2_low < bin_second < reconstructed_second < s2_high
    assert archive["old_limits"]["S2"] < s2_high
    assert sepem["peak_of_transferred_construction"] < F("0.525")
    assert sepem["J_in_old_background_coordinates"] < 24
    s1_cap = max(sepem["S1_any_start_upper"],
                 *(r["S1_on_accepted_windows_or_gap_completion"] for r in rows.values()))
    assert ceil(s1_cap) == 164372 and archive["conditional_class_covers"]
    return {"start":witness["start_utc"],"stop":witness["stop_utc_exclusive"],
            "start_bin":witness["start_bin"],"number_bins":int(T/300),
            "archive_rows":list(rows),"affine_excess_multiplier":str(float(k)),
            "S1_witness_approx":float(first),"S2_from_bin_means_approx":float(bin_second),
            "S2_reconstruction_approx":float(reconstructed_second),
            "S2_witness_lower_used":int(s2_low),"S2_upper_used":int(s2_high),
            "S1_all_upper_used":ceil(s1_cap),"B_witness_upper":"0.525","U_witness_upper":24}


def witness_test(inputs):
    b = F(inputs["B_witness_upper"])
    u = F(inputs["U_witness_upper"])
    s2_low, s2_high = inputs["S2_witness_lower_used"], inputs["S2_upper_used"]
    p_max = CAP/W_LO
    m_max = 2*p_max*C*b
    # Each scan's four-slot frames repeat identically in its two halves.
    # Sum of absolute phase deviations from xi*L/2 is exactly A*xi*L/4.
    relative_dead = (A*XI_HI*L/4 + W_HI*D_E)/CAP
    longest_dead = XI_HI*L + D_E
    loss = longest_dead*(b*b+4*b*u) + (1+4*p_max)*b*b + p_max*b*u
    overlap = (W_HI-1)*m_max**2/8 + m_max/2 + F(1,4*(W_LO-1))
    z = C**2*CAP*(F(37,76)*(1-m_max)*((1-relative_dead)**2*s2_low-loss)-overlap*s2_high)
    assert 0 < longest_dead < CAP/W_HI and 0 < m_max < 1 and z > 0
    lower = z/(1+z)-DELTA
    assert lower>EPS
    return {"CAP_word_seconds":int(CAP),"rate_mass_upper":show(m_max,12,True),
            "relative_dead_upper":show(relative_dead,12,True),
            "finite_edge_and_variation_loss_upper":show(loss,9,True),
            "Z_lower":show(z,12,False),"physical_Q_lower":show(lower,12,False)}


def fixed_floor(words):
    # One common denominator makes this read lower affine in W over all maps.
    return (1-DELTA)*A*(T*words/(CAP+2*J*W_HI)-2)*(XI_LO*READ-2*J)


def fees():
    levels = [2**i*L for i in range(9)]
    thresholds = base["thresholds"](scan,8)
    h = [XI_LO*p-2*J for p in levels]
    increments = [1/x-1/y for x,y in zip(h,h[1:])]
    read_fee,write_fee = READ*XI_HI+2*J,REPAIR*XI_HI+2*J
    start = 2+T/h[-1]+(XI_HI*L+J)*sum(increments)
    recovery = (XI_HI*levels[-1]+2*J)*sum(d*(n+1) for d,n in zip(increments,thresholds))
    reset = A*read_fee*recovery
    assert reset <= COST_PER_RESET
    return A*read_fee*start,reset,write_fee,(read_fee+write_fee)*base["max_accesses"]()


def comparison(s1, q0):
    baseline,reset,write_fee,tail = fees()
    rows = []
    margins = []
    for w in (W_LO,W_HI):
        # All coefficients other than W are nonincreasing in the visibility
        # rate s=(W-1)c/2 in #449 (7). The accepted stop upper is also available.
        q_aff = DELTA+F(w,W_LO)*(q0-DELTA)
        hits = (w+1)*C*s1
        bus = baseline+reset*(1+hits)+write_fee*hits+tail*q_aff
        fixed = fixed_floor(w)
        margin = fixed/2-bus
        rows.append({"words":w,"excluded_period_from_s_upper":show(CAP/w,12,True),
                     "fixed_bus_s_lower":show(fixed,3,False),
                     "ladder_bus_s_upper_at_I0":show(bus,3,True),
                     "half_floor_minus_ladder_s_lower":show(margin,3,False)})
        margins.append(margin)
    reserve = min(margins)
    limit = reserve/COST_PER_RESET
    return {"S1_cap":int(s1),"endpoints":rows,
            "uniform_margin_s_lower":show(reserve,3,False),
            "s_per_invalid_upper":show(COST_PER_RESET,6,True),
            "sufficient_mean_resets_lower":show(limit,6,False),
            "sufficient_whole_resets":floor(limit),
            "remaining_s_at_whole_limit_lower":show(reserve-floor(limit)*COST_PER_RESET,3,False)}


def calculate():
    archive = histories()
    published = read_json(NATIVE / "result.json")["131072"]
    q0 = F(published["closed"]["staircase"]["stop_and_Q_upper"])
    global_q = F(published["quarter_eligible"]["staircase"]["stop_and_Q_upper"])
    uniform_bus = F(published["quarter_eligible"]["staircase"]["price"]["bus_read_repair_s_at_I0"])
    direct_gap = uniform_bus-fixed_floor(W_LO)/2
    assert q0==F("0.000762790") and global_q==F("0.000902581")
    assert uniform_bus==F("1061779.678")
    return {"archive":archive,"witness":witness_test(archive),
            "archive_price":comparison(F(archive["S1_all_upper_used"]),q0),
            "unchanged_exposure_control":comparison(base["S1"],q0),
            "direct_gap_using_global_ladder_upper_s":show(direct_gap,3,True),
            "accepted_global_Q_upper":show(global_q,9,True),"register_port_X_s":0}


def verify_cache(cache):
    import numpy as np
    receipt = read_json(EXP / "t141-radiation-chain/outputs/profile-provenance.json")["input"]
    path = cache/"bands.npy"
    with path.open("rb") as stream:
        assert hashlib.file_digest(stream,"sha256").hexdigest()==receipt["arrays_sha256"][path.name]
    bands = np.load(path,mmap_mode="r")
    source = read_json(EXP/"c1-geo-fixed-20261109/sepem.json")
    ost = read_json(EXP/"t186-ost-geo-3g/result.json")
    i=source["maxima"]["S2"]["start_bin"]
    times=int(T/300)
    # Include the predecessor of the window to reconstruct its first left edge.
    raw=bands[i-1:i+times,1,0]+bands[i-1:i+times,1,1]
    b=float(ost["ost_tabulated"]["b"])
    means=b+(1+float(ost["archive"]["beta_ost_tabulated"]))*np.maximum(raw-float(source["H_p10"]),0)
    r=means[1:]
    low=np.minimum(r,means[:-1])
    high=2*r-low
    s1=float(300*np.sum(r,dtype=np.float64))
    s2=float(100*np.sum(low**2+low*high+high**2,dtype=np.float64))
    ref=histories()
    assert abs(s1-ref["S1_witness_approx"])<1e-6
    assert abs(s2-ref["S2_reconstruction_approx"])<1e-6
    # Bound the transformed stored bin means below, starting from the
    # canonical binary64 C1 reconstruction. Verify the squared sum exactly
    # in integer chunks; this does not require the affine sub-bin shape.
    def below(x):
        return np.nextafter(x,-np.inf)

    archive=ost["archive"]
    old_b=float(source["background_per_s"])
    old_mean=old_b+(1+float(source["HI_to_H"]))*np.maximum(raw[1:]-float(source["H_p10"]),0)
    excess_lo=np.maximum(0,below(old_mean-np.nextafter(float(archive["old_limits"]["b"]),np.inf)))
    mean_lo=below(below(b)+below(below(float(archive["excess_multiplier"]))*excess_lo))
    scale=2**26
    units=np.floor(mean_lo*scale).astype(np.int64)
    assert units.min()>=0 and int(units.max())**2*1024<2**63
    squares=sum(int((chunk*chunk).sum(dtype=np.int64))
                for chunk in np.array_split(units,ceil(len(units)/1024)))
    integral_lower=F(300*squares,scale**2)
    assert integral_lower > ref["S2_witness_lower_used"]
    return s1,s2,integral_lower


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--sepem-cache",type=Path)
    args=parser.parse_args()
    result=calculate()
    if args.sepem_cache:
        s1,s2,lower=verify_cache(args.sepem_cache)
        print(f"SEPEM cache verified: S1={s1:.9f}, S2={s2:.9f}, "
              f"directed bin lower={show(lower,9,False)}.")
    if args.check:
        assert result==json.loads((HERE/"result.json").read_bytes())
        print("Directed bounds match result.json.")
    else:
        print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()

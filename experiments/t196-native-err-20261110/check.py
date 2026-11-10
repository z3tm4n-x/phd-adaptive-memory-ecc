"""Native 32+6 SEC, two-word parent, full x16 scan and directed lifetime bounds."""
import argparse
from dataclasses import dataclass
from fractions import Fraction as F
from hashlib import sha1
from math import ceil, floor
from pathlib import Path
from runpy import run_path
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
# Scalar integral, aperture mask and outward exponential from accepted PR449.
accepted = run_path(str(ROOT / "experiments/t196-dyadic-local-count-20261110/check.py"))
exp_upper = accepted["exp_upper"]
phase_mask = accepted["phase_mask"]
scalar_bound = accepted["scalar_bound"]


C1 = json.loads((ROOT / "experiments/c1-common-geo-20261109/six.json").read_bytes())
ENV = json.loads((ROOT / "experiments/c1-common-geo-20261109/coverage.json").read_bytes())
CAL_BYTES = (HERE / "calendar.json").read_bytes().replace(b"\r\n", b"\n")
CAL_BLOB = sha1(f"blob {len(CAL_BYTES)}\0".encode() + CAL_BYTES).hexdigest()
assert CAL_BLOB == "6d937af0f819a4ffab579194f7e34217cd60a12c"
CAL = json.loads(CAL_BYTES)
NS = F(1,10**9)
T, D = F(C1["T"]), C1["D"]
N = CAL["inner_data_bits"] + CAL["inner_check_bits"]
C = F(N,D)
B, B0 = F(ENV["B_s_inv"]), F(ENV["b_s_inv"])
S1, S2 = F(C1["S1_max"]), F(C1["S2_max"])
U, EPS, DELTA = F("28.855"), F("0.001"), F(C1["delta_exec"])
RATIO = F("0.00168")
XI_LO, XI_HI = F(CAL["xi_min"]), F(CAL["xi_max"])
J = F(CAL["edge_jitter_ns"])*NS
FRAME = CAL["frame_ns"]*NS
OFFSETS = CAL["visit_offsets_ns"]
PER_FRAME = len(OFFSETS)
OP = CAL["operation_ns"]
APERTURE = OP["write_release"]*NS*XI_HI+3*J
READ = OP["read_release_or_drive_write"]*NS
REPAIR = OP["write_release"]*NS-READ


def emit(x, digits=9, upward=True):
    scale = 10**digits
    v = (ceil if upward else floor)(x*scale)
    whole, frac = divmod(abs(v),scale)
    return f"{'-' if v<0 else ''}{whole}.{frac:0{digits}d}"


@dataclass(frozen=True)
class Scan:
    payload_bytes: int

    @property
    def addresses(self):
        return self.payload_bytes//2

    @property
    def L(self):
        assert self.addresses % PER_FRAME == 0
        return self.addresses//PER_FRAME*FRAME

    @property
    def drain(self):
        return self.L-CAL["report_cut_ns_before_next_pass"]*NS

    @property
    def phase_max(self):
        return self.L-FRAME+OFFSETS[-1]*NS

    @property
    def aperture(self):
        return APERTURE

    @property
    def xi_lo(self):
        return XI_LO


def physical_q(scan, words, stride=1):
    width = XI_HI*stride*scan.L + 2*J + APERTURE
    distinct_bits = F(words*N*(N-1),2*D**2)
    return DELTA + distinct_bits*(width*S2 + 2*B*APERTURE*S1)


def thresholds(scan, top):
    anchor = 2**top*scan.L
    return [ceil(((2**i*scan.L/RATIO+2*J)/XI_LO+scan.L)/anchor)
            for i in range(1,top+1)]


def registration(scan):
    top = 0
    while XI_HI*2**(top+1)*scan.L+2*J <= 6:
        top += 1
    anchor = 2**top*scan.L
    return {"top_level":top, "top_rounds":2**top, "period_local_s":emit(anchor),
            "period_physical_upper_s":emit(XI_HI*anchor+2*J,12),
            "following_physical_s":emit(XI_HI*2*anchor+2*J,12),
            "quiet_frames":thresholds(scan,top)}


def headroom(scan):
    words_min,words_max=scan.addresses//2,scan.addresses
    capital = floor((EPS/4-DELTA)/(physical_q(scan,1)-DELTA))
    out = {"addresses":scan.addresses,"L_s":emit(scan.L),"pairs_closed_W":words_min,
           "max_touched_W":words_max,"largest_W_for_quarter":capital}
    aux_slope=C*C/2*(XI_HI*scan.L+APERTURE)*(S2+phase_mask(scan,scan.L))
    out["largest_W_for_quarter_with_stop_bound_only"]=floor((EPS/4-DELTA)/aux_slope)
    for label,words in (("closed",words_min),("no_partner_inside",words_max)):
        q=physical_q(scan,words)
        out[label]={"Q_upper":emit(q,12),"stop_only_upper":emit(DELTA+words*aux_slope,12),"epsilon_shares":{
            str(e):emit(q/e,9) for e in (F("0.1"),F("0.01"),EPS,F("0.0001"))}}
    return out


def max_accesses():
    return PER_FRAME*(ceil((T+2*J+APERTURE)/(XI_LO*FRAME))+2)


def true_reports(words):
    # A birth can be charged again only when it was born in the first
    # read/write aperture that reported it. At most one word is open at t.
    return (words+1)*C*S1


def constant_lower(scan, period, wlo, whi, clustered=False):
    """Bonferroni for the registered two-word law and all paid aliases."""
    plateau = F(C1["lower_witness_plateau_used_s"])
    blocks = ceil(plateau/10)
    span = plateau/blocks
    rate = C*B
    mass = rate*span
    # On a particular admissible pairing the two visits lie within one envelope.
    aperture = APERTURE
    multiplicity = F(scan.addresses,wlo)
    if clustered:
        assert wlo==whi
        multiplicity = F(1)
        if wlo < scan.addresses:
            aperture += (OFFSETS[1]-OFFSETS[0])*NS*XI_HI
    # Average over the whole plateau. Only one disjoint port aperture can
    # straddle each of the internal block boundaries.
    visits = multiplicity*(span/period+F(2,blocks)) + F(blocks-1,blocks*wlo)
    free = max(0,span-visits*aperture)
    one = F(N-1,2*N)*(1-mass)*rate**2*free**2/(1+visits)
    intersections = (F(whi*(whi-1),8)*mass**4 + F(whi,2)*mass**3
                     + F(wlo,4*(wlo-1))*mass**2)
    z = blocks*max(0,wlo*one-intersections)
    return max(0,z/(1+z)-DELTA)


def necessary_price(scan, wlo, whi, clustered=False):
    left,right = F(0),F(1)
    assert constant_lower(scan,right,wlo,whi,clustered)>EPS
    for _ in range(44):
        mid = (left+right)/2
        if constant_lower(scan,mid,wlo,whi,clustered)>EPS:
            right = mid
        else:
            left = mid
    assert constant_lower(scan,left,wlo,whi,clustered) <= EPS < constant_lower(scan,right,wlo,whi,clustered)
    least_reads=(1-DELTA)*scan.addresses*(T/(right+2*J)-2)
    return right,max(0,least_reads)*(XI_LO*READ-2*J)


def fixed(scan, wlo, whi):
    cutoff, lower_cost = necessary_price(scan,wlo,whi)
    q1=physical_q(scan,whi)
    qlow=constant_lower(scan,scan.L*XI_HI,wlo,whi)
    k=max(0,1+floor((EPS-q1)/(physical_q(scan,whi,2)-q1)))
    data={"constant_cutoff_physical_s_upper":emit(cutoff,12),
          "continuous_Q_lower":emit(qlow,12,False),
          "class_excluded_on_witness":qlow>EPS,
          "necessary_bus_s_if_nonempty":emit(lower_cost,3,False),"k_certified":k}
    if k:
        p=k*scan.L
        q=physical_q(scan,whi,k)
        assert q<=EPS<physical_q(scan,whi,k+1)
        pre_stop = DELTA+F(whi,2)*C*C*(XI_HI*p+APERTURE)*(S2+phase_mask(scan,p))
        hard=max_accesses()
        reads=min(hard, scan.addresses*(2+T/(p*XI_LO-2*J))+DELTA*hard)
        repairs=min(reads, true_reports(whi)+pre_stop*hard)
        subtotal=reads*(XI_HI*READ+2*J)+repairs*(XI_HI*REPAIR+2*J)
        data.update(candidate_period_s=emit(p,12),candidate_Q_upper=emit(q),
                    candidate_stop_upper=emit(pre_stop),
                    candidate_bus_read_repair_s=emit(subtotal,3))
        # One fixed start every whole number of 1400 ns frames; the scan
        # itself uses the unchanged address sequence and application slots.
        frames=floor((1+(EPS-q1)/(physical_q(scan,whi,2)-q1))*scan.L/FRAME)
        period=frames*FRAME
        q=physical_q(scan,whi,period/scan.L)
        assert period>=scan.L and q<=EPS<physical_q(scan,whi,(period+FRAME)/scan.L)
        stop=DELTA+F(whi,2)*C*C*(XI_HI*period+APERTURE)*(S2+phase_mask(scan,period))
        reads=min(hard,scan.addresses*(2+T/(XI_LO*period-2*J))+DELTA*hard)
        repairs=min(reads,true_reports(whi)+stop*hard)
        cost=reads*(XI_HI*READ+2*J)+repairs*(XI_HI*REPAIR+2*J)
        active_frames=min(F(hard,PER_FRAME),reads/PER_FRAME+2)
        active=active_frames*management_fee()
        data["frame_candidate"]={"frames":frames,"period_s":emit(period,12),
            "Q_upper":emit(q,12),"stop_upper":emit(stop,12),"read_repair_s":emit(cost,3),
            "with_active_management_s":emit(cost+active,3),
            "with_all_management_s":emit(cost+F(hard,PER_FRAME)*management_fee(),3)}
    return lower_cost, data


def admissibility(scan, wlo, whi, levels, quiet_frames):
    anchor=levels[-1]*scan.L
    histories = [XI_LO*(n*anchor-scan.drain)-2*J for n in quiet_frames]
    terms=[XI_HI*stride*scan.L/2 for stride in levels[1:]]
    # Every geometric bisection of a long binary step has the same public gate.
    s=F(wlo-1,2)*C
    factor=F(whi,2)*C**2
    fast=XI_HI*scan.L+APERTURE
    profile,_,_=scalar_bound(B0,terms,histories,fast,s)
    omega=fast*phase_mask(scan,scan.L)
    omega+=sum(a*phase_mask(scan,k*scan.L) for a,k in zip(terms,levels[1:]))
    exposure=B*XI_HI*anchor
    kernel=exposure/(1-exp_upper(s*exposure))+B*XI_HI*scan.phase_max
    rises=(1+1/F("2.71828")**2)*sum(terms)*U*kernel
    q=DELTA+factor*(profile+omega+rises)
    return F(emit(q)),{"profile_upper":emit(factor*profile,12),
                        "overlap_upper":emit(factor*omega,12),
                        "variation_upper":emit(factor*rises,12),
                        "stop_and_Q_upper":emit(q),"visible_history_lower_s":[
                            emit(h,12,False) for h in histories]}


def management_fee():
    start,end=CAL["management_ns"]
    return (end-start)*NS*XI_HI+2*J


def budget(scan, words, levels, quiet_frames, q, lower_cost):
    periods=[k*scan.L for k in levels]
    anchor=periods[-1]
    frame_max=XI_HI*anchor+2*J
    gaps=[XI_LO*p-2*J for p in periods]
    true=true_reports(words)
    times=[min(T,XI_HI*scan.L+J+(n+1)*frame_max*(1+true))
           for n in quiet_frames]
    weights=[1/x-1/y for x,y in zip(gaps,gaps[1:])]
    hard=max_accesses()
    reads=min(hard,scan.addresses*(2+T/gaps[-1]+sum(a*t for a,t in zip(weights,times)))+q*hard)
    writes=min(reads,true+q*hard)
    read_hi, write_hi=XI_HI*READ+2*J, XI_HI*REPAIR+2*J
    subtotal=read_hi*reads+write_hi*writes
    per_invalid=read_hi*scan.addresses*sum(a*(n+1)*frame_max for a,n in zip(weights,quiet_frames))
    top=len(quiet_frames)
    switches=ceil(top+(top+1)*true+q*(2*ceil(T/(XI_LO*anchor-2*J))+4))
    # Full-port effect of charging every management slot through the entire mission.
    fee=management_fee()
    management=F(hard,PER_FRAME)*fee
    active_frames=min(F(hard,PER_FRAME),reads/PER_FRAME+2)
    active=active_frames*fee
    active_rate=per_invalid*(1+fee/(PER_FRAME*read_hi))
    data={"reads_upper_at_I0":ceil(reads),"repairs_upper_at_I0":ceil(writes),
            "bus_read_repair_s_at_I0":emit(subtotal,3),"bus_percent_at_I0":emit(100*subtotal/T,6),
            "fast_s_upper_at_I0":emit(min(T,times[0]+q*T),3),"switch_upper_at_I0":switches,
            "s_per_invalid_upper":emit(per_invalid,6),
            "full_management_reserve_s":emit(management,3),
            "bus_including_full_management_at_I0_s":emit(subtotal+management,3),
            "bus_including_active_management_at_I0_s":emit(subtotal+active,3),
            "s_per_invalid_including_active_management_upper":emit(active_rate,6)}
    if lower_cost is not None:
        data.update(budget_X_for_twice_s=emit(lower_cost/2-subtotal,3,False),
                    budget_after_full_management_s=emit(lower_cost/2-subtotal-management,3,False),
                    budget_after_active_management_s=emit(lower_cost/2-subtotal-active,3,False))
    return data


def bounded_case(scan,wlo,whi,stairs=False):
    lower_cost, rival = fixed(scan,wlo,whi)
    robust_cut, robust_cost = necessary_price(scan,whi,whi,True)
    robust_low = constant_lower(scan,scan.L*XI_HI,whi,whi,True)
    excluded = robust_low>EPS
    out={"W_interval":[wlo,whi],"fixed":rival,
         "shared_unknown_map_rival":{
             "clustered_witness_W":whi, "excluded_from_s":emit(robust_cut,12),
             "bus_lower_s_if_nonempty":emit(robust_cost,3,False),
             "Q_lower_fast_grid":emit(robust_low,12,False),
             "all_fixed_and_binary_excluded":excluded,
             "first_integer_stride_excluded":ceil(robust_cut/(scan.L*XI_HI))}}
    if excluded:
        lower_cost=None
    n=ceil(300/(32*scan.L))
    q, binary=admissibility(scan,wlo,whi,[1,2,4,8,16,32],[n]*5)
    binary.update(full_cells=n,nominal_history_s=emit(n*32*scan.L),
                  price=budget(scan,whi,[1,32],[n],q,lower_cost))
    if not excluded:
        common=budget(scan,whi,[1,32],[n],q,robust_cost)
        binary["shared_map_twice_margin_s"]=common["budget_X_for_twice_s"]
        binary["shared_map_margin_after_full_management_s"]=common["budget_after_full_management_s"]
    out["L32"]=binary
    if stairs:
        assert physical_q(scan,whi)<=EPS/4
        reg=registration(scan)
        strides=[2**i for i in range(reg["top_level"]+1)]
        counts=reg["quiet_frames"]
        assert all(XI_LO*(n*strides[-1]*scan.L-scan.drain)-2*J >= (XI_HI*k*scan.L+2*J)/RATIO
                   for n,k in zip(counts,strides[1:]))
        parts = [(wlo,whi)] if wlo==whi else [(wlo,(wlo+whi)//2),((wlo+whi)//2+1,whi)]
        bounds = [admissibility(scan,a,b,strides,counts) for a,b in parts]
        q, staircase=max(bounds,key=lambda pair:pair[0])
        staircase["word_ranges_certified"]=[dict(low=a,high=b,q=bound[1]["stop_and_Q_upper"])
                                            for (a,b),bound in zip(parts,bounds)]
        staircase["registration"]=reg
        staircase["price"]=budget(scan,whi,strides,counts,q,lower_cost)
        common=budget(scan,whi,strides,counts,q,robust_cost)
        staircase["shared_map_twice_margin_s"]=common["budget_X_for_twice_s"]
        staircase["shared_map_margin_after_full_management_s"]=common["budget_after_full_management_s"]
        out["staircase"]=staircase
    return out


def calculate(headroom_only=False):
    out={"calendar_git_blob":CAL_BLOB}
    for nbytes in CAL["protected_payload_bytes"]:
        scan=Scan(nbytes)
        gate=headroom(scan)
        row={"continuous":gate}
        if not headroom_only:
            lo,hi=scan.addresses//2,scan.addresses
            row["closed"]=bounded_case(scan,lo,lo,physical_q(scan,lo)<=EPS/4)
            row["partners_outside"]=bounded_case(scan,hi,hi)
            row["all_pairings"]=bounded_case(scan,lo,hi)
            if lo<gate["largest_W_for_quarter"]<hi:
                row["quarter_eligible"]=bounded_case(scan,lo,gate["largest_W_for_quarter"],True)
        out[str(nbytes)]=row
    if not headroom_only:
        window=F(1,1000)
        frames=ceil((window+2*J+APERTURE)/(XI_LO*FRAME))+2
        guard=management_fee()
        app=(CAL["application_ns"][1]-CAL["application_ns"][0])*NS*XI_HI+2*J
        used=PER_FRAME*((READ+REPAIR)*XI_HI+4*J)
        out["resources"]={"window_s":"0.001","frame_count_upper":frames,
            "protected_word_operations_peak_pct":emit(100*frames*used/window,6),
            "with_all_app_and_control_slots_peak_pct":emit(100*frames*(used+app+guard)/window,6),
            "nominal_min_gap_ns":min(b-a for a,b in zip(OFFSETS,OFFSETS[1:]+[CAL["frame_ns"]])),
            "additional_true_reports_due_to_inflight_births_upper":emit(C*S1,9)}
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headroom-only",action="store_true")
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    out=calculate(args.headroom_only)
    if args.check:
        ref=json.loads((HERE/"result.json").read_bytes())
        if args.headroom_only:
            ref={k:({"continuous":v["continuous"]} if k.isdecimal() else v)
                 for k,v in ref.items() if k!="resources"}
        assert out==ref
        print("Directed bounds match result.json.")
    else:
        print(json.dumps(out,indent=2))


if __name__ == "__main__":
    main()

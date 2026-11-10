"""Recompute fixed risk, necessary price and registered (4)/(6) on this port."""
from argparse import ArgumentParser
from fractions import Fraction as F
from math import ceil, comb
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE/"calendar.json").read_text(encoding="utf-8"))
C1=json.loads((HERE.parent/"c1-common-geo-20261109/six.json").read_text(encoding="utf-8"))
ENV=json.loads((HERE.parent/"c3-candidate-price-20261109/basis.json").read_text(encoding="utf-8"))
W,T,D=DATA["W"],F(DATA["mission_s"]),C1["D"]
xm,xp=F(DATA["xi_minus"]),F(DATA["xi_plus"])
ns=F(1,10**9);J=F(DATA["J_ns"])*ns
L=DATA["L_ns"]*ns;d=F(DATA["aperture_upper_ns"])*ns
S1,S2,B=F(C1["S1_max"]),F(C1["S2_max"]),F(ENV["B"])
delta,eps=F(C1["delta_exec"]),F(1,1000)
c=F(39,D); U=F(ENV["J_cap"])
read_lo=DATA["read_port_ns"]*ns*xm-2*J
read_hi=DATA["read_port_ns"]*ns*xp+2*J
write_hi=DATA["repair_extra_ns"]*ns*xp+2*J
max_reads=2*(ceil((T+2*J+d)/(DATA["frame_ns"]*ns*xm))+2)


def fixed(k):
    P=k*L
    kpair=F(W*39*38,2*D**2)
    q=delta+kpair*((P*xp+2*J+d)*S2+2*B*d*S1)
    nr=min(max_reads,W*(T/(P*xm-2*J)+2)+delta*max_reads)
    nw=min(nr,2*W*c*S1+q*max_reads)
    return dict(P_nominal=P,Q_upper=q,read_upper=nr,repair_upper=nw,
                bus_upper_s=nr*read_hi+nw*write_hi)


def lower(P,two_words):
    tau=F(C1["lower_witness_plateau_used_s"])
    blocks=ceil(tau/(10 if two_words else 120))
    t=tau/blocks
    m=c*B*t; apertures=t/P+2
    free=max(0,t-apertures*d)
    one=F(38,78)*(1-m)*(c*B)**2*free**2/(apertures+1)
    if two_words:
        # Bivariate Poisson counts: one shared component of mean m/(W-1).
        common=m/(W-1)
        pair_intersection=m**4/4 + common*m*m + common*common/2
        z=blocks*max(0,W*one-comb(W,2)*pair_intersection)
    else:
        z=blocks*W*one                    # accepted independent-singleton witness
    return max(0,z/(1+z)-delta)


def floor_price(two):
    lo,hi=F(0),F(1)
    while hi-lo>F(1,10**12):
        mid=(lo+hi)/2
        if lower(mid,two)>eps: hi=mid
        else: lo=mid
    assert lower(hi,two)>eps
    nr=(1-delta)*W*(T/(hi+2*J)-2)
    return dict(excluded_physical_P_ge_s=hi,low_bracket=lo,Q_lower=lower(hi,two),
                fixed_class_bus_lower_s=nr*read_lo,half_lower_s=nr*read_lo/2,
                Q_lower_2L=lower(2*L*xp,two),Q_lower_4L=lower(4*L*xp,two))


def registered(k,half_floor,paired_half):
    P=k*L; N=ceil(300/P); mu=F(1,2)*c*(W-1)
    hf=xp*L+d;hs=xp*P+d;history=xm*(N*P-L)-2*J
    age=xp*((N+1)*P+L)+d+2*J
    nf=ceil((T+2*J+d)/(xm*L))+3
    nslow=ceil((T+2*J+d)/(xm*P))+3
    na=ceil((age+2*d+2*J)/(xm*P))+3
    C=W*c*c/2
    fast=C*hf*(S2+B*B*nf*d)
    visibility=C*hs*(S1+B*nslow*d)/(F("2.71828")*mu*history)
    old=delta+fast+visibility+C*hs*B*U*(age+na*d)
    # Left-sum bound issued by #196. M/(1-exp(-s*M)) <= 1/s+M
    # from exp(s*M)>=1+s*M. Add last-word phase and aperture repetitions.
    mass=B*xp*P; qlast=(DATA["L_ns"]-880)*ns
    group=1/mu+mass+B*xp*qlast+B*na*d
    new=delta+fast+visibility+C*hs*U*group
    # This price upper uses the larger, already established bound (4)
    # on the first proof stop. No risk below epsilon is assumed.
    hold=(N+1)*(xp*P+2*J);hminus=xm*L-2*J;sminus=xm*P-2*J
    flips=W*c*S1
    tfast=min(T,xp*L+J+hold*(1+2*flips))
    nr=W*(2+T/sminus+(1/hminus-1/sminus)*tfast)+old*max_reads
    nw=2*flips+old*max_reads
    price=nr*read_hi+nw*write_hi
    return dict(k=k,history_cells=N,history_lower_s=history,old_Q_upper=old,
        new_variation_element_upper=group,new_conservative_Q_upper=new,
        fast_pair_term=fast,visibility_term=visibility,price_uses_stop_upper=old,
        expected_fast_s_upper=min(T,tfast+old*T),expected_switch_upper=ceil(1+4*flips+old*(ceil((T+2*J)/(xm*P))+2)),
        bus_s_upper_at_I0=price,extra_s_per_invalid=read_hi*W*(1/hminus-1/sminus)*hold,
        sufficient_unknown_s_at_I0_if_certified=half_floor-price,
        paired_unknown_s_at_I0_if_certified=paired_half-price)


def binary_dyadic(k,broad_half,paired_half):
    """PR449 (5)-(7): all splits of one long binary step share one admission.
    Use the same formula at k=64 (published check) and k=32 (five splits)."""
    P=k*L
    m=k.bit_length()-1
    assert k==2**m
    N=ceil(300/P)
    h=xm*(N*P-DATA["D_o_ns"]*ns)-2*J
    s=F(1,2)*c*(W-1); b=F(ENV["b"])
    def exp_hi(x):
        return F(ceil(10**18 / (1+x/64)**64),10**18)
    fast=xp*L+d
    amplitude=xp*(P-L)  # sum of half-widths at the m nodes
    def G(x):
        return fast+amplitude*exp_hi(s*h*x)
    maximum=F(0);left=b;pieces=0
    while left<B:
        right=min(B,2*left)
        width=(right-left)/32
        for j in range(32):
            a=left+j*width
            maximum=max(maximum,(a+width+b)*G(a))
        pieces+=32;left=right
    def omega(p):
        return d*(S2/(xm*p)+B**2+4*B*U)
    C=W*c*c/2
    profile=C*(T*b*b*G(b)+(S1-b*T)*maximum)
    repeat=C*(fast*omega(L)+sum(xp*2**(i-1)*L*omega(2**i*L) for i in range(1,m+1)))
    mass=B*xp*P
    qmax=(DATA["frame_ns"]*((W-1)//2)+DATA["word_slots_ns"][(W-1)%2])*ns
    kernel=mass/(1-exp_hi(s*mass))+B*xp*qmax
    rise=C*(1+1/F("2.71828")**2)*U*kernel*amplitude
    exact=delta+profile+repeat+rise
    q=F(ceil(exact*10**9),10**9)
    hold=(N+1)*(xp*P+2*J)
    hf=xm*L-2*J;hs=xm*P-2*J
    low=min(T,xp*L+J+hold*(1+2*W*c*S1))
    switches_hard=2*ceil(T/(xm*P-2*J))+4
    def ledger(stop):
        read=W*(2+T/hs+(1/hf-1/hs)*low)+stop*max_reads
        write=2*W*c*S1+stop*max_reads
        seconds=read_hi*read+write_hi*write
        return dict(reads=read,repairs=write,known_bus_s=seconds,bus_pct=100*seconds/T,
                    total_fast_s=min(T,low+stop*T),switches=ceil(1+4*W*c*S1+stop*switches_hard),
                    broad_extra_s=broad_half-seconds,paired_extra_s=paired_half-seconds)
    return dict(frame_multiple=k,splits=m,quiet_cells=N,history_lower_s=h,scalar_intervals=pieces,
                profile=profile,apertures=repeat,variation=rise,delta=delta,Qstop_upper=q,
                Qstop_d1e4=q+F(1,10000),budget_d0=ledger(q),budget_d1e4=ledger(q+F(1,10000)),
                bus_s_per_recognized_invalid=read_hi*W*(1/hf-1/hs)*hold)


def view(x):
    if isinstance(x,F):
        return dict(exact=str(x),estimate=float(x))
    if isinstance(x,dict): return {k:view(v) for k,v in x.items()}
    if isinstance(x,list): return [view(v) for v in x]
    return x


def staircase_price(half_floor):
    """Telescoping charge for the ten levels actually installed; no separate risk budget per level."""
    anchor=512*L
    levels=[2**m for m in range(10)]
    gaps=[xm*k*L-2*J for k in levels]
    thresholds=[ceil(((k*L/F("0.00168")+2*J)/xm+L)/anchor) for k in levels[1:]]
    mass=W*c*S1
    count=W*(2+T/gaps[-1])
    invalid_rate=F(0)
    low_times=[]
    for i,n in enumerate(thresholds):
        hold=(n+1)*(xp*anchor+2*J)
        budget=min(T,xp*L+J+hold*(1+2*mass))
        coefficient=W*(1/gaps[i]-1/gaps[i+1])
        count+=coefficient*budget
        invalid_rate+=coefficient*hold*read_hi
        low_times.append(budget)
    baseline=count*read_hi+2*mass*write_hi
    per_stop=max_reads*(read_hi+write_hi)
    return dict(history_cells=thresholds,pre_low_time_s=low_times,pre_known_bus_s=baseline,
                bus_s_per_invalid=invalid_rate,bus_s_per_unit_stop_probability=per_stop,
                conditional_known_if_Qstop_le_epsilon_I0=baseline+eps*per_stop,
                unknown_budget_if_Qstop_le_epsilon_I0=half_floor-baseline-eps*per_stop)


def calculate():
    broad=floor_price(False);paired=floor_price(True)
    frames=2+ceil((F(1,1000)+d+2*J)/(DATA["frame_ns"]*ns*xm))
    core=frames*2*(read_hi+write_hi)
    all_slot=core+frames*(40*ns*xp+2*J)+3*read_hi
    assert all_slot<F(8,10000) and fixed(1)["Q_upper"]<eps
    assert lower(2*L*xp,True)>eps
    # Unconditional deterministic lag envelope, valid even when the selected
    # gaps are history-dependent and there is no mandatory periodic slow anchor.
    def lag_bound(k):
        lag=k*L*xp+2*J+d
        return min(1,delta+F(W*39*38,D**2)*lag*S2)
    return view(dict(fixed={str(k):fixed(k) for k in (1,2,4)},broad_class=broad,
        binary_split={str(k):binary_dyadic(k,broad["half_lower_s"],paired["half_lower_s"]) for k in (32,64)},
        ladder_price=staircase_price(paired["half_lower_s"]),
        generic_max_lag_Q={str(k):lag_bound(k) for k in (32,64,128,512)},
        registered_ladder_mandatory_512_Q=fixed(512)["Q_upper"],
        exact_two_word_class=paired,registered={str(k):registered(k,broad["half_lower_s"],paired["half_lower_s"]) for k in (32,64)},
        peak_window_s=F(1,1000),peak_frames=frames,pure_protection_peak_percent=core*100000,
        all_reserved_plus_app_peak_percent=all_slot*100000,read_hard_cap=max_reads))


if __name__=="__main__":
    p=ArgumentParser(description=__doc__);p.add_argument("--check",action="store_true");a=p.parse_args()
    data=calculate();out=HERE/"bounds.json"
    text=json.dumps(data,indent=2)+"\n"
    if a.check: assert out.read_text(encoding="utf-8")==text
    else:out.write_text(text,encoding="utf-8",newline="\n")
    for k,r in data["fixed"].items(): print(k,r["Q_upper"]["estimate"],r["bus_upper_s"]["estimate"])
    for k in ("broad_class","exact_two_word_class"):
        print(k,data[k]["excluded_physical_P_ge_s"]["estimate"],data[k]["fixed_class_bus_lower_s"]["estimate"])
    for k,r in data["registered"].items():
        print("registered",k,r["old_Q_upper"]["estimate"],r["new_conservative_Q_upper"]["estimate"],
              r["bus_s_upper_at_I0"]["estimate"])

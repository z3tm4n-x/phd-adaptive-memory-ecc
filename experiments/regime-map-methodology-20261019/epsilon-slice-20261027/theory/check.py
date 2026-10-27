#!/usr/bin/env python3
"""Directed checks of one repeated family and the epsilon axis; no MC."""
from fractions import Fraction as F
from decimal import Decimal, localcontext, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path
from hashlib import sha256
import importlib.util
import json
import csv
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT / "experiments/hybrid-p-r-20261026/inputs.json"
COMMON = ROOT / "experiments/t186-method-comparison/code-strength/common-input.json"
INTERVALS = ROOT / "experiments/t114-two-stage-err/intervals.py"
BASE_HASH = "cc72a44914b0aa5547fe1e2b5a2a654c84573ab1c5fe6e35a4f4122831ec86c6"
raw = BASE.read_bytes().replace(b"\r\n", b"\n")
assert sha256(raw).hexdigest() == BASE_HASH
inp = json.loads(raw)
for p in (COMMON, INTERVALS):
    assert sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == inp["source_sha256"][p.relative_to(ROOT).as_posix()]
spec = importlib.util.spec_from_file_location("accepted_intervals", INTERVALS)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
I = mod.I
cfg = json.loads(COMMON.read_bytes())
e, fx = inp["proposed_environment"], inp["fixed"]
W,T = fx["words"],F(fx["mission_s"])
assert (W,T,fx["code"]) == (131072,315576000,[39,32,1])
assert fx["useful_writes"] == 0 and fx["initial_K0"] == 0
assert F(e["spatial"]["q"]) == F(e["spatial"]["chi"]) == F(1,W)
b,Ap,R,g,Fr,Fs,B = map(F,(
    e["background"],e["p"]["amplitude_above_background"],e["residual"]["cap_R"],
    e["residual"]["growth_g"],e["residual"]["mass_F_r"],e["total_solar_mass"],e["total_peak"]))
pm=b+Ap
assert B==pm+R and Fs==2*Fr
P=F(".025702")
J=F(cfg["service"]["operation_endpoint_span_ns"])/10**9
xm,xp=map(F,(cfg["service"]["clock_lower"],cfg["service"]["clock_upper"]))
block=F(25701088,10**9)
blo,bhi=block*xm,block*xp
assert bhi+J <= P
Kcell,m,eta = 24000,6,2
Hlo,Hhi=Kcell*blo,Kcell*bhi
Llo,Lhi=m*Hlo-2*J,m*Hhi+2*J
delta0=F(fx["lifetime_other_budget"])
deltaC_design=F("0.00005")  # retained conditional design limit, not measured evidence
mass=b*T+Fs/2+Fr
Ip2=b*b*T+b*Fs+Ap*Fs/3
Cp=Ip2+2*pm*Fr
S2=Cp+R*Fr
weak=B*P*mass/W
kappa_lower=F(".8646")
assert F((I(1)-I(-eta).exp()).lo)>kappa_lower

def ceil(x):
    return -((-x.numerator)//x.denominator)

N=ceil(T/Hlo)  # also covers startup shift, terminal partial cell and all queries
max_per_cell=lambda k:1+ceil(F(Kcell-2,k))
assert 2*blo-J>0 and blo>J  # first scan starts after the cell fence
assert Lhi+P < F(e["p"]["cycle_s"])-F(e["p"]["width_s"])
mu_p=b*(Lhi+P)+Ap*F(e["p"]["width_s"])/2
# Every time is in <=m+1 extended observation groups, at every fixed admissible clock.
assert P < Hlo
ql=inp["retained_quotas"]
false_mean=F(ql["ordinary_false_expected_per_s"])*T
loss_bad=F(ql["ordinary_outage_fraction"])*T/Hlo+(m+1)*ql["ordinary_loss_episodes_upper"]
false_bad=(m+1)*false_mean
Rbus=(48*xp+F(".5"))/10**9
Rcore=(68*xp+F(".5"))/10**9
Dwrite=(56*xp+F(".5"))/10**9
Dcore=56*xp/10**9
Rbuslo=(48*xm-F(".5"))/10**9
Rcorelo=(68*xm-F(".5"))/10**9
hard_reads=W*(ceil(T/(F(25690112,10**9)*xm-J))+2)
hard_bus=hard_reads*(Rbus+Dwrite)/T
hard_core=hard_reads*(Rcore+Dcore)/T

# One fixed profile pass, not an environment or period grid. Use integer ns/1e5.
# A cell is labelled quiet only if its entire physical clock envelope misses p's pulse.
den=100000
tickblock=25701088
left_ns=int(F(e["p"]["left_s"])*10**9)*den
width_ns=int(F(e["p"]["width_s"])*10**9)*den
cycle_ns=int(F(e["p"]["cycle_s"])*10**9)*den
ncycles=int(T/F(e["p"]["cycle_s"]))
quiet_cells=0
for j in range(N):
    ticks=tickblock*(1+j*Kcell)
    l=ticks*99999-50000
    z=(ticks+tickblock*Kcell)*100001+50000
    first=max(0,ceil(F(l-left_ns-width_ns,cycle_ns)))
    last=min(ncycles-1,(z-left_ns)//cycle_ns)
    if first>last:quiet_cells+=1
high_cells=N-quiet_cells

def exposure(u,k):
    nwin=m*max_per_cell(k)
    v=max(F(0),u-2*g*J)
    tail=max(F(0),v-g*Llo)
    return b*Llo+(v*v-tail*tail)/(2*g)-(b+u)*nwin*P

def poisson_tail_upper(mu,n):
    term=poly=I(1)
    for j in range(1,n):
        term=term*I(mu)/I(j);poly=poly+term
    z=I(1)-I(-mu).exp()*poly
    return max(F(0),F(z.hi))

def derivative_max_upper(n):
    # d/dmu Pr{Pois(mu)>=n}=Pr{Pois(mu)=n-1}, max at n-1.
    if n==1:return F(1)
    fact=1
    for j in range(1,n):fact*=j
    return F((I(-(n-1)).exp()*I(F((n-1)**(n-1),fact))).hi)

def froot(y,L,d):
    if y>=L*L:return F(0)
    a,z=F(0),L/d
    for _ in range(116):
        mid=(a+z)/2
        if max(F(0),L-d*mid)**2/(mid+1)>y:a=mid
        else:z=mid
    return a  # certified lower root

hr=R/g;plat=Fr/R-hr/2;Dur=hr+plat
dE=(124*xp+F("1.5"))/10**9
kap=I(F(38,78)*((b+R)/W)**2)*I(-B*plat/W).exp()
off_lb=F((I(1)-(I(0)-kap*I(W*plat*plat)).exp()-I(delta0)).lo)
assert plat>0 and Dur<T and off_lb>F(".1")

def rivals(eps):
    H=I(0)-I(1-eps-delta0).ln()  # no small-probability replacement
    target=H/(kap*I(W))
    xlo=froot(F(target.hi),plat,dE)
    ns=ceil(W*xlo*(T-Dur)/(plat+dE))
    nf=ns
    if xlo>1:
        nf=max(nf,ceil(W*((T-P)*(xlo-1)/(plat+dE)-1)))
    out=dict(off_Q_lower=off_lb,x_star_lower=xlo,scheduled_visits_lower=ns,
             fixed_visits_lower=nf,
             schedule_read_bus_lower=(1-delta0)*max(0,ns-2)*Rbuslo/T,
             constant_read_bus_lower=(1-delta0)*max(0,nf-2)*Rbuslo/T,
             constant_read_core_lower=(1-delta0)*max(0,nf-2)*Rcorelo/T,
             schedule_read_core_lower=(1-delta0)*max(0,ns-2)*Rcorelo/T)
    # Sufficient fixed batch-pass candidate; also a member of the full schedule class.
    rhs=2*W*(eps-delta0-weak)/S2
    k=int((rhs-J)/bhi) if rhs>J else 0
    method="cell-pair plus first-moment residual"
    if k<1:
        # Accepted A7/A8, with no observation or new delta_C: a fixed member.
        k=int(((eps-delta0)*W/S2-P-J)/bhi)
        if k<1:
            out.update(constant_candidate=None,reason="both displayed sufficient bounds fail; not impossibility")
            return out
        method="accepted PR271 A7/A8; counter disabled"
    a=k*bhi+J
    risk=delta0+(a+P)*S2/W if method.startswith("accepted") else delta0+weak+a*S2/(2*W)
    assert risk<=eps
    reads=W*(ceil(T/(k*blo-J))+2)
    repair=min(reads,2*mass+(risk-delta0)*reads)
    out.update(constant_candidate=dict(method=method,period_blocks=k,period_upper_s=a,Q_upper=risk,
       reads_upper=reads,known_bus_upper=(reads*Rbus+repair*Dwrite)/T+delta0*hard_bus,
       known_core_upper=(reads*Rcore+repair*Dcore)/T+delta0*hard_core,
       extra_controller_CPU_energy="parameters, not zero"),
       schedule_candidate="same retuned fixed member supplies a sufficient upper, not the schedule optimum")
    # Independent sufficient p-aware candidate. The lower-bound class is NOT this grid.
    ratio=(R+2*pm)/(R+2*b)
    rhsS=2*W*(eps-delta0-weak)/((R+2*pm)*Fr+ratio*Ip2)
    kfast=int((rhsS-J)/bhi) if rhsS>J else 0
    if kfast>=1:
        afast=kfast*bhi+J
        kslow=int((afast*ratio-J)/bhi)
        aslow=kslow*bhi+J
        assert kslow>=kfast and aslow*(R+2*b)<=afast*(R+2*pm)
        qs=delta0+weak+(aslow*Ip2+afast*(R+2*pm)*Fr)/(2*W)
        assert qs<=eps
        nr=W*(1+quiet_cells*ceil(F(Kcell,kslow))+high_cells*ceil(F(Kcell,kfast)))
        nw=min(F(nr),2*mass+(qs-delta0)*nr)
        us=(nr*Rbus+nw*Dwrite)/T+delta0*hard_bus
        out["p_schedule_candidate"]=dict(high_period_blocks=kfast,quiet_period_blocks=kslow,
              quiet_cells=quiet_cells,high_or_uncertain_cells=high_cells,Q_upper=qs,
              reads_upper=nr,known_bus_upper=us,
              price_controller="additional p-calendar work remains a parameter")
        out["schedule_known_upper"]=min(us,out["constant_candidate"]["known_bus_upper"])
        out["schedule_upper_selected_member"]="p-aware" if us<out["constant_candidate"]["known_bus_upper"] else "constant member"
    else:
        out["p_schedule_candidate"]=None
        out["schedule_known_upper"]=out["constant_candidate"]["known_bus_upper"]
        out["schedule_upper_selected_member"]="accepted A7/A8 constant member"
    return out

def tune(eps,c):
    alpha=eps/20
    log_up=F(I(F(N,1)/alpha).ln().hi)
    target=log_up+F(1,10**6)
    umax=R-g*Hhi
    def informative(k):
        return kappa_lower*exposure(umax,k)-eta*c>target
    if not informative(Kcell-2):
        return dict(status="UNCERTIFIED",reason="registered group's test has no nontrivial target")
    lo,hi=1,Kcell-2
    while hi-lo>1:
        mid=(lo+hi)//2
        if informative(mid):hi=mid
        else:lo=mid
    kmin=max(2,hi)
    def candidate(k):
        a,z=F(0),umax
        for _ in range(66):
            u=(a+z)/2
            if kappa_lower*exposure(u,k)-eta*c>target:z=u
            else:a=u
        # Round target upward to a rational decimal; this is the transmitted setting.
        u=F(ceil(z*10**12),10**12);U=u+g*Hhi
        ab=k*bhi+J
        ks=min(Kcell-2,int((ab*R/U-J)/bhi))
        assert ks>=k
        ar=ks*bhi+J
        assert ar*U<=ab*R and U<R
        pair=weak+(ar*Cp+ab*R*Fr)/(2*W)
        risk=delta0+deltaC_design+alpha+pair
        return dict(k_base=k,k_rare=ks,u=u,U=U,a_base_upper_s=ab,a_rare_upper_s=ar,
                    exposure_lower=exposure(u,k),log_score_lower=kappa_lower*exposure(u,k)-eta*c,
                    log_threshold_upper=log_up,pair_upper=pair,Q_upper_at_deltaC_design=risk)
    if weak+delta0+deltaC_design+alpha>=eps or candidate(kmin)["Q_upper_at_deltaC_design"]>eps:
        return dict(status="UNCERTIFIED",reason="new sufficient residual/budget bound fails; no impossibility claim",
                    alpha_total=alpha,residual_upper=weak,minimum_informative_k=kmin)
    lo,hi=kmin,Kcell-1
    while hi-lo>1:
        mid=(lo+hi)//2
        if candidate(mid)["Q_upper_at_deltaC_design"]<=eps:lo=mid
        else:hi=mid
    x=candidate(lo)
    assert x["log_score_lower"]>log_up
    assert x["a_base_upper_s"]>=2*P
    assert m*max_per_cell(lo)*P<Llo
    nb,nr=max_per_cell(x["k_base"]),max_per_cell(x["k_rare"])
    assert nb>=nr
    nparent=c//2+1  # C>c and C<=2N imply N>=floor(c/2)+1
    tp=poisson_tail_upper(mu_p,nparent)
    lip=derivative_max_upper(nparent)
    # Uniform over r: sum window residual means <=(m+1)*Fr, no law on r.
    qpath=alpha+x["pair_upper"]
    bad_count=min(F(N),N*tp+lip*(m+1)*Fr+loss_bad+false_bad+qpath*N)
    # z is the additional fraction of ineligible queries, kept symbolic.
    slow=min(F(N),m+bad_count)
    main0=W*(1+N*nr+slow*(nb-nr))
    main_max=W*(1+N*nb)
    repair=min(main_max,2*mass+qpath*main_max)
    U0=(main0*Rbus+repair*Dwrite)/T+delta0*hard_bus
    U0core=(main0*Rcore+repair*Dcore)/T+delta0*hard_core
    x.update(status="CONDITIONAL_CERTIFICATE",threshold=c,eta=eta,alpha_total=alpha,alpha_each=alpha/N,
        zeta_total=F(0),zeta_reason="new first-moment residual proof; not old quantile with zero probability",
        delta0=delta0,deltaC_design_cap=deltaC_design,
        deltaC_risk_allowable=eps-delta0-alpha-x["pair_upper"],
        risk_margin_at_design=eps-x["Q_upper_at_deltaC_design"],
        relative_risk_margin_at_design=(eps-x["Q_upper_at_deltaC_design"])/eps,
        cell_blocks=Kcell,history_cells=m,attempts_upper=N,
        baseline_passes_per_cell=nb,rare_passes_per_cell=nr,
        price_parent_tail_upper=tp,price_parent_tail_lipschitz=lip,
        priced_fallback_fraction_upper=slow/N,
        main_reads_upper_excluding_additional_invalid=main0,
        main_reads_hard_on_good_execution=main_max,
        main_repairs_upper=repair,
        bus_intercept_U0=U0,core_intercept_U0=U0core,
        bus_deltaC_coefficient=hard_bus,
        bus_additional_invalid_coefficient=W*N*(nb-nr)*Rbus/T,
        bus_guard_read_coefficient=(Rbus+Dwrite)/T,
        core_deltaC_coefficient=hard_core,
        core_additional_invalid_coefficient=W*N*(nb-nr)*Rcore/T,
        core_guard_read_coefficient=(Rcore+Dcore)/T,
        price_formula="U0 + hard_bus*delta_C + invalid_coefficient*z + guard_read_coefficient*G + bus_controller; CPU/energy separate",
        price_parameters={"delta_C":None,"z":None,"G_expected_additional_reads_all_memory_histories_on_Gexec":None,"bus_controller":None})
    return x

rows=[]
for eps in (F(".1"),F(".01"),F(".001"),F(".0001")):
    rv=rivals(eps); ad=tune(eps,4)
    if ad["status"]=="CONDITIONAL_CERTIFICATE":
        for name,key in (("schedule","schedule_read_bus_lower"),("constant","constant_read_bus_lower")):
            low=rv[key]
            ad[name+"_20pct_unpaid_allowance"]=F(".8")*low-ad["bus_intercept_U0"]
            ad[name+"_30pct_unpaid_allowance"]=F(".7")*low-ad["bus_intercept_U0"]
            ad[name+"_comparison"]="unknown until ALL nonnegative additions satisfy allowance" if low else "ratio undefined"
    rows.append(dict(epsilon=eps,input_override={"fixed.epsilon":str(eps)},rivals=rv,adaptive=ad))
# Keep the first registered c=6 diagnostic: same family, no new environment.
diagnostic6=[dict(epsilon=ep,adaptive=tune(ep,6)) for ep in (F(".1"),F(".01"),F(".001"))]
result=dict(status="AUTHOR_THEORY_AND_PARAMETER_GATE_NOT_FULL_COST_VICTORY",
    base_main="430ebe46c4be584e402bf64bcd98836d62bcfb08",
    plan_commit="06f9aa9bf3d0d8042c891f30e05dba546a30e2ae",
    canonical_input=BASE.relative_to(ROOT).as_posix(),canonical_input_sha256=BASE_HASH,
    checker_sha256=sha256(Path(__file__).read_bytes().replace(b"\r\n",b"\n")).hexdigest(),
    constants=dict(P_obs=P,H_lower=Hlo,H_upper=Hhi,L_lower=Llo,L_upper=Lhi,query_upper=N,
                   parent_mass=mass,p_squared=Ip2,S2=S2,residual_first_moment=weak,
                   hard_reads=hard_reads,hard_bus=hard_bus,hard_core=hard_core,known_parent_window_mu_upper=mu_p),
    rows=rows,first_registered_threshold6_diagnostic=diagnostic6,
    caveats=["fixed exogenous physical query fences / clock-epoch applicability requires #186 signoff",
             "extra E invalidates every affected group; its work and all bad histories are priced",
             "no law for C as Poisson; parent Poisson is used only in the PRICE upper",
             "no empirical quotas, mean savings or full-cost winner are inferred",
             "best of two sufficient schedule candidates is not the optimum of the full schedule class",
             "optional .0001 failure concerns this sufficient bound only"])
encoded=json.dumps(result,default=str,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
if "--write" in sys.argv:
    (HERE/"result.json").write_text(encoded,encoding="utf-8",newline="\n")
    with (HERE/"table.csv").open("w",encoding="utf-8",newline="") as fd:
        wr=csv.writer(fd,lineterminator="\n");wr.writerow(["epsilon","constant_read_lower_percent","schedule_read_lower_percent",
                                      "constant_candidate_known_upper_percent","schedule_selected_known_upper_percent","adaptive_U0_percent_PLUS_PARAMETERS","adaptive_status",
                                      "base_blocks","rare_blocks","Q_at_deltaC_design","allowance_20pct_schedule_fraction",
                                      "allowance_20pct_constant_fraction"])
        for row in rows:
            rv,ad=row["rivals"],row["adaptive"]
            fv=rv["constant_candidate"]
            def val(x,up=True,places=12):
                if x is None:return ""
                x=F(x)
                with localcontext() as ctx:
                    ctx.prec=80
                    return str((Decimal(x.numerator)/Decimal(x.denominator)).quantize(
                        Decimal(1).scaleb(-places),rounding=ROUND_CEILING if up else ROUND_FLOOR))
            wr.writerow([str(row["epsilon"]),val(100*rv["constant_read_bus_lower"],False),val(100*rv["schedule_read_bus_lower"],False),
                val(100*fv["known_bus_upper"]) if fv else "",
                val(100*rv["schedule_known_upper"]) if fv else "",
                val(100*ad["bus_intercept_U0"]) if "bus_intercept_U0" in ad else "",ad["status"],
                ad.get("k_base",""),ad.get("k_rare",""),val(ad.get("Q_upper_at_deltaC_design")),
                val(ad.get("schedule_20pct_unpaid_allowance"),False),val(ad.get("constant_20pct_unpaid_allowance"),False)])
    print("PASS: four epsilon points; exact/interval gates; JSON and CSV written with LF.")
else:
    print(encoded,end="")

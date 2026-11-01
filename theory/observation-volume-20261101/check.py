#!/usr/bin/env python3
"""T361: six prescribed substitutions, exact rationals / accepted intervals.

No import/execution of old research checkers, no Monte Carlo, no new grid.
Run without flags to verify saved result; --write writes only sibling result.json.
"""
from decimal import Decimal, localcontext, ROUND_CEILING, ROUND_FLOOR
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PV = "experiments/regime-map-methodology-20261019/predictability-volume-20261028/"
OLD = "experiments/regime-map-methodology-20261019/epsilon-slice-20261027/"
SOURCES = [PV + "inputs.json", PV + "resource-result.json", PV + "RESOURCE.md", PV + "THEORY.md",
           "experiments/hybrid-p-r-20261026/inputs.json",
           "experiments/t186-method-comparison/code-strength/common-input.json",
           "experiments/t114-two-stage-err/intervals.py",
           "theory/hybrid-epsilon-repeat-20261027.md",
           "theory/t196-count-error-price-20261027.md",
           "theory/hybrid-p-r-20261026.md", OLD + "theory/result.json",
           OLD + "cell-service/CONTRACT.md", OLD + "REVIEW_CELL_20261027.md"]

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def digest(path):
    return sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()

inp = read(PV + "inputs.json")
old = read("experiments/hybrid-p-r-20261026/inputs.json")
accepted = read(OLD + "theory/result.json")
resource = {r["words"]: r for r in read(PV + "resource-result.json")["rows"]}
interval_path = "experiments/t114-two-stage-err/intervals.py"
assert digest(interval_path) == old["source_sha256"][interval_path]
spec = importlib.util.spec_from_file_location("accepted_intervals", ROOT / interval_path)
iv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iv)
I = iv.I
T, W0, M, ETA = F(315576000), 131072, 6, 2
DELTA0, DELTAC = F(".000006"), F(".00005")
J, XM, XP = F(1, 2 * 10**9), F(".99999"), F("1.00001")
SCORE = F(".8646")
assert SCORE < F((I(1) - I(-ETA).exp()).lo)

def ceil(x):
    x = F(x)
    return -((-x.numerator) // x.denominator)

def decimal(x, up=True, places=12):
    with localcontext() as c:
        c.prec = 80
        y = F(x)
        return str((Decimal(y.numerator) / Decimal(y.denominator)).quantize(
            Decimal(1).scaleb(-places), rounding=ROUND_CEILING if up else ROUND_FLOOR))

def triangular_mass(length, cycle=F(5400), width=F(600)):
    """Exact max integral of periodic unit triangles over any interval."""
    q, rem = divmod(F(length), cycle)
    v = min(rem, width)
    return q * width / 2 + v - v * v / (2 * width)

def tail_upper(mu, n):
    term = poly = I(1)
    for j in range(1, n):
        term = term * I(mu) / I(j)
        poly = poly + term
    return min(F(1), max(F(0), F((I(1) - I(-mu).exp() * poly).hi)))

def lip_upper(n):
    if n == 1:
        return F(1)
    fact = 1
    for j in range(1, n):
        fact *= j
    return F((I(-(n - 1)).exp() * I(F((n - 1)**(n - 1), fact))).hi)

def lower_root(target, length, aperture):
    if target >= length * length:
        return F(0)
    low, high = F(0), length / aperture
    for _ in range(116):
        mid = (low + high) / 2
        if max(F(0), length - aperture * mid)**2 / (mid + 1) > target:
            low = mid
        else:
            high = mid
    return low

class Bank:
    def __init__(self, words):
        self.w, self.scale = words, F(words, W0)
        e = inp["environment"]
        self.refscale = F(39 * words, e["reference_positions"])
        ref_a = F(e["Fs"]) / (e["template"]["count"] * e["template"]["width_s"])
        self.b = self.refscale * F(e["b"])
        self.ap = self.refscale * ref_a
        self.B = self.refscale * F(e["B"])
        self.R = self.B - self.b - self.ap
        self.g = self.refscale * (F(e["rho"]) * F(e["ell"]) - ref_a / 300)
        self.Fr = self.refscale * F(e["Fs"]) / 2
        self.pm = self.b + self.ap
        self.mass = self.b * T + 2 * self.Fr
        self.ip = self.b**2 * T + 2 * self.b * self.Fr + 2 * self.ap * self.Fr / 3
        self.cp = self.ip + 2 * self.pm * self.Fr
        self.s2 = self.cp + self.R * self.Fr
        self.block = F(1568 * (words // 8 + 7), 10**9)
        old_block = F(25701088, 10**9)
        self.kcell = int(24000 * old_block / self.block)
        self.blo, self.bhi = self.block * XM, self.block * XP
        self.p = F(ceil((self.bhi + J) * 10**6), 10**6)
        self.hlo, self.hhi = self.kcell * self.blo, self.kcell * self.bhi
        self.llo, self.lhi = M * self.hlo - 2 * J, M * self.hhi + 2 * J
        self.n = ceil(T / self.hlo)
        self.nfull = max(0, int((T - self.bhi - J) / self.hhi))
        self.c = int(4 * self.scale)
        self.weak = self.B * self.p * self.mass / words
        self.mu_p = self.b * (self.lhi + self.p) + self.ap * triangular_mass(self.lhi + self.p)
        self.hard = words * (ceil(T / (F(196 * words, 10**9) * XM - J)) + 2)
        self.frame_slots = 8 * ceil((T+2*J)/(F(1568,10**9)*XM)) + 16
        assert self.frame_slots <= self.hard
        self.dE = (124 * XP + F("1.5")) / 10**9
        self.cost = {"bus": ((48 * XP + F(".5")) / 10**9,
                             (56 * XP + F(".5")) / 10**9,
                             (48 * XM - F(".5")) / 10**9),
                     "serial": ((68 * XP + F(".5")) / 10**9,
                                56 * XP / 10**9,
                                (68 * XM - F(".5")) / 10**9)}
        # Same last-word geometry at both W; this is NOT prefix/WCET evidence.
        last_anchor = 1568 * (words // 8 - 1) + 7 * 164
        self.scan_span_lower = last_anchor * XM / 10**9 - 2 * J
        self.release_slack = self.block * XM - (last_anchor * XM + 124 * XP) / 10**9 - 2 * J
        self.gate_budget = self.release_slack - F(10000, 10**9)
        assert self.blo > J and self.p+2*J < self.hlo and self.kcell > 2
        assert self.release_slack == F(".0000112708848")
        assert SCORE*self.b*self.llo-ETA*self.c < 0  # E3 root is on the increasing branch
        assert M * self.hlo <= M * 24000 * old_block * XM
        assert M * self.hlo > M * 24000 * old_block * XM - M * self.blo
        if words == W0:
            oe = old["proposed_environment"]
            assert (self.b, self.ap, self.R, self.g, self.Fr, self.B) == tuple(map(F, (
                oe["background"], oe["p"]["amplitude_above_background"],
                oe["residual"]["cap_R"], oe["residual"]["growth_g"],
                oe["residual"]["mass_F_r"], oe["total_peak"])))
            assert self.p == F(accepted["constants"]["P_obs"])
            assert self.mu_p == F(accepted["constants"]["known_parent_window_mu_upper"])

    def passes(self, k):
        return 1 + ceil(F(self.kcell - 2, k))

    def legal_k(self, k):
        return 2 <= k <= self.kcell - 2 and (self.kcell - 2) % k != 1

    def round_k(self, k):
        while k >= 2 and not self.legal_k(k):
            k -= 1
        return k

    def duration(self, k):
        return max(2 * self.p, k * self.bhi + J)

    def exposure(self, u, k):
        v = max(F(0), u - 2 * self.g * J)
        tail = max(F(0), v - self.g * self.llo)
        return self.b * self.llo + (v*v - tail*tail) / (2*self.g) - (self.b+u)*M*self.passes(k)*self.p

    def common(self, x):
        app = resource[self.w]["application"]
        prefix = "pure_bus" if x == "bus" else "serial"
        ticks = 56 if x == "bus" else 76
        low = F(app[prefix + "_mission_lower"]) + self.w * (ticks * XM - F(".5")) / 10**9 / T
        high = F(app[prefix + "_mission_upper"]) + self.w * (ticks * XP + F(".5")) / 10**9 / T
        return low, high

    def rivals(self, eps):
        hr = self.R / self.g
        plat = self.Fr / self.R - hr / 2
        dur = hr + plat
        assert plat > 0 and dur < T
        kap = I(F(38, 78) * ((self.b+self.R)/self.w)**2) * I(-self.B*plat/self.w).exp()
        entropy = I(0) - I(1-eps-DELTA0).ln()
        xlo = lower_root(F((entropy/(kap*I(self.w))).hi), plat, self.dE)
        ns = ceil(self.w * xlo * (T-dur) / (plat+self.dE))
        nf = max(ns, ceil(self.w*((T-self.p)*(xlo-1)/(plat+self.dE)-1))) if xlo>1 else ns
        off = F((I(1) - (I(0)-kap*I(self.w*plat*plat)).exp() - I(DELTA0)).lo)
        out = dict(ramp_s=hr, plateau_s=plat, duration_s=dur, x_star_lower=xlo,
                   off_Q_lower=off, visits_lower={"schedule":ns,"constant":nf}, costs={})
        out["all_slot_reads_upper"]=self.hard
        out["good_execution_frame_slots_upper"]=self.frame_slots
        out["expected_reads_lower"]={j:(1-DELTA0)*max(0,n-2)
                                     for j,n in (("schedule",ns),("constant",nf))}
        out["excluded_with_inherited_all_slot_contract"]={j:v>self.hard
                                                          for j,v in out["expected_reads_lower"].items()}
        for x,(r,d,rlo) in self.cost.items():
            common_lo, _ = self.common(x)
            out["costs"][x] = {j:{"protection_lower":(1-DELTA0)*max(0,n-2)*rlo/T,
                                   "with_common_lower":(1-DELTA0)*max(0,n-2)*rlo/T+common_lo}
                                for j,n in (("schedule",ns),("constant",nf))}
        # This is an existence witness, not a rival optimum. Old E8 first.
        rhs = 2*self.w*(eps-DELTA0-self.weak)/self.s2
        k = int((rhs-J)/self.bhi) if rhs>J else 0
        if k >= 1:
            q = DELTA0+self.weak+(k*self.bhi+J)*self.s2/(2*self.w)
            out["constant_member"] = dict(basis="E8",period_blocks=k,Q_upper=q)
        else:
            out["constant_member"] = None
            out["nonemptiness_status"] = "not established by E8; class NOT excluded"
            # One pre-existing physical certificate, no period search: fixed block 1.
            a=self.bhi+J
            q=DELTA0+F(38,39)*((a+self.dE)*self.s2+2*self.B*self.dE*self.mass)/(2*self.w)
            out["physical_fixed_block1_Q_upper"]=q
            if q<=eps:
                out["constant_member"]=dict(basis="predictability-volume THEORY(11); fixed block 1; no own count",
                                            period_blocks=1,Q_upper=q)
                out["nonemptiness_status"]="sufficient physical fixed member; not adaptive E5"
        if any(out["excluded_with_inherited_all_slot_contract"].values()):
            assert out["constant_member"] is None
            out["nonemptiness_status"]="excluded under inherited slot/hard-cap contract by lower count; not by failed upper"
        return out

    def tune(self, eps):
        alpha = eps/20
        log = F(I(F(self.n)/alpha).ln().hi)
        target = log+F(1,10**6)
        umax = self.R-self.g*self.hhi
        floor_risk = DELTA0+DELTAC+alpha+self.weak
        initial = dict(alpha_total=alpha, delta0=DELTA0, deltaC_design=DELTAC,
                       residual_upper=self.weak, sufficient_expression_floor=floor_risk,
                       P_obs_needed_from_residual_budget=(eps-DELTA0-DELTAC-alpha)*self.w/(self.B*self.mass))
        # Stop before tuning if the nonnegative E4 term alone prevents E5.
        if floor_risk >= eps:
            return dict(initial,status="E5_UNRESOLVED",reason="E4 term exhausts E5 at every period; not a lower physical Q")
        if umax<=0 or SCORE*self.exposure(umax,self.kcell-2)-ETA*self.c<=target:
            return dict(initial,status="E3_UNRESOLVED",reason="no nontrivial endpoint in this sufficient E3 test")
        low, high = 1,self.kcell-2
        while high-low>1:
            mid=(low+high)//2
            if SCORE*self.exposure(umax,mid)-ETA*self.c>target: high=mid
            else: low=mid
        kmin=max(2,high)
        eligible=[k for k in range(kmin,self.kcell-1) if self.legal_k(k)]

        def candidate(k):
            a,z=F(0),umax
            for _ in range(66):
                u=(a+z)/2
                if SCORE*self.exposure(u,k)-ETA*self.c>target: z=u
                else: a=u
            u=F(ceil(z*10**12),10**12)
            U=u+self.g*self.hhi
            ab=self.duration(k)
            ks=self.round_k(min(self.kcell-2,int((ab*self.R/U-J)/self.bhi)))
            if ks<k or U>=self.R:
                return None
            ar=self.duration(ks)
            assert ar*U<=ab*self.R
            pair=(ar*self.cp+ab*self.R*self.Fr)/(2*self.w)
            return dict(k_base=k,k_rare=ks,u=u,U=U,U_over_R=U/self.R,
                        u_reference=u/self.refscale,a_base_upper_s=ab,a_rare_upper_s=ar,
                        exposure_lower=self.exposure(u,k),log_score_lower=SCORE*self.exposure(u,k)-ETA*self.c,
                        log_threshold_upper=log,pair_within_upper=pair,Q_upper=floor_risk+pair)

        # Candidates' periods and Q upper are nondecreasing in k; only one scalar bisection.
        first=candidate(eligible[0]) if eligible else None
        if first is None or first["Q_upper"]>eps:
            return dict(initial,status="E3_E5_UNRESOLVED",reason="no certified overlap by registered scalar criterion",minimum_informative_k=kmin)
        low,high=0,len(eligible)
        while high-low>1:
            mid=(low+high)//2
            c=candidate(eligible[mid])
            if c is not None and c["Q_upper"]<=eps: low=mid
            else: high=mid
        k=eligible[low]
        c=candidate(k)
        if c is None or c["log_score_lower"]<=log or c["Q_upper"]>eps:
            return dict(initial,status="ROUNDING_UNRESOLVED",reason="registered integer tail restriction did not close")
        assert self.legal_k(k) and self.legal_k(c["k_rare"])
        nb,nr=self.passes(k),self.passes(c["k_rare"])
        nparent=self.c//2+1
        tail,lip=tail_upper(self.mu_p,nparent),lip_upper(nparent)
        qpath=alpha+self.weak+c["pair_within_upper"]
        loss=F(".0001")*T/self.hlo+(M+1)*1001
        false=(M+1)*F(".000001")*T
        d0=min(F(self.n),self.n*tail+lip*(M+1)*self.Fr+loss+false+self.n*qpath)
        fallback=min(F(self.n),M+d0)
        main=self.w*(1+self.n*nr+fallback*(nb-nr))
        maximum=self.w*(1+self.n*nb)
        repairs=min(maximum,2*self.mass+qpath*maximum)
        rare=max(F(0),F(self.nfull-M)-d0-self.n*(DELTA0+DELTAC))
        c.update(initial)
        c.update(status="CONDITIONAL_MATH_TEST_ONLY",implementation_confirmed=False,
                 risk_margin=eps-c["Q_upper"],deltaC_max=eps-DELTA0-alpha-self.weak-c["pair_within_upper"],
                 baseline_passes=nb,rare_passes=nr,first_eligible_fence_upper_s=self.bhi+M*self.hhi+J,
                 history_parent_mu_p_upper=self.mu_p,parent_tail_upper=tail,parent_tail_lipschitz=lip,
                 D0_upper=d0,priced_fallback_fraction_upper=fallback/self.n,
                 expected_rare_full_cells_lower_before_extra_z=rare,
                 rare_fraction_lower_before_extra_z=rare/self.n,
                 main_reads_upper=main,main_reads_maximum=maximum,main_repairs_upper=repairs,
                 bits_for_main_ERR_count_without_false_or_extra=(self.w*nb).bit_length(),
                 bits_for_six_main_counts=(M*self.w*nb).bit_length(),costs={})
        for x,(r,d,_) in self.cost.items():
            hard=self.hard*(r+d)/T
            cb=maximum*(r+d)/T
            u0=(main*r+repairs*d)/T+DELTA0*hard
            common_lo,common_up=self.common(x)
            v=u0+cb*DELTAC
            c["costs"][x]=dict(U0=u0,C_b=cb,V_at_deltaC_design=v,with_common_upper=v+common_up,
                                A_z=self.w*self.n*(nb-nr)*r/T,A_G_rate=r+d,
                                C_escape=hard-cb,common_lower=common_lo,common_upper=common_up,
                                actual_extra_processing=None)
        return c

def calculate():
    banks=[]
    for w in (W0,8*W0):
        b=Bank(w)
        long_history=M*24000*b.bhi+2*J+b.p
        geom=dict(words=w,bank_scale=b.scale,reference_scale=b.refscale,cell_blocks=b.kcell,
                  history_cells=M,count_threshold=b.c,scan_nominal_s=F(196*w,10**9),
                  block_nominal_s=b.block,P_obs=b.p,H_lower=b.hlo,H_upper=b.hhi,
                  history_lower_s=b.llo,history_upper_s=b.lhi,attempts_upper=b.n,
                  completed_cells_lower=b.nfull,bank_parent_mass=b.mass,known_p_squared=b.ip,
                  residual_first_moment=b.weak,release_to_fence_lower_s=b.release_slack,
                  scan_span_lower_s=b.scan_span_lower,
                  E4_at_scan_span_lower=b.B*b.scan_span_lower*b.mass/w,
                  final_gate_budget_after_10us_s=b.gate_budget,
                  fixed_24000_history_upper_s=long_history,
                  fixed_24000_triangle_mass_units=triangular_mass(long_history),
                  chosen_history_triangle_mass_units=triangular_mass(b.lhi+b.p))
        rows=[]
        for eps in (F(".1"),F(".01"),F(".001")):
            rival,ad=b.rivals(eps),b.tune(eps)
            if "costs" in ad:
                for x,v in ad["costs"].items():
                    v["strict_full_cost_budget"]={j:rival["costs"][x][j]["with_common_lower"]-v["with_common_upper"]
                                                   for j in ("schedule","constant")}
                    v["strict_protection_cost_budget"]={j:rival["costs"][x][j]["protection_lower"]-v["V_at_deltaC_design"]
                                                         for j in ("schedule","constant")}
            rows.append(dict(epsilon=eps,adaptive=ad,rivals=rival))
        banks.append(dict(geometry=geom,rows=rows))
    # Required control: the unchanged small bank recovers the accepted three rows.
    for row, saved in zip(banks[0]["rows"],accepted["rows"][:3]):
        a,old_a=row["adaptive"],saved["adaptive"]
        for new_key,old_key in (("k_base","k_base"),("k_rare","k_rare"),("u","u"),
                                ("Q_upper","Q_upper_at_deltaC_design"),
                                ("main_reads_upper","main_reads_upper_excluding_additional_invalid")):
            assert F(a[new_key])==F(old_a[old_key]),(new_key,row["epsilon"])
        for x,old_name in (("bus","bus"),("serial","core")):
            assert a["costs"][x]["U0"]==F(old_a[old_name+"_intercept_U0"])
            for rival in ("schedule","constant"):
                assert row["rivals"]["costs"][x][rival]["protection_lower"]==F(
                    saved["rivals"][rival+"_read_"+old_name+"_lower"])
    return dict(task=361,scientific_base="d43aecf7e18b29e2b7b0c9d03382b326e41c4174",
                base_main="de80ad2fcd274d749923a94f24adf144cc67bab6",
                pre_calculation_plan_commit="79bce79",alpha=F(1,2),mission_s=T,
                sources_sha256_LF={p:digest(p) for p in SOURCES},
                checker_sha256_LF=digest(Path(__file__).relative_to(ROOT)),banks=banks,
                status="conditional mathematical transfer; no full cost or implementation acceptance")

def summarize(result):
    for b in result["banks"]:
        g=b["geometry"]
        print("W",g["words"],"K",g["cell_blocks"],"P_obs",decimal(g["P_obs"]),
              "history",decimal(g["history_upper_s"]),"E4",decimal(g["residual_first_moment"]))
        for row in b["rows"]:
            a=row["adaptive"]
            print(" eps",row["epsilon"],a["status"],"E5 floor",decimal(a["sufficient_expression_floor"]))
            if "costs" in a:
                print(" k",a["k_base"],a["k_rare"],"Q",decimal(a["Q_upper"]),"U/R",decimal(a["U_over_R"]),
                      "rare fraction lower",decimal(a["rare_fraction_lower_before_extra_z"],False))
                for x,c in a["costs"].items():
                    print(" ",x,"V us/s",decimal(10**6*c["V_at_deltaC_design"]),"full-cost margin S/F us/s",
                          {j:decimal(v*10**6,False) for j,v in c["strict_full_cost_budget"].items()})

if __name__=="__main__":
    result=calculate()
    encoded=json.dumps(result,default=str,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    dest=HERE/"result.json"
    if "--write" in sys.argv:
        dest.write_text(encoded,encoding="utf-8",newline="\n")
    else:
        assert dest.read_text(encoding="utf-8")==encoded,"saved result differs"
    summarize(result)
    print("PASS: six registered substitutions; directed arithmetic; old sources read-only.")

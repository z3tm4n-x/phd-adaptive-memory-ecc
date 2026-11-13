"""Apply the registered PR 484 one-factor comparisons on the selected volume."""
import argparse
import json
from dataclasses import replace
from fractions import Fraction as F
from functools import cache
from math import ceil, floor
from pathlib import Path
from replay import MODEL as M, RULE, W


HERE = Path(__file__).resolve().parent
EXP = HERE.parent
Profile = M["REVIEW"]["Profile"]
T,C,DELTA,B0,XP,J,DE = (M[k] for k in ("T","C","DELTA","B0","XP","J","DE"))
GEO,up,down = M["GEO"],M["up"],M["down"]
EPS = F(1,1000)
PARENTS = M["PARENTS"]
HARD_FEE = (M["READ"]+M["WRITE"])*M["HARD"]


class BackgroundLadder(M["Ladder"]):
    """Only the scalar construction in (1) #473 depends explicitly on the floor b."""
    @cache
    def risk(self,eta,env):
        delta,_,phase,rises = super().risk(eta,env)
        b = tabulated()["b"]
        scale = self.words*C*eta
        def kernel(x):
            return self.fast+sum(a*M["weight"](scale*h*x) for a,h in zip(self.amplitude,self.history))
        left, slope = b, F(0)
        while left<env.peak:
            right = min(env.peak,2*left)
            step = (right-left)/32
            for i in range(32):
                x = left+i*step
                slope = max(slope,(x+step+b)*kernel(x))
            left = right
        scalar = T*b*b*kernel(b)+(env.exposure-b*T)*slope
        return delta,self.words*C**2/2*scalar,phase,rises


@cache
def tabulated():
    src = json.loads((EXP/"t186-ost-geo-3g/result.json").read_bytes(),parse_float=F)
    a,tab = src["archive"],src["ost_tabulated"]
    b, k = tab["b"],a["excess_multiplier"]
    excess = k*(GEO.exposure-B0*T)
    B = max(tab["B"],b+k*(GEO.peak-B0))
    S1, U = b*T+excess,k*GEO.rise
    observed = a["archives_on_transferred_profiles"]
    # The #423 exposure quota is an explicit design choice. A sub-bin start can
    # replace 300 s of exposure; cover the separate registered #459 edge bound.
    S1 = max(S1,observed["SEPEM_archive"]["S1_any_start_upper"])
    S2 = b*b*T+(B+b)*(S1-b*T)
    for r in observed.values():
        assert r["S1_on_accepted_windows_or_gap_completion"]<=S1
        assert r["peak_of_transferred_construction"]<=B
        assert r["J_in_old_background_coordinates"]-(b-B0)<=U
        assert r["max_upward_slope_inside_bins"]<=k*F("0.004392116")+F(1,10**12)
    dur = (S1-b*T)/(B-b)
    assert b>B0 and B-b<=U and 1<dur<T
    return {"b":b,"B":B,"S1":S1,"S2":S2,"U":U,"g":k*F("0.004392116"),"k":k,
            "plateau_s":dur,"affine_cap":b*T+excess,"shifted_archive_cap":observed["SEPEM_archive"]["S1_any_start_upper"]}


def ost_floor(b,env,eps):
    # The witness starts at *this* peak and drops to *this* background.
    peak, u = env.peak, env.peak-b
    t_high = (env.exposure-b*T)/u
    second = floor(t_high*peak**2+(T-t_high)*b*b)
    assert 0 < t_high < T and u<=env.rise and second<=env.second
    mean = M["MEAN"]
    a = PARENTS["overlap_success"]("compact_1p2",W)
    def lower(cap):
        p = F(cap,W)
        mask = RULE.fast/p
        mass = 2*cap*C*peak/mean
        loss = RULE.fast*(peak**2+4*peak*u)+(1+4*p)*peak**2+p*peak*u
        rem = (1-mask)**2*second-loss
        if mask>=1 or mass>=1 or rem<=0:
            return F(0)
        z = (1-mass)*C*C*cap*a*rem/(2*mean**2)
        return max(F(0),z/(1+z)-DELTA)
    lo,hi = 0,ceil(2*W*RULE.fast)
    while lower(hi)<=eps:
        lo,hi = hi,2*hi
        assert 2*hi*C*peak<mean
    while hi-lo>1:
        mid = (hi+lo)//2
        if lower(mid)>eps:
            hi = mid
        else:
            lo = mid
    p = F(hi,W)
    seconds = (1-DELTA)*RULE.scan.addresses*M["READ_LO"]*(T/(p+2*J)-2)
    return dict(class_empty=False,s_lower=down(seconds,3),K_word_s=hi,
                exclusion_Q_lower=down(lower(hi),15),plateau_s=str(t_high),plateau_S2_lower=second)


def sufficient(env,eps,extra):
    q = M["physical"]
    L, frame = RULE.scan.L,M["FRAME"]
    q0 = q(RULE.scan,W,L,env=env)
    assert q0<=eps
    slope = W*C**2*F(37,76)*XP*env.second*frame
    p = L+frame*floor((eps-q0)/slope)
    assert q(RULE.scan,W,p,env=env)<=eps<q(RULE.scan,W,p+frame,env=env)
    _,candidate = M["fixed_price"](RULE,p,env)
    candidate["s_upper_with_direct"] = up(F(candidate["s_upper"])+extra,3)
    return candidate


def comparison(name,env=GEO,eta=RULE.eta,allocation=EPS,direct=F(0),total=None,ost=False):
    rule = BackgroundLadder(W) if ost else RULE
    fee,q = rule.cost(env,M["MEAN"],eta)
    if total is None:
        total = allocation+direct
    assert total==allocation+direct
    # A bound on a new independent/direct process does not force it to occur.
    # The necessary witness uses the permitted zero-direct member of this class.
    fixed = ost_floor(tabulated()["b"],env,total) if ost else M["fixed_floor"](RULE,total)
    allocated_floor = None
    if direct:
        allocated_floor = M["fixed_floor"](RULE,allocation)["s_lower"]
    extra = HARD_FEE*direct
    fixed["candidate"] = sufficient(env,allocation,extra)
    fixed["candidate"]["q_plus_direct_upper"] = up(F(fixed["candidate"]["physical_Q_upper"])+direct,12)
    ladder_s = F(fee["s_upper"])+extra
    f_low = F(fixed["s_lower"])
    margin = f_low/2-ladder_s
    eligible = q<=allocation and q+direct<=total
    return {"name":name,"allocation":str(allocation),"direct_upper":str(direct),"total":str(total),
            "eta":str(eta),"B":str(env.peak),"U":str(env.rise),"S1":str(env.exposure),"S2":str(env.second),
            "q_ladder_upper":up(q,12),"q_plus_direct_upper":up(q+direct,12),"ladder_pass":eligible,
            "ladder_before_direct_s_upper":fee["s_upper"],"q_parts":fee["q_terms_upper"],
            "additional_direct_tail_s_upper":up(extra,3),"ladder_s_upper":up(ladder_s,3),
            "ladder_pct_upper":up(100*ladder_s/T,6),"fixed":fixed,"componentwise_fixed_lower_s":allocated_floor,
            "twofold_margin_s_lower":down(margin,3),
            "twofold_resets_X0":floor(margin/F(fee["reset_fee_s_upper"])) if eligible and margin>=0 else None,
            "factor_lower_if_admissible":down(f_low/ladder_s,6) if eligible else None}


def result():
    t = tabulated()
    env = Profile(t["B"],t["U"],t["S1"],t["S2"])
    eta = RULE.threshold(EPS,GEO)
    rows = [comparison("COSRAD"),comparison("OST",env,ost=True),
            comparison("3U",replace(GEO,rise=3*GEO.rise)),comparison("10U",replace(GEO,rise=10*GEO.rise)),
            comparison("eta_sufficient",eta=F(eta["pass"])),comparison("eta_adjacent",eta=F(eta["fail"])),
            comparison("direct_separate",direct=F(1,10000)),
            comparison("direct_shared",allocation=F(9,10000),direct=F(1,10000),total=EPS)]
    accepted = json.loads((EXP/"t186-native-cost-map/result.json").read_bytes())
    base = next(r for r in accepted["rows"] if r["scope"]=="geo" and r["words"]==W and r["law"]=="compact_1p2"
                and F(r["epsilon"])==EPS)
    assert rows[0]["fixed"]["s_lower"]==base["fixed"]["s_lower"]
    assert rows[0]["ladder_before_direct_s_upper"]==base["ladder"]["s_upper"]
    assert rows[0]["q_ladder_upper"]==base["ladder"]["q"]
    assert rows[0]["fixed"]["candidate"]["s_upper"]==base["fixed"]["candidate"]["s_upper"]
    q1 = sum(RULE.risk(RULE.eta,GEO))
    q3 = sum(RULE.risk(RULE.eta,replace(GEO,rise=3*GEO.rise)))
    threshold_u = 1+2*(EPS-q1)/(q3-q1)
    assert sum(RULE.risk(RULE.eta,replace(GEO,rise=threshold_u*GEO.rise)))==EPS
    # Cost guarantees for direct effects require the same residual word rates,
    # valid history, and a hard cap through T. No independence is needed for the union.
    return {"ost_class":{k:str(v) for k,v in t.items()},"hard_post_stop_port_s":up(HARD_FEE,6),
            "baseline_threshold":eta,"U_multiplier_passing_lower":down(threshold_u,9),
            "U_multiplier_failing_upper":up(threshold_u,9),"rows":rows}


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    args = parser.parse_args()
    data = result()
    path = HERE/"sensitivity.json"
    if args.check:
        assert data==json.loads(path.read_bytes())
    else:
        path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")
    for row in data["rows"]:
        print(row["name"],row["q_ladder_upper"],row["ladder_s_upper"],row["fixed"]["s_lower"],
              row["factor_lower_if_admissible"],row["twofold_margin_s_lower"])

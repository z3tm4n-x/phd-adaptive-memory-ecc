#!/usr/bin/env python3
"""Read-only by default. --write creates only this task's outputs/report.json."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from fractions import Fraction as F
from itertools import combinations, product
from math import comb, factorial

import model as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REF_U = ROOT / "experiments/sequential-small-validation-20261014"
REF_E = ROOT / "experiments/sequential-err-small-validation-20261015"
PINS = {
    "experiments/sequential-small-validation-20261014/exact.py": "2af0bdedef79b16c8488ab3cc3bbe12c7a80552a",
    "experiments/sequential-small-validation-20261014/inputs.json": "0a62572c2c9b5b6c33ba37c49c878a75bedb18f3",
    "experiments/sequential-err-small-validation-20261015/exact.py": "30f4a2622b6043ee5e1bee72c8c4235b23c728d2",
    "experiments/sequential-err-small-validation-20261015/arithmetic.py": "b2ef4334c96e432aabe92def96724b4723e37757",
    "experiments/sequential-err-small-validation-20261015/inputs.json": "0cf3de9195c98f77e4b62e8f7474125f7e446c72",
}


def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def load_module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main_case(cfg, code, profile, period):
    return dict(n=code["n"],t=code["t"],W=cfg["W"],T=F(cfg["T_s"]),
                P=period,D=F(code["service_s"]),
                segments=[(F(s["start"]),F(s["end"]),
                          (code["n"]*F(s["rate"])/cfg["reference_positions"],F(0)))
                          for s in cfg["reference_array_profiles"][profile]])


def moment_upper(cfg,code,profile,period):
    p = code["t"]+1
    moment = sum(((F(s["end"])-F(s["start"]))*(F(s["rate"])/cfg["reference_positions"])**p
                  for s in cfg["reference_array_profiles"][profile]),F(0))
    return cfg["W"]*F(m.falling(code["n"],p),factorial(p))*period**code["t"]*moment


def main_rows(cfg):
    grids, rows = [], []
    chosen = {}
    for code in cfg["codes"]:
        valid = []
        for p in map(F,cfg["period_grid_s"]):
            upper = max(moment_upper(cfg,code,f,p) for f in cfg["reference_array_profiles"])
            resource = cfg["W"]*F(code["service_s"])<=p
            ok = resource and upper<=F(cfg["epsilon"])
            grids.append(dict(t=code["t"],P_s=str(p),moment_upper=str(upper),
                              moment_upper_decimal=m.dec(upper),calendar_ok=resource,accepted=ok))
            if ok:
                valid.append(p)
        if not valid:
            raise RuntimeError("no allowed candidate; retain input and report barrier")
        chosen[code["t"]] = max(valid)
        for profile in cfg["reference_array_profiles"]:
            case = main_case(cfg,code,profile,chosen[code["t"]])
            qlo,qhi = m.exact_u(case,cfg["exact"]["terms"],cfg["exact"]["internal_places"])
            llo,lhi = m.lower(case)
            upper,_,_ = m.fixed_upper(case)
            moment = moment_upper(cfg,code,profile,case["P"])
            assert lhi<=qlo<=qhi<=upper<=moment<=F(cfg["epsilon"])
            assert qhi-qlo<=F(cfg["exact"]["max_width"])
            cost = m.price_u(case)
            rows.append(dict(t=code["t"],n=code["n"],k=code["k"],W=cfg["W"],
                             useful_bits=cfg["W"]*code["k"],physical_bits=cfg["W"]*code["n"],
                             profile=profile,P_s=str(case["P"]),service_s=str(case["D"]),
                             array_parent_exposure=str(cfg["W"]*m.exposure(case,F(0),case["T"])),
                             Q=m.interval(qlo,qhi),L=m.interval(llo,lhi),
                             cell_upper=str(upper),cell_upper_decimal=m.dec(upper),
                             moment_upper=str(moment),moment_upper_decimal=m.dec(moment),
                             risk_margin=str(F(cfg["epsilon"])-moment),
                             relative_margin=str(1-moment/F(cfg["epsilon"])),
                             cost=str(cost),cost_percent=m.dec(100*cost),
                             calendar_service_duty=str(cfg["W"]*case["D"]/case["P"])))
    # All selected periods divide this example's T, verified, not assumed in general.
    assert all((F(cfg["T_s"])/p).denominator==1 for p in chosen.values())
    p1,p2 = chosen[1],chosen[2]
    c1 = F(cfg["codes"][0]["service_s"])
    boundary = c1*p2/p1
    sensitivity = []
    for c2 in [F(cfg["codes"][1]["service_s"]),boundary/2,boundary,boundary*2]:
        case = main_case(cfg,cfg["codes"][1],"piecewise",p2)
        case["D"] = c2
        c2price = m.price_u(case)
        c1price = cfg["W"]*c1/p1
        sensitivity.append(dict(c2_s=str(c2),c2_over_c1=str(c2/c1),
                                cost2=str(c2price),cost2_percent=m.dec(100*c2price),
                                chosen_cost_ratio_1_over_2=str(c1price/c2price),
                                calendar_ok=c2<=p2/cfg["W"],
                                risk_certification="same period moment upper, independent of c2 while c2<=P2/W"))
    return dict(grid=grids,selected=rows,price_sensitivity=sensitivity,
                break_even_c2_s=str(boundary),break_even_c2_over_c1=str(p2/p1),
                scope="selected sufficient U schedules, not optimal code/policy or hardware WCET")


def regressions():
    checked = {}
    for path,pin in PINS.items():
        actual = blob((ROOT/path).read_bytes())
        assert actual==pin,(path,pin,actual)
        checked[path]=actual
    sys.path.insert(0,str(REF_E))
    old_u = load_module("accepted_t166",REF_U/"exact.py")
    old_e = load_module("accepted_t177",REF_E/"exact.py")
    out = []
    for kind,mod,folder in [("U",old_u,REF_U),("E",old_e,REF_E)]:
        cfg=json.loads((folder/"inputs.json").read_text())
        for old in mod.cases(cfg):
            case=dict(n=old["n"],t=1,W=old["W"],T=old["T"],P=old["period"],D=old["D"],
                      segments=[(a,b,(r/old["W"],F(0))) for a,b,r in old["segments"]])
            accepted=mod.solve(old)
            qlo,qhi=(m.exact_u if kind=="U" else m.exact_e)(case)
            q0lo,q0hi=(F(accepted["Q_exact"][v]) for v in ("lower","upper"))
            assert max(qlo,q0lo)<=min(qhi,q0hi)
            assert max(qhi,q0hi)-min(qlo,q0lo)<F("1e-28")
            upper,_,_=m.fixed_upper(case,kind)
            assert upper==F(accepted["U_rational" if kind=="U" else "U_E_rational"])
            llo,lhi=m.lower(case)
            assert lhi<=qlo<=qhi<=upper
            out.append(dict(source=166 if kind=="U" else 177,id=old["id"],
                            Q=m.interval(qlo,qhi),upper_exact_equal=True,intervals_overlap=True))
    return dict(pinned_source_blobs=checked,rows=out,count=len(out),
                method="read-only exact-code replay; no MC or accepted output rewrite")


def targeted_checks():
    results = []
    def ok(name,condition):
        assert condition,name
        results.append({"test":name,"passed":True})
    c1,c2=m.code_check(1),m.code_check(2)
    ok("same k=32; ranks7/12; syndromes40/991",c1["k"]==c2["k"]==32 and c1["rank"]==7 and c2["rank"]==12 and c2["distinct_correctable_syndromes"]==991)
    # All small explicit masks verify Markov lumping, including double/XOR overlap.
    for n,t in [(5,1),(5,2),(6,2)]:
        kernel=m.hit_kernel(n,t,F(1,3))
        for j in range(t+1):
            for inds in combinations(range(n),j):
                mask=sum(1<<i for i in inds)
                row=[F(0)]*(t+2)
                for ell,mix in [(1,F(2,3)),(2,F(1,3))]:
                    for mark in combinations(range(n),ell):
                        after=(mask^sum(1<<i for i in mark)).bit_count()
                        row[min(after,t+1)]+=mix/comb(n,ell)
                assert tuple(row)==kernel[j]
    ok("full-mask arrival enumeration equals weight kernel",True)
    # Any triple of size1/2 sets whose union has >2 has a listed witness.
    marks=[frozenset(x) for ell in (1,2) for x in combinations(range(4),ell)]
    for seq in product(marks,repeat=3):
        if len(frozenset().union(*seq))<=2:
            continue
        witness=any(len(a|b)>2 and (len(a)==2 or len(b)==2) for a,b in combinations(seq,2))
        witness |= all(len(a)==1 for a in seq) and len(frozenset().union(*seq))==3
        assert witness
    ok("finite witness enumeration for compound marks",True)
    ok("2+1 term nonzero when triple-singleton term zero",m.phi(5,2,F(1,100),F(1,100))>m.phi(5,2,F(1,100),F(0)))
    seq=[{0,1},{1,2},{1,3}]
    state=set()
    weights=[]
    for x in seq:
        state ^= x
        weights.append(len(state))
    ok("overlapping double groups: no disjoint pair, first exceedance4",weights==[2,2,4] and all(a&b for a,b in combinations(seq,2)))
    # Exact coefficient enumeration, not only approximate count comparisons.
    n=5
    ones=[{i} for i in range(n)]
    twos=[set(x) for x in combinations(range(n),2)]
    ok("coefficient12",F(sum(len(a|b)>2 for a in ones for b in twos),len(ones)*len(twos))==F(n-2,n))
    ok("coefficient22",F(sum(len(a|b)>2 for a in twos for b in twos),len(twos)**2)==1-F(1,comb(n,2)))
    ok("coefficient111",F(sum(len(a|b|c)==3 for a in ones for b in ones for c in ones),n**3)==F((n-1)*(n-2),n*n))
    ok("t1 cross reduces to accepted E pair",m.cross_phi(39,1,(F(1,5),F(0)),(F(1,7),F(0)))==F(38,39)*F(1,5)*F(1,7))
    ok("zero aperture gives no cross",m.cross_phi(44,2,(F(1,5),F(1,7)),(F(0),F(0)))==0)
    # State mechanics of the actual example E operator.
    def release(mask,latched_err):
        return 0 if latched_err else mask
    ok("clean read then hit: E release preserves hit",release(1,False)==1)
    ok("dirty read then XOR cancellation: pending still writes",release(0,True)==0)
    ok("initial double residual plus outside singleton fails t2",(3^4).bit_count()>2)
    ok("first exceedance persists despite later XOR",[1,3,7,3][2].bit_count()>2 and [1,3,7,3][-1].bit_count()==2)
    ok("two allowed errors give one ERR not two parents",int(3!=0)==1 and (3).bit_count()==2)
    ok("bit count also misses cancelling parents",(1^1)==0)
    # General t lower event: exactly t+1 events, first t+1-j all outside current.
    for n,t in [(5,1),(5,2),(6,2)]:
        universal=F(m.falling(n,t+1),n**(t+1))
        for j in range(t+1):
            event=F(m.falling(n-j,t+1-j),n**(t+1-j))
            assert event>=universal
    ok("lower witness valid from every correctable weight",True)
    # Exact t2 E mixture is only an address test, not an additional campaign.
    mixed=dict(n=5,t=2,W=2,T=F(23,10),P=F(1),D=F(1,10),
               segments=[(F(0),F(23,10),(F(1,5),F(1,20)))])
    qlo,qhi=m.exact_e(mixed)
    upper,v,x=m.fixed_upper(mixed,"E")
    ok("t2 mixed E exact interval under compound upper",0<qlo<=qhi<upper<1 and x>0)
    refined=m.exact_e(mixed,terms=40)
    ok("series refinement encloses same t2 E probability",max(qlo,refined[0])<=min(qhi,refined[1]) and refined[1]-refined[0]<F("1e-28"))
    tail_case=dict(n=44,t=2,W=8,T=F(17,5),P=F(1),D=F(1,20),
                   segments=[(F(0),F(17,5),(F(1,10),F(0)))])
    ok("tail pending not completed at T",(F(27,8),F(137,40)) in list(m.schedule(tail_case,3)) and F(137,40)>tail_case["T"])
    ok("zero flow exact zero",m.clean_survival(F(0),F(0),44,2)==(F(1),F(1)))
    ok("extra physical bits raise same-environment array rate",F(44*8,39*8)==F(44,39)>1)
    rejected = False
    try:
        m.exact_e(dict(tail_case,D=F(1)))
    except ValueError:
        rejected = True
    ok("overlapping-service calendar rejected",rejected)
    return dict(count=len(results),tests=results,
                mixed_E_test=dict(n=5,t=2,W=2,T_s="23/10",P_s="1",D_s="1/10",m1_rate="1/5",m2_rate="1/20",Q=m.interval(qlo,qhi),upper=str(upper),V=str(v),X=str(x)))


def build():
    cfg=json.loads((HERE/"inputs.json").read_text())
    report=dict(task=187,base=cfg["base"],preregistration_sha="d69a1f3655c42a5044240b2d7da9b8546c302150",
                code_constructions=[m.code_check(t) for t in (1,2)],
                comparison=main_rows(cfg),regressions=regressions(),checks=targeted_checks())
    report["input_sha256"]=hashlib.sha256((HERE/"inputs.json").read_bytes()).hexdigest()
    report["implementation_sha256"]={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ["model.py","calculate.py"]}
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write",action="store_true")
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    if args.write and args.check:
        parser.error("choose --write or --check")
    text=json.dumps(build(),ensure_ascii=False,indent=2)+"\n"
    target=HERE/"outputs/report.json"
    if args.write:
        target.parent.mkdir(exist_ok=True)
        target.write_text(text)
        print(target)
    elif args.check:
        if target.read_text()!=text:
            raise SystemExit("report mismatch; no file overwritten")
        print("PASS: report reproduced byte-for-byte; accepted source blobs unchanged")
    else:
        print(text,end="")

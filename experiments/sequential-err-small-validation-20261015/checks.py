"""Directed scientific invariants; no full rerun of the accepted U package."""
from copy import deepcopy
from fractions import Fraction as F
import math
import numpy as np
from exact import (cases,exposure,schedule,lower_cells,transition,propagate,action,
                   READ,RELEASE,mass_check,solve,word_probability,bounds)
from arithmetic import fixed_decimal
from enumerated import reference
from mc import flip,snapshot,release,confidence_interval

def run_checks(cfg):
    names=[]
    def check(condition,name):
        if not condition: raise AssertionError(name)
        names.append(name)
    cs=cases(cfg)
    check(len(cs)==8 and all(c["n"]==38 for c in cs),"eight preregistered E/full38 cases")
    check(all(exposure(c,0,c["T"])==F(68,25) for c in cs),"equal exposure of fixed profiles")
    for c in cs:
        check(c["D"]<c["period"]/c["W"],"nonoverlapping calendar "+c["id"])
        for w in range(c["W"]):
            for a,b,_ in lower_cells(c,w):
                check(all(max(a,e)>=min(b,f) for e,f in schedule(c,w)),
                      "lower cell outside service "+c["id"]+f" word{w} [{a},{b}]")
    # Summarize repeated cell assertions as one check without hiding failure locations.
    names=[n for n in names if not n.startswith("lower cell") and not n.startswith("nonoverlapping")]
    names+=["all eight calendars nonoverlapping","all lower cells outside whole potential service windows"]
    zero=deepcopy(cs[1]); zero["segments"]=[(F(0),zero["T"],F(0))]
    z=solve(zero)
    check(F(z["Q_exact"]["upper"])==0,"zero flow gives exactly zero Q")
    for m in (F(0),F(1,100),F(1,5),F(17,25)):
        K,_=transition(m,38,32)
        check(all(sum(a for a,b in r)<=1<=sum(b for a,b in r) for r in K),
              f"kernel mass at m={m}")
        phi=math.exp(-float(m))*(math.cosh(float(m)/math.sqrt(38))+
                                   math.sqrt(38)*math.sinh(float(m)/math.sqrt(38)))
        mid=sum(float((a+b)/2) for a,b in K[0][:4])
        check(abs(mid-phi)<2e-15,f"analytic one-word survival at m={m}")
    coarse,_=transition(F(1,5),38,12)
    fine,_=transition(F(1,5),38,32)
    check(all(a<=c<=d<=b for r,s in zip(coarse,fine) for (a,b),(c,d) in zip(r,s)),
          "uniformization refinement 12 to32 nests")
    K,_=transition(F(1,5),1,32)
    check(K[0][4][0]==0,"single-bit limit enclosure contains zero absorption")
    c=cs[0]
    q=solve(c)["Q_exact"]
    survival=1.
    for w in range(c["W"]):
        ends=sorted({F(0),c["T"]}|{e for e,_ in schedule(c,w)})
        for a,b in zip(ends[:-1],ends[1:]):
            m=float(exposure(c,a,b)/c["W"])
            survival*=math.exp(-m)*(math.cosh(m/math.sqrt(38))+math.sqrt(38)*math.sinh(m/math.sqrt(38)))
    check(abs(1-survival-float(q["midpoint"]))<2e-15,"zero-gap E analytic reset limit")
    m=float(exposure(c,0,c["T"])/c["W"])
    phi=math.exp(-m)*(math.cosh(m/math.sqrt(38))+math.sqrt(38)*math.sinh(m/math.sqrt(38)))
    check(abs(reference(c,disable_service=True)["Q"]-(1-phi**c["W"]))<2e-15,
          "global enumeration no-service analytic limit")
    def basis(i): return [(F(j==i),F(j==i)) for j in range(5)]
    check(action(basis(1),RELEASE,48)==basis(1),"exact ERR0 release preserves dirty state")
    check(action(basis(1),READ,48)==basis(3),"exact snapshot latches ERR1 without cleaning")
    check(action(basis(2),RELEASE,48)==basis(0),"exact cancelled error retains pending until release")
    check(action(basis(4),READ,48)==action(basis(4),RELEASE,48)==basis(4),
          "exact absorption survives both operators")
    def fixture():
        words=np.zeros((1,2),dtype=np.uint64)
        return words,np.zeros_like(words),np.zeros_like(words,dtype=bool),np.zeros(1,dtype=bool)
    ids=np.array([0])
    def clean_snapshot_case(unconditional=False):
        words,latched,pending,bad=fixture()
        snapshot(words,latched,pending,0)
        flip(words,bad,ids,0,0)
        release(words,latched,pending,0,unconditional=unconditional)
        return int(words[0,0]),bool(bad[0])
    check(clean_snapshot_case()==(1,False),"clean snapshot then hit survives ERR0 release")
    check(clean_snapshot_case(True)!=(1,False),"unconditional-cleanup mutation is rejected")
    words,latched,pending,bad=fixture()
    flip(words,bad,ids,0,0); snapshot(words,latched,pending,0)
    flip(words,bad,ids,0,1)
    check(bool(bad[0]) and pending[0,0],"ERR1 plus distinct gap hit absorbs before repair")
    release(words,latched,pending,0)
    check(words[0,0]==0 and bad[0],"repair cannot undo historical first hit")
    words,latched,pending,bad=fixture()
    flip(words,bad,ids,0,0); snapshot(words,latched,pending,0)
    flip(words,bad,ids,0,0)
    check(words[0,0]==0 and pending[0,0] and not bad[0],"same-bit cancellation keeps pending ERR")
    flip(words,bad,ids,0,1); release(words,latched,pending,0)
    check(words[0,0]==0 and not bad[0],"conditional corrected image clears permitted new error")
    flip(words,bad,ids,0,2)
    check(words[0,0]==4 and not bad[0],"hit after release remains live")
    words,latched,pending,bad=fixture()
    flip(words,bad,ids,1,0); snapshot(words,latched,pending,0); release(words,latched,pending,0)
    check(words[0,1]==1,"one operation does not clean another word")
    partial=cs[-1]
    _,audit=word_probability(partial,3,32,48)
    check(schedule(partial,3)[-1]==(F(27,8),F(137,40)),"last snapshot3.375 release3.425 beyondT")
    check(audit["history"][-1]["t"]=="17/5" and
          not any("release" in x["actions"] for x in audit["history"] if F(x["t"])>=F(27,8)),
          "partial last pass never executes future release")
    check(F(audit["history"][-1]["state"][3]["upper"])>0,"pending ERR1 mass retained atT")
    check(reference(partial)["active_operation_word_at_T"]==3,"full enumeration retains unfinished last operation")
    _,_,cross,audits=bounds(partial,32)
    last=audits[3]["crossing_pairs"][-1]
    check(F(last["pair_term"])==F(37,38)*F(3,40)*F(3,1600),
          "X_E retains clipped final window3.375 to3.4")
    check(all(bounds(case,32)[2]==0 for case in cs if case["D"]==0),
          "X_E vanishes exactly at zero gap")
    _,_,_,a=bounds(cs[1],32)
    witness=a[0]["crossing_pairs"][1]
    before,after=F(99,100),F(101,100)
    check(F(witness["J"][0])<before<F(witness["J"][1]) and
          F(witness["H"][0])<after<F(witness["H"][1]) and
          not any(F(cell["start"])<before<after<F(cell["end"]) for cell in a[0]["virtual_cells"]),
          "cross-boundary first-hit witness needs X_E outside same-cell pairs")
    ci0=confidence_interval(0,200000); ci1=confidence_interval(200000,200000)
    check(ci0[0]==0 and ci0[1]>0,"zero MC count has positive upper limit")
    check(ci1[1]==1 and ci1[0]<1,"all MC successes retain lower uncertainty")
    ci=confidence_interval(3,10); inv=confidence_interval(7,10)
    check(abs(ci[0]+inv[1]-1)<1e-14 and abs(ci[1]+inv[0]-1)<1e-14,"Clopper-Pearson symmetry")
    check(F(fixed_decimal(F(-1,3),8))<=F(-1,3)<=F(fixed_decimal(F(-1,3),8,True)),
          "outward negative decimal rounding")
    return names

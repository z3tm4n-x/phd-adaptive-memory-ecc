"""Directed checks of the model, absorbing event, interval arithmetic and MC."""
from fractions import Fraction as F
import copy
import numpy as np
from exact import (cases,exponential_enclosure,local_transition,analytic_survival,
                   solve,fence_intervals,lower_cells,exposure,enclosure)
from enumerated import enumerate_reference
from mc import flip,latch,confidence_interval

def run_checks(cfg):
    names=[]
    def check(name,condition):
        if not condition:
            raise AssertionError(name)
        names.append(name)
    selected=cases(cfg)
    check("preregistered eight points",len(selected)==8)
    check("same total exposure in both profiles",
          all(exposure(c,F(0),c["T"])==F(68,25) for c in selected))
    from exact import word_schedule
    check("word partitions include exactly the full horizon",
          all(sum((b-a for a,b in fence_intervals(c,w)),F(0))==c["T"]
              for c in selected for w in range(c["W"])))
    check("all lower cells avoid the entire read-fence window",
          all(max(a,r)>=min(b,f) for c in selected for w in range(c["W"])
              for a,b,_ in lower_cells(c,w) for r,f in word_schedule(c,w)))
    zero=copy.deepcopy(selected[0])
    zero["segments"]=[(F(0),zero["T"],F(0))]
    result=solve(zero)
    check("zero rate has exactly zero risk",F(result["Q_exact"]["upper"])==0)
    for m in (F(0),F(1,100),F(1,5),F(17,25)):
        interval,components,_=local_transition(m,39,32)
        analytical=analytic_survival(m,39)
        check("closed form m="+str(m),abs(float((interval[0]+interval[1])/2)-analytical)<5e-15)
        check("mass m="+str(m),sum(x[0] for x in components)<=1<=sum(x[1] for x in components))
    # A one-bit word can never exceed one wrong bit, under arbitrarily many XORs.
    survival,_,_=local_transition(F(5),1,48)
    check("one-bit analytic limit",survival[0]<=1<=survival[1])
    coarse=local_transition(F(1,3),39,12)[0]
    refined=local_transition(F(1,3),39,32)[0]
    check("uniformization refinement nests",coarse[0]<=refined[0]<=refined[1]<=coarse[1])
    # No repairs: independent word first-hit law, checked by full enumeration.
    base=selected[0]
    global_q=enumerate_reference(base,disable_fences=True)["Q"]
    analytic_q=1-analytic_survival(exposure(base,F(0),base["T"])/base["W"],base["n"])**base["W"]
    check("no-service analytic limit",abs(global_q-analytic_q)<2e-13)
    # Separate synchronous limit; not substituted into the main sequential matrix.
    m=F(1,5)
    one=local_transition(m,39,32)[0]
    synchronous=1-float((one[0]+one[1])/2)**8
    closed=1-analytic_survival(m,39)**8
    check("synchronous two-cycle four-word limit",abs(synchronous-closed)<2e-13)
    check("sequential first-fence phases differ",
          fence_intervals(base,0)[0][1]!=fence_intervals(base,1)[0][1])
    gap=selected[5]  # W8, constant, D=.05.
    check("partial last pass does not apply future fence",
          fence_intervals(gap,3)[-1]==(F(97,40),F(17,5)))
    check("lower cell excludes final pending window",
          all(b<=F(27,8) for a,b,_ in lower_cells(gap,3)))
    check("upper retains exposure after last read",
          exposure(gap,F(27,8),gap["T"])>0)
    # Explicit MC primitive: read clean, two distinct flips in gap, then write0.
    words=np.zeros((1,4),dtype=np.uint64); latched=np.zeros_like(words)
    failed=np.zeros(1,dtype=bool); ids=np.array([0])
    latch(words,latched,0)
    flip(words,failed,ids,np.array([0]),np.array([2]))
    flip(words,failed,ids,np.array([0]),np.array([3]))
    words[:,0]=latched[:,0]
    check("gap first hit survives subsequent correction",bool(failed[0]) and words[0,0]==0)
    words[:]=0; failed[:]=False
    flip(words,failed,ids,np.array([1]),np.array([7]))
    flip(words,failed,ids,np.array([1]),np.array([7]))
    check("same-bit XOR cancellation is not failure",not failed[0] and words[0,1]==0)
    flip(words,failed,ids,np.array([1]),np.array([8]))
    latch(words,latched,0); words[:,0]=latched[:,0]
    check("one fence does not synchronously clean other words",words[0,1]!=0)
    # U intentionally overwrites an arrival after a clean latch.
    latch(words,latched,2)
    flip(words,failed,ids,np.array([2]),np.array([4]))
    words[:,2]=latched[:,2]
    check("U handles post-latch arrival as declared",words[0,2]==0)
    ci=confidence_interval(0,200000)
    check("zero MC count has positive upper",ci[0]==0 and 0<ci[1]<1)
    check("all MC successes interval includes one",confidence_interval(200000,200000)[1]==1)
    c=confidence_interval(120,1000); d=confidence_interval(880,1000)
    check("Clopper-Pearson symmetry",abs(c[0]+d[1]-1)<1e-13 and abs(c[1]+d[0]-1)<1e-13)
    # Outward decimal output is checked as rational arithmetic, including negative endpoints.
    x=F(-1,3); y=F(2,7); box=enclosure(x,y,12)
    check("outward decimal enclosure",F(box["lower"])<=x<=y<=F(box["upper"]))
    return names

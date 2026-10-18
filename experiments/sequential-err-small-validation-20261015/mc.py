"""Independent explicit-bit E simulation; no exact transitions or schedule imports."""
from fractions import Fraction
import numpy as np
from scipy.stats import beta

def confidence_interval(successes,trials,level=.95):
    a=(1-level)/2
    return (0. if successes==0 else float(beta.ppf(a,successes,trials-successes+1)),
            1. if successes==trials else float(beta.ppf(1-a,successes+1,trials-successes)))

def flip(words,failed,ids,word,bit):
    words[ids,word]^=np.left_shift(np.uint64(1),np.asarray(bit,dtype=np.uint64))
    current=words[ids,word]
    failed[ids]|=(current&(current-np.uint64(1)))!=0

def snapshot(words,latched,pending,word):
    current=words[:,word]
    pending[:,word]=current!=0
    multiple=(current&(current-np.uint64(1)))!=0
    # Correct 0/1 to original zero; decoder after first failure is immaterial.
    latched[:,word]=np.where(multiple,current,np.uint64(0))

def release(words,latched,pending,word,unconditional=False):
    selected=np.arange(len(words)) if unconditional else np.flatnonzero(pending[:,word])
    words[selected,word]=latched[selected,word]
    pending[:,word]=False

def monte_carlo(case,trials,seed_base):
    points={}
    def at(t):
        return points.setdefault(t,dict(snapshot=[],end=[],rate=None))
    for cycle in range(int(case["T"]/case["period"])+2):
        for word in range(case["W"]):
            start=(Fraction(cycle)+Fraction(word,case["W"]))*case["period"]
            finish=start+case["D"]
            if start<=case["T"]: at(start)["snapshot"].append(word)
            if finish<=case["T"]: at(finish)["end"].append(word)
    for start,end,rate in case["segments"]:
        at(start)["rate"]=float(rate); at(end)
    at(case["T"])
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed_base,case["index"]])))
    words=np.zeros((trials,case["W"]),dtype=np.uint64)
    latched=np.zeros_like(words)
    pending=np.zeros((trials,case["W"]),dtype=bool)
    failed=np.zeros(trials,dtype=bool)
    previous=rate=0.; total_arrivals=0
    for instant,op in sorted(points.items()):
        t=float(instant)
        if rate>0 and t>previous:
            arrival=previous+rng.exponential(1/rate,size=trials)
            ids=np.flatnonzero(arrival<t)
            while len(ids):
                word=rng.integers(0,case["W"],size=len(ids))
                bit=rng.integers(0,case["n"],size=len(ids))
                flip(words,failed,ids,word,bit)
                total_arrivals+=len(ids)
                arrival[ids]+=rng.exponential(1/rate,size=len(ids))
                ids=ids[arrival[ids]<t]
        for word in op["snapshot"]: snapshot(words,latched,pending,word)
        for word in op["end"]: release(words,latched,pending,word)
        if op["rate"] is not None: rate=op["rate"]
        previous=t
    k=int(failed.sum())
    return dict(trials=trials,events_Q=k,Q_MC=k/trials,
        CI_95_pointwise=list(confidence_interval(k,trials)),
        confidence_procedure="two-sided equal-tailed Clopper-Pearson",
        seed_entropy=[seed_base,case["index"]],bit_generator="PCG64",
        generated_arrivals=total_arrivals,
        absorbing_event="ever Hamming weight>1; later XOR or conditional write cannot erase event")

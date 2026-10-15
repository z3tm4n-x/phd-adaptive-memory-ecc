"""Independent explicit-bit event simulation; no exact/bound/calendar imports."""
from fractions import Fraction
import numpy as np
from scipy.stats import beta

def confidence_interval(successes, trials, level=.95):
    alpha = 1-level
    low = 0. if successes == 0 else float(beta.ppf(alpha/2,successes,trials-successes+1))
    high = 1. if successes == trials else float(beta.ppf(1-alpha/2,successes+1,trials-successes))
    return low, high

def flip(words, failed, ids, word, bit):
    words[ids,word] ^= np.left_shift(np.uint64(1),np.asarray(bit,dtype=np.uint64))
    current = words[ids,word]
    bad = (current & (current-np.uint64(1))) != 0
    failed[ids] |= bad

def latch(words, latched, word):
    current = words[:,word]
    bad = (current & (current-np.uint64(1))) != 0
    # Correct zero/one error to original all-zero codeword; after A arbitrary.
    latched[:,word] = np.where(bad,current,np.uint64(0))

def monte_carlo(case, trials, seed_base):
    # Read/fence construction deliberately independent of exact.word_schedule.
    events = {}
    def at(t):
        return events.setdefault(t,dict(read=[],write=[],rate=None))
    horizon = case["T"]
    for k in range(int(horizon/case["period"])+2):
        for word in range(case["W"]):
            read = (Fraction(k)+Fraction(word,case["W"]))*case["period"]
            write = read+case["D"]
            if read <= horizon:
                at(read)["read"].append(word)
            if write <= horizon:
                at(write)["write"].append(word)
    for start,end,rate in case["segments"]:
        at(start)["rate"] = float(rate)
        at(end)
    at(horizon)
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed_base,case["index"]])))
    words = np.zeros((trials,case["W"]),dtype=np.uint64)
    latched = np.zeros_like(words)
    failed = np.zeros(trials,dtype=bool)
    previous,rate,total_events = 0.,0.,0
    for instant,actions in sorted(events.items()):
        t = float(instant)
        if rate > 0 and t > previous:
            arrivals = previous+rng.exponential(1/rate,size=trials)
            ids = np.flatnonzero(arrivals < t)
            while len(ids):
                word = rng.integers(0,case["W"],size=len(ids))
                bit = rng.integers(0,case["n"],size=len(ids))
                flip(words,failed,ids,word,bit)
                total_events += len(ids)
                arrivals[ids] += rng.exponential(1/rate,size=len(ids))
                ids = ids[arrivals[ids] < t]
        # At a deterministic tie: latch before fence; Poisson ties have measure0.
        for word in actions["read"]:
            latch(words,latched,word)
        for word in actions["write"]:
            words[:,word] = latched[:,word]
        if actions["rate"] is not None:
            rate = actions["rate"]
        previous = t
    successes = int(failed.sum())
    low,high = confidence_interval(successes,trials)
    return dict(trials=trials,events_Q=successes,Q_MC=successes/trials,
        CI_95_pointwise=[low,high],confidence_procedure="two-sided equal-tailed Clopper-Pearson",
        seed_entropy=[seed_base,case["index"]],bit_generator="PCG64",
        generated_arrivals=total_events,absorbing_event="ever Hamming weight>1, retained after writes")

"""Run the three preregistered archive pairs; pass --check to compare saved results."""
import argparse
from bisect import bisect_right
from datetime import datetime, timedelta
import json
from pathlib import Path
from statistics import mean, stdev

import numpy as np

from histories import GROUPS, HERE, NAMES, T, load_profiles
from replay import Calendar, NS, simulate
from risk import pair_upper


def illustrative_return(profile, marks, returns, cal):
    if not returns:
        return None
    # Pick the registered example after replay. Nothing here feeds the controller.
    def observed(j):
        t = (j*cal.P+cal.drain)/NS
        return profile.group[bisect_right(profile.edges,t)-1] == 0
    j, reports = next(((j,r) for j,r in returns if observed(j)),returns[0])
    decision = j*cal.P+cal.drain
    detections = []
    for word,start,release in reports:
        h = np.flatnonzero((marks[:,0] < start) & ((marks[:,1]==word) | (marks[:,3]==word)))
        i = int(h[-1])
        t,w1,b1,w2,b2 = map(int,marks[i])
        detections.append(dict(word=word,read_ns=start,release_ns=release,
                          latest_prior_parent=i,particle_ns=t,mark=[w1,b1,w2,b2]))
    # UTC is for the evaluator; keep nominal nanoseconds in the proof trace.
    epoch = datetime.fromisoformat(profile.utc.replace("Z","+00:00"))
    utc = (epoch+timedelta(microseconds=decision//1000)).isoformat(timespec="microseconds")
    return dict(cell=j,utc_to_microsecond=utc,observed_event=bool(observed(j)),
                decision_ns=decision,mount_deadline_ns=(32*j+1)*cal.L,
                first_fast_pass_ns=(32*j+1)*cal.L,closed_count=len(reports),reports=detections)


def spread(values):
    return dict(n=len(values),mean=mean(values),sd=stdev(values),minimum=min(values),maximum=max(values))


def calendar_parts(profile, marks, cal, switches, repair_starts, adaptive, row):
    """Evaluator only. Count exact word-start prefixes at each change of support."""
    changes = np.r_[0,np.flatnonzero(np.diff(profile.group) != 0)+1]
    labels = profile.group[changes]
    cuts = np.r_[profile.edges[changes],T]
    assert (cuts == np.floor(cuts)).all()
    cuts = cuts.astype(np.int64)*NS
    starts = np.array([0]+[j*cal.P for j,_,_ in switches],dtype=np.int64)
    step = np.array([1 if adaptive else 4]+[1 if fast else 32 for _,fast,_ in switches])
    period = step*cal.L
    length = np.diff(starts)
    assert np.all(length % period[:-1] == 0)
    prior_reads = np.r_[0,np.cumsum(length//period[:-1]*cal.words)]
    prior_fast = np.r_[0,np.cumsum(length*(step[:-1] == 1))]
    run = np.searchsorted(starts,cuts,side="right")-1
    elapsed = cuts-starts[run]
    whole,rest = np.divmod(elapsed,period[run])
    frames,offset = np.divmod(rest,1568)
    last_reads = np.minimum(cal.words,8*frames+np.minimum(8,(offset+163)//164))
    nreads = np.diff(prior_reads[run]+whole*cal.words+last_reads)
    nfast = np.diff(prior_fast[run]+elapsed*(step[run] == 1))
    def histogram(times):
        indices = np.searchsorted(cuts,np.array(times,dtype=np.int64),side="right")-1
        return np.bincount(labels[indices],minlength=len(GROUPS))
    repairs = histogram(repair_starts)
    parents = histogram(marks[:,0])
    resets = histogram([j*cal.P+cal.drain for j,f,_ in switches if f])
    result = {}
    for i,name in enumerate(GROUPS):
        reads = int(np.sum(nreads[labels == i]))
        writes = int(repairs[i])
        result[name] = dict(parents=int(parents[i]),word_reads=reads,repair_writes=writes,
            fast_ns=int(np.sum(nfast[labels == i])) if adaptive else None,
            to_fast=int(resets[i]),bus_ns=48*reads+56*writes)
    assert sum(q["bus_ns"] for q in result.values()) == row["protection_bus_ns"]
    assert sum(q["parents"] for q in result.values()) == len(marks)
    assert sum(q["to_fast"] for q in result.values()) == row["to_fast"]
    if adaptive:
        assert sum(q["fast_ns"] for q in result.values()) == row["fast_ns"]
    return result


def calculate(profile):
    cal = Calendar()
    rows = []
    for r in range(16):
        marks,digest = profile.draw(r)
        row = dict(rep=r,seed=[436,20261110,NAMES.index(profile.name),r],parents=len(marks),marks_sha256=digest)
        for adaptive,name in ((True,"L/32L"),(False,"4L")):
            repair_log = [] if r == 0 else None
            result, switches, returns, _ = simulate(marks,adaptive,T*NS,cal,repair_log)
            row[name] = result
            if r == 0:
                result["by_calendar"] = calendar_parts(profile,marks,cal,switches,repair_log,adaptive,result)
            if r == 0 and adaptive:
                row["first_rare_decision_ns"] = next((j*cal.P+cal.drain for j,fast,_ in switches if not fast),None)
                row["example"] = illustrative_return(profile,marks,returns,cal)
        row["saved_bus_ns"] = row["4L"]["protection_bus_ns"]-row["L/32L"]["protection_bus_ns"]
        rows.append(row)
    return dict(history=profile.name,start_utc=profile.utc,input=profile.summary,
                pair_upper=pair_upper(profile),pairs=rows,
                spread=dict(saving_s=spread([r["saved_bus_ns"]/NS for r in rows]),
                    fast_s=spread([r["L/32L"]["fast_ns"]/NS for r in rows]),
                    switches=spread([r["L/32L"]["switches"] for r in rows]),
                    parents=spread([r["parents"] for r in rows])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path,required=True,help="parent of t141-cache and c1-goes")
    parser.add_argument("--histories",nargs="+",choices=NAMES,default=NAMES)
    parser.add_argument("--check",action="store_true")
    args = parser.parse_args()
    for profile in load_profiles(args.cache,args.histories):
        result = calculate(profile)
        path = HERE/(profile.name.lower()+".json")
        data = json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2)+"\n"
        if args.check:
            if path.read_text(encoding="utf-8") != data:
                raise ValueError(f"Replay differs from {path.name}")
        else:
            path.write_text(data,encoding="utf-8",newline="\n")
        sample = result["pairs"][0]
        print(profile.name, sample["parents"], sample["L/32L"]["protection_bus_ns"]/NS,
              sample["4L"]["protection_bus_ns"]/NS, result["spread"]["saving_s"], flush=True)


if __name__ == "__main__":
    main()

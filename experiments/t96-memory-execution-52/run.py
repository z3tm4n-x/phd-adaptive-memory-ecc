#!/usr/bin/env python3
"""Rebuild and replay section 5.2. The --work directory holds temporary RTL files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time

from build import BLOB, build
from inputs import bound, cp, directed, no_events_upper, parents
from reference import CFG, CHECKPOINT, L, METRICS, Run, metrics, oracle
import numpy as np

HERE = Path(__file__).resolve().parent
NAMES = (*METRICS, "terminal_step", "word0", "word1", "word2", "word3")


def joined(row):
    return " ".join(map(str,row))


def write_stimulus(path, jobs):
    with path.open("w", newline="\n") as f:
        for name, horizon, events, literal, record_from in jobs:
            print(name,horizon,len(events),int(literal),record_from,file=f)
            for e in events:
                print(*e,file=f)


def reached_prefix():
    p = oracle([], CHECKPOINT, record_from=CHECKPOINT)
    assert (p.passes,p.read_ns,p.fast_ns,p.sealed,p.step,p.switches)==(
        1280,1280*800,CHECKPOINT,1280,1,0)
    return p


def reference(job, prefix):
    _, horizon, events, literal, record_from = job
    if literal or record_from==0:
        return oracle(events,horizon,record_from=record_from)
    # The dictionary state is clean at this boundary and is reallocated per path.
    seed = Run(**{k:getattr(prefix,k) for k in (*METRICS,"step","last_bad_cell")})
    return oracle(events,horizon,prefix=seed,record_from=record_from)


def check_batch(work, jobs, prefix, trace_hash, witnesses):
    stim=work/"stimulus.txt"
    write_stimulus(stim,jobs)
    streams=[]
    try:
        for variant in CFG["both_check_local"]:
            path=work/f"last-{variant}.trace"
            subprocess.run([str(work/f"pins{variant}"),str(stim),str(path)],check=True)
            streams.append(path.open())
        records=[]
        for job in jobs:
            name,horizon,events,literal,record_from=job
            ref=reference(job,prefix)
            expected=["T "+name,*(joined(row) for row in ref.trace),"M "+joined(metrics(ref))]
            for variant, stream in enumerate(streams):
                for line in expected:
                    actual=stream.readline().rstrip("\r\n")
                    if line!=actual:
                        failure=work/"first_mismatch.json"
                        failure.write_text(json.dumps({"case":name,"variant":variant,"horizon_ns":horizon,
                            "input":events,"record_from_ns":record_from,"expected":line,
                            "actual":actual},indent=2)+"\n")
                        raise ValueError(f"{name}, RTL {variant}: expected {line!r}, observed {actual!r}; {failure}")
            trace_hash.update(("\n".join(expected)+"\n").encode())
            if name in ("sample_before","write_before","terminal_before_write",
                        "interread_exceed_cancel","first_slow_then_fallback","positive_on_promotion"):
                witnesses[name]={"horizon_ns":horizon,"parents":events,"first_ns":ref.first_ns,
                                 "events":[row for row in ref.trace if row[1] in ("H","W","R","C","I")
                                 or (row[1]=="S" and row[3]==1)
                                 or (row[1]=="P" and row[2:5]==(0,1,0))]}
            records.append((metrics(ref),len(ref.trace)))
        if any(s.readline() for s in streams):
            raise ValueError("extra RTL records after the last trial")
        return records
    finally:
        for f in streams:
            f.close()


def run(work, smoke=False):
    prefix=reached_prefix()
    direct=[]
    for name,horizon,events in directed():
        cut=CHECKPOINT if horizon>CHECKPOINT and min((e[0] for e in events),default=horizon)>=CHECKPOINT else 0
        direct.append((name,horizon,events,cut==0,cut))
    t=CFG["T_ns"]
    for k in CFG["literal_random_ids"]:
        direct.append((f"literal_{k}",t,parents(k),True,CHECKPOINT))
    digest=hashlib.sha256()
    witnesses={}
    checked=check_batch(work,direct,prefix,digest,witnesses)
    direct_hash=digest.hexdigest()
    direct_map={job[0]:row for job,(row,_) in zip(direct,checked)}
    # Search obligations for the directed cases, independently of the aggregates.
    def metric(case,key):
        return direct_map[case][NAMES.index(key)]
    assert all(metric(f"position_{bit}","writes")==1 for bit in range(38))
    assert metric("last_address","positive")==1 and metric("ring_wrap","word3")==0
    assert metric("cancel_before_read","writes")==0
    assert metric("interread_exceed_cancel","first_ns")==111 and metric("same_bucket","first_ns")==110
    assert metric("same_bit_reborn","writes")==2
    assert metric("terminal_before_write","writes")==0 and metric("terminal_after_write","writes")==1
    assert metric("late_terminal_parent","first_ns")==2774
    assert metric("positive_on_promotion","switches")==0 and metric("first_slow_then_fallback","switches")==2
    assert metric("pause_exceed_cleared","first_ns")==CHECKPOINT+L+101
    trace_hash=hashlib.sha256()
    event_hash=hashlib.sha256()
    count=32 if smoke else CFG["trials"]
    totals=dict.fromkeys(METRICS[1:],0)
    failures=parents_total=inversions=observations=0
    switches_hist={}
    for lo in range(0,count,128):
        jobs=[(f"mc{k}",t,parents(k),False,CHECKPOINT) for k in range(lo,min(lo+128,count))]
        outputs=check_batch(work,jobs,prefix,trace_hash,witnesses)
        for k,(job,(row,nrows)) in enumerate(zip(jobs,outputs),lo):
            events=job[2]
            event_hash.update((joined((k,len(events)))+"\n").encode())
            for ev in events:
                event_hash.update((joined(ev)+"\n").encode())
            parents_total+=len(events)
            inversions+=sum(1+(e[3]>=0) for e in events)
            vals=dict(zip(NAMES,row))
            failures+=int(vals["first_ns"]>=0)
            observations+=nrows
            for key in totals:
                totals[key]+=vals[key]
            switches_hist[vals["switches"]]=switches_hist.get(vals["switches"],0)+1
            if k in CFG["literal_random_ids"] and row!=direct_map[f"literal_{k}"]:
                raise ValueError(f"accelerated versus literal trial {k}")
    confidence=cp(failures,count)
    port=totals["read_ns"]+totals["write_ns"]
    record={"base":CFG["base"],"native8_blob":BLOB,"trials":count,"horizon_ns":t,
        "both_CHECK_LOCAL":[0,1],"first_count":failures,"frequency":failures/count,
        "clopper_pearson_95":confidence,"cp_half_width":(confidence[1]-confidence[0])/2,
        "analytic":bound(),"totals":totals,"port_mean_seconds":port/(1e9*count),
        "port_fraction":port/(t*count),"fast_mean_seconds":totals["fast_ns"]/(1e9*count),
        "fast_fraction":totals["fast_ns"]/(count*t),"mean_switches":totals["switches"]/count,
        "switch_histogram":{str(s):v for s,v in sorted(switches_hist.items())},
        "parents":parents_total,"word_inversions":inversions,"random_event_sha256":event_hash.hexdigest(),
        "random_trace_sha256":trace_hash.hexdigest(),"random_compared_trace_rows_per_rtl_after_prefix":observations,
        "directed_ids":[x[0] for x in direct if not x[0].startswith("literal_")],
        "literal_random_ids":CFG["literal_random_ids"],"directed_and_literal_sha256":direct_hash,
        "directed_trace_rows_per_rtl":sum(n for _,n in checked),
        "mismatches":[0,0],"prefix_ns":CHECKPOINT}
    if failures==0:
        record["one_sided_95"]=no_events_upper(count)
    if not smoke and record["cp_half_width"]>CFG["max_cp95_half_width"]:
        raise ValueError("preregistered precision was missed")
    return record,witnesses


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--include",type=Path,default=os.environ.get("CXXRTL_INCLUDE",
                    "/usr/share/yosys/include/backends/cxxrtl/runtime"))
    p.add_argument("--reuse-build",action="store_true")
    p.add_argument("--smoke",action="store_true")
    p.add_argument("--check",action="store_true")
    args=p.parse_args()
    start=time.monotonic()
    work=args.work.resolve()
    if not args.reuse_build:
        build(work,args.include.resolve())
    record,witnesses=run(work,args.smoke)
    result={"result.json":record,"witnesses.json":witnesses}
    for name,data in result.items():
        payload=json.dumps(data,indent=2,sort_keys=True)+"\n"
        (work/name).write_text(payload)
        if args.check and payload!=(HERE/name).read_text():
            raise ValueError(f"replay differs in {name}")
    print(f"{record['first_count']}/{record['trials']} first exceedances; 0 mismatches per RTL; "
          f"{record['random_compared_trace_rows_per_rtl_after_prefix']} random observations each")
    print(f"Python {platform.python_version()}, numpy {np.__version__}; elapsed {time.monotonic()-start:.1f}s")


if __name__=="__main__":
    main()

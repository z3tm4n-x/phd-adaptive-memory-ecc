#!/usr/bin/env python3
"""Independent bitmask/state-machine check; does not import executor_model/check_executor."""
from __future__ import annotations
import argparse, itertools, json
from pathlib import Path

def run(marks, slots, checks, delay, H, nbits=3):
    p=i=0; pending_bit=None; commit=None; fp=fi=B=False
    bounds=[0.0]+list(checks)+[H]; labels=[0]*(len(bounds)-1)
    events=[(tm,"hit",b) for tm,b in zip(slots,marks) if b>=0] + [(c,"check",None) for c in checks]
    k=0
    while True:
        next_base=events[k] if k<len(events) else (float("inf"),"",None)
        ct=commit if commit is not None else float("inf")
        if ct < next_base[0]: e=(ct,"commit",None)
        else: e=next_base; k += (e is next_base)
        time,kind,bit=e
        if time>H or time==float("inf"): break
        if kind=="hit":
            interval=max(j for j in range(len(bounds)-1) if bounds[j] <= time < bounds[j+1]); labels[interval] |= 1<<bit
            if pending_bit is not None and bit != pending_bit: B=True
            p ^= 1<<bit; i ^= 1<<bit
        elif kind=="check":
            i=0
            if p.bit_count()==1:
                pending_bit=(p & -p).bit_length()-1; commit=time+delay
            else:
                pending_bit=None; commit=None
        else:
            p=0; pending_bit=None; commit=None
        fp |= p.bit_count()>=2; fi |= i.bit_count()>=2
    P=any(x.bit_count()>=2 for x in labels)
    return fp,fi,B,P

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",required=True);ap.add_argument("--out",required=True);a=ap.parse_args();c=json.loads(Path(a.config).read_text());tc=c["trace_check"]
    total=old_bad=new_bad=0
    for marks in itertools.product(tc["symbols"], repeat=len(tc["arrival_slots"])):
        fp,fi,B,P=run(marks,tc["arrival_slots"],tc["check_times"],tc["write_delay"],tc["horizon"],tc["bits"])
        total+=1; old_bad += bool(fp and not(fi or B)); new_bad += bool(fp and not(P or B))
    result={"streams":total,"old_inclusion_violations":old_bad,"repaired_inclusion_violations":new_bad,
            "checks":{"expected_streams":total==tc["expected_streams"],"old_falsified":old_bad>0,"new_holds":new_bad==0}}
    if not all(result["checks"].values()): raise SystemExit("independent check failed")
    Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__":main()

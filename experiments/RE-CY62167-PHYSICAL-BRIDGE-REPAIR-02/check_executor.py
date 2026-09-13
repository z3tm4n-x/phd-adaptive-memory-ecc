#!/usr/bin/env python3
from __future__ import annotations
import argparse, itertools, json
from pathlib import Path
from executor_model import run_trace


def load(path): return json.loads(Path(path).read_text())

def one(events, checks=(1.0,2.0), delay=.2, H=3.0):
    return run_trace(events, list(checks), delay, H, 3)

def t(time, bit): return {"time": time, "kind": "toggle", "bit": bit}


def targeted(counterexample):
    out = {}
    ce = run_trace(counterexample["events"], counterexample["check_times"], counterexample["write_delay"], counterexample["horizon"], 3)
    out["mandatory_counterexample"] = {
        "pass": all(ce[k] == v for k,v in counterexample["required"].items()),
        "result": ce
    }
    clean = one([t(1.1,0)])
    out["clean_no_write_post_error_persists"] = clean["physical_at_horizon"] == [0]
    distinct = one([t(.5,0), t(1.1,1)])
    out["distinct_RMW_hit"] = distinct["physical_failure"] and distinct["B"]
    same = one([t(.5,0), t(1.1,0)])
    out["same_bit_RMW_cancellation"] = (not same["B"]) and (not same["physical_failure"])
    pending = run_trace([t(.5,0), t(1.1,1)], [1.0], .5, 1.2, 3)
    out["pending_write_at_horizon"] = pending["pending_at_horizon"] and pending["physical_failure"] and pending["B"]
    initial = run_trace([t(.2,0), t(.3,1)], [1.0], .2, 1.5, 3)
    out["initial_interval_P"] = initial["physical_failure"] and initial["P"]
    final = one([t(2.1,0), t(2.3,1)])
    out["final_interval_P"] = final["physical_failure"] and final["P"]
    sticky = one([t(.5,0), t(1.1,1)])
    out["sticky_after_writeback"] = sticky["physical_failure"] and sticky["physical_at_horizon"] == []
    return out


def exhaustive(cfg):
    tc = cfg["trace_check"]; slots=tc["arrival_slots"]; symbols=tc["symbols"]
    total=old_bad=new_bad=0; witness=None
    for marks in itertools.product(symbols, repeat=len(slots)):
        events=[t(tm,b) for tm,b in zip(slots,marks) if b >= 0]
        r=run_trace(events, tc["check_times"], tc["write_delay"], tc["horizon"], tc["bits"])
        total += 1
        if r["physical_failure"] and not (r["ideal_failure"] or r["B"]):
            old_bad += 1
            if witness is None: witness={"marks": marks, "result": r}
        if r["physical_failure"] and not (r["P"] or r["B"]):
            new_bad += 1
    return {"streams": total, "old_inclusion_violations": old_bad,
            "repaired_inclusion_violations": new_bad, "first_old_violation": witness}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--config",required=True); ap.add_argument("--counterexample",required=True); ap.add_argument("--out",required=True); ap.add_argument("--trace-out",required=True); a=ap.parse_args()
    cfg=load(a.config); counter=load(a.counterexample)
    targeted_result=targeted(counter); exhaustive_result=exhaustive(cfg)
    checks={k:(v["pass"] if isinstance(v,dict) and "pass" in v else bool(v)) for k,v in targeted_result.items()}
    checks["exhaustive_count"] = exhaustive_result["streams"] == cfg["trace_check"]["expected_streams"]
    checks["old_inclusion_is_falsified"] = exhaustive_result["old_inclusion_violations"] > 0
    checks["repaired_inclusion_holds_exhaustive"] = exhaustive_result["repaired_inclusion_violations"] == 0
    result={"checks":checks,"targeted":targeted_result,"exhaustive":exhaustive_result,
            "physical_slice":{"bound":None,"status":"NOT_ESTABLISHED"},
            "scientific_acceptance_rate_interface":"EXCLUDED"}
    if not all(checks.values()): raise SystemExit("executor repair check failed")
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    Path(a.trace_out).write_text(json.dumps(targeted_result["mandatory_counterexample"]["result"],indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()

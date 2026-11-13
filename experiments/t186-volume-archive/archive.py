"""Paired whole-life port occupancy on the nine registered histories."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from math import ceil, floor
from pathlib import Path
from runpy import run_path

import numpy as np
from scipy.stats import beta, t as student

from profiles import NAMES, PERIOD, goes, sepem
from replay import A, CAP, EXP, L, MODEL, RULE, T, THRESHOLDS, W, branch_envelope, selftest


HERE = Path(__file__).resolve().parent
ROBUST = run_path(str(EXP/"native-service-robustness-20261113/check_theory.py"))
EPS = F(1,1000)
N = 128


def inputs_on_history(meta):
    # Same outward rounding as PR 484, including cumulative-sum guards.
    return MODEL["REVIEW"]["Profile"](
        F(ceil(1000*(meta["peak_per_s"]+1e-9)),1000),
        F(ceil(meta["J_old_floor_per_s"]+1e-6)),
        F(ceil(meta["S1"]+1e-5)), F(ceil(meta["S2_per_s"]+1e-5)))


def fixed_period(env):
    q = MODEL["physical"]
    frame = MODEL["FRAME"]
    base = q(RULE.scan,W,RULE.scan.L,env=env)
    increment = W*MODEL["C"]**2*F(37,76)*MODEL["XP"]*frame*env.second
    p = RULE.scan.L + frame*floor((EPS-base)/increment)
    assert p >= RULE.scan.L and q(RULE.scan,W,p,env=env)<=EPS<q(RULE.scan,W,p+frame,env=env)
    return p


def series_summary(low, high, scale=1):
    x, y = low.astype(float)/scale, high.astype(float)/scale
    n = len(x)
    sd = [float(z.std(ddof=1)) for z in (x,y)]
    se = np.asarray(sd)/np.sqrt(n)
    crit = student.ppf(.975,n-1)
    return dict(mean=[round(float(x.mean()),9),round(float(y.mean()),9)],
                sd=[round(s,8) for s in sd],se=[round(float(s),8) for s in se],
                nominal_t95=[round(float(x.mean()-crit*se[0]),8),round(float(y.mean()+crit*se[1]),8)])


def summarize(data, stats, period):
    # [trial, lower/upper, cost_ns / passes / writes / reset cells / returns]
    result = dict(period_ns=period)
    for j,name in enumerate(("busy_s","scans","completed_writes","dirty_cells","returns_to_fast")):
        result[name] = series_summary(data[:,0,j],data[:,1,j],10**9 if j==0 else 1)
    result["mean_pct"] = [round(x*100/PERIOD,10) for x in result["busy_s"]["mean"]]
    if period:
        # The fixed schedule has a known read prefix even past a proof stop.
        # Evaluate the four-address frame independently of the replay.
        complete, remainder = divmod(T,period)
        frames, rem_ns = divmod(min(remainder,L),1400)
        prefix = frames*400+sum(max(0,min(100,rem_ns-offset)) for offset in (0,240,520,760))
        exact_read = complete*A*100+prefix
        assert np.all(data[:,:,1] == complete+int(remainder>0))
        closed = stats[:,2] == 0
        # At most one clipped final write can contribute fractional slot time.
        write_cost = data[closed,:,0]-exact_read-100*data[closed,:,2]
        assert np.all((0<=write_cost)&(write_cost<100))
        result["exact_read_ns"] = int(exact_read)
    open_trials = int(np.count_nonzero(stats[:,2]))
    result.update(branching_trials=int(np.count_nonzero(stats[:,0])), unresolved_trials=open_trials,
                  unresolved_frequency_CP95_upper=float(beta.ppf(.95,open_trials+1,len(stats)-open_trials))
                  if open_trials<len(stats) else 1.)
    return result


def simulate(h, reps):
    idx = NAMES.index(h.name)
    env = inputs_on_history(h.meta)
    common = fixed_period(MODEL["ARCHIVE"])
    local = fixed_period(env)
    periods = dict(ladder=0,fixed_history=int(local*10**9),fixed_all_archives=int(common*10**9))
    records = {k:[] for k in periods}
    states = {k:[] for k in periods}
    marks = hashlib.sha256()
    parents = []
    for rep in range(reps):
        ticks, words, bits, count = h.draw(idx,rep)
        data = (ticks,words,bits)
        for a in data:
            marks.update(len(a).to_bytes(8,"little"))
            marks.update(a.astype("<i8",copy=False).tobytes())
        parents.append(count)
        for name,p in periods.items():
            lo,hi,stat = branch_envelope(data,T,p)
            assert np.all(lo<=hi) and 0<=lo[0]<=hi[0]<=T
            records[name].append((lo,hi))
            states[name].append(stat)
    arrays = {k:np.asarray(v,dtype=np.int64) for k,v in records.items()}
    runs = {k:summarize(v,np.asarray(states[k]),periods[k]) for k,v in arrays.items()}
    for comparison in ("fixed_history","fixed_all_archives"):
        a, b = arrays[comparison], arrays["ladder"]
        runs[comparison]["paired_fixed_minus_ladder_s"] = series_summary(
            a[:,0,0]-b[:,1,0],a[:,1,0]-b[:,0,0],10**9)
        p = F(periods[comparison],10**9)
        runs[comparison]["Q_upper_on_history"] = MODEL["up"](MODEL["physical"](RULE.scan,W,p,env=env),12)
        runs[comparison]["analytic_price_upper_s"] = MODEL["up"](MODEL["fixed_price"](RULE,p,env)[0],3)
    doubling = 2*arrays["ladder"][:,:,0]
    runs["fixed_history"]["paired_fixed_minus_twice_ladder_s"] = series_summary(
        arrays["fixed_history"][:,0,0]-doubling[:,1],arrays["fixed_history"][:,1,0]-doubling[:,0],10**9)
    analytic,_ = RULE.cost(env,MODEL["MEAN"],RULE.eta)
    return dict(name=h.name,history=h.meta,replications=reps,marks_sha256=marks.hexdigest(),
                parents_mean=float(np.mean(parents)),sample_sha256={k:hashlib.sha256(v.astype("<i8").tobytes()).hexdigest()
                for k,v in arrays.items()},bounds_input=dict(peak=str(env.peak),rise=int(env.rise),
                exposure=int(env.exposure),second=int(env.second)), analytic_ladder=analytic, runs=runs)


def class_prices():
    out = dict(addresses=A,words=W,L_ns=L,cap=CAP,nominal_count_thresholds=THRESHOLDS.tolist())
    for name, env in (("geo",MODEL["GEO"]),("archive",MODEL["ARCHIVE"])):
        stair,_ = RULE.cost(env,MODEL["MEAN"],RULE.eta)
        fixed = ROBUST["common_witness"](RULE,W,W,ROBUST["WITNESSES"][name])
        p = fixed_period(env)
        room = fixed/2 - F(stair["s_upper"])
        out[name] = dict(ladder=stair, fixed_best_necessary_s=MODEL["down"](fixed,3),
                         fixed_registered_period_ns=int(p*10**9),
                         fixed_candidate=MODEL["fixed_price"](RULE,p,env)[1],
                         same_map_ratio_lower=MODEL["down"](fixed/F(stair["s_upper"]),5),
                         margin_for_twofold_s=MODEL["down"](room,3),
                         max_extra_resets_if_X0=floor(room/F(stair["reset_fee_s_upper"])) if room>=0 else None)
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path,required=True)
    parser.add_argument("--part",choices=("sepem","goes","all"),default="all")
    parser.add_argument("--pilot",action="store_true",help="two SEPEM seeds, no artifact")
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    selftest()
    if args.pilot:
        v=simulate(sepem(args.cache),2)
        print("Pilot",v["runs"]["ladder"]["busy_s"]["mean"],v["runs"]["fixed_history"]["period_ns"])
        return
    for part in ("sepem","goes"):
        if args.part not in (part,"all"):
            continue
        source = [sepem(args.cache)] if part=="sepem" else goes(args.cache)
        rows = []
        for h in source:
            row=simulate(h,N)
            print(h.name,row["runs"]["ladder"]["busy_s"]["mean"],flush=True)
            rows.append(row)
        out = dict(class_prices=class_prices(),rows=rows) if part=="sepem" else dict(rows=rows)
        path=HERE/(part+".json")
        if args.check:
            assert json.loads(path.read_bytes())==out
        else:
            path.write_text(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8",newline="\n")


if __name__=="__main__":
    main()

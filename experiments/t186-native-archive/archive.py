"""Reproducible fixed-history Monte Carlo estimate and analytic whole-life ceiling."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from math import ceil
from pathlib import Path
from runpy import run_path

import numpy as np
from scipy.stats import beta, t as student

from profiles import EXP, NAMES, PERIOD, goes, sepem
from replay import T, branch_envelope, replay, selftest


HERE = Path(__file__).resolve().parent
MAP = run_path(str(EXP/"t186-native-cost-map/calculate.py"))
RULE = MAP["Ladder"](32768)
N = 128


def analytic(meta):
    # Round out at coarse decimal units, with a guard larger than the checked
    # reconstruction/float summation error. The accepted floor b0 also covers b1.
    env = MAP["REVIEW"]["Profile"](F(ceil(1000*(meta["peak_per_s"]+1e-9)),1000),
                                  F(ceil(meta["J_old_floor_per_s"]+1e-6)),
                                  F(ceil(meta["S1"]+1e-5)),F(ceil(meta["S2_per_s"]+1e-5)))
    cost,q = RULE.cost(env,MAP["MEAN"],RULE.eta)
    assert q < F(1,1000)
    return dict(S1_upper=int(env.exposure),S2_upper_per_s=int(env.second),peak_upper=str(env.peak),
                J_upper=str(env.rise),background_lower=str(MAP["B0"]),**cost)


def simulate(hist, idx):
    results = []
    marks = hashlib.sha256()
    for rep in range(N):
        ticks,words,bits,parents = hist.draw(idx,rep)
        for a in (ticks,words,bits):
            marks.update(len(a).to_bytes(8,"little"))
            marks.update(a.astype("<i8",copy=False).tobytes())
        coarse = replay(ticks,words,bits,T)
        read,write,scans,repairs,tail,stop,_ = coarse
        bounds = branch_envelope((ticks,words,bits),T,coarse)
        assert read+write<=bounds[0]<=bounds[1]<=read+write+tail
        results.append((read,write,scans,repairs,tail,stop,parents,len(words),
                        *bounds))
    counts = np.array(results,dtype=np.int64)
    coarse_lo = (counts[:,0]+counts[:,1])/1e9
    coarse_hi = coarse_lo+counts[:,4]/1e9
    lo,hi = counts[:,8]/1e9,counts[:,9]/1e9
    low,high = float(lo.mean()),float(hi.mean())
    se0,se1 = (float(x.std(ddof=1)/np.sqrt(N)) for x in (lo,hi))
    crit = student.ppf(.975,N-1)
    stopped = int(np.count_nonzero(counts[:,5]))
    open_end = int(np.count_nonzero(counts[:,12]))
    output = dict(realizations=N,coarse_stops=stopped,
                  coarse_double=int(np.count_nonzero(counts[:,5]==1)),
                  coarse_single_aperture=int(np.count_nonzero(counts[:,5]==2)),
                  coarse_complex_aperture=int(np.count_nonzero(counts[:,5]==3)),
                  unresolved_trials=open_end,
                  coarse_mean_s=[round(float(coarse_lo.mean()),3),round(float(coarse_hi.mean()),3)],
                  mean_lower_s=round(low,6),mean_upper_s=round(high,6),
                  sample_mean_branch_width_s=float(np.sum(counts[:,9]-counts[:,8]))/(N*1e9),
                  mean_lower_pct=round(100*low/PERIOD,9),mean_upper_pct=round(100*high/PERIOD,9),
                  se_lower_s=round(se0,3),se_upper_s=round(se1,3),
                  nominal_t95_s=[round(low-crit*se0,3),round(high+crit*se1,3)],
                  unresolved_rate_one_sided_CP95_upper=float(beta.ppf(.95,open_end+1,N-open_end)) if open_end<N else 1.,
                  average_scans_before_coarse_stop=float(counts[:,2].mean()),
                  average_completed_writes_before_coarse_stop=float(counts[:,3].mean()),
                  mean_full_horizon_scans_range=counts[:,13:15].mean(axis=0).tolist() if not open_end else None,
                  mean_full_horizon_repairs_range=counts[:,15:17].mean(axis=0).tolist() if not open_end else None,
                  average_read_prefix_s=round(float(counts[:,0].mean()/1e9),6),
                  average_write_prefix_s=round(float(counts[:,1].mean()/1e9),9),
                  mean_parents=float(counts[:,6].mean()),mean_inversions=float(counts[:,7].mean()),
                  marks_sha256=marks.hexdigest(),trials_sha256=hashlib.sha256(counts.astype("<i8").tobytes()).hexdigest(),
                  stopped_trials=[dict(rep=i,prefix_ns=int(counts[i,0]+counts[i,1]),
                                       unpriced_ns_upper=int(counts[i,4]),reason=int(counts[i,5]),
                                       branched_lo_ns=int(counts[i,8]),branched_hi_ns=int(counts[i,9]),
                                       branch_nodes=int(counts[i,10]),leaves=int(counts[i,11]),open_leaves=int(counts[i,12]))
                                  for i in np.flatnonzero(counts[:,5]).tolist()])
    return {"name":hist.name,"history":hist.meta,"sample":output,"analytic":analytic(hist.meta)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache",type=Path,required=True)
    parser.add_argument("--part",choices=("sepem","goes","all"),default="all")
    parser.add_argument("--check",action="store_true")
    args = parser.parse_args()
    selftest()
    for part in ("sepem","goes"):
        if args.part not in (part,"all"):
            continue
        source = [sepem(args.cache)] if part=="sepem" else goes(args.cache)
        rows = []
        for h in source:
            row = simulate(h,NAMES.index(h.name))
            rows.append(row)
            print(h.name,row["sample"]["mean_lower_s"],row["sample"]["mean_upper_s"],
                  row["sample"]["se_lower_s"],row["analytic"]["s_upper"],flush=True)
        path = HERE/f"{part}.json"
        if args.check:
            assert rows==json.loads(path.read_bytes()), path
        else:
            path.write_text(json.dumps(rows,indent=2,ensure_ascii=False,allow_nan=False)+"\n",
                            encoding="utf-8",newline="\n")


if __name__=="__main__":
    main()

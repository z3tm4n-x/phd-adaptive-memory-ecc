"""Compile both experiments, replay paired paths and reduce each history separately."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from statistics import mean, stdev
import subprocess

from original import HERE, NAMES, prepare

TRIALS = 1500
T = 315576000
Z = 1.959963984540054


def wilson(k,n):
    q = k/n
    den = 1+Z*Z/n
    center = (q+Z*Z/(2*n))/den
    half = Z*math.sqrt(q*(1-q)/n+Z*Z/(4*n*n))/den
    return [0 if k==0 else max(0,center-half),1 if k==n else min(1,center+half)]


def raw_baseline():
    groups = defaultdict(list)
    for line in (HERE/"original-stdout.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("p"):
            profile = line[1]
        else:
            label,q,se,scan = re.fullmatch(r"\s*(\S+)\s+Q=(\S+) \+-(\S+)\s+scanning=(\S+)% of time",line).groups()
            count = round(float(q)*TRIALS)
            assert format(count/TRIALS,".4f")==q
            groups[profile].append(dict(label=label,failures=count,wilson95=wilson(count,TRIALS),
                                        printed_q=q,printed_se=se,stopped_scan_pct=float(scan)))
    return groups


def simulate(work,scenario,name):
    path = work/(name+"-"+scenario+".tsv")
    with path.open("wb") as out:
        subprocess.run(["./replay","p"+name+".txt",str(TRIALS),scenario],cwd=work,stdout=out,check=True)
    print("completed",scenario,name,flush=True)
    return path


def reduce(path,scenario,name,raw):
    buckets = defaultdict(list)
    with path.open(encoding="ascii") as stream:
        fields = next(stream).split()
        for line in stream:
            r = dict(zip(fields,line.split(),strict=True))
            rule = r.pop("rule")
            buckets[rule].append({k:int(v) for k,v in r.items()})
    phys = scenario=="ge"
    rows = {}
    for i,(rule,runs) in enumerate(buckets.items()):
        assert [r["trial"] for r in runs] == list(range(TRIALS))
        assert all(r["flips"]==buckets["fixed4"][j]["flips"] for j,r in enumerate(runs))
        hits = sum(r["fail"] for r in runs)
        def avg(key):
            return mean(r[key] for r in runs)
        result = dict(failures=hits,Q_MC=hits/TRIALS,wilson95=wilson(hits,TRIALS),
                      mean_passes=avg("passes"),mean_word_reads=avg("reads"),mean_repairs=avg("repairs"),
                      mean_fast_s=None if rule.startswith("fixed") else avg("fast_ns")/1e9,
                      mean_switches=avg("switches"),full_scan_pct=100*avg("scan_ns")/(T*1e9),
                      trials_with_partial=sum(r["partial_reads"]>0 for r in runs),
                      trials_with_idle_tail_hits=sum(r["idle_tail_hits"]>0 for r in runs),
                      first_in_idle_tail=sum(r["tail_first"] for r in runs),
                      total_hits_in_visited_apertures=sum(r["aperture_hits"] for r in runs))
        if phys:
            costs = [(240*r["reads"]+260*r["repairs"])/1e9 for r in runs]
            fixed = buckets["fixed1"]
            diffs = [((240*s["reads"]+260*s["repairs"])/1e9)-v for s,v in zip(fixed,costs)]
            result.update(read_bus_s=240*avg("reads")/1e9,repair_bus_s=260*avg("repairs")/1e9,
                          bus_s=mean(costs),bus_pct=100*mean(costs)/T,
                          bus_MC_se_s=stdev(costs)/math.sqrt(TRIALS),
                          paired_saved_vs_fixed1_s=mean(diffs),paired_saving_MC_se_s=stdev(diffs)/math.sqrt(TRIALS),
                          fast_pct=None if rule.startswith("fixed") else 100*avg("fast_ns")/(T*1e9))
            writes_peak=max(r["max_writes_window"] for r in runs)
            result.update(max_writes_intersecting_1ms_upper=writes_peak,
                          nominal_path_peak_lower_pct=34.296,
                          nominal_path_peak_upper_pct=(342960+260*writes_peak)/10000)
        else:
            result.update(source=raw[name][i],new_minus_original_failures=hits-raw[name][i]["failures"])
        rows[rule] = result
    first_bucket=next(iter(buckets.values()))
    return dict(sha256_trial_table=sha256(path.read_bytes()).hexdigest(),
                mean_inversions=mean(r["flips"] for r in first_bucket),rows=rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--check",action="store_true")
    p.add_argument("--reduce-only",action="store_true")
    p.add_argument("--jobs",default=4,type=int)
    args=p.parse_args()
    work=args.work.resolve()
    prepare(args.zip,work)
    subprocess.run(["gcc","-std=c11","-O3","-Wall","-Wextra",str(HERE/"replay.c"),"-I"+str(work),"-lm",
                    "-o",str(work/"replay")], check=True)
    subprocess.run([str(work/"replay"),"--test"],check=True)
    jobs=[(s,k) for k in NAMES for s in ("ideal","ge")]
    if not args.reduce_only:
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            list(pool.map(lambda job:simulate(work,*job),jobs))
    raw=raw_baseline()
    for s in ("ideal","ge"):
        result={k:reduce(work/(k+"-"+s+".tsv"),s,k,raw) for k in NAMES}
        output=json.dumps(result,indent=2,allow_nan=False)+"\n"
        dest=HERE/(s+"-results.json")
        if args.check:
            if dest.read_text(encoding="utf-8")!=output: raise ValueError("Different results: "+s)
        else:
            dest.write_text(output,encoding="utf-8",newline="\n")


if __name__=="__main__":
    main()

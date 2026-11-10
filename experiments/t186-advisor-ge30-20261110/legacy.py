"""Faithful binary64 prefix comparison and explicitly continued source-clock cost."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from statistics import mean
import subprocess
from original import HERE,NAMES,prepare
from run import raw_baseline,wilson,TRIALS,T


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--work",type=Path,required=True)
    cli.add_argument("--zip",type=Path,required=True)
    cli.add_argument("--check",action="store_true")
    args=cli.parse_args(); work=args.work.resolve();prepare(args.zip,work)
    subprocess.run(["gcc","-O2","-std=c11",str(HERE/"legacy.c"),"-I"+str(work),"-lm","-o",str(work/"legacy")],check=True)
    def one(k):
        path=work/(k+"-legacy.tsv")
        with path.open("wb") as dest:
            subprocess.run(["./legacy","p"+k+".txt",str(TRIALS),"rules.txt"],cwd=work,stdout=dest,check=True)
        rows=defaultdict(list)
        with path.open(encoding="ascii") as stream:
            fields=next(stream).split()
            for line in stream:
                r=dict(zip(fields,line.split(),strict=True))
                rows[r.pop("rule")].append({name:int(v) for name,v in r.items()})
        result={}
        for i,(tag,records) in enumerate(rows.items()):
            src=sum(r["raw_fail"] for r in records)
            assert src==raw_baseline()[k][i]["failures"] and len(records)==TRIALS
            failures=sum(r["corrected_fail"] for r in records)
            result[tag]=dict(raw_failures=src,corrected_failures=failures,wilson95=wilson(failures,TRIALS),
                paired_disagreements=sum(r["raw_fail"]!=r["corrected_fail"] for r in records),
                first_failures_in_idle_tail=sum(r["tail_first"] for r in records),
                trials_with_idle_tail_hits=sum(r["tail_hits"]>0 for r in records),
                mean_reads=mean(r["reads"] for r in records),mean_repairs=mean(r["repairs"] for r in records),
                full_scan_pct=100*.012845056*mean(r["reads"] for r in records)/(656*T),
                mean_fast_s=mean(r["fast_ns"] for r in records)/1e9 if i else None,
                mean_switches=mean(r["switches"] for r in records))
        print("checked legacy",k,flush=True)
        return k,result
    with ThreadPoolExecutor(max_workers=4) as pool: results=dict(pool.map(one,NAMES))
    path=HERE/"legacy-results.json"; text=json.dumps(results,indent=2)+"\n"
    if args.check: assert path.read_text(encoding="utf-8")==text
    else: path.write_text(text,encoding="utf-8",newline="\n")


if __name__=="__main__":
    main()

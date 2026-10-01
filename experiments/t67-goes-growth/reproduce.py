"""One-command frozen-input reproduction; never refresh or patch source bytes."""
from __future__ import annotations
import argparse
import csv
import gzip
import json
from pathlib import Path
import subprocess
import sys
import analyze
import selection

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache",type=Path,required=True,help="External data/cache directory (not tracked by Git)")
    p.add_argument("--out",type=Path,required=True,help="Generated tables and figures")
    p.add_argument("--reference",type=Path,default=HERE/"outputs")
    args=p.parse_args()
    args.cache.mkdir(parents=True,exist_ok=True)
    args.out.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,"-B","-m","unittest","discover","-s",str(HERE),"-p","test_*.py","-v"],check=True)
    manifest=json.loads((args.reference/"source_manifest.json").read_text())
    with gzip.open(args.reference/"archive_files.csv.gz","rt",newline="") as f:
        files=list(csv.DictReader(f))
    for row in files:
        row["satellite"],row["cadence_s"]=int(row["satellite"]),int(row["cadence_s"])
        row["selected_version"]=row["selected_version"]=="True"
    inv={"files":files,"indexes":json.loads((args.reference/"archive_indexes.json").read_text()),"catalogue":manifest["catalogue"]}
    pinned=selection.download(manifest,args.cache/"raw",args.cache/"verified_manifest.json")
    analyze.main(pinned,inv,args.cache/"raw",args.out)
    from checks import integration_checks
    from supplement import supplement
    from figures import make_figures
    integration_checks(pinned,args.cache/"raw",args.out)
    supplement(pinned,args.cache/"raw",args.cache/"series",args.out)
    make_figures(pinned,args.cache/"series",args.out)
    print("T67 reproduction complete. Sources verified; future/continuous coverage NOT certified.")


if __name__=="__main__":
    main()

"""Reproduce the two author files unchanged on Linux. Keep the private input outside Git."""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
import json
import os
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
NAMES = "ABCDEFGH"
FILES = {"advisor_sanity_model.c":"57321dff441c71e6e65ff51298c3466454ab5ec5acb1a360d151417e13eac8ab",
         "advisor_make_profiles.py":"f7a9b00011acacde1c5c5aaa78f55f8de522cf36b5fcc019a3aca898dd9a0146"}


def prepare(archive, work):
    work.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for name,digest in FILES.items():
            data = z.read(name)
            if sha256(data).hexdigest() != digest:
                raise ValueError("Different private input: "+name)
            (work/name).write_bytes(data)
    subprocess.run([sys.executable,"advisor_make_profiles.py"],cwd=work,check=True)
    subprocess.run(["gcc","-O2","-o","original","advisor_sanity_model.c","-lm"],cwd=work,check=True)


def run(work):
    rules = (work/"rules.txt").read_bytes()
    def one(name):
        p = subprocess.run(["./original","656","39","0.012845056","315576000","p"+name+".txt","1500","1","2"],
                           cwd=work,input=rules,stdout=subprocess.PIPE,check=True)
        print("original",name,flush=True)
        return p.stdout
    with ThreadPoolExecutor(max_workers=min(4,os.cpu_count() or 1)) as pool:
        return b"".join(pool.map(one,NAMES))


def main():
    p = ArgumentParser(description=__doc__)
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--check",action="store_true")
    p.add_argument("--prepare-only",action="store_true")
    args = p.parse_args()
    work = args.work.resolve()
    if work.is_relative_to(HERE.parents[1]):
        raise ValueError("Use a private directory outside the repository")
    prepare(args.zip,work)
    if args.prepare_only:
        return
    data = run(work)
    target = HERE/"original-stdout.txt"
    if args.check:
        assert target.read_bytes().replace(b"\r\n",b"\n")==data
    else:
        target.write_bytes(data)


if __name__=="__main__":
    main()

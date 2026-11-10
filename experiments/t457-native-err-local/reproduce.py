"""One-command fresh model execution, independent replay and price check."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from build_model import HERE, PINS, verify_inputs
from cases import CASES, capture
from oracle import audit
from gates import verify, sentinels
from bounds import calculate
from window_audit import check as window_check

def extract(work):
    chunks=[]
    for name in ("clean","last_check_bit","one_birth_two_alias_ERR","terminal_inside_write","loss_and_requalification",
                 "one_tick_late_and_stale","all_rungs_long_pause","post_stop_accounting"):
        short=name in ("clean","last_check_bit","one_birth_two_alias_ERR","terminal_inside_write","post_stop_accounting")
        chunks.append("# "+name+(" (full)" if short else " (selected cuts, installs and next starts)"))
        with (work/(name+".trace")).open() as src:
            for line in src:
                if "$finish called" in line: continue
                f=line.split(); t=int(f[1])
                if short or (f[0] in ("B","P","C","K") and t//280 in (1280,1282,1283,1284,1536,2816,2818,152576,152832,152833)):
                    chunks.append(line.rstrip())
    return "# First numeric field: local 10 ns tick. No reconstruction of missing rows.\n"+"\n".join(chunks)+"\n"

def evaluate(work):
    verify_inputs()
    for n,h in json.loads((work/"source.json").read_text()).items():
        assert hashlib.sha256((HERE/n).read_bytes()).hexdigest()==h,n
    rows={}
    for n,(case,end,mixed,literal) in CASES.items():
        with (work/(n+".trace")).open() as h: rows[n]=audit(h,case,end,mixed)
    verify(rows)
    # Isolate negative DUTs from both the good traces and previous checker runs.
    with tempfile.TemporaryDirectory() as tmp:
        import shutil
        d=Path(tmp);shutil.copyfile(work/"policy_vpi.vpi",d/"policy_vpi.vpi")
        rejected=sentinels(d)
    result=dict(scope="native x16 reduced functional/clocked model, not chip qualification",
                baseline="34a6875ee0803e46a47e520d6f4bd5e2008ecb80",
                pre_run_contract="3e3c09ac1ae6989a1b466ca94bf7df1d36bd69bd",
                upstream_inputs_sha256={p.relative_to(HERE.parents[1]).as_posix():h for p,h in PINS.items()},
                input_hash_convention="LF canonical for upstream text=auto replay.c; bytes for other inputs",
                execution_sources=json.loads((work/"source.json").read_text()),
                checker_sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest()
                                 for n in ("oracle.py","gates.py","bounds.py","reproduce.py","window_audit.py")},
                scenarios=rows,price=calculate(rows),detected_actual_DUT_mutations=rejected)
    return {"results.json":json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
            "witnesses.txt":extract(work),
            "port-windows.json":json.dumps(window_check(work,rows,result["price"]),indent=2)+"\n"}

def main():
    if not __debug__: raise SystemExit("verification requires enabled assertions")
    p=argparse.ArgumentParser()
    opt=p.add_mutually_exclusive_group()
    opt.add_argument("--record",action="store_true",help="Create previously absent deterministic outputs")
    opt.add_argument("--check",action="store_true",help="Default: compare results byte-for-byte")
    p.add_argument("--from-capture",type=Path,help="Local development: check a retained source-pinned execution")
    args=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        if args.from_capture: work=args.from_capture.resolve()
        else:
            work=Path(tmp)/"capture"; capture(work)
        documents=evaluate(work)
        for name,content in documents.items():
            out=HERE/name
            if args.record and not out.exists(): out.write_bytes(content.encode("utf8"))
            else: assert out.read_bytes()==content.encode("utf8"),("published evidence differs",name)
    print(f"OK: {len(CASES)} model executions, all 8 promotions, 4 RTL sentinels, whole-life price.")
if __name__=="__main__": main()

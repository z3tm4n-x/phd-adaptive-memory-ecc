"""Repeat and preserve the domain-split checkpoint; no accepted outputs edited.

Full run includes old regression, real XPM simulation, safety and routed -1/-2.
Non-closure of STA is a recorded engineering result, NOT a successful gate.
Failure of a functional/proof/source-identity check terminates the run.
"""
import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = BASE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sources():
    own = [p for p in HERE.iterdir() if p.suffix in (".sv", ".py", ".xdc", ".tcl")]
    shared = [BASE/p for p in ("reference.py", "pdr_check.py", "run.py",
                               "rtl/e_backend.sv", "rtl/absolute_calendar.sv")]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(own+shared)}


def command(args, build, name, timeout):
    start = time.monotonic()
    log = build/(name+".log")
    with log.open("w") as stream:
        result = subprocess.run(args, cwd=build, stdout=stream, stderr=subprocess.STDOUT,
                                text=True, timeout=timeout)
    item = {"command": [str(x) for x in args], "exit_code": result.returncode,
            "elapsed_s": round(time.monotonic()-start, 3), "log_sha256": sha(log)}
    print(json.dumps({"step": name, **item}), flush=True)
    if result.returncode:
        raise RuntimeError(name+" failed; inspect "+str(log))
    return item


def summary(out):
    timing=(out/"timing.rpt").read_text()
    fields=re.search(r"WNS\(ns\).*?\n\s*[- ]+\n\s*([-\d.]+)\s+([-\d.]+)\s+(\d+)\s+(\d+)\s+([-\d.]+)\s+([-\d.]+)", timing).groups()
    def slack(name):
        return float(re.search(r"Slack \([A-Z]+\)\s*:\s*([-\d.]+)ns", (out/name).read_text())[1])
    util=(out/"utilization.rpt").read_text()
    def resource(name):
        return float(re.search(r"\|\s*"+re.escape(name)+r"\s*\|\s*([\d.]+)\s*\|",util)[1])
    effective=(out/"effective.xdc").read_text()
    maxima=[float(x) for x in re.findall(r"set_max_delay[^\n]*? ([\d.]+)\s*$",effective,re.M)]
    assert sorted(maxima)==[4.,60.], ("unexpected XPM max-delay envelope",maxima)
    check=(out/"check_timing.rpt").read_text()
    categories={name:int(n) for name,n in re.findall(r"checking (\w+) \((\d+)\)",check)}
    assert categories and not any(categories.values()), categories
    data={"full_WNS_ns":float(fields[0]),"full_TNS_ns":float(fields[1]),
          "setup_failing_endpoints":int(fields[2]),"setup_total_endpoints":int(fields[3]),
          "full_WHS_ns":float(fields[4]),"full_THS_ns":float(fields[5]),
          "fast_register_setup_ns":slack("fast_setup.rpt"),
          "fast_register_hold_ns":slack("fast_hold.rpt"),
          "resources":{x:resource(x) for x in ("Slice LUTs","Slice Registers","Block RAM Tile","DSPs")},
          "check_timing":categories,"XPM_max_delay_ns":maxima,
          "scope":"component OOC; functional non-clock ports virtual; not SRAM/FMC timing"}
    data["component_timing_target_met"]=(data["full_WNS_ns"]>=.2 and data["full_WHS_ns"]>=0)
    return data


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--full",action="store_true",help="also run old regression and both routed grades")
    p.add_argument("--vivado",default="/home/z3tm4n/bin/vivado-wsl")
    args=p.parse_args()
    start=time.monotonic()
    build=BASE/".build"/("split-delivery-"+str(time.time_ns()))
    build.mkdir(parents=True)
    before=sources()
    record={"base":"cc0ce6d7149dc8e69b4dd30c1603b7338ce9c47b",
            "instruction_version":"68982b44ea7b1eb52c7b608b4a16a86c05a2f347",
            "sources":before,"python":sys.version,"system":platform.platform(),
            "build":str(build),"steps":{},"STA":{},
            "scope":"first verifiable components and conditional balance; B remains open"}
    steps=record["steps"]
    steps["balance"]=command([sys.executable,"-B",HERE/"timing_balance.py"],build,"balance",30)
    steps["safety"]=command([sys.executable,"-B",HERE/"prove_lane.py"],build,"safety",240)
    steps["components"]=command([sys.executable,"-B",HERE/"check.py","--vendor","--write","--vivado",args.vivado],build,"components",2400)
    # Bytecode goes only into this ignored build, not next to source inputs.
    steps["compileall"]=command([sys.executable,"-X","pycache_prefix="+str(build/"pycache"),"-m","compileall","-q",HERE],build,"compileall",60)
    if args.full:
        steps["baseline"]=command([sys.executable,"-B",BASE/"run.py","--rtl","--formal","--regression-A"],build,"baseline",1800)
        for grade in (1,2):
            name="grade-"+str(grade)
            out=build/name
            steps[name]=command([args.vivado,"-mode","batch","-nojournal","-nolog",
                                 "-source",HERE/"component_sta.tcl","-tclargs",
                                 "xc7z020clg484-"+str(grade),out],build,name,7200)
            record["STA"][name]=summary(out)
    command([args.vivado,"-version"],build,"vivado-version",90)
    record["vivado_version"]=(build/"vivado-version.log").read_text().strip()
    xpm=Path("/home/z3tm4n/tools/Xilinx/2025.2/Vivado/data/ip/xpm")
    record["installed_vendor_sources"]={str(xpm/rel):sha(xpm/rel) for rel in (
        "xpm_cdc/hdl/xpm_cdc.sv","xpm_cdc/tcl/xpm_cdc_handshake.tcl",
        "xpm_fifo/hdl/xpm_fifo.sv")}
    record["outputs"]={name:sha(HERE/name) for name in ("checks.json","lane_proof.json","timing_balance.json")}
    assert sources()==before, "code or constraints changed during verification"
    archive=HERE/"evidence.zip"
    members=[x for x in build.glob("*.log")]
    if args.full:
        for out in (build/"grade-1",build/"grade-2"):
            members.extend(out.glob("*.rpt"))
            members.extend(out.glob("*.xdc"))
    record["archived_evidence"]={str(x.relative_to(build)):sha(x) for x in sorted(members)}
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for x in sorted(members):
            info=zipfile.ZipInfo(str(x.relative_to(build)))
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,x.read_bytes())
    record["evidence_zip_sha256"]=sha(archive)
    record["elapsed_s"]=round(time.monotonic()-start,3)
    record["B_closed"]=False
    (HERE/"manifest.json").write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"elapsed_s":record["elapsed_s"],"STA":record["STA"],"B_closed":False},indent=2),flush=True)


if __name__=="__main__":
    main()

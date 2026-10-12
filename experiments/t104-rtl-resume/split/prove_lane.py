"""Inductive safety of our real lane under an explicit vendor-boundary abstraction."""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0,str(BASE))
from pdr_check import classify


def main():
    build=BASE/".build"/("split-lane-proof-"+str(time.time_ns()))
    build.mkdir(parents=True)
    source=(HERE/"operation_lane.sv").read_text()
    assertions=(HERE/"formal_lane_contract.sv").read_text()
    assert source.count("endmodule")==1
    instrumented=source.replace("endmodule", assertions+"\nendmodule")
    cases=[]
    for mutant in (False, True):
        name="mutant" if mutant else "actual"
        copy=build/(name+".sv")
        if mutant:
            assert instrumented.count("phase[0] && !return_wr_busy")==1
            code=instrumented.replace("phase[0] && !return_wr_busy", "!return_wr_busy")
        else:
            code=instrumented
        copy.write_text(code)
        script=(f'read_verilog -formal -sv "{copy}" "{HERE}/predecision_guard.sv" '
                f'"{BASE}/rtl/e_backend.sv" "{HERE}/formal_vendor_boundary.sv"; '
                'prep -top formal_lane; flatten; clk2fflogic; opt; '
                f'techmap; opt; abc -g AND; opt_clean; write_aiger -zinit -symbols {name}.aig')
        before=time.monotonic()
        result=subprocess.run(["yosys","-Q","-T","-p",script],cwd=build,text=True,
                              capture_output=True,timeout=90)
        log=result.stdout+result.stderr
        (build/(name+"-synth.log")).write_text(log)
        assert result.returncode==0,log[-3000:]
        header=(build/(name+".aig")).read_bytes().splitlines()[0].decode()
        expected=len(re.findall(r'\bassert\(',assertions))+6
        assert int(header.split()[4])==0, "ordinary outputs exported as properties"
        result=subprocess.run(["yosys-abc","-c",f"read_aiger {name}.aig; pdr -a -v -d -T 60"],
                              cwd=build,text=True,capture_output=True,timeout=90)
        log=result.stdout+result.stderr
        (build/(name+".log")).write_text(log)
        classified=classify(header,log,expected,result.returncode)
        cases.append({"name":name,**classified,"aiger_header":header,
                      "elapsed_s":round(time.monotonic()-before,3),
                      "log_sha256":hashlib.sha256(log.encode()).hexdigest()})
        if mutant and classified["status"]!="disproved":
            raise AssertionError("sentinel not detected")
    report={"cases":cases,"scope":"our lane under nondeterministic vendor boundaries; no XPM/liveness/board proof",
            "assumptions":"RTL initialization, running fast clock; arbitrary queue capacity/valid/payload/loss; no added assumes",
            "source_sha256":hashlib.sha256(source.encode()).hexdigest(),
            "prior_attempts":["four-state SAT required explicit binary boundary inputs",
                              "k-induction30s step timeout; strengthened version180s wall timeout; not negative RTL results"],
            "build":str(build)}
    (HERE/"lane_proof.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    if cases[0]["status"] != "proved":
        raise SystemExit("actual lane safety not proved within the declared limit")


if __name__=="__main__":
    main()

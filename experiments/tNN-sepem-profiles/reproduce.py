"""One offline command, SEPEM_RDS_V2 supplied; raw sources stay outside Git."""
import hashlib
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    start=time.perf_counter()
    out=HERE/"outputs"
    out.mkdir(exist_ok=True)
    commands=[
        ["-m","unittest","discover","-s",str(HERE),"-p","test_*.py","-v"],
        [str(HERE/"audit.py"),*sys.argv[1:]],
        [str(HERE/"baseline.py")],
        [str(HERE/"check_numerics.py")],
        [str(HERE/"pipeline.py"),"--profiles-only"],
        [str(HERE/"finish.py"),"--with-helium"],
        [str(HERE/"check_legacy.py"),"--events",str(out/"events.csv")],
        [str(HERE/"implications.py")],
        ["-m","compileall","-q","-l",str(HERE)],
    ]
    checks=[]
    for i,command in enumerate(commands):
        step=time.perf_counter()
        print("Step",i+1,"/",len(commands),command[0],flush=True)
        result=subprocess.run([sys.executable,"-B",*command],capture_output=True,text=True,encoding="utf-8")
        log=result.stdout+result.stderr
        print(log,flush=True)
        if i==0:
            (out/"tests.txt").write_text(log,encoding="utf-8",newline="\n")
        checks.append({"arguments":command,"returncode":result.returncode,"seconds":time.perf_counter()-step})
        if result.returncode:
            (out/"failed_step.json").write_text(json.dumps(checks[-1],indent=2)+"\n")
            raise SystemExit(result.returncode)
    scientific_json={"analysis_summary.json","baseline_audit.json","gost_convolution.json",
                     "helium_manifest.json","implications.json","input_audit.json",
                     "legacy_transport_comparison.json","numerical_checks.json","transport_manifest.json"}
    scientific=[p for p in sorted(out.iterdir()) if p.suffix in (".csv",".png",".svg") or p.name in scientific_json]
    repo=HERE.parents[1]
    upstream=["experiments/RE-CY62167-PROTON-01/sigma_bit_experimental.csv",
              "experiments/RE-GOES19-PROTON-RATE-01/sigma_model.py",
              "experiments/RE-CY62167-COVERAGE-THRESHOLD-01/recovery/outputs/radar_transport.npz",
              "experiments/t67-goes-growth/response.py",
              "experiments/t67-goes-growth/outputs/reference_events.csv",
              "experiments/t68-v21-inputs/inputs/calc_v18.zip",
              "experiments/t68-v21-inputs/inputs/cosrad_main/sl_x.txt",
              "experiments/t68-v21-inputs/inputs/cosrad_main/sp_x.txt",
              "experiments/t68-v21-inputs/outputs/v21_reconstructed.json",
              "theory/t73-burst-mode-count-inputs.json"]
    receipt={"python":sys.version,"dependencies":{p:importlib.metadata.version(p) for p in ("numpy","scipy","pandas","matplotlib","psutil")},
             "base_commit":json.loads((HERE/"config.json").read_text())["base_commit"],
             "elapsed_seconds":time.perf_counter()-start,"steps":checks,
             "scientific_outputs_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in scientific},
             "source_code_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob("*.py"))},
             "small_inputs_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/"inputs").iterdir()) if p.is_file()},
             "upstream_sources_sha256":{p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in upstream},
             "config_sha256":hashlib.sha256((HERE/"config.json").read_bytes()).hexdigest(),
             "completion":"conditional profile calculations; full R0-A normative replacement not established"}
    (out/"reproduction_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("Conditional calculations reproduced. Accepted rules/certificates unchanged.")

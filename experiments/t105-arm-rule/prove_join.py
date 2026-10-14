"""Reapply accepted admission/join lemma to the ACTUAL T105 executor.

Reuses the disclosed proof contract, not a new independent transport oracle.
"""
import hashlib,importlib.util,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    path=HERE.parent/'t104-rtl-resume/physical/prove_join.py'
    spec=importlib.util.spec_from_file_location('accepted_join',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    source=(HERE/'arm_executor.sv').read_text()
    prefix=source[:source.index('    wire forward_valid,forward_ready')]
    build=HERE/'.build/arm-join';build.mkdir(parents=True,exist_ok=True)
    rows=[]
    for label in ('actual','id-mutant','third-credit'):
        code=prefix+module.CONTRACT
        if label=='id-mutant':code=code.replace('response_data={id_data[63:0],returned_data}',"response_data={id_data[63:0]^64'd1,returned_data}")
        if label=='third-credit':code=code.replace('credits<2','credits<3',1)
        (build/(label+'.sv')).write_text(code)
        cmd=f'read_verilog -formal -sv {label}.sv; prep -top arm_executor; flatten; memory_map; opt; async2sync; opt; chformal -lower; sat -seq 1 -tempinduct -maxsteps 8 -prove-asserts -verify -timeout 40 -dump_json {label}.json'
        run=subprocess.run(['yosys','-Q','-T','-p',cmd],cwd=build,capture_output=True,text=True,timeout=60)
        log=run.stdout+run.stderr;(build/(label+'.log')).write_text(log)
        proved=run.returncode==0 and 'Induction step proven: SUCCESS' in log
        rejected='model found for base case: FAIL' in log
        assert proved if label=='actual' else rejected,log[-2500:]
        rows.append({'case':label,'proved':proved,'counterexample':rejected,'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
    result={'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
      'shared_contract_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cases':rows,
      'scope':'actual T105 admission/ID join; two total credits including held response',
      'assumptions':'ordered metadata XPM FIFO and ordered E responses; separate accepted transport/chain lemmas'}
    (HERE/'outputs/join-proof.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

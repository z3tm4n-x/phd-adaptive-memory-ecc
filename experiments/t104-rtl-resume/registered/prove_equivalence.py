"""All-input inductive miter; old backend is a reference, not shared update code."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
from pdr_check import classify

PORTS={'ready':1,'busy':1,'accepted':1,'rejected':1,'fault':1,'word_out':19,
       'ce':1,'oe':1,'we':1,'drive':1,'alias_high':1,'byte_enable':2,'dq_out':16,
       'sample':1,'flag':1,'err_due':1,'done':1,'release_due':1,
       'commit_pulse':1,'pending':1,'read_data':32,'kind_active':2,'age':8}

def main():
    build=BASE/'.build'/('registered-proof-'+str(time.time_ns()))
    build.mkdir(parents=True)
    harness='''module miter(input wire clk,cold_init,soft_reset,go,
      input wire [1:0] kind,input wire [18:0] word_in,input wire [31:0] data_in,
      input wire [3:0] byte_enable_in,input wire [15:0] dq_in,input wire err_in);
    '''
    inputs='clk,cold_init,soft_reset,go,kind,word_in,data_in,byte_enable_in,dq_in,err_in'.split(',')
    for prefix,module in [('a','e_backend'),('b','e_backend_registered')]:
        harness+='\n'.join(f'wire [{width-1}:0] {prefix}_{name};' for name,width in PORTS.items())+'\n'
        harness+=module+' '+prefix+'('+','.join(f'.{p}({p})' for p in inputs)+','
        harness+=','.join(f'.{p}({prefix}_{p})' for p in PORTS)+');\n'
    harness+='always @(posedge clk) begin\n'
    harness+='\n'.join(f'assert(a_{p}==b_{p});' for p in PORTS)+'\nend\nendmodule\n'
    original=(HERE/'e_backend_registered.sv').read_text()
    results=[]
    for name in ('actual','prevalidated','mutant'):
        mutant=name=='mutant'
        this_harness=harness
        if name=='prevalidated':
            this_harness=this_harness.replace('clk,cold_init,soft_reset,go,','clk,cold_init,soft_reset,raw_go,')
            this_harness=this_harness.replace('input wire err_in);','input wire err_in);\n wire go=raw_go && kind!=3 && byte_enable_in!=0;')
            this_harness=this_harness.replace('e_backend_registered b(','e_backend_registered #(.PREVALIDATED(1)) b(')
        (build/(name+'-miter.sv')).write_text(this_harness)
        assert original.count('step[35] && op==CONTROL')==1
        source=original.replace('step[35] && op==CONTROL','step[36] && op==CONTROL') if mutant else original
        (build/(name+'.sv')).write_text(source)
        # Old FORMAL adds six reachable-state assertions; all are exported too.
        script=(f'read_verilog -formal -sv "{BASE}/rtl/e_backend.sv" "{build}/{name}.sv" "{build}/{name}-miter.sv"; '
                'prep -top miter; flatten; clk2fflogic; opt; techmap; opt; abc -g AND; opt_clean; '
                f'write_aiger -zinit -symbols {name}.aig')
        before=time.monotonic()
        r=subprocess.run(['yosys','-Q','-T','-p',script],cwd=build,capture_output=True,text=True,timeout=180)
        (build/(name+'-synth.log')).write_text(r.stdout+r.stderr)
        assert r.returncode==0,(r.stdout+r.stderr)[-3000:]
        header=(build/(name+'.aig')).read_bytes().splitlines()[0].decode()
        r=subprocess.run(['yosys-abc','-c',f'read_aiger {name}.aig; pdr -a -v -d -T 120'],
                         cwd=build,capture_output=True,text=True,timeout=150)
        log=r.stdout+r.stderr
        (build/(name+'.log')).write_text(log)
        status=classify(header,log,len(PORTS)+6,r.returncode)
        results.append({'case':name,**status,'elapsed_s':time.monotonic()-before,
                        'aiger_header':header,'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
        print(name,status,flush=True)
    report={'source_sha256':hashlib.sha256(original.encode()).hexdigest(),
            'reference_sha256':hashlib.sha256((BASE/'rtl/e_backend.sv').read_bytes()).hexdigest(),
            'scope':'all binary inputs and initialized RTL; no timing/metastability/board assumptions proved',
            'cases':results,'build':str(build)}
    (HERE/'equivalence.json').write_text(json.dumps(report,indent=2)+'\n')
    assert results[0]['status']=='proved',results[0]
    assert results[1]['status']=='proved','legal-go specialization unproved'
    assert results[2]['status']=='disproved','mutation was not rejected'

if __name__=='__main__': main()

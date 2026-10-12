"""All-input equivalence against the unchanged original E, including pins."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
from pdr_check import classify
from registered.prove_equivalence import PORTS

def main():
    build=BASE/'.build'/('physical-e-proof-'+str(time.time_ns()))
    build.mkdir(parents=True)
    inputs='clk,cold_init,soft_reset,go,kind,word_in,data_in,byte_enable_in,dq_in,err_in'.split(',')
    harness='''module miter(input wire clk,cold_init,soft_reset,go,
      input wire [1:0] kind,input wire [18:0] word_in,input wire [31:0] data_in,
      input wire [3:0] byte_enable_in,input wire [15:0] dq_in,input wire err_in);
    wire pad_ce_n,pad_oe_n,pad_we_n;
    wire [1:0] pad_be_n;wire [15:0] pad_t_n;
    '''
    reference=(BASE/'registered/e_backend_registered.sv').read_text()
    (build/'reference.sv').write_text(reference.replace('module e_backend_registered','module e_reference'))
    for prefix,module in [('a','e_reference'),('b','e_backend_registered')]:
        harness+='\n'.join(f'wire [{w-1}:0] {prefix}_{n};' for n,w in PORTS.items())+'\n'
        harness+=module+' '+prefix+'('+','.join(f'.{p}({p})' for p in inputs)+','
        harness+=','.join(f'.{p}({prefix}_{p})' for p in PORTS)
        if prefix=='b':
            harness+=','+','.join(f'.{p}({p})' for p in ['pad_ce_n','pad_oe_n','pad_we_n','pad_be_n','pad_t_n'])
        harness+=');\n'
    harness+='always @(posedge clk) begin\n'
    harness+='\n'.join(f'assert(a_{p}==b_{p});' for p in PORTS)+'\n'
    harness+='assert(pad_ce_n==!a_ce);assert(pad_oe_n==!a_oe);assert(pad_we_n==!a_we);\n'
    harness+="if(a_busy)assert(pad_be_n==~a_byte_enable);else assert(!a_ce);assert(pad_t_n=={16{!a_drive}});\nend\nendmodule\n"
    original=(HERE/'e_backend_registered.sv').read_text()
    results=[]
    for name in ['actual','prevalidated','mutant']:
        h=harness
        if name=='prevalidated':
            h=h.replace('clk,cold_init,soft_reset,go,','clk,cold_init,soft_reset,raw_go,')
            h=h.replace('input wire err_in);','input wire err_in);\n wire go=raw_go && kind!=3 && byte_enable_in!=0;')
            h=h.replace('e_backend_registered b(','e_backend_registered #(.PREVALIDATED(1)) b(')
        (build/(name+'-miter.sv')).write_text(h)
        assert original.count('step[34] && is_control')==1
        s=original.replace('step[34] && is_control','step[35] && is_control') if name=='mutant' else original
        (build/(name+'.sv')).write_text(s)
        script=(f'read_verilog -formal -sv "{build}/reference.sv" "{build}/{name}.sv" "{build}/{name}-miter.sv"; '
                'prep -top miter; flatten; clk2fflogic; opt; techmap; opt; abc -g AND; opt_clean; '
                f'write_aiger -zinit -symbols {name}.aig')
        before=time.monotonic()
        r=subprocess.run(['yosys','-Q','-T','-p',script],cwd=build,capture_output=True,text=True,timeout=180)
        (build/(name+'-synth.log')).write_text(r.stdout+r.stderr)
        assert r.returncode==0,(r.stdout+r.stderr)[-4000:]
        header=(build/(name+'.aig')).read_bytes().splitlines()[0].decode()
        r=subprocess.run(['yosys-abc','-c',f'read_aiger {name}.aig; pdr -a -v -d -T 120'],
                         cwd=build,capture_output=True,text=True,timeout=150)
        log=r.stdout+r.stderr
        (build/(name+'.log')).write_text(log)
        status=classify(header,log,len(PORTS)+6,r.returncode)
        results.append({'case':name,**status,'elapsed_s':time.monotonic()-before,'aiger_header':header,
                        'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
        print(name,status,flush=True)
    report={'source_sha256':hashlib.sha256(original.encode()).hexdigest(),
            'reference_sha256':hashlib.sha256((BASE/'registered/e_backend_registered.sv').read_bytes()).hexdigest(),
            'scope':'All semantic outputs on all initialized binary-input traces. Native byte enables equal while busy; when idle CE is inactive and pre-restoring byte enables is observationally irrelevant. Other native pins equal always. Analog timing separate.',
            'cases':results,'build':str(build)}
    (build/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(build,flush=True)
    assert results[0]['status']=='proved',results[0]
    assert results[1]['status']=='proved',results[1]
    assert results[2]['status']=='disproved',results[2]

if __name__=='__main__': main()

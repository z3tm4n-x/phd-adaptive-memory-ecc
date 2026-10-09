"""One-step generation arithmetic and priority; mission bound is independent."""
import hashlib,json,subprocess,time,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from pdr_check import classify

ASSERTIONS='''
reg proof_past=0;
always @(posedge clk) begin
    proof_past<=1;
    assert(exhausted==(&generation));
    assert(!permitted || (candidate_valid && !loss && !err_event && !invalidate &&
                         !exhausted && candidate_generation==generation));
    if(proof_past) begin
        assert(previous_loss==$past(loss));
        if($past(change && !exhausted)) assert(generation==$past(generation)+64'd1);
        else assert(generation==$past(generation));
    end
end
'''
def main():
    build=HERE.parent/'.build'/('registered-guard-proof-'+str(time.time_ns()));build.mkdir(parents=True)
    source=(HERE/'generation_guard.sv').read_text()
    results=[]
    for mutant in (False,True):
        name='mutant' if mutant else 'actual'
        code=source.replace('&& !err_event','') if mutant else source
        wrapper='''\nmodule formal_guard_wrapper(input wire clk,loss,err_event,invalidate,candidate_valid,
          input wire [63:0] candidate_generation);
          generation_guard dut(.clk(clk),.loss(loss),.err_event(err_event),.invalidate(invalidate),
            .candidate_valid(candidate_valid),.candidate_generation(candidate_generation)); endmodule\n'''
        (build/(name+'.sv')).write_text(code.replace('endmodule',ASSERTIONS+'\nendmodule')+wrapper)
        script=(f'read_verilog -formal -sv {name}.sv; prep -top formal_guard_wrapper; flatten; '
          'clk2fflogic; opt; techmap; opt; abc -g AND; opt_clean; '
          f'write_aiger -zinit -symbols {name}.aig')
        r=subprocess.run(['yosys','-Q','-T','-p',script],cwd=build,capture_output=True,text=True,timeout=90)
        (build/(name+'-synth.log')).write_text(r.stdout+r.stderr)
        assert r.returncode==0,(r.stdout+r.stderr)[-3000:]
        header=(build/(name+'.aig')).read_bytes().splitlines()[0].decode()
        r=subprocess.run(['yosys-abc','-c',f'read_aiger {name}.aig; pdr -a -v -d -T 60'],
                         cwd=build,capture_output=True,text=True,timeout=90)
        log=r.stdout+r.stderr;(build/(name+'.log')).write_text(log)
        # Five source assertions. In the actual implementation the two pure
        # Boolean identities collapse into one constant property in Yosys.
        # The mutant makes the permission assertion nonconstant: five exports.
        expected=5 if mutant else 4
        assert int(header.split()[4])==0,'ordinary outputs must not be properties'
        status=classify(header,log,expected,r.returncode)
        assert status['status']==('disproved' if mutant else 'proved'),status
        results.append({'case':name,**status,'source_assertions':5,'unique_exported':expected,'returncode':r.returncode,
                        'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
    report={'cases':results,'build':str(build),'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
      'scope':'64-bit update, no reset, same-edge priority; no full LOW pipeline timing proof',
      'independent_bound':'contract.json; at most 78894788947889481 fast edges per declared mission'}
    (HERE/'guard_proof.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()

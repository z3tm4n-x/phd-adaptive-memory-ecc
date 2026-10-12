"""Combinational SAT bijection/coverage of actual address_map RTL, plus mutant."""
import hashlib,json,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    build=HERE.parent/'.build'/('physical-map-'+str(time.time_ns()));build.mkdir(parents=True)
    original=(HERE/'address_map.sv').read_text();rows=[]
    harness='''module proof(input [18:0] w0,w1,input h0,h1,input [19:0] arbitrary_address);
    wire [19:0] a0,a1,a2;
    address_map x(w0,h0,a0),y(w1,h1,a1),z(arbitrary_address[19:1],arbitrary_address[0],a2);
    always @* begin
      assert(a0==2*w0+h0);
      assert(a0!=a1 || (w0==w1 && h0==h1));
      assert(a2==arbitrary_address);
      assert((a0>>1)==w0);
    end
    endmodule
    '''
    for label,source in [('normal',original),('collision',original.replace('{word_index,half}',"{word_index,1'b0}"))]:
        (build/(label+'.sv')).write_text(source+harness)
        command=f'read_verilog -formal -sv {label}.sv; prep -top proof; flatten; opt; chformal -lower; sat -prove-asserts -verify -show-inputs -show-outputs'
        r=subprocess.run(['yosys','-Q','-T','-p',command],cwd=build,text=True,capture_output=True,timeout=60)
        log=r.stdout+r.stderr;(build/(label+'.log')).write_text(log)
        proved=r.returncode==0 and 'SUCCESS' in log
        rejected='proof did fail' in log
        assert proved if label=='normal' else rejected,log[-3000:]
        rows.append({'case':label,'proved':proved,'counterexample':rejected})
    result={'cases':rows,'source_sha256':hashlib.sha256(original.encode()).hexdigest(),'build':str(build)}
    (build/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

"""Safety composition using the backend equivalence proved separately at this SHA."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
from pdr_check import classify

def main():
    build=BASE/'.build'/('registered-lane-proof-'+str(time.time_ns()));build.mkdir(parents=True)
    eq=json.loads((HERE/'equivalence.json').read_text())
    assert all(x['status']=='proved' for x in eq['cases'][:2])
    assert eq['source_sha256']==hashlib.sha256((HERE/'e_backend_registered.sv').read_bytes()).hexdigest()
    old=(BASE/'rtl/e_backend.sv').read_text()
    assert eq['reference_sha256']==hashlib.sha256((BASE/'rtl/e_backend.sv').read_bytes()).hexdigest()
    old=old.replace('module e_backend #','module e_backend_registered #').replace(
        'parameter integer WORD_BITS = 19','parameter integer PREVALIDATED=0, parameter integer WORD_BITS = 19')
    (build/'equivalent_backend.sv').write_text(old)
    boundary=(BASE/'split/formal_vendor_boundary.sv').read_text()
    boundary+='''\nmodule slow_queue #(parameter WIDTH=64)(input wire clk,rst,in_valid,out_ready,
      input wire [WIDTH-1:0] in_data,output wire in_ready,out_valid,
      output wire [WIDTH-1:0] out_data,output wire wr_busy,rd_busy);
      (* anyseq *) reg cap,val,bw,br; (* anyseq *) reg [WIDTH-1:0] payload;
      assign in_ready=cap; assign out_valid=val; assign wr_busy=bw; assign rd_busy=br;
      assign out_data=payload; endmodule\n'''
    (build/'boundary.sv').write_text(boundary)
    assertions=(HERE/'lane_assertions.sv').read_text()
    source=(HERE/'operation_lane.sv').read_text()
    instrumented=source.replace('endmodule',assertions+'\nendmodule')
    results=[]
    for mutant in (False,True):
        name='mutant' if mutant else 'actual'
        code=instrumented.replace('receive_idle && !receipt && !return_wr_busy','!receipt && !return_wr_busy') if mutant else instrumented
        (build/(name+'.sv')).write_text(code)
        script=(f'read_verilog -formal -sv "{build}/{name}.sv" "{HERE}/generation_guard.sv" '
          f'"{build}/equivalent_backend.sv" "{build}/boundary.sv"; prep -top formal_lane; flatten; '
          f'clk2fflogic; opt; techmap; opt; abc -g AND; opt_clean; write_aiger -zinit -symbols {name}.aig')
        r=subprocess.run(['yosys','-Q','-T','-p',script],cwd=build,capture_output=True,text=True,timeout=90)
        (build/(name+'-synth.log')).write_text(r.stdout+r.stderr)
        assert r.returncode==0,(r.stdout+r.stderr)[-3000:]
        header=(build/(name+'.aig')).read_bytes().splitlines()[0].decode()
        r=subprocess.run(['yosys-abc','-c',f'read_aiger {name}.aig; pdr -a -v -d -T 60'],
                         cwd=build,capture_output=True,text=True,timeout=90)
        log=r.stdout+r.stderr;(build/(name+'.log')).write_text(log)
        status=classify(header,log,len(re.findall(r'\bassert\(',assertions))+6,r.returncode)
        results.append({'case':name,**status,'log_sha256':hashlib.sha256(log.encode()).hexdigest(),'header':header})
        print(name,status,flush=True)
    report={'cases':results,'build':str(build),'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
      'scope':'fast lane cutpoint safety, not FIFO ordering/liveness/full system',
      'composition':'backend replaced by old RTL using separately proved all-input equivalence',
      'assumptions':'initialized RTL, binary inputs, running clock; arbitrary vendor boundary; no added assumes'}
    (HERE/'lane_proof.json').write_text(json.dumps(report,indent=2)+'\n')
    assert results[0]['status']=='proved' and results[1]['status']=='disproved',results

if __name__=='__main__': main()

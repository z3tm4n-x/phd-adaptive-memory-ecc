"""Actual admission arithmetic, composed with the metadata-FIFO count contract.

This proves the two-credit bound including held replies. It does NOT assume
or prove correctness of response data, payload transport or physical service.
"""
import hashlib,json,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
CONTRACT=r'''
(* anyseq *) reg pf_capacity,pf_return,pf_running;
(* anyseq *) reg [64:0] pf_id;
reg [4:0] pf_metadata_count=0;
assign running_slow=pf_running;
assign forward_capacity=pf_capacity;
assign returned_valid=pf_return;
assign returned_data=0;
assign id_data=pf_id;
assign id_capacity=pf_metadata_count<16;
assign id_valid=pf_metadata_count!=0;
always @(posedge slow_clk) begin
 // Standard lossless FIFO count semantics, depth16 as the actual slow_queue.
 case({capture,consume})
 2'b10:pf_metadata_count<=pf_metadata_count+1'b1;
 2'b01:pf_metadata_count<=pf_metadata_count-1'b1;
 endcase
 assert(credits<=2);
 assert(credits==pf_metadata_count);
 assert(!(request_ready[0] && request_ready[1]));
 assert(!capture || (credits<2 && forward_capacity && id_capacity && legal));
 assert(!consume || credits>0);
end
endmodule
'''

def main():
 source=(HERE/'executor.sv').read_text()
 # Keep the actual declarations, ready selection, capture/consume and
 # credit transition verbatim. Replace only the rest of the system by the
 # explicitly stated FIFO-count interface contract (not a helper oracle).
 code=source[:source.index('    wire forward_valid,forward_ready')]+CONTRACT
 build=HERE.parent/'.build'/('integrated-admission-'+str(time.time_ns()));build.mkdir(parents=True)
 (build/'proof.sv').write_text(code)
 command='read_verilog -formal -sv proof.sv; prep -top integrated_executor; flatten; opt; async2sync; opt; sat -seq 1 -tempinduct -maxsteps 6 -prove-asserts -verify -timeout 30'
 r=subprocess.run(['yosys','-Q','-T','-p',command],cwd=build,text=True,capture_output=True,timeout=60)
 log=r.stdout+r.stderr;(build/'proof.log').write_text(log)
 passed=r.returncode==0 and 'Induction step proven: SUCCESS' in log
 result=dict(status='proved' if passed else 'not proved',engine='SAT induction',properties=5,
   source_sha256=hashlib.sha256(source.encode()).hexdigest(),
   scope='two shared credits including in-flight and held response; admission/metadata-count conservation',
   assumption='ordered lossless metadata FIFO count contract; arbitrary data/return availability, no payload or backend proof',
   log_sha256=hashlib.sha256(log.encode()).hexdigest(),build=str(build))
 (build/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 assert passed,log[-4000:]
if __name__=='__main__':main()

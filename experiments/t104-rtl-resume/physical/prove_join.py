"""Actual slow admission/return join, not merely a credit-count proof."""
import hashlib,json,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
CONTRACT=r'''
(* anyseq *) reg arbitrary_capacity,arbitrary_return,arbitrary_running;
(* anyseq *) reg [32:0] arbitrary_result;
// Trusted XPM ordered metadata FIFO, implemented here as a circular array.
// Actual bound<=2 makes depth2 equivalent to the production depth16.
reg [64:0] meta[0:1];
reg wp=0,rp=0;
reg [4:0] metadata_count=0;
initial begin meta[0]=0;meta[1]=0;end
assign running_slow=arbitrary_running;
assign forward_capacity=arbitrary_capacity;
assign returned_valid=arbitrary_return;
assign returned_data=arbitrary_result;
assign id_data=meta[rp];
assign id_capacity=metadata_count<16;
assign id_valid=metadata_count!=0;
// Independent shift-register history, including ID/owner and payload.
// A returned payload is the next completed E response by transport+fast
// lemmas. This proof checks that the actual join pairs its matching ID.
reg [121:0] first=0,second=0;
reg [1:0] reference_count=0;
always @(posedge slow_clk) begin
 if(capture) begin meta[wp]<={owner,chosen[120:57]};wp<=!wp;end
 if(consume) rp<=!rp;
 case({capture,consume})
 2'b10:begin
  metadata_count<=metadata_count+1'b1;
  reference_count<=reference_count+1'b1;
  if(reference_count==0) first<={owner,chosen};else second<={owner,chosen};
 end
 2'b01:begin metadata_count<=metadata_count-1'b1;reference_count<=reference_count-1'b1;first<=second;end
 2'b11:begin
  if(reference_count==1) first<={owner,chosen};
  else begin first<=second;second<={owner,chosen};end
 end
 endcase
 assert(credits<=2);
 assert(reference_count==metadata_count && credits==metadata_count);
 assert((wp==rp)==(reference_count!=1));
 if(id_valid) assert(id_data=={first[121],first[120:57]});
 if(|response_valid) begin
  assert(reference_count>0);
  assert(response_data=={first[120:57],arbitrary_result});
  assert(response_valid==(first[121]?2'b10:2'b01));
 end
 assert(!consume || credits>0);
 assert(!capture || (credits<2 && forward_capacity && id_capacity && legal));
 assert(!(request_ready[0] && request_ready[1]));
 if(capture) assert(chosen==(owner?request_data[241:121]:request_data[120:0]));
end
endmodule
'''
def main():
    source=(HERE/'executor.sv').read_text()
    code=source[:source.index('    wire forward_valid,forward_ready')]+CONTRACT
    build=BASE/'.build'/('physical-join-'+str(time.time_ns()));build.mkdir(parents=True)
    rows=[]
    for label in ['actual','id-mutant','third-credit']:
        s=code
        if label=='id-mutant':s=s.replace('response_data={id_data[63:0],returned_data}',"response_data={id_data[63:0]^64'd1,returned_data}")
        if label=='third-credit':s=s.replace('credits<2','credits<3',1)
        (build/(label+'.sv')).write_text(s)
        cmd=f'read_verilog -formal -sv {label}.sv; prep -top integrated_executor; flatten; memory_map; opt; async2sync; opt; chformal -lower; sat -seq 1 -tempinduct -maxsteps 8 -prove-asserts -verify -timeout 40 -show-all -dump_json {label}-counterexample.json'
        r=subprocess.run(['yosys','-Q','-T','-p',cmd],cwd=build,text=True,capture_output=True,timeout=80)
        log=r.stdout+r.stderr;(build/(label+'.log')).write_text(log)
        proved=r.returncode==0 and 'Induction step proven: SUCCESS' in log
        rejected='model found for base case: FAIL' in log or 'SAT proof finished - model found' in log
        rows.append({'case':label,'proved':proved,'counterexample':rejected,'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
        print(rows[-1],flush=True)
        assert proved if label=='actual' else rejected,log[-4000:]
    result={'build':str(build),'cases':rows,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'contract':'ordered metadata XPM FIFO; ordered E response channel from transport+chain lemmas',
            'scope':'full64-bit ID, owner, response pairing, two credits incl held reply'}
    (build/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(build)
if __name__=='__main__':main()


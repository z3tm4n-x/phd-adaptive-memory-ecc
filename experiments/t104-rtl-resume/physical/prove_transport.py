"""The real handshake wrapper under the declared four-phase XPM contract.

Clock enables model arbitrary interleavings, including simultaneous edges.
No assertion about analog metastability; standard digital synchronizer
progress is assumed. All wrapper capture/hold/ack logic is kept verbatim.
"""
import hashlib,json,subprocess,time,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
from pdr_check import classify

VENDOR=r'''
 // Trusted XPM digital contract: registered source packet/send,3-stage
 // synchronization, registered destination request/data;3-stage return ACK.
 // Independent abstract implementation, not redistributed vendor code.
 reg [2:0] req_pipe=0,ack_pipe=0;
 reg launch=0,arrived=0,observed=0;
 reg [WIDTH-1:0] source_packet=0;
 reg [WIDTH-1:0] vendor_packet=0;
 assign requested=arrived;
 assign received=ack_pipe[2];
 assign out_data=vendor_packet;
 always @(posedge proof_clk) begin
  if(dest_edge) begin
   req_pipe<={req_pipe[1:0],launch};
   arrived<=req_pipe[2];observed<=req_pipe[2];
   if(req_pipe[2] && !observed) vendor_packet<=source_packet;
  end
  if(src_edge) begin
   ack_pipe<={ack_pipe[1:0],acknowledged};
   launch<=send;
   if(!launch) source_packet<=hold_data;
  end
 end
 reg live=0;
 reg [WIDTH-1:0] expected=0;
 wire input_take=src_edge && in_valid && in_ready;
 wire output_take=dest_edge && out_valid && out_ready;
 always @(posedge proof_clk) begin
  if(input_take) begin expected<=in_data;live<=1;end
  if(output_take) live<=0;
  assert(!input_take || !live);
  assert(!output_take || live);
  if(out_valid) assert(live && out_data==expected);
  assert(!live || occupied);
  if(capture) assert(occupied && snapshot==expected);
  if(send) assert(hold_data==expected);
  assert(!send || occupied);
  assert(!await_drop || occupied);
  assert(!acknowledged || !out_valid);
 end
endmodule
'''
def main():
    original=(BASE/'registered/handshake_channel.sv').read_text()
    code=original[:original.index('    xpm_cdc_handshake')]
    code=code.replace('input wire src_clk,dest_clk,src_rst,dest_rst,',
                      'input wire proof_clk,src_edge,dest_edge,')
    code=code.replace('!occupied && !src_rst','!occupied').replace(' && !dest_rst','')
    code=code.replace('always @(posedge src_clk) begin','always @(posedge proof_clk) if(src_edge) begin')
    code=code.replace('always @(posedge dest_clk) begin','always @(posedge proof_clk) if(dest_edge) begin')
    code+=VENDOR
    code+='''\nmodule proof(input proof_clk,src_edge,dest_edge,in_valid,out_ready,in_data);
 handshake_channel #(.WIDTH(1)) dut(.proof_clk(proof_clk),.src_edge(src_edge),.dest_edge(dest_edge),
  .in_valid(in_valid),.out_ready(out_ready),.in_data(in_data));
 endmodule\n'''
    build=BASE/'.build'/('physical-transport-'+str(time.time_ns()));build.mkdir(parents=True)
    rows=[]
    for label in ['actual','stale-payload','repeat']:
        s=code
        if label=='stale-payload':s=s.replace('hold_data<=snapshot','hold_data<=in_data')
        if label=='repeat':s=s.replace('requested && !acknowledged','requested')
        (build/(label+'.sv')).write_text(s)
        # Payload bits do not control this wrapper; one arbitrary-bit theorem
        # extends pointwise to all WIDTH bits (121/160/57/33/32).
        command=f'read_verilog -formal -sv {label}.sv; prep -top proof; flatten; opt; clk2fflogic; opt; techmap; opt; abc -g AND; opt_clean; write_aiger -zinit -symbols {label}.aig'
        r=subprocess.run(['yosys','-Q','-T','-p',command],cwd=build,text=True,capture_output=True,timeout=90)
        log=r.stdout+r.stderr;(build/(label+'-synth.log')).write_text(log)
        assert r.returncode==0,log[-4000:]
        header=(build/(label+'.aig')).read_bytes().splitlines()[0].decode()
        count=int(header.split()[6]);assert int(header.split()[4])==0
        r=subprocess.run(['yosys-abc','-c',f'read_aiger {label}.aig; pdr -a -v -d -T 60'],cwd=build,text=True,capture_output=True,timeout=80)
        log=r.stdout+r.stderr;(build/(label+'.log')).write_text(log)
        status=classify(header,log,count,r.returncode)
        proved=status['status']=='proved';counterexample=status['status']=='disproved'
        rows.append({'case':label,'proved':proved,'counterexample':counterexample,
                     'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
        print(rows[-1],flush=True)
        assert proved if label=='actual' else counterexample,log[-4000:]
    result={'build':str(build),'source_sha256':hashlib.sha256(original.encode()).hexdigest(),
            'width_argument':'wrapper control is independent of every data bit; pointwise1-bit proof',
            'cases':rows,'scope':'initialized digital contract; safety for any clock interleaving; no analog proof'}
    (build/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(build)
if __name__=='__main__':main()

"""Safety of actual candidate acceptance/cache, under its composition contract.

Cut the vendor transports, CRC arithmetic and the tag-match rejection. Packets and CRC acceptance
are arbitrary: this strengthens generation-safety obligations, not CRC/CDC
liveness. The independent trace checker tests real CRC32 and vendor XPM.
"""
import hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from pdr_check import classify

ASSERTIONS=r'''
(* anyseq *) reg arbitrary_crc;
reg proof_seen=0;
reg [63:0] arrival_generation=0,prepared_generation=0;
reg [63:0] lease_generation[0:3];
integer p;
initial for(p=0;p<4;p=p+1) lease_generation[p]=0;
always @(posedge fast_clk) begin
 proof_seen<=1;
 // The wrapper constructs only same-edge-invalidated generation changes.
 // It even allows arbitrary new values, not just the implemented +1.
 if(receipt) arrival_generation<=generation;
 assert(!uninterrupted || generation==arrival_generation);
 assert($onehot0(check_valid));
 assert(!receipt || (checking && check_valid==0));
 assert(checking==(receipt || check_valid!=0));
 // The equality register still refers to the OLD payload for the one edge
 // immediately following receipt. It is not used for installation then.
 if(proof_seen && checking && $past(checking) && !$past(receipt) && uninterrupted && $past(uninterrupted))
    assert((&generation_equal)==(payload[95:32]==generation));
 if(check_valid[17]) assert(checking && !receipt);
 if(proof_seen && check_valid[17] && uninterrupted) assert($past(checking && uninterrupted));
 if(proof_seen && check_valid[17]) assert(!$past(receipt));
 if(check_valid[17] && crc_good && (&target_equal) && !frame_pulse &&
      (&generation_equal) && uninterrupted && !invalidate && !loss)
    lease_generation[payload[1:0]]<=payload[95:32];
 for(p=0;p<4;p=p+1) assert(!cache_low[p] || lease_generation[p]==generation);
 prepared_generation<=lease_generation[freeze_frame[1:0]];
 assert(!prepared_permit || prepared_generation==generation);
 assert(!permit || (prepared_generation==generation && !invalidate && !loss && !fault));
end
'''

STUB=r'''
module handshake_channel #(parameter WIDTH=1)(
 input wire src_clk,dest_clk,src_rst,dest_rst,in_valid,out_ready,
 input wire [WIDTH-1:0] in_data,
 output wire in_ready,out_valid,
 output wire [WIDTH-1:0] out_data);
 (* anyseq *) reg r,v;
 (* anyseq *) reg [WIDTH-1:0] d;
 assign in_ready=r; assign out_valid=v; assign out_data=d;
endmodule
module proof(input wire fast_clk,slow_clk,rst_fast,rst_slow,frame_pulse,rule_low,invalidate,loss,
 input wire [31:0] frame_id,freeze_frame,
 input wire [63:0] processed_generation);
 (* anyseq *) reg [63:0] next_generation;
 reg [63:0] generation=0;
 always @(posedge fast_clk) if(invalidate) generation<=next_generation;
 candidate_link dut(.fast_clk(fast_clk),.slow_clk(slow_clk),.rst_fast(rst_fast),.rst_slow(rst_slow),
   .frame_pulse(frame_pulse),.frame_id(frame_id),.freeze_frame(freeze_frame),
   .rule_low(rule_low),.invalidate(invalidate),.loss(loss),
   .processed_generation(processed_generation),.generation(generation));
endmodule
'''
def main():
 source=(HERE/'candidate_link.sv').read_text()
 code=source.replace('crc_good<=~crc_pipe[15]==expected_crc && payload[127:97]==0;',
                     'crc_good<=arbitrary_crc;').replace('endmodule',ASSERTIONS+'\nendmodule')
 # Every retained cache line must carry the CURRENT generation, even if a
 # corrupted tag were accepted for any selected line. Removing tag rejection
 # strengthens this proof of generation safety; it does NOT prove frame tags.
 code=code.replace('cache_tag[freeze_frame[1:0]]==freeze_frame[3:2] &&\n            freeze_frame[31:4]==0 && ', '')
 assert code!=source
 build=HERE.parent/'.build'/('integrated-guard-'+str(time.time_ns()));build.mkdir(parents=True)
 (build/'proof.sv').write_text(code+'\n'+STUB)
 induction='read_verilog -formal -sv proof.sv; prep -top proof; flatten; memory_map; opt; async2sync; opt; sat -seq 1 -tempinduct -maxsteps 24 -prove-asserts -verify -timeout 60 -dump_json counterexample.json -show dut.checking -show dut.receipt -show dut.check_valid -show dut.uninterrupted -show dut.arrival_generation -show generation -show dut.prepared_permit -show dut.prepared_generation'
 r=subprocess.run(['yosys','-Q','-T','-p',induction],cwd=build,text=True,capture_output=True,timeout=95)
 ilog=r.stdout+r.stderr;(build/'induction.log').write_text(ilog)
 if r.returncode==0 and 'Induction step proven: SUCCESS' in ilog:
  report={'status':'proved','engine':'SAT joint-invariant induction',
          'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
          'assumption':'constructed generation changes on invalidate; actual wrapping and saturating counters are stricter',
          'abstraction':'arbitrary packets/CRC accept; tag rejection removed; no frame identity, CDC liveness or CRC correctness claim',
          'log_sha256':hashlib.sha256(ilog.encode()).hexdigest(),'build':str(build)}
  (build/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return
 command='read_verilog -formal -sv proof.sv; prep -top proof; flatten; memory_map; opt; clk2fflogic; opt; techmap; opt; abc -g AND; opt_clean; write_aiger -zinit -symbols proof.aig'
 r=subprocess.run(['yosys','-Q','-T','-p',command],cwd=build,text=True,capture_output=True,timeout=120)
 (build/'synth.log').write_text(r.stdout+r.stderr);assert r.returncode==0,(r.stdout+r.stderr)[-3000:]
 header=(build/'proof.aig').read_bytes().splitlines()[0].decode();count=int(header.split()[6])
 assert int(header.split()[4])==0
 r=subprocess.run(['yosys-abc','-c','read_aiger proof.aig; pdr -a -v -d -T 90'],cwd=build,text=True,capture_output=True,timeout=110)
 log=r.stdout+r.stderr;(build/'proof.log').write_text(log)
 report={**classify(header,log,count,r.returncode),'properties':count,
         'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
         'assumption':'wrapper constructs clocked generation changes only on invalidate, with arbitrary next value; startup initialization',
         'abstraction':'arbitrary packet deliveries/CRC; tag rejection removed; no frame identity or transport liveness claimed',
         'log_sha256':hashlib.sha256(log.encode()).hexdigest(),'build':str(build)}
 (build/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

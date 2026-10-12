"""Safety of actual candidate acceptance/cache, under its composition contract.

Cut the vendor transports, CRC arithmetic and the tag-match rejection. Packets and CRC acceptance
are arbitrary: this strengthens generation-safety obligations, not CRC/CDC
liveness. The independent trace checker tests real CRC32 and vendor XPM.
"""
import hashlib,json,re,subprocess,sys,time
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
 if(proof_seen) begin
  for(p=0;p<4;p=p+1)
   assert(generation_equal[p]==($past(payload[32+16*p+:16])==$past(generation[16*p+:16])));
  if(checking && $past(checking) && !$past(receipt)) assert(payload==$past(payload));
 end
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
def sentinels(build,code):
 rows=[]
 for label in ['same-edge-veto-mutant','generation-gate-mutant','permit-reachable']:
  broken=code
  if label=='same-edge-veto-mutant':
   broken=broken.replace('assign permit=prepared_permit && !invalidate && !loss && !fault;',
                         'assign permit=prepared_permit && !loss && !fault;')
  elif label=='generation-gate-mutant':
   broken=broken.replace('(proof_equal) && uninterrupted','(1\'b1) && uninterrupted') if '(proof_equal) && uninterrupted' in broken else broken.replace('proof_equal && uninterrupted',"1'b1 && uninterrupted")
  else:broken=broken.replace('endmodule','always @(posedge fast_clk) assert(!permit);\nendmodule')
  assert broken!=code
  (build/(label+'.sv')).write_text(broken+'\n'+STUB)
  cmd=f'read_verilog -formal -sv {label}.sv; prep -top proof; flatten; memory_map; opt; async2sync; opt; sat -seq 28 -prove-asserts -timeout 45 -dump_json {label}.json'
  r=subprocess.run(['yosys','-Q','-T','-p',cmd],cwd=build,text=True,capture_output=True,timeout=65)
  log=r.stdout+r.stderr;(build/(label+'.log')).write_text(log)
  rejected=r.returncode==0 and 'SAT proof finished - model found: FAIL' in log
  assert rejected,log[-2500:]
  rows.append({'case':label,'counterexample':True,'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
 return rows

def main():
 source=(HERE/'candidate_link.sv').read_text()
 # Full-width induction twice exhausted the bounded solver effort. Factor
 # the theorem pointwise: allowing a candidate when ONE generation bit
 # matches is a strict over-approximation of the actual all64-bit gate.
 # Packet indexing/invalidation/installation remain actual RTL. Each bit
 # follows the same copy/equality recurrence; no generation arithmetic is
 # abstracted here (the source may change arbitrarily on invalidate).
 # First machine-check the full comparator implication from its real RHS.
 build=HERE.parent/'.build'/('integrated-guard-'+str(time.time_ns()));build.mkdir(parents=True)
 rhs=re.search(r'generation_equal<=([^;]+);',source)[1]
 lemma='module proof(input [127:0] payload,input [63:0] generation);\nwire [3:0] parts='+rhs+';\nalways @* assert(!(&parts) || payload[95:32]==generation);\nendmodule\n'
 (build/'comparator.sv').write_text(lemma)
 cmd='read_verilog -formal -sv comparator.sv; prep -top proof; flatten; opt; chformal -lower; sat -prove-asserts -verify'
 r=subprocess.run(['yosys','-Q','-T','-p',cmd],cwd=build,text=True,capture_output=True,timeout=60)
 comparator_log=r.stdout+r.stderr;(build/'comparator.log').write_text(comparator_log)
 assert r.returncode==0 and 'SUCCESS' in comparator_log
 point=ASSERTIONS
 start=point.index(' if(proof_seen) begin\n  for(p=0;p<4;p=p+1)')
 end=point.index(' // The equality register',start)
 point=point[:start]+point[end:]
 point=point.replace('[63:0]','').replace('payload[95:32]','payload[32]')
 point=re.sub(r'\bgeneration\b','generation[0]',point)
 point=point.replace('(&generation_equal)','proof_equal')
 point='reg proof_equal=0;\nalways @(posedge fast_clk) proof_equal<=payload[32]==generation[0];\n'+point
 point+='\nalways @(posedge fast_clk) if(installed) assert($past(payload[32]==generation[0]));\n'
 code=source.replace('assign crc_good=&crc_equal && reserved_good;',
                     'assign crc_good=arbitrary_crc;')
 code=code.replace('(&generation_equal)','proof_equal')
 code=code.replace('endmodule',point+'\nendmodule')
 # Every retained cache line must carry the CURRENT generation, even if a
 # corrupted tag were accepted for any selected line. Removing tag rejection
 # strengthens this proof of generation safety; it does NOT prove frame tags.
 code=code.replace('cache_tag[freeze_frame[1:0]]==freeze_frame[3:2] &&\n            freeze_frame[31:4]==0 && ', '')
 assert code!=source
 (build/'proof.sv').write_text(code+'\n'+STUB)
 induction='read_verilog -formal -sv proof.sv; prep -top proof; flatten; memory_map; opt; async2sync; opt; sat -seq 1 -tempinduct -maxsteps 24 -prove-asserts -verify -timeout 60 -dump_json counterexample.json -show dut.checking -show dut.receipt -show dut.check_valid -show dut.uninterrupted -show dut.arrival_generation -show generation -show dut.prepared_permit -show dut.prepared_generation'
 r=subprocess.run(['yosys','-Q','-T','-p',induction],cwd=build,text=True,capture_output=True,timeout=95)
 ilog=r.stdout+r.stderr;(build/'induction.log').write_text(ilog)
 if r.returncode==0 and 'Induction step proven: SUCCESS' in ilog:
  report={'status':'proved','engine':'SAT joint-invariant induction',
          'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
          'assumption':'constructed generation changes on invalidate; actual wrapping and saturating counters are stricter',
          'abstraction':'arbitrary packets/CRC accept; tag rejection removed; generation acceptance weakened to one bit; symmetric theorem for each of64 bits',
          'comparator_implication':'full64-bit implication proved from actual RTL RHS; registered one-cycle alignment unchanged',
          'comparator_log_sha256':hashlib.sha256(comparator_log.encode()).hexdigest(),
          'log_sha256':hashlib.sha256(ilog.encode()).hexdigest(),'build':str(build)}
  report['sentinels']=sentinels(build,code)
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
         'abstraction':'arbitrary packets/CRC; tag rejection removed; one-bit generation over-approximation, symmetric pointwise theorem',
         'comparator_log_sha256':hashlib.sha256(comparator_log.encode()).hexdigest(),
         'log_sha256':hashlib.sha256(log.encode()).hexdigest(),'build':str(build)}
 assert report['status']=='proved',report
 report['sentinels']=sentinels(build,code)
 (build/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

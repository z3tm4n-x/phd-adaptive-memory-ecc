"""Unbounded compositional lemmas, with actual source instrumented in build.

No claim that vendor FIFO fairness or physical timing follows from these.
The arithmetic/trace checker is separate. PDR's undecided result is retained.
"""
import argparse,hashlib,json,re,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from pdr_check import classify

COUNTER='''
reg seen=0;
integer p;
always @(posedge clk) begin
 seen<=1;
 for(p=0;p<8;p=p+1) assert(maximum[p]==(&value[p*8+:8]));
 assert(exhausted==(&value));
 if(seen) begin
   if($past(inc && !exhausted)) assert(value==$past(value)+64'd1);
   else assert(value==$past(value));
 end
end
'''
FRAME='''
reg seen=0;
// Ghost phase is not an RTL input or an assumption. Its independently
// generated phase table is asserted against the actual local counters.
reg [8:0] proof_phase=0;
reg [6:0] expected_start,expected_freeze;
reg [8:0] expected_app;
reg [2:0] expected_slot,expected_freeze_pos;
always @* begin
 if(proof_phase==0) begin expected_start=0;expected_slot=0;end
 else if(proof_phase<=41) begin expected_start=41-proof_phase;expected_slot=1;end
 else if(proof_phase<=82) begin expected_start=82-proof_phase;expected_slot=2;end
 else if(proof_phase<=123) begin expected_start=123-proof_phase;expected_slot=3;end
 else if(proof_phase<=164) begin expected_start=164-proof_phase;expected_slot=4;end
 else if(proof_phase<=205) begin expected_start=205-proof_phase;expected_slot=5;end
 else if(proof_phase<=246) begin expected_start=246-proof_phase;expected_slot=6;end
 else if(proof_phase<=287) begin expected_start=287-proof_phase;expected_slot=7;end
 else begin expected_start=392-proof_phase;expected_slot=0;end
 if(proof_phase<=2) begin expected_freeze=2-proof_phase;expected_freeze_pos=2;end
 else if(proof_phase<=43) begin expected_freeze=43-proof_phase;expected_freeze_pos=3;end
 else if(proof_phase<=84) begin expected_freeze=84-proof_phase;expected_freeze_pos=4;end
 else if(proof_phase<=125) begin expected_freeze=125-proof_phase;expected_freeze_pos=5;end
 else if(proof_phase<=166) begin expected_freeze=166-proof_phase;expected_freeze_pos=6;end
 else if(proof_phase<=207) begin expected_freeze=207-proof_phase;expected_freeze_pos=7;end
 else if(proof_phase<=312) begin expected_freeze=312-proof_phase;expected_freeze_pos=0;end
 else if(proof_phase<=353) begin expected_freeze=353-proof_phase;expected_freeze_pos=1;end
 else begin expected_freeze=394-proof_phase;expected_freeze_pos=2;end
 expected_app=proof_phase<=328 ? 328-proof_phase : 720-proof_phase;
end
always @(posedge clk) begin
 seen<=1;
 if(running) proof_phase<=proof_phase==391 ? 0 : proof_phase+1'b1;
 assert(proof_phase<=391);
 assert(running || proof_phase==0);
 assert(start_wait==expected_start && slot_pos==expected_slot);
 assert(freeze_wait==expected_freeze && freeze_pos==expected_freeze_pos);
 assert(app_wait==expected_app);
 assert(start_ring==slot_pos[1:0] && freeze_ring==freeze_pos[1:0]);
 assert(start_wait<=104); assert(freeze_wait<=104); assert(app_wait<=391);
 assert(freeze_mod3<=2);
 assert(slot_tick==(running && start_wait==0));
 assert(freeze_tick==(running && freeze_wait==0));
 assert(app_tick==(running && app_wait==0));
 assert(frame_tick==(slot_tick && slot_pos==0));
 assert(!freeze_due || start_wait==39 || start_wait==80);
 if(freeze_due && start_wait==39) assert(freeze_ring!=start_ring);
 if(running && start_wait<=39) assert(execute_slot==(decisions[start_ring] || !valid_decisions[start_ring]));
 if(slot_pos==0) begin
   assert({1'b0,app_wait}=={3'b0,start_wait}+10'd328 ||
          {1'b0,app_wait}+10'd64=={3'b0,start_wait});
 end else begin
   assert(start_wait<=40);
   assert({1'b0,app_wait}=={3'b0,start_wait}+10'd328-10'd41*slot_pos);
 end
 assert(!control_due || slot_due);
 if(slot_due) assert(execute_slot==(decisions[start_ring] || !valid_decisions[start_ring]));
 assert(!(control_due && app_due));
 if(seen && $past(running)) begin
   assert(running);
   if($past(slot_due)) begin
      assert(start_wait==($past(slot_pos)==7?104:40));
      assert(word_due==$past(word_due)+WORD_BITS'(INVERSE));
      assert(start_ring==2'($past(start_ring)+1));
   end else begin assert(start_wait==$past(start_wait)-1'b1);assert(word_due==$past(word_due));end
   if($past(freeze_due)) begin
     assert(frozen_execute==$past(must_execute || !permit || alarm || fault));
     assert(freeze_wait==($past(freeze_pos)==7?104:40));
   end else assert(freeze_wait==$past(freeze_wait)-1'b1);
   if($past(app_due)) assert(app_wait==391);
   else assert(app_wait==$past(app_wait)-1'b1);
 end
end
'''
RULE='''
reg seen=0;
always @(posedge clk) begin
 seen<=1;
 assert(!low || (started && healthy && !fault && !history_fault && !event_valid &&
         short_left==0 && long_left==0 && recovery_left==0));
 if(seen) begin
   if($past(event_valid)) assert(processed_generation==$past(event_generation));
   else assert(processed_generation==$past(processed_generation));
   if($past(event_valid && event_err)) begin
     assert(short_left==NW);
     assert(last_err==$past(timestamp));
     if($past(seen_err && timestamp>=last_err && timestamp-last_err<=PAIR_WINDOW)) assert(long_left==NH);
   end
   if($past(event_valid && event_loss)) assert(!healthy);
   if($past(event_valid && !event_loss && !healthy)) assert(recovery_left>=NR);
   if($past(fault || history_fault)) assert(fault);
 end
end
'''
WARMUP='''
reg seen=0;
always @(posedge clk) begin
 seen<=1;
 assert(warmup_left<=((1<<WORD_BITS)-2));
 assert(must_execute==(warmup_left!=0 || freeze_mod3==0));
 if(seen && $past(running)) begin
  if($past(freeze_due && warmup_left!=0)) assert(warmup_left==$past(warmup_left)-1'b1);
  else assert(warmup_left==$past(warmup_left));
  if($past(freeze_due)) assert(freeze_mod3==($past(freeze_mod3)==2?0:$past(freeze_mod3)+1'b1));
  else assert(freeze_mod3==$past(freeze_mod3));
  if($past(freeze_due && must_execute)) assert(frozen_execute);
 end
end
'''

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--case');args=ap.parse_args()
 build=HERE.parent/'.build'/('integrated-proof-'+str(time.time_ns()));build.mkdir(parents=True)
 results=[]
 cases=[('counter','segmented_counter.sv','segmented_counter',COUNTER,None),
        ('frame','frame_engine.sv','frame_engine',FRAME,None),
        ('warmup','frame_engine.sv','frame_engine',WARMUP,None),
        ('rule','slow_rule.sv','slow_rule',RULE,None),
        ('counter-mutant','segmented_counter.sv','segmented_counter',COUNTER,("==8'hfe","==8'hfd")),
        ('frame-mutant','frame_engine.sv','frame_engine',FRAME,('must_execute || !permit || alarm || fault','must_execute || !permit || fault'))]
 for name,file,top,asserts,mutation in cases:
  if args.case and name!=args.case:continue
  source=(HERE/file).read_text();code=source
  abstraction=None
  if name in ('frame','frame-mutant'):
   # Arbitrary freeze obligation is a superset of warmup/mod3/permit.
   # Cut the long prefix from this safety proof, never from the actual RTL.
   code=code.replace('wire must_execute=warmup_left!=0 || freeze_mod3==0;',
                     '(* anyseq *) reg must_execute;')
   abstraction='arbitrary must_execute at every edge; actual warmup/mod3 recurrences separate'
  if mutation:
   assert mutation[0] in code;code=code.replace(*mutation)
  # Do not export ordinary module outputs as extra verification targets.
  instrumented=code.replace('endmodule',asserts+'\nendmodule')
  # Yosys ignores exposed values after selecting only assertions with chformal.
  # Wrapper has no outputs; the actual inputs stay symbolic.
  if top=='segmented_counter':wrapper='module proof(input wire clk,inc); segmented_counter dut(.clk(clk),.inc(inc)); endmodule'
  elif top=='frame_engine':
   parameters='#(.WORD_BITS(3),.INVERSE(3))' if mutation else ''
   wrapper='module proof(input wire clk,start,permit,alarm,backend_busy); frame_engine '+parameters+' dut(.clk(clk),.start(start),.permit(permit),.alarm(alarm),.backend_busy(backend_busy)); endmodule'
  else:wrapper='module proof(input wire clk,start,event_valid,history_fault,input wire [129:0] event_data); slow_rule dut(.clk(clk),.start(start),.event_valid(event_valid),.history_fault(history_fault),.event_data(event_data)); endmodule'
  (build/(name+'.sv')).write_text(instrumented+'\n'+wrapper)
  if not mutation:
   sat_script=(f'read_verilog -formal -sv {name}.sv; prep -top proof; flatten; '
      'async2sync; opt; sat -seq 1 -tempinduct -maxsteps 6 -prove-asserts -verify -timeout 45 -show-all -dump_json induction_counterexample.json')
   r=subprocess.run(['yosys','-Q','-T','-p',sat_script],cwd=build,text=True,capture_output=True,timeout=75)
   sat_log=r.stdout+r.stderr;(build/(name+'-induction.log')).write_text(sat_log)
   if r.returncode==0 and 'Induction step proven: SUCCESS' in sat_log:
    result=dict(case=name,status='proved',engine='SAT joint-invariant induction',
       abstraction=abstraction,
       source_sha256=hashlib.sha256(source.encode()).hexdigest(),
       log_sha256=hashlib.sha256(sat_log.encode()).hexdigest())
    results.append(result);print(json.dumps(result),flush=True);continue
  script=(f'read_verilog -formal -sv {name}.sv; prep -top proof; flatten; clk2fflogic; opt; '
          f'techmap; opt; abc -g AND; opt_clean; write_aiger -zinit -symbols {name}.aig')
  r=subprocess.run(['yosys','-Q','-T','-p',script],cwd=build,text=True,capture_output=True,timeout=100)
  (build/(name+'-synth.log')).write_text(r.stdout+r.stderr)
  assert r.returncode==0,(r.stdout+r.stderr)[-4000:]
  header=(build/(name+'.aig')).read_bytes().splitlines()[0].decode()
  assert int(header.split()[4])==0,'ordinary outputs cannot be properties'
  count=int(header.split()[6])
  r=subprocess.run(['yosys-abc','-c',f'read_aiger {name}.aig; pdr -a -v -d -T 60'],
                   cwd=build,text=True,capture_output=True,timeout=85)
  log=r.stdout+r.stderr;(build/(name+'.log')).write_text(log)
  status=classify(header,log,count,r.returncode)
  result=dict(case=name,**status,properties=count,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
              abstraction=abstraction,
              log_sha256=hashlib.sha256(log.encode()).hexdigest())
  results.append(result);print(json.dumps(result),flush=True)
 report={'cases':results,'build':str(build),'assumptions':'binary inputs, initialized RTL, clock edges; no added assume',
         'scope':'counter arithmetic, schedule recurrences and rule transitions; not complete CDC liveness'}
 (build/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
 print('BUILD',build)

if __name__=='__main__':main()

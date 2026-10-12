"""Rerun actual component induction with physical overrides, plus address lock."""
import hashlib,json,shutil,sys,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
from integrated import admission_proof
import guard_proof
# Reuse the historical proof driver read-only, updating its exact cut-point
# spelling for this registered terminal predicate. Warmup is proved uncut.
driver=(BASE/'integrated/prove.py').read_text()
needle='wire must_execute=warmup_left!=0 || freeze_mod3==0;'
assert driver.count(needle)==1
driver=driver.replace(needle,'wire must_execute=warmup_active || freeze_mod3==0;')
prove=types.ModuleType('physical_component_driver')
prove.__file__=str(BASE/'integrated/prove.py')
exec(compile(driver,prove.__file__,'exec'),prove.__dict__)
prove.WARMUP=prove.WARMUP.replace('always @(posedge clk) begin',
 'always @(posedge clk) begin\n assert(warmup_active==(warmup_left!=0));')
prove.RULE+=r'''
// Full production-width timers, not accelerated simulation parameters.
always @(posedge clk) begin
 assert(short_left<=NW && long_left<=NH && recovery_left<=NR);
 if(seen) begin
  assert(started==($past(started) || $past(start)));
  assert(healthy==($past(event_valid) ? !$past(event_loss) : $past(healthy)));
  if(!$past(event_valid && event_err))
   assert(short_left==($past(started && short_left!=0) ? $past(short_left)-34'd1 : $past(short_left)));
  if(!$past(event_valid && event_err && seen_err && timestamp>=last_err && timestamp-last_err<=PAIR_WINDOW))
   assert(long_left==($past(started && long_left!=0) ? $past(long_left)-34'd1 : $past(long_left)));
  if($past((start && !started) || (event_valid && !event_loss && !healthy))) assert(recovery_left==NR);
  else assert(recovery_left==($past(started && recovery_left!=0) ? $past(recovery_left)-34'd1 : $past(recovery_left)));
  if($past(event_valid && event_generation!=processed_generation+64'd1)) assert(fault);
 end
end
'''

EXTRA_FRAME=r'''
reg [5:0] service_remaining=0,service_upper;
reg [18:0] proof_command=0,proof_pad_word=0,proof_locked_word=0;
(* anyseq *) reg [18:0] proof_new_command;
integer proof_j;
always @* begin
 service_upper=0;
 for(proof_j=0;proof_j<8;proof_j=proof_j+1)
  if(proof_phase>41*proof_j && proof_phase<=41*proof_j+37)
   service_upper=41*proof_j+38-proof_phase;
 if(proof_phase>328 && proof_phase<=382) service_upper=383-proof_phase;
end
always @(posedge clk) begin
 assert(control_prepare==(running && start_wait==1));
 assert(app_prepare==(running && app_wait==1));
 assert(!(control_prepare && app_prepare));
 assert(service_remaining<=service_upper);
 assert(!(control_due && app_due));
 if(control_due || app_due || control_prepare || app_prepare) assert(service_remaining==0);
 if(service_remaining!=0) service_remaining<=service_remaining-1'b1;
 if(control_due) service_remaining<=37;
 if(app_due) service_remaining<=54;
 if(control_prepare || app_prepare) proof_command<=proof_new_command;
 proof_pad_word<=proof_command;
 if(control_due || app_due) proof_locked_word<=proof_command;
 if(service_remaining!=0) assert(proof_pad_word==proof_locked_word);
end
'''

def main():
    stage=BASE/'.build'/('physical-components-'+str(time.time_ns()))/'sources'
    stage.mkdir(parents=True)
    inputs={}
    for name in ['segmented_counter.sv','frame_engine.sv','slow_rule.sv','candidate_link.sv','executor.sv']:
        p=HERE/name
        if not p.exists():p=BASE/'integrated'/name
        data=p.read_bytes();(stage/name).write_bytes(data)
        inputs[name]=hashlib.sha256(data).hexdigest()
    (stage.parent/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    prove.HERE=stage
    prove.FRAME+=EXTRA_FRAME
    # The old script writes only under its .build; no accepted artifacts change.
    sys.argv=[sys.argv[0]]
    prove.main()
    guard_proof.HERE=stage;guard_proof.main()
    admission_proof.HERE=stage;admission_proof.main()
    print('STAGE',stage,flush=True)
if __name__=='__main__':main()


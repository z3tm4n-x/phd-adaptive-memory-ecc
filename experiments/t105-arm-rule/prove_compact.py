"""Actual collector identities and mailbox ACK contract, with counterexamples.

Assertions are instrumented into copies, not a replacement implementation.
No assumptions on event contents, AXI traffic or decision_ready: malformed
history must set fault. Clock/startup initial values are the production ones.
"""
import hashlib, json, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
COLLECTOR=r"""
 reg proof_seen=0;
 always @(posedge clk) begin
  proof_seen<=1;
  if(!fault) begin
   assert(end_generation>=base_generation);
   assert(end_generation-base_generation=={32'd0,event_count});
   if(!err_count) assert({first_source,last_source,first_tick,last_tick}==0);
   if(!had_recovery) assert(recovery_tick==0);
  end
  assert(!snapshot_valid || started);
  if(snapshot_valid) begin
   assert(snapshot[767:736]==0);
   assert(snapshot[319:256]==start_tick);
   assert(snapshot[191:128]==base_generation);
   if(!snapshot[708]) begin
    assert(snapshot[191:128]>=snapshot[127:64]);
    assert(snapshot[191:128]-snapshot[127:64]=={32'd0,snapshot[671:640]});
   end
  end
  if(proof_seen) begin
   if($past(fault)) assert(fault);
   if($past(started)) assert(started);
   if($past(started)) assert(start_tick==$past(start_tick));
   if($past(snapshot_valid) && !$past(snapshot_ack)) begin
    assert(snapshot_valid);assert(snapshot==$past(snapshot));
   end
   if($past(snapshot_valid) && !snapshot_valid) assert($past(snapshot_ack));
   if($past(cut)) begin
    assert(base_generation==$past(end_generation));
    assert(snapshot[127:64]==$past(base_generation));
    assert(snapshot[63:0]==$past(packet_seq)+64'd1);
   end else assert(base_generation==$past(base_generation));
  end
 end
"""
MAILBOX=r"""
 reg proof_seen=0;
 always @(posedge clk) begin
  proof_seen<=1;
  assert(!(validating && decision_valid));
  if(validating) assert(word_index<=6);
  if(proof_seen) begin
   assert(snapshot_ack==$past(decision_valid && decision_ready));
   if($past(snapshot_valid) && !snapshot_valid) assert($past(snapshot_ack));
   if(snapshot_ack) assert(stored_sequence==$past(decision[63:0]));
   if(decision_valid && !$past(decision_valid)) begin
    assert($past(validating && word_index==6 && content_good));
    assert(decision==$past(checking));
   end
   if($past(decision_valid && !decision_ready)) begin
    assert(decision_valid);assert(decision==$past(decision));
   end
  end
 end
"""

def main():
    build=HERE/'.build/compact-proof';build.mkdir(parents=True,exist_ok=True)
    col=(HERE/'history_batch.sv').read_text();mb=(HERE/'rule_mailbox.sv').read_text()
    cases=[]
    for label,top in [('collector','history_batch'),('ack','rule_mailbox'),
                      ('missing-event','history_batch'),('early-ack','rule_mailbox')]:
        c,m=col,mb
        if label=='missing-event':
            c=c.replace('end_generation<=incoming_gen;event_count<=next_event_count;',
                        'end_generation<=incoming_gen;event_count<=event_count;')
        if label=='early-ack':m=m.replace('snapshot_request<=1;written<=0;',
                                         'snapshot_request<=1;snapshot_ack<=1;written<=0;')
        c=c.replace('endmodule',COLLECTOR+'\nendmodule') if top=='history_batch' else c
        m=m.replace('endmodule',MAILBOX+'\nendmodule')
        (build/(label+'.sv')).write_text(c+'\n'+m)
        actual=label in ('collector','ack')
        mode='-seq 1 -tempinduct -maxsteps 8 -verify' if actual else '-seq 8'
        cmd=f'read_verilog -formal -sv {label}.sv; prep -top {top}; flatten; async2sync; chformal -lower; opt; sat {mode} -prove-asserts -timeout 45 -dump_json {label}.json'
        run=subprocess.run(['yosys','-Q','-T','-p',cmd],cwd=build,text=True,capture_output=True,timeout=180)
        log=run.stdout+run.stderr;(build/(label+'.log')).write_text(log)
        passed=run.returncode==0 and 'Induction step proven: SUCCESS' in log
        rejected='SAT proof finished - model found: FAIL' in log
        assert passed if actual else rejected,log[-3500:]
        cases.append({'case':label,'induction':passed,'counterexample':rejected,
                      'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
    result={'cases':cases,'source_sha256':{p:hashlib.sha256((HERE/p).read_bytes()).hexdigest()
             for p in ('history_batch.sv','rule_mailbox.sv')},
      'assumptions':['production initial values, no runtime reset','one software owner for ACK interpretation',
                     'Device/non-cacheable MMIO and ordered completion, no silent corruption'],
      'scope':'G64/count and immutable-bank identities; ACK/control only, not a new CRC proof or ARM timing'}
    (HERE/'outputs/compact-proof.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()

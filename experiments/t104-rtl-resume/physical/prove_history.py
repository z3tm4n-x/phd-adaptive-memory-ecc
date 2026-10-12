"""Actual two-register source-history staging versus an independent delay.

Segmented counter arithmetic is separately proved equivalent to integer +1.
The vendor event FIFO then preserves this sequence; the actual slow-rule
proof checks consecutive generation and source-time processing.
"""
import hashlib,json,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
 source=(HERE/'executor.sv').read_text()
 start=source.index('    always @(posedge fast_clk) begin\n        event_capture<=history_change;')
 end=source.index('    event_fifo history',start)
 actual=source[start:end]
 prefix='''module proof(input fast_clk,history_change,loss_fast,err_due,input [63:0] uptime);
 reg [63:0] generation=0;
 always @(posedge fast_clk) if(history_change) generation<=generation+1'b1;
 reg event_capture=0,event_write=0;
 reg [65:0] event_snapshot=0;
 reg [129:0] event_staged=0;
 reg [129:0] expected0=0,expected1=0;
 reg [1:0] valid=0;
 always @(posedge fast_clk) begin
  expected0<={generation+64'd1,uptime,loss_fast,err_due};
  expected1<=expected0;
  valid<={valid[0],history_change};
  assert(event_write==valid[1]);
  if(event_write) assert(event_staged==expected1);
  if(event_capture) assert(generation==expected0[129:66]);
  if(event_capture) assert(event_snapshot==expected0[65:0]);
 end
'''
 build=HERE.parent/'.build'/('physical-history-'+str(time.time_ns()));build.mkdir(parents=True)
 rows=[]
 for label in ['actual','wrong-generation','wrong-time']:
  code=actual
  if label=='wrong-generation':code=code.replace('{generation,event_snapshot}',"{generation+64'd1,event_snapshot}")
  if label=='wrong-time':code=code.replace('{generation,event_snapshot}', '{generation,uptime,loss_fast,err_due}')
  (build/(label+'.sv')).write_text(prefix+code+'endmodule\n')
  cmd=f'read_verilog -formal -sv {label}.sv; prep -top proof; flatten; opt; async2sync; opt; sat -seq 1 -tempinduct -maxsteps 6 -prove-asserts -verify -timeout 30 -dump_json {label}-counterexample.json'
  if label!='actual':cmd=cmd.replace('-seq 1 -tempinduct -maxsteps 6','-seq 6').replace(' -verify','')
  r=subprocess.run(['yosys','-Q','-T','-p',cmd],cwd=build,text=True,capture_output=True,timeout=90)
  log=r.stdout+r.stderr;(build/(label+'.log')).write_text(log)
  row={'case':label,'proved':r.returncode==0 and 'Induction step proven: SUCCESS' in log,
       'counterexample':'SAT proof finished - model found: FAIL' in log,'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
  assert row['proved'] if label=='actual' else row['counterexample'],log[-2000:]
  rows.append(row);print(row,flush=True)
 report={'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'cases':rows,'build':str(build),
         'scope':'all consecutive source edges and128 generation/timestamp bits; no FIFO behavior assumed in the staging proof'}
 (build/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
 print(build,flush=True)
if __name__=='__main__':main()

"""Inductive check of actual fast guard, under accepted same-edge G updates."""
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROOF=r"""
 reg seen=0;
 reg [63:0] ghost_generation=0;
 always @(posedge clk) begin
  seen<=1;
  assert(!captured || !checking);
  if(seen) begin
   assert(equal_generation[0]==($past(payload[16:1])==$past(generation[15:0])));
   assert(equal_generation[1]==($past(payload[32:17])==$past(generation[31:16])));
   assert(equal_generation[2]==($past(payload[48:33])==$past(generation[47:32])));
   assert(equal_generation[3]==($past(payload[64:49])==$past(generation[63:48])));
   if(checking) assert(payload==$past(payload));
   if(generation!=$past(generation)) assert(!cached);
  end
  if(checking && (&equal_generation) && uninterrupted && !invalidate && !loss)
   ghost_generation<=payload[64:1];
  if(cached) assert(ghost_generation==generation);
  assert(!permit || (!invalidate && !loss));
 end
"""
WRAP=r"""
module proof(input clk,valid,invalidate,loss,input [64:0] data);
 reg [63:0] generation=0;
 always @(posedge clk) if(invalidate) generation<=generation+1'b1;
 wire ready,permit,installed;
 interval_guard dut(.*);
endmodule
"""
def main():
    source=(HERE/"interval_guard.sv").read_text()
    build=HERE/".build/interval-proof";build.mkdir(parents=True,exist_ok=True)
    results=[]
    for label in ("actual","late-veto","wrong-generation"):
        code=source
        if label=="late-veto":code=code.replace("cached && !invalidate && !loss","cached && !loss")
        if label=="wrong-generation":code=code.replace("checking && (&equal_generation)","checking")
        code=code.replace("endmodule",PROOF+"\nendmodule")+WRAP
        (build/(label+".sv")).write_text(code)
        induction="-seq 1 -tempinduct -maxsteps 8 -verify" if label=="actual" else "-seq 9"
        cmd=f"read_verilog -formal -sv {label}.sv; prep -top proof; flatten; async2sync; chformal -lower; opt; sat {induction} -prove-asserts -timeout 45 -dump_json {label}.json"
        run=subprocess.run(["yosys","-Q","-T","-p",cmd],cwd=build,text=True,capture_output=True,timeout=60)
        log=run.stdout+run.stderr;(build/(label+".log")).write_text(log)
        proved="Induction step proven: SUCCESS" in log and run.returncode==0
        rejected="SAT proof finished - model found: FAIL" in log
        assert proved if label=="actual" else rejected,log[-4000:]
        results.append({"case":label,"induction":proved,"counterexample":rejected,
                        "log_sha256":hashlib.sha256(log.encode()).hexdigest()})
    result={"source_sha256":hashlib.sha256(source.encode()).hexdigest(),
      "cases":results,"scope":"all 65 payload bits and 64 G bits; initial G=0 and change only on invalidate",
      "not_proved":["analog CDC","ARM computation","CRC","CPU WCET","full executor"]}
    (HERE/"outputs/interval-proof.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()

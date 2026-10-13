"""Actual mailbox response proof + protocol-valid delayed completion witnesses.

No assumption that PS7 really exhibits these delays. They refute deriving a
finite *end-to-end* bound from AXI safety/local responder timing alone.
"""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ASSERTIONS=r'''
 reg service_seen=0;
 reg prev_read=0,prev_rheld=0,prev_bheld=0,prev_assemble=0,prev_commit=0,prev_validating=0;
 reg [31:0] prev_rdata=0;reg [1:0] prev_rresp=0,prev_bresp=0;reg [2:0] prev_index=0;
 wire service_assemble=aw_have && w_have && !s_axi_bvalid && !validating && !decision_valid;
 wire service_commit=awaddr==12'h008 && wstrb==15 && wdata==1 && snapshot_valid && written==32'hffffffff;
 always @(posedge clk) begin
  service_seen<=1;
  prev_read<=s_axi_arvalid && s_axi_arready;
  prev_rheld<=s_axi_rvalid && !s_axi_rready;prev_bheld<=s_axi_bvalid && !s_axi_bready;
  prev_rdata<=s_axi_rdata;prev_rresp<=s_axi_rresp;prev_bresp<=s_axi_bresp;
  prev_assemble<=service_assemble;prev_commit<=service_commit;
  prev_validating<=validating;prev_index<=word_index;
 end
 // Explicit past registers + combinational assertions avoid a triggered
 // $check clock gate in this Yosys version. Mutation checks are mandatory.
 always @* begin
  if(validating) assert(word_index<=6);
  if(service_seen) begin
   if(prev_read) assert(s_axi_rvalid);
   if(prev_rheld) begin
    assert(s_axi_rvalid);assert(s_axi_rdata==prev_rdata);
    assert(s_axi_rresp==prev_rresp);
   end
   if(prev_bheld) begin
    assert(s_axi_bvalid);assert(s_axi_bresp==prev_bresp);
   end
   if(prev_assemble) begin
    if(prev_commit) begin assert(validating);assert(word_index==0);end
    else assert(s_axi_bvalid);
   end
   if(prev_validating) begin
    if(prev_index==6) begin assert(!validating);assert(s_axi_bvalid);end
    else begin assert(validating);assert(word_index==prev_index+3'd1);end
   end
  end
 end
'''


def main():
    build=HERE/'.build/service-progress';build.mkdir(parents=True,exist_ok=True)
    source=(HERE/'rule_mailbox.sv').read_text()
    collector=(HERE/'history_batch.sv').read_text()
    cases=[]
    for label in ('actual','no-read-response','stopped-crc'):
        edited=source
        if label=='no-read-response':
            edited=edited.replace('s_axi_rvalid<=1;s_axi_rresp<=0;', 's_axi_rvalid<=0;s_axi_rresp<=0;')
        if label=='stopped-crc':
            edited=edited.replace("word_index<=word_index+1'b1;", 'word_index<=word_index;')
        instrumented=collector+'\n'+edited.replace('endmodule',ASSERTIONS+'\nendmodule')
        (build/(label+'.sv')).write_text(instrumented)
        actual=label=='actual'
        mode='-seq 1 -tempinduct -maxsteps 10 -verify' if actual else ('-seq 3' if label=='no-read-response' else '-seq 38')
        command=f'read_verilog -formal -sv {label}.sv; prep -top rule_mailbox; flatten; async2sync; chformal -lower; opt; sat {mode} -prove-asserts -timeout 45 -dump_json {label}.json'
        run=subprocess.run(['yosys','-Q','-T','-p',command],cwd=build,text=True,capture_output=True,timeout=120)
        log=run.stdout+run.stderr;(build/(label+'.log')).write_text(log)
        ok='Induction step proven: SUCCESS' in log and run.returncode==0
        rejected='SAT proof finished - model found: FAIL' in log
        if not (ok if actual else rejected):
            raise RuntimeError(log[-3000:])
        cases.append({'case':label,'inductive':ok,'counterexample':rejected})
    exe=build/'tb.vvp'
    subprocess.run(['iverilog','-g2012','-s','tb_service_progress','-o',str(exe),
        *[str(HERE/n) for n in ('history_batch.sv','rule_mailbox.sv','tb_service_progress.sv')]],check=True)
    traces=[]
    for kind in (0,1):
        for ticks in (7,50001,100001):
            run=subprocess.run(['vvp',str(exe),f'+KIND={kind}',f'+DELAY={ticks}'],
                               text=True,capture_output=True,timeout=30)
            log=run.stdout+run.stderr
            (build/f'stall-{kind}-{ticks}.log').write_text(log)
            if run.returncode or 'SERVICE_STALL_OK' not in log:
                raise RuntimeError(log)
            traces.append({'channel':'R' if kind==0 else 'B','held_ticks':ticks,
                           'nominal_held_ns':20*ticks,'log':log.strip()})
    result={
        'kind':'local responder progress, not hard-PS/OCM/SmartConnect WCET',
        'inductive_cases':cases,'witnesses':traces,
        'local_response':{'read':'RVALID in the state after AR acceptance edge',
            'ordinary_write':'BVALID one edge after last AW/W acceptance',
            'complete_COMMIT':'BVALID eight edges after last AW/W acceptance'},
        'unbounded_by_AXI_safety':'request presentation, response consumption, PS return and CPU completion',
        'source_hashes':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest()
                         for n in ('history_batch.sv','rule_mailbox.sv','tb_service_progress.sv')},
        'counterexample_scope':'arbitrarily delayed ready is permitted by the verified port contract; NOT an observed or predicted PS7 stall',
        'full_ARM_service_upper_ns':None,
    }
    with zipfile.ZipFile(HERE/'outputs/service-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(build.iterdir()):
            if p.suffix not in ('.sv','.log','.json'):
                continue
            info=zipfile.ZipInfo(p.name,(2026,10,13,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,p.read_bytes())
    (HERE/'outputs/service-progress.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

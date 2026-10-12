"""Actual fast application datapath, under separately proved calendar/E contracts.

This is a compositional proof, not a replacement implementation of XPM.
The two FIFO/handshake directions are ordered lossless channels. The shadow
FIFO below records every accepted payload, including while E is running.
Arbitrary channel backpressure and arbitrary completed E data are allowed.
"""
import hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
from pdr_check import classify

HEADER=r'''
module proof(input wire fast_clk,forward_valid,return_ready,
 input wire [56:0] forward_data,input wire [18:0] control_word,
 input wire start_operation,select_app,finish_operation,err_request,
 input wire [31:0] read_data);
localparam WORD_BITS=19;
reg [1:0] calendar_phase=0;
reg selected_app=0,did_go=0;
wire control_prepare=calendar_phase==0 && start_operation && !select_app;
wire app_prepare=calendar_phase==0 && start_operation && select_app;
wire control_due=calendar_phase==1 && !selected_app;
wire app_due=calendar_phase==1 && selected_app;
wire busy=calendar_phase==2 && did_go;
wire err_due=busy && err_request;
wire release_due=busy && finish_operation && !err_due;
wire forward_ready;
wire app_grant_debug,grant_debug;
wire [56:0] grant_data_debug;
wire [18:0] prepared_word;
always @(posedge fast_clk) begin
 if(calendar_phase==0 && start_operation) begin calendar_phase<=1;selected_app<=select_app;end
 if(calendar_phase==1) begin calendar_phase<=2;did_go<=grant_debug;end
 if(calendar_phase==2 && (!did_go || release_due)) begin calendar_phase<=0;did_go<=0;end
end
'''
GHOST=r'''
reg [56:0] expected[0:1];
reg head=0,tail=0;
reg [1:0] count=0;
reg executed=0,returnable=0,expected_err=0;
reg [32:0] expected_response=0;
wire take=forward_valid && forward_ready;
wire put=reply_pending && return_ready;
initial begin expected[0]=0;expected[1]=0;end
always @(posedge fast_clk) begin
 if(take) begin expected[tail]<=forward_data;tail<=!tail;end
 if(put) begin head<=!head;executed<=0;returnable<=0;end
 case({take,put})
  2'b10:count<=count+1'b1;
  2'b01:count<=count-1'b1;
 endcase
 if(grant_debug) expected_err<=0;
 if(err_due) expected_err<=1;
 if(app_grant_debug) executed<=1;
 if(release_due && active_app) begin
  expected_response<={read_data,expected_err};returnable<=1;
 end
 assert(count<=2);
 assert(count=={1'b0,app_receipt}+{1'b0,app_waiting}+{1'b0,executed});
 assert(!(app_receipt && app_waiting));
 assert(!executed || count>0);
 assert(!busy || active_app==selected_app);
 assert(!busy || !active_app || executed);
 assert(observed_err==expected_err);
 assert(head==tail || count==1);
 assert(head!=tail || count!=1);
 assert(calendar_phase<=2);
 assert(!returnable || !busy || !active_app);
 assert(!take || count<2 || put);
 if(app_receipt) assert(app_snapshot==expected[!tail]);
 if(app_waiting) assert(app_command==expected[!tail]);
 assert(!app_prepared || app_waiting);
 assert(!app_prepared || (calendar_phase==1 && selected_app && !reply_pending));
 if(app_prepared) assert(backend_command==app_command);
 assert(!overlap_fault && !outbox_fault);
 assert(!executed || returnable || (busy && active_app));
 assert(reply_pending==returnable);
 assert(!returnable || executed);
 if(app_grant_debug) begin
  assert(count>0 && !executed);
  assert(backend_command==expected[head]);
  assert(!busy);
 end
 if(release_due && active_app) assert(executed && !returnable);
 if(reply_pending) assert(reply==expected_response);
 if(put) assert(count>0 && executed && returnable);
 assert(!application_fault);
end
endmodule
'''

def main():
    source=(HERE/'executor.sv').read_text()
    start=source.index('    reg [56:0] app_snapshot')
    end=source.index('    wire return_ready',start)
    data=source[start:end]
    assign_line=source[source.index('    assign forward_ready='):source.index('    wire start_fast')]
    a=source.index('    assign app_grant_debug=')
    b=source.index('    e_backend_registered',a)
    body=source[a:b].replace('    wire [31:0] read_data;\n','')
    original=HEADER+data+assign_line+body+GHOST
    build=BASE/'.build'/('physical-chain-'+str(time.time_ns()))
    build.mkdir(parents=True)
    results=[]
    for name in ['actual','payload-mutant','response-mutant','duplicate-mutant']:
        code=original
        if name=='payload-mutant':code=code.replace('app_command<=app_snapshot;', "app_command<=app_snapshot ^ 57'd4;")
        if name=='response-mutant':code=code.replace('reply<={read_data,observed_err}',"reply<={read_data ^ 32'd1,observed_err}")
        if name=='duplicate-mutant':code=code.replace('if(app_grant_debug) app_waiting<=0;', 'if(app_grant_debug) app_waiting<=1;')
        if name!='actual':assert code!=original
        (build/(name+'.sv')).write_text(code)
        command=f'read_verilog -formal -sv {name}.sv; prep -top proof; flatten; memory_map; opt; async2sync; opt; chformal -lower; sat -seq 1 -tempinduct -maxsteps 12 -prove-asserts -verify -timeout 40 -dump_json {name}-counterexample.json -show-all'
        r=subprocess.run(['yosys','-Q','-T','-p',command],cwd=build,text=True,capture_output=True,timeout=100)
        log=r.stdout+r.stderr
        (build/(name+'.log')).write_text(log)
        passed=r.returncode==0 and 'Induction step proven: SUCCESS' in log
        # A failed induction step alone is NOT a reachable counterexample.
        rejected='model found for base case: FAIL' in log or 'SAT proof finished - model found' in log
        result={'case':name,'proved':passed,'counterexample':rejected,
                'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
                'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
        results.append(result)
        print(result,flush=True)
        if name=='actual':assert passed,log[-5000:]
        else:assert rejected and not passed,log[-5000:]
    report={'build':str(build),'cases':results,'contracts':[
        'actual frame engine: exclusive prepare then due, no overlapping atomic operations',
        'E: one release, valid completed read_data, ERR strictly before release',
        'ordered channel boundary; arbitrary backpressure; startup initialized, no runtime reset'],
        'scope':'payload capture/preparation/dispatch and response formation, ordering and exact-once conservation'}
    (build/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(build,flush=True)
if __name__=='__main__':main()

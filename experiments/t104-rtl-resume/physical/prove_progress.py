"""Post-consumption recycling of the real wrapper, under standard XPM.

Safety uses arbitrary clock interleavings in prove_transport.py. Here the
additional progress premise is continuous 5:1 clocks and no new packet
before the previous channel is empty. Both clock orientations are proved.
This premise follows at system level from the common application envelope
only AFTER response plus recycling have been bounded (see bounds.py).
"""
import hashlib,json,subprocess,time,sys
from pathlib import Path
from prove_transport import VENDOR
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
from pdr_check import classify

PROGRESS=r'''
 reg tracking=0;
 reg [6:0] watchdog=0;
 wire drained=!occupied && !capture && !send && !await_drop &&
   !acknowledged && !launch && !arrived && req_pipe==0 && ack_pipe==0;
 always @(posedge proof_clk) begin
  if(tracking) begin
   assert(watchdog<80);
   if(drained) tracking<=0;
   else watchdog<=watchdog+1'b1;
  end
  if(output_take) begin tracking<=1;watchdog<=0;end
 end
'''

def main():
    original=(BASE/'registered/handshake_channel.sv').read_text()
    code=original[:original.index('    xpm_cdc_handshake')]
    code=code.replace('input wire src_clk,dest_clk,src_rst,dest_rst,','input wire proof_clk,src_edge,dest_edge,')
    # Encode the no-new-packet premise as an environment driver, not an
    # AIGER constraint (ABC's multi-property reader does not honor those).
    code=code.replace('input wire in_valid,output wire in_ready,','input wire in_valid_external,output wire in_ready,')
    code=code.replace('    reg occupied=0,', '    wire in_valid=in_valid_external && !tracking;\n    reg occupied=0,')
    code=code.replace('!occupied && !src_rst','!occupied').replace(' && !dest_rst','')
    code=code.replace('always @(posedge src_clk) begin','always @(posedge proof_clk) if(src_edge) begin')
    code=code.replace('always @(posedge dest_clk) begin','always @(posedge proof_clk) if(dest_edge) begin')
    code+=VENDOR.replace('endmodule',PROGRESS+'\nendmodule')
    build=BASE/'.build'/('physical-progress-'+str(time.time_ns()));build.mkdir(parents=True)
    rows=[]
    for label in ['slow-fast','fast-slow','stuck-ack-mutant','consumption-reachable']:
        s=code
        if label=='stuck-ack-mutant':s=s.replace('else if(!requested) acknowledged<=0','else if(!requested) acknowledged<=acknowledged')
        if label=='consumption-reachable':s=s.replace('endmodule','always @(posedge proof_clk) assert(!output_take);\nendmodule')
        src,dest=('phase==0',"1'b1") if label!='fast-slow' else ("1'b1",'phase==0')
        s+=f'''\nmodule proof(input proof_clk,in_valid,out_ready,in_data);
 reg [2:0] phase=0;
 always @(posedge proof_clk) phase<=phase==4 ? 0 : phase+1'b1;
 handshake_channel #(.WIDTH(1)) dut(.proof_clk(proof_clk),.src_edge({src}),.dest_edge({dest}),
  .in_valid_external(in_valid),.out_ready(out_ready),.in_data(in_data));
 endmodule\n'''
        (build/(label+'.sv')).write_text(s)
        cmd=f'read_verilog -formal -sv {label}.sv; prep -top proof; flatten; opt; clk2fflogic; opt; techmap; opt; abc -g AND; opt_clean; write_aiger -zinit -symbols {label}.aig'
        r=subprocess.run(['yosys','-Q','-T','-p',cmd],cwd=build,text=True,capture_output=True,timeout=100)
        (build/(label+'-synth.log')).write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
        header=(build/(label+'.aig')).read_bytes().splitlines()[0].decode()
        assert int(header.split()[4])==0
        r=subprocess.run(['yosys-abc','-c',f'read_aiger {label}.aig; pdr -a -v -d -T 60'],cwd=build,text=True,capture_output=True,timeout=90)
        log=r.stdout+r.stderr;(build/(label+'.log')).write_text(log)
        result=classify(header,log,int(header.split()[6]),r.returncode)
        rows.append({'case':label,**result,'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
        print(rows[-1],flush=True)
        assert result['status']==('disproved' if label in ['stuck-ack-mutant','consumption-reachable'] else 'proved'),log[-4000:]
    report={'cases':rows,'source_sha256':hashlib.sha256(original.encode()).hexdigest(),
      'fast_edges_upper':80,'bound_nominal_ns':320,'build':str(build),
      'shared_dependency':'same explicit XPM digital abstraction as transport safety; not independent analog evidence'}
    (build/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(build)
if __name__=='__main__':main()

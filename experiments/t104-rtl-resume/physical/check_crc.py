"""Affine-basis certificate for the actual 16-stage CRC datapath.

For a fixed payload the pipeline consists only of shifts, XOR and selection
between zero and a constant by one linear bit. Thus its settled32-bit value
is affine over GF(2). Zero plus all128 unit vectors determine it completely.
Test the actual RTL, not a Python transcription; independent oracle is zlib.
This is not a claim that128 random tests cover a nonlinear function.
"""
import hashlib,json,re,subprocess,time,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
STUB='''module handshake_channel #(parameter WIDTH=1)(input src_clk,dest_clk,src_rst,dest_rst,in_valid,out_ready,
 input [WIDTH-1:0] in_data,output in_ready,out_valid,output [WIDTH-1:0] out_data);
 assign in_ready=1;assign out_valid=0;assign out_data=0;endmodule
'''
TB='''module tb;
 reg clk=0;always #2 clk=!clk;
 reg [127:0] data=0;reg [31:0] expected=0;reg [31:0] injected=0;
 candidate_link dut(.fast_clk(clk),.slow_clk(clk),.rst_fast(1'b0),.rst_slow(1'b0),
  .frame_pulse(1'b0),.frame_id(32'd0),.processed_generation(64'd0),.rule_low(1'b0),
  .generation(64'd0),.invalidate(1'b0),.loss(1'b0),.freeze_frame(32'd0));
 task check(input [127:0] x,input [31:0] crc,input [31:0] flip);
 begin
  @(negedge clk);data=x;expected=crc;injected=crc^flip;
  force dut.payload=data;force dut.expected_crc=injected;
  repeat(18) @(negedge clk);
  if((~dut.crc_pipe[15])!==expected) $fatal(1,"CRC affine basis");
  if(dut.crc128(data)!==expected) $fatal(1,"Sender CRC affine basis");
  if(dut.crc_good!==((flip==0) && data[127:97]==0)) $fatal(1,"CRC comparator or reserved bits");
 end endtask
 initial begin
'''

def main():
 source=(HERE/'candidate_link.sv').read_text()
 # Protect the premise of the finite affine certificate. A nonlinear RTL
 # change must update and justify this audit, not silently inherit it.
 body=source[source.index('function [31:0] crc_byte;'):source.index('endfunction',source.index('function [31:0] crc_byte;'))]
 normalized=''.join(body.split())
 assert normalized=="function[31:0]crc_byte;input[31:0]c0;input[7:0]b;reg[31:0]c;integerk;beginc=c0;for(k=0;k<8;k=k+1)c=(c>>1)^((c[0]^b[k])?32'hedb88320:32'd0);crc_byte=c;end"
 body=source[source.index('function [31:0] crc128;'):source.index('endfunction',source.index('function [31:0] crc128;'))]
 assert ''.join(body.split())=="function[31:0]crc128;input[127:0]data;reg[31:0]c;integerk;beginc=32'hffffffff;for(k=0;k<128;k=k+1)c=(c>>1)^((c[0]^data[k])?32'hedb88320:32'd0);crc128=~c;end"
 assert "crc_pipe[0]<=crc_byte(32'hffffffff,payload[7:0]);" in source
 assert 'crc_pipe[i]<=crc_byte(crc_pipe[i-1],payload[i*8+:8]);' in source
 vectors=[(0,0)]+[(1<<i,0) for i in range(128)]+[(0,1<<i) for i in range(32)]
 # Complement/full payload tests supplement, not replace, the full basis.
 vectors += [((1<<128)-1,0),((1<<97)-1,0)]
 tb=TB
 for x,flip in vectors:
  crc=zlib.crc32(x.to_bytes(16,'little'))
  tb+=f" check(128'h{x:032x},32'h{crc:08x},32'h{flip:08x});\n"
 tb+='$display("CRC_BASIS_COMPLETE");$finish;end endmodule\n'
 build=HERE.parent/'.build'/('physical-crc-'+str(time.time_ns()));build.mkdir(parents=True)
 (build/'tb.sv').write_text(STUB+tb)
 rows=[]
 for label in ['actual','polynomial-mutant','comparison-mutant']:
  code=source
  if label=='polynomial-mutant':code=code.replace("32'hedb88320:32'd0", "32'hedb88321:32'd0")
  if label=='comparison-mutant':code=code.replace('assign crc_good=&crc_equal && reserved_good;', 'assign crc_good=crc_equal[0] && reserved_good;')
  (build/(label+'.sv')).write_text(code)
  r=subprocess.run(['iverilog','-g2012','-s','tb','-o',label+'.vvp',label+'.sv','tb.sv'],cwd=build,text=True,capture_output=True)
  assert r.returncode==0,r.stderr
  r=subprocess.run(['vvp',label+'.vvp'],cwd=build,text=True,capture_output=True)
  log=r.stdout+r.stderr;(build/(label+'.log')).write_text(log)
  passed=r.returncode==0 and 'CRC_BASIS_COMPLETE' in log
  assert passed if label=='actual' else not passed,log
  rows.append({'case':label,'passed':passed,'returncode':r.returncode,'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
 report={'cases':rows,'vectors':len(vectors),'independent_oracle':'zlib.crc32; zero + full GF(2) basis',
         'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'build':str(build),
         'scope':'all fixed payloads by affine basis; pipeline scheduling separately proved'}
 (build/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

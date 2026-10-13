`timescale 1ns/1ps
module tb_mailbox;
 reg clk=0;always #10 clk=~clk;
 reg start=0,event_valid=0;reg [129:0] event_data=0;
 reg [11:0] awaddr=0,araddr=0;reg awvalid=0,wvalid=0,arvalid=0;
 reg [31:0] wdata=0;reg [3:0] wstrb=0;reg bready=0,rready=0;
 wire awready,wready,arready,bvalid,rvalid;wire [1:0] bresp,rresp;
 wire [31:0] rdata;wire decision_valid;reg decision_ready=0;
 wire [255:0] decision;wire [63:0] tick;wire fault;
 rule_mailbox dut(.clk(clk),.start(start),.event_valid(event_valid),.event_data(event_data),
  .history_fault(1'b0),.s_axi_awaddr(awaddr),.s_axi_awvalid(awvalid),.s_axi_awready(awready),
  .s_axi_wdata(wdata),.s_axi_wstrb(wstrb),.s_axi_wvalid(wvalid),.s_axi_wready(wready),
  .s_axi_bresp(bresp),.s_axi_bvalid(bvalid),.s_axi_bready(bready),
  .s_axi_araddr(araddr),.s_axi_arvalid(arvalid),.s_axi_arready(arready),
  .s_axi_rdata(rdata),.s_axi_rresp(rresp),.s_axi_rvalid(rvalid),.s_axi_rready(rready),
  .decision_valid(decision_valid),.decision_ready(decision_ready),.decision(decision),
  .tick(tick),.fault(fault));
 integer q=-1,gen=0,rawfile,tracefile,packet,word,mode=0,accepted=0;
 reg [767:0] snapshot;reg [255:0] reply,submitted;
 reg [31:0] readback;reg [63:0] source_time;
 // Independent exogenous raw events; CPU reads never stop the collector.
 always @(negedge clk) begin
  q=q+1;start=(q==0);event_valid=0;
  if((q>=3 && q<2003) || q==2400 || q==3500 || q==5200) begin
   gen=gen+1;source_time=5*q-1;event_valid=1;
   event_data={64'(gen),source_time,1'(q<2003 && q%2==1),1'(q%31==0 || q>=2003)};
   $fdisplay(rawfile,"%d %h",q,event_data);
  end
 end
 task write_bus(input [11:0] addr,input [31:0] data,input [3:0] strobe,
                input integer skew,input [1:0] expected);
  begin
   // Independently delayed AW and W, no assumption of same-cycle arrival.
   fork
    begin
     repeat(skew==1?3:0) @(negedge clk);
     @(negedge clk);awaddr=addr;awvalid=1;
     do @(posedge clk);while(!awready);
     @(negedge clk);awvalid=0;
    end
    begin
     repeat(skew==2?4:0) @(negedge clk);
     @(negedge clk);wdata=data;wstrb=strobe;wvalid=1;
     do @(posedge clk);while(!wready);
     @(negedge clk);wvalid=0;
    end
   join
   wait(bvalid); #1;
   if(bresp!==expected) $fatal(1,"B response addr=%h actual=%h expected=%h",addr,bresp,expected);
   repeat(2) begin @(posedge clk);#1;
    if(!bvalid || bresp!==expected) $fatal(1,"B changed under backpressure");end
   @(negedge clk);bready=1;@(negedge clk);bready=0;
  end
 endtask
 task read_bus(input [11:0] addr,output [31:0] value);
  begin
   @(negedge clk);araddr=addr;arvalid=1;
   do @(posedge clk);while(!arready);
   @(negedge clk);arvalid=0;
   wait(rvalid);#1;value=rdata;
   if(rresp!==0) $fatal(1,"R response");
   repeat(2) begin @(posedge clk);#1;
    if(!rvalid || rresp!==0 || rdata!==value) $fatal(1,"R changed under backpressure");end
   @(negedge clk);rready=1;@(negedge clk);rready=0;
  end
 endtask
 function [31:0] crc32(input [223:0] bytes);
  integer i;reg [31:0] c;
  begin c=32'hffffffff;for(i=0;i<224;i=i+1)
   c=(c>>1)^((c[0]^bytes[i])?32'hedb88320:32'd0);crc32=~c;end
 endfunction
 always @(posedge clk) if(decision_valid && decision_ready) accepted<=accepted+1;
 initial begin
  if(!$value$plusargs("MODE=%d",mode)) mode=0;
  rawfile=$fopen("raw.txt","w");tracefile=$fopen("trace.txt","w");
  repeat(5) @(posedge clk);
  for(packet=0;packet<12;packet=packet+1) begin
   write_bus(12'h004,1,15,packet%3,0);
   for(word=0;word<24;word=word+1) begin
    read_bus(12'h100+word*4,readback);snapshot[word*32+:32]=readback;
   end
   // The source is still active: bank remains identical for a second read.
   read_bus(12'h100,readback);if(readback!==snapshot[31:0]) $fatal(1,"snapshot mutated");
   $t105_decide_batch(snapshot,reply);
   $fdisplay(tracefile,"%h %h",snapshot,reply);
   submitted=reply;
   if(packet==2 && mode!=0) begin
    if(mode==1) submitted[255:224]=~submitted[255:224];
    if(mode==2) begin submitted[63:0]=submitted[63:0]-1;submitted[255:224]=crc32(submitted[223:0]);end
    if(mode==3) begin submitted[127:64]=submitted[127:64]-1;submitted[255:224]=crc32(submitted[223:0]);end
   end
   // Intentionally incomplete publication, then fill the missing byte.
   for(word=0;word<8;word=word+1)
    write_bus(12'h200+word*4,submitted[word*32+:32],word==3?4'b0111:4'b1111,word%3,0);
   write_bus(12'h008,1,15,0,2);
   if(decision_valid) $fatal(1,"partially written answer published");
   write_bus(12'h20c,submitted[127:96],4'b1000,1,0);
   write_bus(12'h008,1,15,2,(packet==2 && mode!=0)?2:0);
   if(packet==2 && mode!=0) begin
    repeat(5) @(posedge clk);
    if(!fault || decision_valid || accepted!=2) $fatal(1,"invalid decision accepted");
    $display("MAILBOX_REJECTED mode=%d accepted=%d",mode,accepted);$finish;
   end
   repeat(5) begin @(posedge clk);#1;
    if(!decision_valid || decision!==reply || fault) $fatal(1,"answer changed or fault");end
   @(negedge clk);decision_ready=1;@(negedge clk);decision_ready=0;
   repeat(4) @(posedge clk);
   read_bus(12'h010,readback);if(readback!=packet+1) $fatal(1,"wrong slow ACK");
  end
  if(accepted!=12 || fault) $fatal(1,"delivery count/fault");
  $display("MAILBOX_OK packets=%d events=%d",accepted,gen);$finish;
 end
 initial begin #10000000;$fatal(1,"mailbox timeout");end
endmodule

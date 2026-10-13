`timescale 1ns/1ps
module tb_isa;
 reg clk=0,start=0,event_valid=0;reg [129:0] event_data=0;
 reg [11:0] awaddr=0,araddr=0;reg awvalid=0,wvalid=0,arvalid=0;
 reg [31:0] wdata=0;reg [3:0] wstrb=15;reg bready=1,rready=1;
 wire awready,wready,arready,bvalid,rvalid;wire [31:0] rdata;
 wire [1:0] bresp,rresp;wire [255:0] decision;wire decision_valid;
 wire [63:0] tick;wire fault;reg decision_ready=1;
 rule_mailbox dut(.clk(clk),.start(start),.event_valid(event_valid),.event_data(event_data),.history_fault(1'b0),
  .s_axi_awaddr(awaddr),.s_axi_awvalid(awvalid),.s_axi_awready(awready),
  .s_axi_wdata(wdata),.s_axi_wstrb(wstrb),.s_axi_wvalid(wvalid),.s_axi_wready(wready),
  .s_axi_bresp(bresp),.s_axi_bvalid(bvalid),.s_axi_bready(bready),
  .s_axi_araddr(araddr),.s_axi_arvalid(arvalid),.s_axi_arready(arready),
  .s_axi_rdata(rdata),.s_axi_rresp(rresp),.s_axi_rvalid(rvalid),.s_axi_rready(rready),
  .decision_valid(decision_valid),.decision_ready(decision_ready),.decision(decision),.tick(tick),.fault(fault));
 always #10 clk=~clk;
 integer op,addr,data,delay,cycles=0,trace,raw,cuts,packets=0;
 reg [31:0] value;reg [1:0] response;reg [63:0] gen=0;
 reg lost=0,newloss,iserr;
 initial begin
  trace=$fopen("packets.txt","w");raw=$fopen("raw.txt","w");cuts=$fopen("cuts.txt","w");
  repeat(4) @(negedge clk);start=1;
  repeat(4) @(negedge clk);
  forever begin
   $isa_next(op,addr,data,delay);
   if(op==2) begin $fclose(trace);$fclose(raw);$fclose(cuts);$isa_reply(0,packets,cycles);$finish;end
   repeat(delay) @(negedge clk);
   if(op==0) begin
    araddr=addr;arvalid=1;
    do @(posedge clk);while(!arready);
    @(negedge clk);arvalid=0;
    wait(rvalid);value=rdata;response=rresp;
    @(negedge clk);
   end else begin
    awaddr=addr;wdata=data;awvalid=1;wvalid=1;
    do @(posedge clk);while(!(awready && wready));
    @(negedge clk);awvalid=0;wvalid=0;
    wait(bvalid);value=0;response=bresp;
    @(negedge clk);
   end
   $isa_reply(response,value,cycles);
  end
 end
 always @(negedge clk) begin
  newloss=cycles>=50 && cycles<2050 ? !lost : 0;
  iserr=cycles>12 && cycles<2200 && cycles%17==0;
  event_valid=start && (iserr || newloss!=lost);
  if(event_valid) begin
   gen=gen+1;event_data={gen,64'(cycles*5),newloss,iserr};
  end
  lost=newloss;
  decision_ready=cycles%29!=0 && cycles%29!=1;
 end
 always @(posedge clk) begin
  cycles<=cycles+1;
  if(dut.collector.cut) $fdisplay(cuts,"%d",tick);
  if(event_valid) $fdisplay(raw,"%d %h",tick,event_data);
  if(decision_valid && decision_ready) begin
   $fdisplay(trace,"%h %h",dut.snapshot,decision);packets<=packets+1;
  end
  if(cycles>200000) $fatal(1,"ISA bridge timeout");
 end
endmodule

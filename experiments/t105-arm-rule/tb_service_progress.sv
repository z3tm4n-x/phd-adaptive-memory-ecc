`timescale 1ns/1ps
// Deliberately unbounded *environment* readiness; NOT a PS7 timing model.
module tb_service_progress;
 reg clk=0;always #10 clk=~clk;
 reg start=0,event_valid=0;reg [129:0] event_data=0;
 reg [11:0] awaddr=0,araddr=0;reg awvalid=0,wvalid=0,arvalid=0;
 reg [31:0] wdata=0;reg [3:0] wstrb=15;reg bready=0,rready=0;
 wire awready,wready,arready,bvalid,rvalid;wire [1:0] bresp,rresp;
 wire [31:0] rdata;wire decision_valid;wire [255:0] decision;
 wire [63:0] tick;wire fault;
 rule_mailbox dut(.clk(clk),.start(start),.event_valid(event_valid),.event_data(event_data),
  .history_fault(1'b0),.s_axi_awaddr(awaddr),.s_axi_awvalid(awvalid),.s_axi_awready(awready),
  .s_axi_wdata(wdata),.s_axi_wstrb(wstrb),.s_axi_wvalid(wvalid),.s_axi_wready(wready),
  .s_axi_bresp(bresp),.s_axi_bvalid(bvalid),.s_axi_bready(bready),
  .s_axi_araddr(araddr),.s_axi_arvalid(arvalid),.s_axi_arready(arready),
  .s_axi_rdata(rdata),.s_axi_rresp(rresp),.s_axi_rvalid(rvalid),.s_axi_rready(rready),
  .decision_valid(decision_valid),.decision_ready(1'b1),.decision(decision),.tick(tick),.fault(fault));
 integer delay_ticks=50001,kind=0,i,read_completions=0,write_completions=0;
 reg [31:0] saved_data;reg [63:0] before_tick;time accepted_at;
 always @(posedge clk) begin
  if(rvalid && rready) read_completions<=read_completions+1;
  if(bvalid && bready) write_completions<=write_completions+1;
 end
 initial begin
  if(!$value$plusargs("DELAY=%d",delay_ticks)) delay_ticks=50001;
  if(!$value$plusargs("KIND=%d",kind)) kind=0;
  @(negedge clk);start=1;@(negedge clk);start=0;
  repeat(3) @(negedge clk);
  if(kind==0) begin
   arvalid=1;araddr=0;
   @(posedge clk);if(!arready) $fatal(1,"read unavailable at start");
   accepted_at=$time;#1;
   if(!rvalid || rresp) $fatal(1,"accepted read did not produce response");
   saved_data=rdata;
   @(negedge clk);arvalid=0;
  end else begin
   // CLAIM creates a retained prefix even when PS has not consumed B.
   awvalid=1;wvalid=1;awaddr=4;wdata=1;
   @(posedge clk);if(!awready || !wready) $fatal(1,"write unavailable at start");
   accepted_at=$time;
   @(negedge clk);awvalid=0;wvalid=0;
   @(posedge clk);#1;if(!bvalid || bresp) $fatal(1,"ordinary write response late");
   @(negedge clk);
  end
  before_tick=tick;
  for(i=0;i<delay_ticks;i=i+1) begin
   // One valid event while the CPU-facing response is stalled.
   event_valid=(i==2);
   event_data={64'd1,64'd50,1'b0,1'b1};
   @(posedge clk);#1;
   if(read_completions || write_completions || fault || decision_valid)
    $fatal(1,"false completion or collector failure during legal stall");
   if(kind==0 && (!rvalid || rdata!==saved_data || rresp)) $fatal(1,"read not held");
   if(kind==1 && (!bvalid || bresp)) $fatal(1,"write not held");
   @(negedge clk);
  end
  event_valid=0;
  if(tick-before_tick!=delay_ticks || dut.collector.end_generation!=1)
   $fatal(1,"collector stopped with CPU");
  if(kind==0) rready=1;else bready=1;
  @(posedge clk);#1;
  if(read_completions+write_completions!=1 || fault) $fatal(1,"recovery duplicated/lost response");
  $display("SERVICE_STALL_OK kind=%0d ticks=%0d elapsed_ns=%0d completions=1 collector_G=1",kind,delay_ticks,$time-accepted_at);
  $finish;
 end
 initial begin #5000000;$fatal(1,"test timeout");end
endmodule

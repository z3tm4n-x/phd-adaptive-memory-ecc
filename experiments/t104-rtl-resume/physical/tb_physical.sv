`timescale 1ns/1ps
// Conditional x16 SRAM, not a manufacturer's ECC model. Real clock/XPM/IOBUF
// primitives; address parts are aliases of the explicitly modeled word.
module tb_physical;
 reg ref100=0;always #5 ref100=!ref100;
 reg startup_rst_fast=1,startup_rst_slow=1,qualified_start=0,loss_slow=0;
 reg [1:0] request_valid=0,response_ready=3;
 reg [241:0] request_data=0;
 wire [1:0] request_ready,response_valid;
 wire [96:0] response_data;
 wire [19:0] sram_a;
 tri [15:0] sram_dq;
 wire sram_ce_n,sram_oe_n,sram_we_n,sram_lb_n,sram_ub_n;
 wire locked,fault,fast_clk,slow_clk;
 reg [15:0] memory[0:1048575];
 reg [524287:0] erroneous=0;
 wire sram_drives=!sram_ce_n && !sram_oe_n && sram_we_n;
 //45ns access,18ns turn-off. Ignoring the shorter22ns OE path is pessimistic.
 assign #(45,45,18) sram_dq=sram_drives?memory[sram_a]:16'hzzzz;
 wire sram_err;
 assign #45 sram_err=erroneous[sram_a[19:1]];
 physical_top dut(.mmcm_startup_reset(1'b0),.*);
 integer a,completed=0;
 realtime arrival,max_response=0;
 reg [63:0] next_id=0;
 reg write_active=0;
 reg [19:0] write_address;
 reg [1:0] write_mask;
 wire writing=!sram_ce_n && !sram_we_n && (!sram_lb_n || !sram_ub_n);
 always @(posedge writing) begin
  write_active=1;write_address=sram_a;write_mask={!sram_ub_n,!sram_lb_n};
 end
 always @(negedge writing) if(write_active) begin
  if(write_address!==sram_a) $fatal(1,"address changed in write");
  if(write_mask[0]) memory[write_address][7:0]=sram_dq[7:0];
  if(write_mask[1]) memory[write_address][15:8]=sram_dq[15:8];
  erroneous[write_address[19:1]]=0;write_active=0;
 end
 always @(posedge fast_clk) begin
  if(dut.controller.busy && sram_a[19:1]!==dut.controller.word_out)
   $fatal(1,"physical word differs from locked semantic word");
  if(sram_drives && dut.drive) $fatal(1,"opposed drive enables");
  if(fault) $fatal(1,"full physical top fault");
 end
 task recycle;
 begin
  #1000;
  if(dut.controller.credits_debug!==0 || dut.controller.app_waiting ||
     dut.controller.app_receipt || dut.controller.reply_pending ||
     dut.controller.app_prepared || dut.controller.active_app && dut.controller.busy)
   $fatal(1,"application state did not recycle");
  if(!dut.controller.app_requests.forward.crossing.in_ready ||
     dut.controller.app_requests.forward.crossing.out_valid ||
     dut.controller.app_requests.forward.crossing.acknowledged ||
     dut.controller.app_requests.forward.crossing.received ||
     dut.controller.app_requests.forward.crossing.requested ||
     !dut.controller.app_responses.backward.crossing.in_ready ||
     dut.controller.app_responses.backward.crossing.out_valid ||
     dut.controller.app_responses.backward.crossing.acknowledged ||
     dut.controller.app_responses.backward.crossing.received ||
     dut.controller.app_responses.backward.crossing.requested)
   $fatal(1,"ACK/request chain did not return to idle");
  if(dut.controller.app_requests.forward.queue.out_valid ||
     dut.controller.app_responses.backward.queue.out_valid ||
     dut.controller.app_ids.out_valid)
   $fatal(1,"application FIFO not empty");
 end endtask
 task transaction(input integer owner,input [1:0] op,input [18:0] word_index,
                  input [31:0] data,input [3:0] mask,input [31:0] expected,input expected_err);
 reg accepted;reg [96:0] observed;
 begin
  @(negedge slow_clk);
  request_data[owner*121+:121]={next_id,mask,data,word_index,op};
  request_valid=1<<owner;arrival=$realtime;accepted=0;
  while(!accepted) begin @(posedge slow_clk);accepted=request_ready[owner];end
  @(negedge slow_clk);request_valid=0;
  wait(response_valid[owner]);observed=response_data;
  if(observed!=={next_id,expected,expected_err})
   $fatal(1,"full pad data/ID mismatch id=%0d actual=%h expected=%h",next_id,observed,{next_id,expected,expected_err});
  @(posedge slow_clk);
  if($realtime-arrival>3000) $fatal(1,"in-envelope response exceeded3us");
  if($realtime-arrival>max_response)max_response=$realtime-arrival;
  completed=completed+1;next_id=next_id+1;
  recycle;
  // First VALID separations >100us; no inference from stress-stream timing.
  #100000;
 end endtask
 initial begin
  for(a=0;a<1048576;a=a+1) memory[a]=0;
  wait(locked);repeat(40) @(posedge slow_clk);
  @(negedge fast_clk);startup_rst_fast=0;
  @(negedge slow_clk);startup_rst_slow=0;
  // The modeled memory is initialized; external qualification occurs only
  // after datasheet's200us stable supply wait, not an implicit warmup reset.
  #210000;@(negedge slow_clk);qualified_start=1;
  wait(dut.controller.running);#2000;
  transaction(0,1,0,0,15,0,0);
  transaction(1,2,5,32'haabbccdd,15,0,0);
  transaction(0,1,5,0,15,32'haabbccdd,0);
  erroneous[5]=1;
  transaction(1,2,5,32'h11223344,5,32'h0000ccdd,1);
  transaction(0,1,5,0,15,32'haa22cc44,0);
  if(erroneous[5]) $fatal(1,"full modeled word not repaired");
  $display("PHYSICAL_PADS_COMPLETE requests=%0d max_response_ns=%0.3f",completed,max_response);
  $finish;
 end
 initial begin #2000000;$fatal(1,"physical test timeout");end
endmodule

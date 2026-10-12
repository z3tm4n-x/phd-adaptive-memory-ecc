`timescale 1ns/1ps
// Actual selected top, production W/timer widths and real UNISIM MMCM/XPM.
// SRAM read data is a directed interface stimulus, NOT a physical SRAM model.
module tb_clocked;
 reg ref100=0,mmcm_startup_reset=1,startup_rst_fast=1,startup_rst_slow=1;
 reg qualified_start=0,loss_slow=0;
 reg [1:0] request_valid=0,response_ready=3;
 reg [241:0] request_data=0;
 wire [1:0] request_ready,response_valid;
 wire [96:0] response_data;
 wire [18:0] word_out;
 wire ce,oe,we,drive,alias_high,locked,fault;
 wire [1:0] byte_enable;wire [15:0] dq_out;
 wire [15:0] dq_in=alias_high?16'hc3a5:16'h5a3c;
 wire err_in=1;
 clocked_integrated dut(.*);
 always #5 ref100=~ref100;
 integer accepted=0,returned=0,j=0,owner=0,fast_edges=0,slow_edges=0;
 realtime last_fast=0,last_slow=0,offered_at=0,max_reply=0;
 reg [120:0] packet;
 always @(posedge dut.fast_clk) begin
   fast_edges=fast_edges+1;
   if(locked && last_fast!=0 && ($realtime-last_fast<3.999 || $realtime-last_fast>4.001))
      $fatal(1,"fast clock period");
   if(locked) last_fast=$realtime;
   if(qualified_start && fault) $fatal(1,"clocked top fault");
 end
 always @(posedge dut.slow_clk) begin
   slow_edges=slow_edges+1;
   if(locked && last_slow!=0 && ($realtime-last_slow<19.999 || $realtime-last_slow>20.001))
      $fatal(1,"slow clock period");
   if(locked) last_slow=$realtime;
   if(|(request_valid & request_ready)) accepted=accepted+1;
   if(|(response_valid & response_ready)) begin
     if(returned>=accepted || response_data[96:33]!=64'(returned) ||
        response_valid!=(returned%2?2:1)) $fatal(1,"clocked ordering/owner");
     if(response_data[32:1]!=(returned%2?32'h00005a3c:32'hc3a55a3c) ||
        response_data[0]!=(returned%2)) $fatal(1,"clocked reply data");
     if($realtime-offered_at>3000) $fatal(1,"clocked response exceeds3us");
     if($realtime-offered_at>max_reply) max_reply=$realtime-offered_at;
     returned=returned+1;
   end
 end
 initial begin
   #200;mmcm_startup_reset=0;
   wait(locked);#500;
   @(negedge dut.fast_clk);startup_rst_fast=0;
   @(negedge dut.slow_clk);startup_rst_slow=0;
   #1000;
   @(negedge dut.slow_clk);qualified_start=1;
   wait(dut.controller.running);#200;
   for(j=0;j<10;j=j+1) begin
     @(negedge dut.slow_clk);
     owner=j%2;packet={64'(j),4'hf,32'hcafebabe,19'(j),2'(1+j%2)};
     request_data[owner*121+:121]=packet;request_valid=owner?2:1;offered_at=$realtime;
     do @(posedge dut.slow_clk); while(!(request_valid&request_ready));
     @(negedge dut.slow_clk);request_valid=0;
     wait(returned==j+1);
     #100020;
   end
   if(accepted!=10 || returned!=10 || fault || dut.controller.rule_low)
      $fatal(1,"clocked completion/default recovery");
   $display("CLOCKED_PASS accepted=%0d returned=%0d max_response_ns=%0.3f fast_edges=%0d slow_edges=%0d",
             accepted,returned,max_reply,fast_edges,slow_edges);
   $finish;
 end
 initial begin #1200000;$fatal(1,"clocked timeout");end
endmodule

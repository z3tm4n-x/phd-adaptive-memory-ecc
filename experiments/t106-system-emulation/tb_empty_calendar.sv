`timescale 1ns/1ps
// A component equivalence witness, not an arm_executor mission. No deposits,
// shortened timers or RTL modifications. Literal clocking through full W.
module tb_empty_calendar;
 parameter integer WB=19;
 localparam integer W=(1<<WB), INV=(W%3==2 ? (W+1)/3 : (2*W+1)/3);
 reg clk=0,start=0;
 always #2 clk=~clk;
 wire [1:0] sd,fd,cd,fault,run;
 wire [WB-1:0] word0,word1;
 wire [2:0] spos0,spos1;
 frame_engine #(.WORD_BITS(WB),.INVERSE(INV)) fast(
  .clk(clk),.start(start),.permit(1'b0),.alarm(1'b0),.backend_busy(1'b0),
  .slot_due(sd[0]),.freeze_due(fd[0]),.control_due(cd[0]),.word_due(word0),
  .fault(fault[0]),.running(run[0]),.slot_pos(spos0));
 // LOW is intentionally supplied before warmup for a stronger component
 // test. This is NOT the legal cold-start rule, which has the full NR hold.
 frame_engine #(.WORD_BITS(WB),.INVERSE(INV)) low(
  .clk(clk),.start(start),.permit(1'b1),.alarm(1'b0),.backend_busy(1'b0),
  .slot_due(sd[1]),.freeze_due(fd[1]),.control_due(cd[1]),.word_due(word1),
  .fault(fault[1]),.running(run[1]),.slot_pos(spos1));
 longint unsigned j=0,f=2,origin=0,t,expected_t;
 longint unsigned executed_fast=0,executed_low=0;
 reg [31:0] digest_fast=0,digest_low=0;
 reg [WB-1:0] expected_word;
 reg expected_low;
 initial begin #20;start=1;end
 always @(posedge clk) begin
  if(sd[0]) begin
   if(j==0) origin=$time;
   t=$time-origin;expected_t=1568*(j/8)+164*(j%8);
   expected_word=(j*INV)%W;expected_low=(j<W || j%3==0);
   if(sd!=2'b11 || t!=expected_t || word0!=expected_word || word1!=expected_word)
    $fatal(1,"slot/time/word j=%0d",j);
   if(!cd[0] || cd[1]!=expected_low || |fault) $fatal(1,"execute/warmup j=%0d",j);
   digest_fast={digest_fast[26:0],digest_fast[31:27]} ^ word0 ^ t[31:0] ^ cd[0];
   digest_low={digest_low[26:0],digest_low[31:27]} ^ word1 ^ t[31:0] ^ cd[1];
   executed_fast=executed_fast+cd[0];executed_low=executed_low+cd[1];
   if(j<8 || (j>=W-8 && j<W+24))
    $display("SLOT %0d %0d %0d %0d %0d",j,t,word0,cd[0],cd[1]);
   j=j+1;
   if(j==W+1024) begin
    $display("EMPTY_CALENDAR WB=%0d slots=%0d freezes=%0d fast=%0d low=%0d hash_fast=%08h hash_low=%08h end_ns=%0d",
      WB,j,f-2,executed_fast,executed_low,digest_fast,digest_low,t);
    $finish;
   end
  end
  if(fd[0]) begin
   t=$time-origin;expected_t=1568*(f/8)+164*(f%8)-320;
   if(fd!=2'b11 || t!=expected_t || low.must_execute!=(f<W || f%3==0))
    $fatal(1,"freeze/warmup f=%0d",f);
   f=f+1;
  end
 end
endmodule

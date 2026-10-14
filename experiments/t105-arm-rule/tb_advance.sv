`timescale 1ns/1ps
// Full-width deadline interface of actual link + vendor XPM + calendar.
// Clock jumps skip idle *input time* only, never policy arithmetic/CDC cycles.
module tb_advance # (parameter integer PHASE=0);
 reg fast_clk=0,slow_clk=0,rst_fast=1,rst_slow=1;
 always #2 fast_clk=~fast_clk;
 initial begin #(PHASE);forever #10 slow_clk=~slow_clk;end
 reg decision_valid=0;
 wire decision_ready;
 reg [255:0] decision=0;
 reg [63:0] slow_tick=0,generation=64'h00000000fffffffe;
 reg invalidate=0,loss=0;
 wire permit,fault,rule_low,installed;
 wire [63:0] processed_generation;
 always @(posedge slow_clk) slow_tick<=slow_tick+1'b1;
 interval_link dut(.*);
 reg start=0;
 wire freeze_due,freeze_pulse,frozen_execute,skip_pulse,running,calendar_fault,control_due;
 frame_engine #(.WORD_BITS(4),.INVERSE(11)) calendar(
  .clk(fast_clk),.start(start),.permit(permit),.alarm(invalidate||loss||fault),
  .backend_busy(1'b0),.control_due(control_due),.app_due(),.slot_due(),.freeze_due(freeze_due),
  .control_prepare(),.app_prepare(),.word_due(),.running(running),.fault(calendar_fault),
  .frame_pulse(),.frame_id(),.freeze_frame(),.slot_pos(),.freeze_pos(),
  .slot_pulse(),.skip_pulse(skip_pulse),.freeze_pulse(freeze_pulse),.frozen_execute(frozen_execute));
 reg monitor_early=0;
 reg [63:0] earliest=0;
 integer successes=0,skips=0;
 realtime expiry_wall;
 always @(posedge fast_clk) begin
  if(!rst_fast) begin
   if((invalidate||loss) && permit) $fatal(1,"same-edge veto missing");
   if(monitor_early && slow_tick<earliest && permit) $fatal(1,"early permission");
   if(fault || calendar_fault) $fatal(1,"unexpected fault");
   if(skip_pulse) skips=skips+1;
  end
 end
 task send;
  input [63:0] gen,due;
  input [31:0] flags;
  integer count;
  begin
   @(negedge slow_clk); count=0;
   while(!decision_ready) begin @(negedge slow_clk);count=count+1;if(count>100) $fatal(1,"link stuck");end
   decision={32'd0,flags,due,gen,64'd1};decision_valid=1;
   @(negedge slow_clk);decision_valid=0;
  end
 endtask
 task jump;
  input [63:0] tick;
  begin @(negedge slow_clk);if(tick<slow_tick) $fatal(1,"backward time");slow_tick=tick;end
 endtask
 task veto;
  begin
   @(negedge fast_clk);invalidate=1;generation=generation+1'b1;
   @(posedge fast_clk);#0.001;if(permit) $fatal(1,"veto failed");
   @(negedge fast_clk);invalidate=0;
  end
 endtask
 task wait_allow;
  integer count;
  begin
   count=0;while(!permit) begin @(negedge fast_clk);count=count+1;if(count>151) $fatal(1,"expiry delivery >604ns");end
   successes=successes+1;
   $display("ALLOW %0d tick=%0d G=%h wall=%0t",successes,slow_tick,generation,$time);
  end
 endtask
 task wait_local_control(input realtime published,input [7:0] reason);
  integer cycles;
  begin
   cycles=0;
   while(!control_due) begin
    @(negedge fast_clk);cycles=cycles+1;
    if(cycles>188) $fatal(1,"local CONTROL waits for ARM");
   end
   if($realtime-published>748.507480) $fatal(1,"local calendar tail");
   $display("LOCAL_CONTROL reason=%0d latency_ns=%0.3f no_CPU_reply=1",reason,$realtime-published);
  end
 endtask
 reg [63:0] due,old_generation;
 realtime publication;
 integer i;
 initial begin
  #160;rst_fast=0;rst_slow=0;start=1;
  // Qualified startup: full NR, prepared long before its expiry.
  due=64'd9015504896; earliest=due;monitor_early=1;
  send(generation,due,1);repeat(2000) @(negedge fast_clk);
  if(permit) $fatal(1,"startup shortened");
  jump(due-8);wait(slow_tick>=due);expiry_wall=$realtime;
  wait_allow();if($realtime-expiry_wall>600.506) $fatal(1,"expiry tail outside contract");
  repeat(800) @(negedge fast_clk);
  if(skips==0) $fatal(1,"no realized LOW slots");
  // Same-edge event at a real calendar freeze; preceding frozen skips
  // remain in the calendar. Do not replace its stored decisions with LOW.
  while(!freeze_due) @(negedge fast_clk);
  invalidate=1;generation=generation+1'b1;publication=$realtime;
  @(posedge fast_clk);#0.001;
  if(permit || !freeze_pulse || !frozen_execute) $fatal(1,"ERR/freeze boundary");
  @(negedge fast_clk);invalidate=0;
  wait_local_control(publication,1);
  // ERR hold; next G crosses bit32. Veto at the precise expiry edge.
  due=slow_tick+64'd4500045002;earliest=due;
  send(generation,due,1);jump(due-1);
  @(posedge slow_clk);#0.001;
  if(slow_tick!=due) $fatal(1,"expiry alignment");
  old_generation=generation;veto();
  repeat(160) @(negedge fast_clk);
  if(permit) $fatal(1,"obsolete expiry survived G change");
  if(generation!=64'h0000000100000000) $fatal(1,"G64 carry not exercised");
  // Old response in flight: old full G, same low32 as a deliberately
  // different generation later, must never install.
  send(old_generation,slow_tick,1);repeat(160) @(negedge fast_clk);
  if(permit) $fatal(1,"old response accepted");
  due=slow_tick+64'd9000090002;earliest=due;
  send(generation,due,1);jump(due-8);wait(slow_tick>=due);wait_allow();
  // Loss remains a local veto; a denied ARM response is not a recovery.
  @(negedge fast_clk);loss=1;invalidate=1;generation=generation+1'b1;publication=$realtime;
  @(negedge fast_clk);invalidate=0;
  wait_local_control(publication,2);
  send(generation,0,0);repeat(160) @(negedge fast_clk);
  if(permit) $fatal(1,"loss permission");
  @(negedge fast_clk);loss=0;invalidate=1;generation=generation+1'b1;
  @(negedge fast_clk);invalidate=0;
  due=slow_tick+64'd9015504896;earliest=due;
  send(generation,due,1);jump(due-8);wait(slow_tick>=due);wait_allow();
  // An event-free refresh arriving on expiry has the same absolute due;
  // decision priority may spend one slow edge, never another hold or B.
  veto();due=slow_tick+64'd4500045002;earliest=due;
  send(generation,due,1);jump(due-2);send(generation,due,1);
  wait(slow_tick>=due);expiry_wall=$realtime;wait_allow();
  if($realtime-expiry_wall>600.506) $fatal(1,"refresh starves due permission");
  // Consecutive events invalidate every predecessor. The final full-width
  // NH deadline works without reset or a new CPU transaction at expiry.
  for(i=0;i<16;i=i+1) begin
   veto();due=slow_tick+64'd9000090002;earliest=due;
   send(generation,due,1);repeat(5) @(negedge slow_clk);
  end
  jump(due-8);wait(slow_tick>=due);wait_allow();
  // Loss of local veto and low32-only equality are separate mutants in
  // the existing inductive guard check; here exercise high-bit alias.
  veto();monitor_early=0;
  send(generation-64'h100000000,slow_tick,1);
  repeat(160) @(negedge fast_clk);
  if(permit) $fatal(1,"high G bits ignored");
  send(generation,slow_tick,1);wait_allow();
  // Installing a due answer and then changing G during pipeline checks.
  veto();send(generation,slow_tick,1);
  wait(dut.received_valid);veto();
  repeat(160) @(negedge fast_clk);if(permit) $fatal(1,"in-flight G accepted");
  $display("PASS ADVANCE phase=%0d allows=%0d skips=%0d full_timers=1",PHASE,successes,skips);
  $finish;
 end
 initial begin #200000;$fatal(1,"test timeout");end
endmodule

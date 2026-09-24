`timescale 1ns/1ps
module schedule_tb;
 logic clk200=0;
 always #2.5 clk200=~clk200;
 logic hard_reset=1,soft_reset=0,ready=1,begin_prep=0,app_valid=1;
 logic transfer_ok=1;
 wire ce_tick,backend_ready,backend_busy,backend_invalid,backend_fault,completed_ack;
 wire command_valid; wire [1:0] command_kind; wire [18:0] command_addr;
 wire epoch_valid,invalid; wire [63:0] tick;
 wire [18:0] addr; wire [47:0] dq; wire ce_n,oe_n,we_n,quiesced;
 wire [2:0] err=0;
 assign dq=(!ce_n&&!oe_n)?48'd0:48'bz;
 reference_slot slot(
 .clk200(clk200),.hard_reset(hard_reset),.soft_reset(soft_reset),.qualified(ready),
 .transfer_ok(transfer_ok),.cmd_valid(command_valid),.cmd_kind(command_kind),
 .cmd_addr(command_addr),.trusted_data({13'd0,command_addr}),.trusted_valid(1'b1),
 .ce_tick(ce_tick),.cmd_ready(backend_ready),.busy(backend_busy),.ack(completed_ack),
 .invalid(backend_invalid),.fault(backend_fault),.quiesced(quiesced),.addr(addr),
 .dq(dq),.err(err),.ce_n(ce_n),.oe_n(oe_n),.we_n(we_n));
 reference_schedule sch(
 .clk200(clk200),.hard_reset(hard_reset),.begin_prep(begin_prep),.ce_tick(ce_tick),
 .ready(ready),.soft_reset(soft_reset),.backend_ready(backend_ready),
 .backend_busy(backend_busy),.backend_invalid(backend_invalid),.backend_fault(backend_fault),
 .completed_ack(completed_ack),.app_valid(app_valid),.app_addr(19'd321),
 .command_valid(command_valid),.command_kind(command_kind),.command_addr(command_addr),
 .epoch_valid(epoch_valid),.invalid(invalid),.tick(tick));
 integer mode=0,prep_seen=0,scrub_seen=0,reads=0;
 logic [63:0] expected_start,last_read=0;
 always @(posedge clk200) begin
   if(!hard_reset && ce_tick && command_valid && backend_ready) begin
     if(command_kind==0) begin
       if(tick!=24*64'(prep_seen) || command_addr!=19'(prep_seen)) $fatal(1,"prep phase/address");
       prep_seen=prep_seen+1;
     end
     if(command_kind==1) begin
       expected_start=20000000+(64'(scrub_seen)*100000000)/524288;
       if(tick!=expected_start || command_addr!=19'(scrub_seen)) $fatal(1,"shifted scrub phase");
       scrub_seen=scrub_seen+1;
     end
     if(command_kind==2) begin
       if(reads>0 && tick-last_read<48) $fatal(1,"read spacing");
       if(tick+24>sch.next_scrub) $fatal(1,"read overlap");
       last_read=tick; reads=reads+1;
     end
   end
 end
 task automatic reset_all;
   hard_reset=1; soft_reset=0; begin_prep=0;
   repeat(3) @(negedge clk200);
   hard_reset=0;
 endtask
 initial begin
   reset_all();
   begin_prep=1; @(negedge clk200); begin_prep=0;
   wait(prep_seen==5);
   repeat(2) @(negedge clk200); // allow registered ACK to reach scheduler
   if(sch.prep_completed<4 || invalid) $fatal(1,"prep completion accounting");
   // Explicit boundary-state injection, not a claimed full preparation run.
   reset_all(); mode=1;
   sch.running=1; sch.tick=19999998; sch.prep_issued=524288; sch.prep_completed=524288;
   wait(scrub_seen==1024);
   @(negedge clk200);
   if(!epoch_valid || invalid || reads<2000) $fatal(1,"epoch/saturation");
   soft_reset=1;
   wait(quiesced);
   repeat(2) @(negedge clk200); // accepted slot may pulse ACK at drain fence
   if(epoch_valid || backend_busy || completed_ack) $fatal(1,"quiesce certificate");
   reset_all();
   if(epoch_valid) $fatal(1,"hard reset epoch");
   // Missing one prepare commit must suppress t0, not delay it.
   sch.running=1; sch.tick=19999998; sch.prep_issued=524288; sch.prep_completed=524287;
   wait(tick>20000001);
   @(negedge clk200);
   if(epoch_valid || !invalid) $fatal(1,"incomplete preparation accepted");
   $display("PASS schedule prep_prefix=5 scrub_slots=1024 reads=%0d boundary_injection=explicit",reads);
   $finish;
 end
 initial begin #10000000; $fatal(1,"timeout"); end
endmodule

`timescale 1ns/1ps
// Command/calendar witness. Same clk200 and ce_tick as reference_slot.
// BEGIN fixes prep tick zero; externally binding epoch tick 20,000,000 to UTC
// is a required integration condition, not demonstrated by these modules.
module reference_schedule(
 input logic clk200, hard_reset, begin_prep, ce_tick, ready, soft_reset,
 input logic backend_ready, backend_busy, backend_invalid, backend_fault, completed_ack,
 input logic app_valid, input logic [18:0] app_addr,
 output logic command_valid, output logic [1:0] command_kind,
 output logic [18:0] command_addr,
 output logic epoch_valid, invalid,
 output logic [63:0] tick
);
 localparam logic [63:0] N=524288, P=100000000, LEAD=20000000;
 logic running, stopping;
 logic [19:0] prep_issued, prep_completed;
 logic [18:0] word_index;
 logic [63:0] period_index, next_scrub, next_app;
 logic [63:0] phase_product;
 always_comb begin
   phase_product={45'd0,word_index}*P;
   next_scrub=LEAD+period_index*P+(phase_product>>19);
   command_valid=0; command_kind=0; command_addr=0;
   if(running && !invalid && !stopping && !soft_reset && ready) begin
     if(tick<LEAD) begin
       command_valid=(prep_issued<N && tick==24*{44'd0,prep_issued});
       command_kind=0; command_addr=prep_issued[18:0];
     end else if(epoch_valid || (tick==LEAD && prep_completed==N && !backend_busy)) begin
       if(tick==next_scrub) begin
         command_valid=1; command_kind=1; command_addr=word_index;
       end else if(app_valid && tick>=next_app && tick+24<=next_scrub) begin
         command_valid=1; command_kind=2; command_addr=app_addr;
       end
     end
   end
 end
 always_ff @(posedge clk200) begin
   if(hard_reset) begin
     running<=0; stopping<=0; epoch_valid<=0; invalid<=0; tick<=0;
     prep_issued<=0; prep_completed<=0; word_index<=0; period_index<=0; next_app<=0;
   end else begin
     if(soft_reset) begin stopping<=1; epoch_valid<=0; end
     if(running && (!ready || backend_invalid || backend_fault)) begin invalid<=1; epoch_valid<=0; end
     if(begin_prep && !running && ready && !invalid && !stopping) running<=1;
     // ACK is a clk200 pulse emitted after the backend's CE edge.
     if(completed_ack && running && tick<=LEAD) prep_completed<=prep_completed+1'b1;
     if(ce_tick && running) begin
       tick<=tick+1'b1;
       if(tick==LEAD) begin
         epoch_valid<=ready && !backend_busy && !backend_invalid && !backend_fault && !invalid &&
                      !stopping && !soft_reset && prep_completed==N;
         if(prep_completed!=N || backend_busy) invalid<=1;
       end
       if(command_valid && backend_ready) begin
         if(command_kind==0) prep_issued<=prep_issued+1'b1;
         if(command_kind==1) begin
           if(word_index==N-1) begin word_index<=0; period_index<=period_index+1'b1; end
           else word_index<=word_index+1'b1;
         end
         if(command_kind==2) next_app<=tick+48;
       end
       // A missed fixed reservation invalidates rather than delaying phase.
       if(command_valid && command_kind!=2 && !backend_ready) begin
         invalid<=1; epoch_valid<=0;
       end
     end
   end
 end
endmodule

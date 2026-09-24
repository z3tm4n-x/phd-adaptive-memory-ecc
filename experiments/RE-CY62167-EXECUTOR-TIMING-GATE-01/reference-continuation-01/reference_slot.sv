`timescale 1ns/1ps
// Minimal conditional slot witness, not a board-ready controller.
// cmd_* and qualification/reset inputs are INTERNAL synchronous integration ports.
// qualified is a design/monitor assumption, NOT an invented SRAM ACK wire.
module reference_slot(
 input logic clk200, hard_reset, soft_reset, qualified, transfer_ok,
 input logic cmd_valid, input logic [1:0] cmd_kind, // 0 prep, 1 scrub, 2 app
 input logic [18:0] cmd_addr, input logic [31:0] trusted_data,
 input logic trusted_valid,
 output logic ce_tick, cmd_ready, busy, ack, invalid, fault, quiesced,
 output logic [18:0] addr,
 inout wire [47:0] dq, input logic [2:0] err,
 output logic ce_n, oe_n, we_n
);
 function automatic logic [38:0] from_bus(input logic [47:0] b);
   integer p,d,h; logic [38:0] v;
   begin
     v='0; d=0; h=0;
     for(p=1;p<=38;p=p+1)
       if((p&(p-1))==0) begin v[p-1]=b[32+h]; h=h+1; end
       else begin v[p-1]=b[d]; d=d+1; end
     v[38]=b[38]; return v;
   end
 endfunction
 function automatic logic [47:0] to_bus(input logic [38:0] v);
   integer p,d,h; logic [47:0] b;
   begin
     b='0; d=0; h=0;
     for(p=1;p<=38;p=p+1)
       if((p&(p-1))==0) begin b[32+h]=v[p-1]; h=h+1; end
       else begin b[d]=v[p-1]; d=d+1; end
     b[38]=v[38]; return b;
   end
 endfunction
 function automatic logic [47:0] encoded(input logic [31:0] data);
   integer p,d,h; logic [38:0] v; logic parity;
   begin
     v='0; d=0;
     for(p=1;p<=38;p=p+1)
       if((p&(p-1))!=0) begin v[p-1]=data[d]; d=d+1; end
     for(h=0;h<6;h=h+1) begin
       parity=0;
       for(p=1;p<=38;p=p+1) if((p&(1<<h))!=0) parity=parity^v[p-1];
       v[(1<<h)-1]=parity;
     end
     v[38]=^v[37:0]; return to_bus(v);
   end
 endfunction
 logic [4:0] age;
 logic [1:0] kind;
 logic [47:0] latched, write_image;
 logic [2:0] latched_err;
 logic write_selected, stopping, slot_fault;
 logic [38:0] code, corrected_code;
 logic corrected, uncorrectable;
 integer p, syndrome;
 always_comb begin
   code=from_bus(latched); corrected_code=code; syndrome=0;
   corrected=0; uncorrectable=0;
   for(p=1;p<=38;p=p+1) if(code[p-1]) syndrome=syndrome^p;
   if(^code) begin
     if(syndrome==0) begin corrected_code[38]=~code[38]; corrected=1; end
     else if(syndrome<=38) begin corrected_code[syndrome-1]=~code[syndrome-1]; corrected=1; end
     else uncorrectable=1;
   end else if(syndrome!=0) uncorrectable=1;
 end
 wire drive=busy && write_selected && age>=12 && age<21;
 assign dq=drive ? write_image : 48'bz;
 always_comb begin
   ce_n=!busy;
   oe_n=!(busy && kind!=0 && age<8);
   we_n=!(busy && write_selected && age>=13 && age<19);
   cmd_ready=ce_tick && (!busy || age==23) && !invalid && !stopping
             && !soft_reset && qualified && transfer_ok;
   quiesced=stopping && !busy && ce_n && oe_n && we_n;
 end
 always_ff @(posedge clk200) begin
   if(hard_reset) begin
     ce_tick<=0; busy<=0; ack<=0; invalid<=0; fault<=0; stopping<=0;
     age<=0; addr<=0; kind<=0; latched<=0; latched_err<=0;
     write_image<=0; write_selected<=0; slot_fault<=0;
     // hard reset destroys the external epoch certificate; see schedule witness.
   end else begin
     ce_tick<=~ce_tick; ack<=0;
     if(soft_reset) stopping<=1;
     if(!qualified || !transfer_ok) invalid<=1;
     if(ce_tick) begin
       if(busy) begin
         age<=age+1'b1;
         if(age==7 && kind!=0) begin latched<=dq; latched_err<=err; end
         if(age==9 && kind!=0) begin
           write_image<=to_bus(corrected_code);
           slot_fault<=uncorrectable; fault<=fault|uncorrectable;
           write_selected<=(kind==1) && !uncorrectable && (corrected || |latched_err);
         end
         if(age==23) begin
           busy<=0;
           ack<=qualified && transfer_ok && !invalid && !slot_fault && we_n && !drive;
         end
       end
       if(cmd_valid && cmd_ready) begin
         busy<=1; age<=0; addr<=cmd_addr; kind<=cmd_kind; slot_fault<=0;
         write_selected<=cmd_kind==0;
         if(cmd_kind==0) begin
           write_image<=encoded(trusted_data);
           if(!trusted_valid) begin invalid<=1; write_selected<=0; end
         end
       end
     end
   end
 end
endmodule

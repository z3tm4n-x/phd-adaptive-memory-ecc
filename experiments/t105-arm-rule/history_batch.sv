// 50MHz collector after the ACCEPTED history FIFO. No policy thresholds.
// Snapshot is the state before its capture edge; a coincident event belongs
// to the next prefix. Only qualified initial values; no runtime reset.
module history_batch(
 input wire clk,start,event_valid,input wire [129:0] event_data,
 input wire history_fault,snapshot_request,snapshot_ack,
 output reg snapshot_valid=0,output reg [767:0] snapshot=0,
 output reg [63:0] tick=0,output reg fault=0
);
 reg started=0,healthy=1,had_recovery=0;
 reg [63:0] start_tick=0,packet_seq=0,base_generation=0,end_generation=0;
 reg [63:0] first_source=0,last_source=0,first_tick=0,last_tick=0;
 reg [63:0] recovery_tick=0,last_event_tick=0;
 reg [31:0] event_count=0,err_count=0;
 wire cut=snapshot_request && !snapshot_valid && started && packet_seq!=64'hffffffffffffffff;
 wire [63:0] incoming_gen=event_data[129:66],src=event_data[65:2];
 wire loss=event_data[1],err=event_data[0];
 wire [31:0] next_event_count=cut?32'd1:event_count+1'b1;
 wire [31:0] next_err_count=cut?32'd1:err_count+1'b1;
 wire [31:0] flags={27'd0,(fault||history_fault),
    (event_count!=0 && last_event_tick==tick-1'b1),had_recovery,healthy,started};
 always @(posedge clk) begin
  if(tick!=64'hffffffffffffffff) tick<=tick+1'b1; else fault<=1;
  if(start && !started) begin started<=1; start_tick<=tick; end
  if(history_fault) fault<=1;
  if(snapshot_ack) snapshot_valid<=0;
  if(snapshot_request && packet_seq==64'hffffffffffffffff) fault<=1;
  if(cut) begin
   snapshot<={32'd0,flags,err_count,event_count,recovery_tick,last_tick,
               first_tick,last_source,first_source,start_tick,tick-64'd1,
               end_generation,base_generation,packet_seq+64'd1};
   snapshot_valid<=1;packet_seq<=packet_seq+1'b1;
   base_generation<=end_generation;event_count<=0;err_count<=0;
   had_recovery<=0;recovery_tick<=0;
   first_tick<=0;last_tick<=0;first_source<=0;last_source<=0;
  end
  if(event_valid) begin
   if(!started || incoming_gen!=end_generation+64'd1 ||
      end_generation==64'hffffffffffffffff ||
      (!cut && event_count==32'hffffffff)) fault<=1;
   end_generation<=incoming_gen;event_count<=next_event_count;
   last_event_tick<=tick;healthy<=!loss;
   if(!loss && !healthy) begin had_recovery<=1;recovery_tick<=tick;end
   if(err) begin
    if(!cut && err_count==32'hffffffff) fault<=1;
    if(cut || err_count==0) begin first_source<=src;first_tick<=tick;end
    last_source<=src;last_tick<=tick;err_count<=next_err_count;
   end
  end
 end
endmodule

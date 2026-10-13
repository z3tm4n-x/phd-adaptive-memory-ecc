// Slow-side programmable deadline + standard complete-bus XPM handshake.
// This replaces per-frame beacons; the unchanged calendar still samples a
// locally prepared permit at its original freeze edge.
module interval_link(
 input wire fast_clk,slow_clk,rst_fast,rst_slow,
 input wire decision_valid,output wire decision_ready,input wire [255:0] decision,
 input wire [63:0] slow_tick,generation,input wire invalidate,loss,
 output wire permit,output wire fault,
 output reg [63:0] processed_generation=0,
 output wire rule_low,output wire installed
);
 reg [63:0] after_tick=0;
 reg slow_fault=0;
 reg allowed=0,active=0,announced=0;
 reg pending=0;reg [64:0] sending=0;
 wire channel_ready,received_valid,received_ready;
 wire [64:0] received;
 assign decision_ready=!pending;
 assign rule_low=active && allowed && slow_tick>=after_tick && !slow_fault;
 xpm_cdc_single #(.DEST_SYNC_FF(3),.SRC_INPUT_REG(1),.INIT_SYNC_FF(1)) fault_cdc(
  .src_clk(slow_clk),.src_in(slow_fault),.dest_clk(fast_clk),.dest_out(fault));
 always @(posedge slow_clk) begin
  if(pending && channel_ready) pending<=0;
  if(decision_valid && decision_ready) begin
   processed_generation<=decision[127:64];after_tick<=decision[191:128];
   allowed<=decision[223:192]==1;active<=1;announced<=0;
   if(decision[223:192]==2) slow_fault<=1;
  end else if(active && !announced && !pending && (!allowed || rule_low)) begin
   sending<={processed_generation,rule_low};pending<=1;announced<=1;
  end
 end
 handshake_channel #(.WIDTH(65)) crossing(
  .src_clk(slow_clk),.dest_clk(fast_clk),.src_rst(rst_slow),.dest_rst(rst_fast),
  .in_valid(pending),.in_ready(channel_ready),.in_data(sending),
  .out_valid(received_valid),.out_ready(received_ready),.out_data(received));
 interval_guard guard(.clk(fast_clk),.valid(received_valid),.data(received),
  .ready(received_ready),.generation(generation),.invalidate(invalidate),
  .loss(loss),.permit(permit),.installed(installed));
endmodule

// Complete placed/routed demonstrator shell. No ARM, hardware qualification,
// or workload claim. The independently tested generic CPU/X interface is
// terminated by registered, dynamic on-chip sources so every interface net
// has a real routed endpoint. Shell cost is reported separately.
module board_top(
 input wire ref100,qualified_switch,loss_switch,
 output wire [19:0] sram_a,inout wire [15:0] sram_dq,
 output wire sram_ce_n,sram_oe_n,sram_we_n,sram_lb_n,sram_ub_n,
 input wire sram_err,output wire locked_led,fault_led
);
 wire fast_clk,slow_clk,locked,core_fault;
 wire rst_fast,rst_slow;
 wire qualified_start,loss_slow;
 xpm_cdc_async_rst #(.DEST_SYNC_FF(4),.INIT_SYNC_FF(1),.RST_ACTIVE_HIGH(1)) rf(
  .src_arst(!locked),.dest_clk(fast_clk),.dest_arst(rst_fast));
 xpm_cdc_async_rst #(.DEST_SYNC_FF(4),.INIT_SYNC_FF(1),.RST_ACTIVE_HIGH(1)) rs(
  .src_arst(!locked),.dest_clk(slow_clk),.dest_arst(rst_slow));
 xpm_cdc_single #(.DEST_SYNC_FF(3),.SRC_INPUT_REG(0),.INIT_SYNC_FF(1)) qualification(
  .src_clk(1'b0),.src_in(qualified_switch),.dest_clk(slow_clk),.dest_out(qualified_start));
 xpm_cdc_single #(.DEST_SYNC_FF(3),.SRC_INPUT_REG(0),.INIT_SYNC_FF(1)) loss_input(
  .src_clk(1'b0),.src_in(loss_switch),.dest_clk(slow_clk),.dest_out(loss_slow));

 wire [1:0] request_ready,response_valid;
 wire [96:0] response_data;
 reg [1:0] request_valid=0;
 wire [241:0] request_data;
 // All payload fields vary; the source holds its request until accepted.
 // Starts are spaced200us, CPU/X staggered100us. This is only a timing shell;
 // envelope proofs and arbitrary interleavings use the generic RTL.
 reg [120:0] stimulus0=121'h1452b196030788695757dc231215ab1;
 reg [120:0] stimulus1=121'h07ced434bac918147abcd2895163732;
 reg [13:0] phase=0;
 reg [96:0] receipt=0;
 reg receipt_valid=0;
 wire [3:0] mask0=stimulus0[56:53]==0?4'hf:stimulus0[56:53];
 wire [3:0] mask1=stimulus1[56:53]==0?4'hf:stimulus1[56:53];
 assign request_data[120:0]={stimulus0[120:57],mask0,stimulus0[52:2],stimulus0[0]?2'd1:2'd2};
 assign request_data[241:121]={stimulus1[120:57],mask1,stimulus1[52:2],stimulus1[0]?2'd1:2'd2};
 always @(posedge slow_clk) begin
  receipt_valid<=|response_valid;
  if(|response_valid) receipt<=response_data;
  if(!rst_slow && qualified_start) begin
   phase<=phase==9999?0:phase+1'b1;
   if(phase==0) request_valid[0]<=1;
   if(phase==5000) request_valid[1]<=1;
   if(request_valid[0] && request_ready[0]) begin
    request_valid[0]<=0;
    stimulus0<={stimulus0[119:0],stimulus0[120]^stimulus0[102]};
   end
   if(request_valid[1] && request_ready[1]) begin
    request_valid[1]<=0;
    stimulus1<={stimulus1[119:0],stimulus1[120]^stimulus1[102]};
   end
  end
 end
 // The response endpoint really uses every returned data/ID bit. It cannot
 // drive the controller's decisions, history, qualification, or input stream.
 reg [96:0] signature=0;
 always @(posedge slow_clk) if(receipt_valid) signature<=
  {signature[95:0],signature[96]} ^ receipt;
 wire fault_slow;
 xpm_cdc_single #(.DEST_SYNC_FF(3),.SRC_INPUT_REG(1),.INIT_SYNC_FF(1)) fault_sync(
  .src_clk(fast_clk),.src_in(core_fault),.dest_clk(slow_clk),.dest_out(fault_slow));
 reg led=0,lock_led=0;
 always @(posedge slow_clk) begin led<=fault_slow ^ (^signature);lock_led<=locked;end
 assign fault_led=led;assign locked_led=lock_led;
 physical_top core(.ref100(ref100),.mmcm_startup_reset(1'b0),
  .startup_rst_fast(rst_fast),.startup_rst_slow(rst_slow),
  .qualified_start(qualified_start),.loss_slow(loss_slow),
  .request_valid(request_valid),.request_ready(request_ready),.request_data(request_data),
  .response_valid(response_valid),.response_ready(2'b11),.response_data(response_data),
  .sram_a(sram_a),.sram_dq(sram_dq),.sram_ce_n(sram_ce_n),.sram_oe_n(sram_oe_n),
  .sram_we_n(sram_we_n),.sram_lb_n(sram_lb_n),.sram_ub_n(sram_ub_n),.sram_err(sram_err),
  .locked(locked),.fault(core_fault),.fast_clk(fast_clk),.slow_clk(slow_clk));
endmodule

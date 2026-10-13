// T105 SRAM I/O boundary. Exact accepted mapping, pin registers and clocks;
// additional AXI-Lite control interface attaches to the real PS7 delivery BD.
module arm_physical_top(
    input wire [11:0] s_axi_awaddr,input wire s_axi_awvalid,output wire s_axi_awready,
    input wire [31:0] s_axi_wdata,input wire [3:0] s_axi_wstrb,
    input wire s_axi_wvalid,output wire s_axi_wready,
    output wire [1:0] s_axi_bresp,output wire s_axi_bvalid,input wire s_axi_bready,
    input wire [11:0] s_axi_araddr,input wire s_axi_arvalid,output wire s_axi_arready,
    output wire [31:0] s_axi_rdata,output wire [1:0] s_axi_rresp,
    output wire s_axi_rvalid,input wire s_axi_rready,
 input wire ref100,mmcm_startup_reset,startup_rst_fast,startup_rst_slow,
 input wire qualified_start,loss_slow,
 input wire [1:0] request_valid,output wire [1:0] request_ready,
 input wire [241:0] request_data,
 output wire [1:0] response_valid,input wire [1:0] response_ready,
 output wire [96:0] response_data,
 output wire [19:0] sram_a,inout wire [15:0] sram_dq,
 output wire sram_ce_n,sram_oe_n,sram_we_n,sram_lb_n,sram_ub_n,
 input wire sram_err,output wire locked,fault,
 output wire fast_clk,slow_clk
);
 clock_250_50 clocks(.ref100(ref100),.startup_reset(mmcm_startup_reset),
  .fast_clk(fast_clk),.slow_clk(slow_clk),.locked(locked));
 reg boundary_rst_fast=1,boundary_rst_slow=1;
 always @(posedge fast_clk) boundary_rst_fast<=startup_rst_fast;
 always @(posedge slow_clk) boundary_rst_slow<=startup_rst_slow;
 wire [18:0] word_out;
 wire [18:0] prepared_word;
 (* IOB="TRUE" *) reg [18:0] pad_word=0;
 always @(posedge fast_clk) pad_word<=prepared_word;
 wire [19:0] physical_address;
 wire ce,oe,we,drive,alias_high,err_in;
 wire [1:0] byte_enable;
 wire [15:0] dq_in,dq_out;
 wire pad_ce_n,pad_oe_n,pad_we_n;
 wire [1:0] pad_be_n;
 wire [15:0] pad_t_n;
 address_map mapping(.word_index(pad_word),.half(alias_high),.address(physical_address));
 arm_executor controller(.running(),.busy(),.pending(),.err_due(),.release_due(),
  .grant_debug(),.app_grant_debug(),.grant_data_debug(),.slot_pulse(),.skip_pulse(),
  .freeze_pulse(),.frozen_execute(),.generation(),.processed_generation(),
  .rule_low(),.candidate_permit(),
  .frame_id(),.credits_debug(),.startup_rst_fast(boundary_rst_fast),
  .startup_rst_slow(boundary_rst_slow),.*);
 genvar b;
 generate for(b=0;b<20;b=b+1) begin: address_pads
  OBUF #(.IOSTANDARD("LVCMOS33"),.DRIVE(8),.SLEW("FAST")) p(.I(physical_address[b]),.O(sram_a[b]));
 end
 for(b=0;b<16;b=b+1) begin: data_pads
  IOBUF #(.IOSTANDARD("LVCMOS33"),.DRIVE(8),.SLEW("FAST")) p(
   .I(dq_out[b]),.O(dq_in[b]),.T(pad_t_n[b]),.IO(sram_dq[b]));
 end endgenerate
 OBUF #(.IOSTANDARD("LVCMOS33"),.DRIVE(8),.SLEW("FAST")) cp(.I(pad_ce_n),.O(sram_ce_n));
 OBUF #(.IOSTANDARD("LVCMOS33"),.DRIVE(8),.SLEW("FAST")) op(.I(pad_oe_n),.O(sram_oe_n));
 OBUF #(.IOSTANDARD("LVCMOS33"),.DRIVE(8),.SLEW("FAST")) wp(.I(pad_we_n),.O(sram_we_n));
 OBUF #(.IOSTANDARD("LVCMOS33"),.DRIVE(8),.SLEW("FAST")) lp(.I(pad_be_n[0]),.O(sram_lb_n));
 OBUF #(.IOSTANDARD("LVCMOS33"),.DRIVE(8),.SLEW("FAST")) up(.I(pad_be_n[1]),.O(sram_ub_n));
 IBUF #(.IOSTANDARD("LVCMOS33")) ep(.I(sram_err),.O(err_in));
endmodule

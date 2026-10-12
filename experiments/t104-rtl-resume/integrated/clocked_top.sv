// Full functional controller with common clocks. Only the SRAM-facing pins
// are promoted to the physical wrapper; application is a 50-MHz fabric port.
// This OOC top is NOT by itself a routed SRAM/FMC physical boundary.
module clocked_integrated(
    input wire ref100,mmcm_startup_reset,startup_rst_fast,startup_rst_slow,
    input wire qualified_start,loss_slow,
    input wire [1:0] request_valid,output wire [1:0] request_ready,
    input wire [241:0] request_data,
    output wire [1:0] response_valid,input wire [1:0] response_ready,
    output wire [96:0] response_data,
    input wire [15:0] dq_in,input wire err_in,
    output wire [18:0] word_out,
    output wire ce,oe,we,drive,alias_high,
    output wire [1:0] byte_enable,output wire [15:0] dq_out,
    output wire locked,fault
);
    wire fast_clk,slow_clk;
    clock_250_50 clocks(.ref100(ref100),.startup_reset(mmcm_startup_reset),
        .fast_clk(fast_clk),.slow_clk(slow_clk),.locked(locked));
    // Initialization-only fabric boundary. Raw top-level reset must not
    // share a combinational path with the FIFO's internal reset FSM.
    // Both incoming resets are synchronous to their named domains and
    // remain asserted until clocks are stable. Qualified start is later
    // than all vendor FIFO reset-busy deassertions. No runtime reset added.
    reg boundary_rst_fast=1,boundary_rst_slow=1;
    always @(posedge fast_clk) boundary_rst_fast<=startup_rst_fast;
    always @(posedge slow_clk) boundary_rst_slow<=startup_rst_slow;
    integrated_executor controller(.running(),.busy(),.pending(),.err_due(),.release_due(),
        .grant_debug(),.app_grant_debug(),.grant_data_debug(),.slot_pulse(),.skip_pulse(),
        .freeze_pulse(),.frozen_execute(),.generation(),.processed_generation(),
        .rule_low(),.candidate_permit(),.short_left(),.long_left(),.recovery_left(),
        .frame_id(),.credits_debug(),.startup_rst_fast(boundary_rst_fast),
        .startup_rst_slow(boundary_rst_slow),.*);
endmodule

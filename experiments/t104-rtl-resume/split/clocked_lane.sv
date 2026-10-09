// Common-clock OOC demonstrator. Non-clock ports remain virtual interfaces.
// It is not a board-top and has no assumed SRAM alias-to-pad mapping.
module clocked_lane(
    input wire ref100, mmcm_startup_reset,
    input wire startup_rst_slow, startup_rst_fast, soft_loss_slow,
    input wire request_valid, output wire request_ready,
    input wire [120:0] request_data,
    output wire response_valid, input wire response_ready,
    output wire [96:0] response_data,
    input wire [15:0] dq_in, input wire err_in,
    output wire [18:0] word_out,
    output wire ce, oe, we, drive, alias_high,
    output wire [1:0] byte_enable, output wire [15:0] dq_out,
    output wire locked,
    output wire queues_ready_slow,
    output wire protocol_fault
);
    wire fast_clk, slow_clk;
    clock_250_50 clocks(.ref100(ref100), .startup_reset(mmcm_startup_reset),
        .fast_clk(fast_clk), .slow_clk(slow_clk), .locked(locked));
    // Simulation reads these witnesses hierarchically. They are not 149
    // physical debug pins and must not force external hold delay on the FSM.
    operation_lane lane(.fast_busy(),.err_due(),.loss_fast(),.generation(),
        .grant_debug(),.release_debug(),.grant_data_debug(),.age_debug(),.*);
endmodule

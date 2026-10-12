// Candidate board component, NOT wired into the OOC executor timing run.
// No operational reset/clock gating of the executor on loss of LOCKED.
// startup_reset must only be used before qualified start / after containment.
module clock_tree(input wire board_100mhz, startup_reset,
    output wire mem_clk, cpu_clk, x_clk, command_clk, locked);
    wire reference_clock, feedback, feedback_buffered;
    wire mem_unbuffered, cpu_unbuffered, x_unbuffered, command_unbuffered;
    IBUF clock_input(.I(board_100mhz), .O(reference_clock));
    MMCME2_BASE #(.BANDWIDTH("OPTIMIZED"), .CLKIN1_PERIOD(10.0),
        .DIVCLK_DIVIDE(1), .CLKFBOUT_MULT_F(10.0), .CLKOUT0_DIVIDE_F(4.0),
        .CLKOUT1_DIVIDE(10), .CLKOUT2_DIVIDE(8), .CLKOUT3_DIVIDE(10),
        .REF_JITTER1(0.005), .STARTUP_WAIT("FALSE")) mmcm(
        .CLKIN1(reference_clock), .CLKFBIN(feedback_buffered),
        .CLKFBOUT(feedback), .CLKOUT0(mem_unbuffered), .CLKOUT1(cpu_unbuffered),
        .CLKOUT2(x_unbuffered), .CLKOUT3(command_unbuffered),
        .LOCKED(locked), .PWRDWN(1'b0), .RST(startup_reset));
    BUFG feedback_buf(.I(feedback), .O(feedback_buffered));
    BUFG mem_buf(.I(mem_unbuffered), .O(mem_clk));
    BUFG cpu_buf(.I(cpu_unbuffered), .O(cpu_clk));
    BUFG x_buf(.I(x_unbuffered), .O(x_clk));
    BUFG command_buf(.I(command_unbuffered), .O(command_clk));
endmodule

// Common physical clock source; not two unrelated primary clocks.
module clock_250_50(input wire ref100, startup_reset,
    output wire fast_clk, slow_clk, locked);
    wire reference, feedback, feedback_buffered, fast_raw, slow_raw;
    IBUF input_buffer(.I(ref100),.O(reference));
    MMCME2_BASE #(.BANDWIDTH("OPTIMIZED"),.CLKIN1_PERIOD(10.0),
        .DIVCLK_DIVIDE(1),.CLKFBOUT_MULT_F(10.0),.CLKOUT0_DIVIDE_F(4.0),
        .CLKOUT1_DIVIDE(20),.REF_JITTER1(0.005),.STARTUP_WAIT("FALSE")) mmcm(
        .CLKIN1(reference),.CLKFBIN(feedback_buffered),.CLKFBOUT(feedback),
        .CLKOUT0(fast_raw),.CLKOUT1(slow_raw),.LOCKED(locked),
        .PWRDWN(1'b0),.RST(startup_reset));
    BUFG fb(.I(feedback),.O(feedback_buffered));
    BUFG fast(.I(fast_raw),.O(fast_clk));
    BUFG slow(.I(slow_raw),.O(slow_clk));
endmodule

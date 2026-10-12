// Standard vendor async FIFO, dedicated to the ordered observation history.
// No runtime reset: only the common qualified startup reset may clear it.
module event_fifo #(parameter integer WIDTH=130, DEPTH=512)(
    input wire wr_clk,rd_clk,rst,
    input wire in_valid, output wire in_ready, input wire [WIDTH-1:0] in_data,
    output wire out_valid,input wire out_ready,output wire [WIDTH-1:0] out_data,
    output wire wr_busy,rd_busy
);
    wire full,empty;
    assign in_ready=!rst && !wr_busy && !full;
    assign out_valid=!rd_busy && !empty;
    xpm_fifo_async #(.FIFO_MEMORY_TYPE("block"),.FIFO_WRITE_DEPTH(DEPTH),
        .WRITE_DATA_WIDTH(WIDTH),.READ_DATA_WIDTH(WIDTH),.READ_MODE("fwft"),
        .FIFO_READ_LATENCY(0),.CDC_SYNC_STAGES(3),.RELATED_CLOCKS(0),
        .WR_DATA_COUNT_WIDTH($clog2(DEPTH)+1),.RD_DATA_COUNT_WIDTH($clog2(DEPTH)+1),
        .PROG_FULL_THRESH(DEPTH-8),.PROG_EMPTY_THRESH(8),.USE_ADV_FEATURES("0000"),
        .ECC_MODE("no_ecc"),.SIM_ASSERT_CHK(1),.DOUT_RESET_VALUE("0"),
        .FULL_RESET_VALUE(0),.WAKEUP_TIME(0)) fifo(
        .wr_clk(wr_clk),.rd_clk(rd_clk),.rst(rst),.sleep(1'b0),
        // XPM itself gates ram_wr_en with !full && !wr_rst_busy. Repeating
        // that reset fanout outside XPM adds no protection. The producer
        // starts only after FIFO initialization; !ready is a latched fault,
        // never permission to silently discard and keep LOW.
        .din(in_data),.wr_en(in_valid),.full(full),
        .dout(out_data),.rd_en(out_valid && out_ready),.empty(empty),
        .wr_rst_busy(wr_busy),.rd_rst_busy(rd_busy),
        .injectsbiterr(1'b0),.injectdbiterr(1'b0));
endmodule

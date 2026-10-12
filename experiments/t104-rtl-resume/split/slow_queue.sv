module slow_queue #(parameter integer WIDTH=121)(
    input wire clk,rst,in_valid,out_ready,
    input wire [WIDTH-1:0] in_data,
    output wire in_ready,out_valid,
    output wire [WIDTH-1:0] out_data,
    output wire wr_busy,rd_busy
);
    wire full,empty;
    assign in_ready=!rst && !wr_busy && !full;
    assign out_valid=!rd_busy && !empty;
    xpm_fifo_sync #(.FIFO_MEMORY_TYPE("block"),.FIFO_WRITE_DEPTH(16),
        .WRITE_DATA_WIDTH(WIDTH),.READ_DATA_WIDTH(WIDTH),
        .READ_MODE("fwft"),.FIFO_READ_LATENCY(0),
        .WR_DATA_COUNT_WIDTH(5),.RD_DATA_COUNT_WIDTH(5),
        .PROG_FULL_THRESH(10),.PROG_EMPTY_THRESH(5),.USE_ADV_FEATURES("0000"),
        .ECC_MODE("no_ecc"),.SIM_ASSERT_CHK(1),.EN_SIM_ASSERT_ERR("fatal"),
        .DOUT_RESET_VALUE("0"),.FULL_RESET_VALUE(0),.WAKEUP_TIME(0)) fifo(
        .wr_clk(clk),.rst(rst),.sleep(1'b0),
        .din(in_data),.wr_en(in_valid && in_ready),.full(full),
        .dout(out_data),.rd_en(out_valid && out_ready),.empty(empty),
        .wr_rst_busy(wr_busy),.rd_rst_busy(rd_busy),
        .injectsbiterr(1'b0),.injectdbiterr(1'b0));
endmodule

// Queue storage is ONLY in the slow domain. Fast side is a vendor handshake.
// Kept interface name for the component boundary, not an XPM_FIFO_ASYNC claim.
module async_queue #(parameter integer WIDTH=121, SLOW_SOURCE=1)(
    input wire wr_clk, rd_clk, rst, rd_rst,
    input wire in_valid, output wire in_ready,
    input wire [WIDTH-1:0] in_data,
    output wire out_valid, input wire out_ready,
    output wire [WIDTH-1:0] out_data,
    output wire wr_busy, rd_busy
);
    wire v,r,unused_busy;
    wire [WIDTH-1:0] data;
    generate if(SLOW_SOURCE) begin: forward
        slow_queue #(.WIDTH(WIDTH)) queue(.clk(wr_clk),.rst(rst),
            .in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),
            .out_valid(v),.out_ready(r),.out_data(data),.wr_busy(wr_busy),.rd_busy(unused_busy));
        handshake_channel #(.WIDTH(WIDTH)) crossing(.src_clk(wr_clk),.dest_clk(rd_clk),
            .src_rst(rst),.dest_rst(rd_rst),.in_valid(v),.in_ready(r),.in_data(data),
            .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data));
        assign rd_busy=rd_rst;
    end else begin: backward
        handshake_channel #(.WIDTH(WIDTH)) crossing(.src_clk(wr_clk),.dest_clk(rd_clk),
            .src_rst(rst),.dest_rst(rd_rst),.in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),
            .out_valid(v),.out_ready(r),.out_data(data));
        slow_queue #(.WIDTH(WIDTH)) queue(.clk(rd_clk),.rst(rd_rst),
            .in_valid(v),.in_ready(r),.in_data(data),
            .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),
            .wr_busy(unused_busy),.rd_busy(rd_busy));
        assign wr_busy=rst;
    end endgenerate
endmodule

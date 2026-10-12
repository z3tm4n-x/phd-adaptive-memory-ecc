// Nondeterministic FIFO boundary, NOT a claimed implementation of XPM.
// Only the operation lane is verified here. End-to-end XPM order is tested
// with the actual vendor simulation; its guarantee remains a trusted contract.
module async_queue #(parameter WIDTH=121,SLOW_SOURCE=1)(
    input wire wr_clk,rd_clk,rst,rd_rst,in_valid,out_ready,
    input wire [WIDTH-1:0] in_data,
    output wire in_ready,out_valid,
    output wire [WIDTH-1:0] out_data,
    output wire wr_busy,rd_busy);
    (* anyseq *) reg arbitrary_capacity,arbitrary_valid,arbitrary_busy_w,arbitrary_busy_r;
    (* anyseq *) reg [WIDTH-1:0] arbitrary_data;
    assign in_ready=arbitrary_capacity;
    assign out_valid=arbitrary_valid;
    assign out_data=arbitrary_data;
    assign wr_busy=arbitrary_busy_w;
    assign rd_busy=arbitrary_busy_r;
endmodule
module xpm_cdc_single #(parameter DEST_SYNC_FF=3,SRC_INPUT_REG=1,INIT_SYNC_FF=1,SIM_ASSERT_CHK=1)(
    input wire src_clk,src_in,dest_clk,output wire dest_out);
    (* anyseq *) reg arbitrary_loss;
    assign dest_out=arbitrary_loss;
endmodule
module formal_lane(input wire clk, input wire [15:0] dq, input wire err);
    operation_lane dut(.fast_clk(clk),.slow_clk(clk),.startup_rst_slow(1'b0),
        .startup_rst_fast(1'b0),.soft_loss_slow(1'b0),.request_valid(1'b0),
        .request_data(121'd0),.response_ready(1'b0),.dq_in(dq),.err_in(err));
endmodule

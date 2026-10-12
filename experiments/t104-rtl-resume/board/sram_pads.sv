// No extra clock edge. Physical address is an EXPLICIT upstream contract:
// no unverified word/alias concatenation is invented here.
// Drive/load choices are provisional engineering choices, not measured paths.
module sram_pads(input wire [19:0] physical_address,
    input wire ce, oe, we, drive,
    input wire [1:0] byte_enable, input wire [15:0] dq_out,
    output wire [15:0] dq_in, output wire err_in,
    output wire [19:0] sram_a,
    inout wire [15:0] sram_dq,
    output wire sram_ce_n, sram_oe_n, sram_we_n, sram_lb_n, sram_ub_n,
    input wire sram_err);
    assign sram_a=physical_address;
    assign sram_ce_n=!ce;
    assign sram_oe_n=!oe;
    assign sram_we_n=!we;
    assign sram_lb_n=!byte_enable[0];
    assign sram_ub_n=!byte_enable[1];
    IBUF #(.IOSTANDARD("LVCMOS33")) err_buffer(.I(sram_err), .O(err_in));
    genvar b;
    generate for(b=0;b<16;b=b+1) begin: data_pads
        IOBUF #(.IOSTANDARD("LVCMOS33"), .DRIVE(8), .SLEW("SLOW")) pad(
            .I(dq_out[b]), .O(dq_in[b]), .T(!drive), .IO(sram_dq[b]));
    end endgenerate
endmodule

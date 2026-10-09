// Standard XPM handshake with a registered source capture enable.
// One added SOURCE-clock preparation cycle, outside the SRAM operation.
// No runtime reset/cancellation; startup only, same vendor CDC primitive.
module handshake_channel #(parameter integer WIDTH=121)(
    input wire src_clk,dest_clk,src_rst,dest_rst,
    input wire in_valid,output wire in_ready,
    input wire [WIDTH-1:0] in_data,
    output wire out_valid,input wire out_ready,
    output wire [WIDTH-1:0] out_data
);
    reg occupied=0,capture=0,send=0,await_drop=0;
    reg [WIDTH-1:0] snapshot=0,hold_data=0;
    reg acknowledged=0;
    wire received,requested;
    assign in_ready=!occupied && !src_rst;
    assign out_valid=requested && !acknowledged && !dest_rst;
    always @(posedge src_clk) begin
        snapshot<=in_data;
        capture<=in_valid && in_ready;
        if(in_valid && in_ready) occupied<=1;
        if(capture) begin hold_data<=snapshot; send<=1; end
        if(send && received) begin send<=0; await_drop<=1; end
        if(await_drop && !received) begin occupied<=0; await_drop<=0; end
    end
    always @(posedge dest_clk) begin
        if(out_valid && out_ready) acknowledged<=1;
        else if(!requested) acknowledged<=0;
    end
    xpm_cdc_handshake #(.WIDTH(WIDTH),.DEST_EXT_HSK(1),
        .DEST_SYNC_FF(3),.SRC_SYNC_FF(3),.INIT_SYNC_FF(1),.SIM_ASSERT_CHK(1)) transfer(
        .src_clk(src_clk),.src_in(hold_data),.src_send(send),.src_rcv(received),
        .dest_clk(dest_clk),.dest_out(out_data),.dest_req(requested),.dest_ack(acknowledged));
endmodule

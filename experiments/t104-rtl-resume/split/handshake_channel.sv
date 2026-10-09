// Standard vendor full handshake; no home-made cross-domain toggle or Gray bus.
// Startup/GSR initializes this channel. Runtime reset must not cancel an owner.
module handshake_channel #(parameter integer WIDTH=121)(
    input wire src_clk,dest_clk,src_rst,dest_rst,
    input wire in_valid, output wire in_ready,
    input wire [WIDTH-1:0] in_data,
    output wire out_valid, input wire out_ready,
    output wire [WIDTH-1:0] out_data
);
    reg [1:0] source_phase=0;
    reg [WIDTH-1:0] hold_data=0;
    reg acknowledged=0;
    wire received, requested;
    assign in_ready=(source_phase==0) && !src_rst;
    assign out_valid=requested && !acknowledged && !dest_rst;
    always @(posedge src_clk) begin
        if(in_valid && in_ready) begin
            hold_data<=in_data;
            source_phase<=1;
        end else if(source_phase==1 && received) source_phase<=2;
        else if(source_phase==2 && !received) source_phase<=0;
    end
    always @(posedge dest_clk) begin
        if(out_valid && out_ready) acknowledged<=1;
        else if(!requested) acknowledged<=0;
    end
    xpm_cdc_handshake #(.WIDTH(WIDTH), .DEST_EXT_HSK(1),
        .DEST_SYNC_FF(3), .SRC_SYNC_FF(3), .INIT_SYNC_FF(1), .SIM_ASSERT_CHK(1)) transfer(
        .src_clk(src_clk),.src_in(hold_data),.src_send(source_phase==1),.src_rcv(received),
        .dest_clk(dest_clk),.dest_out(out_data),.dest_req(requested),.dest_ack(acknowledged));
endmodule

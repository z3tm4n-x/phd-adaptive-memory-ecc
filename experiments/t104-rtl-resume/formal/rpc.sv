// Safety for arbitrary defined source/destination clock edges, no fairness
// or physical metastability model. The endpoint computes bitwise NOT(data).
module formal_rpc #(parameter integer BITS=8)(
    input wire src_clk,dst_clk,src_valid,src_reply_ready,dst_ready,
    input wire [BITS-1:0] src_data
);
    wire src_ready,src_reply_valid,dst_valid,dst_reply_ready,dst_retire,dst_occupied;
    wire [BITS-1:0] src_reply_data,dst_data;
    reg have=0,sent=0;
    reg [BITS-1:0] answer=0;
    wire dst_reply_valid=have&&!sent;
    wire [BITS-1:0] dst_reply_data=answer;
    rpc_cdc #(.REQUEST_BITS(BITS),.REPLY_BITS(BITS)) dut(.*);
    reg source_outstanding=0;
    reg [BITS-1:0] source_expected=0;
    always @(posedge src_clk) begin
        if(src_valid && src_ready) begin
            assert(!source_outstanding);
            source_outstanding<=1;source_expected<=~src_data;
        end
        if(src_reply_valid) begin
            assert(source_outstanding);
            assert(src_reply_data==source_expected);
            if(src_reply_ready) source_outstanding<=0;
        end
    end
    always @(posedge dst_clk) begin
        if(dst_valid && dst_ready) begin
            assert(!have);
            have<=1;answer<=~dst_data;
        end
        if(dst_reply_valid && dst_reply_ready) sent<=1;
        if(dst_retire) begin
            assert(have && sent);
            have<=0;sent<=0;
        end
    end
endmodule

// One outstanding transaction INCLUDING its held reply. No operational reset.
// Only toggle bits pass synchronizers. Payload registers stay stable until
// the remote consumer has used them and the round-trip credit has returned.
// ASYNC_REG is a placement hint, NOT metastability/MTBF qualification.
module rpc_cdc #(parameter integer REQUEST_BITS=128, REPLY_BITS=32)(
    input wire src_clk, dst_clk,
    input wire src_valid,
    input wire [REQUEST_BITS-1:0] src_data,
    output wire src_ready,
    output wire src_reply_valid,
    output wire [REPLY_BITS-1:0] src_reply_data,
    input wire src_reply_ready,
    output wire dst_valid,
    output wire [REQUEST_BITS-1:0] dst_data,
    input wire dst_ready,
    input wire dst_reply_valid,
    input wire [REPLY_BITS-1:0] dst_reply_data,
    output wire dst_reply_ready,
    output wire dst_retire,
    output wire dst_occupied
);
    reg request=0, consumed=0, final_ack=0, response=0;
    reg delivered=0, replied=0;
    reg [REQUEST_BITS-1:0] request_hold=0;
    reg [REPLY_BITS-1:0] response_hold=0;
    (* ASYNC_REG="TRUE" *) reg [2:0] request_sync=0, consume_sync=0;
    (* ASYNC_REG="TRUE" *) reg [2:0] response_sync=0, credit_sync=0;
    assign src_ready = request==credit_sync[2];
    assign src_reply_valid = response_sync[2]!=consumed;
    assign src_reply_data = response_hold;
    assign dst_valid = request_sync[2]!=final_ack && !delivered;
    assign dst_data = request_hold;
    assign dst_reply_ready = delivered && !replied;
    assign dst_retire = replied && consume_sync[2]==response;
    assign dst_occupied = request_sync[2]!=final_ack;
    always @(posedge src_clk) begin
        response_sync <= {response_sync[1:0],response};
        credit_sync <= {credit_sync[1:0],final_ack};
        if (src_valid && src_ready) begin
            request_hold<=src_data;
            request<=!request;
        end
        if (src_reply_valid && src_reply_ready) consumed<=response_sync[2];
    end
    always @(posedge dst_clk) begin
        request_sync <= {request_sync[1:0],request};
        consume_sync <= {consume_sync[1:0],consumed};
        if (dst_valid && dst_ready) delivered<=1;
        if (dst_reply_valid && dst_reply_ready) begin
            response_hold<=dst_reply_data;
            response<=request_sync[2];
            replied<=1;
        end
        if (dst_retire) begin
            final_ack<=response;
            delivered<=0; replied<=0;
        end
    end
endmodule

// Actual RPC RTL; unconstrained Boolean clock edges and endpoint latency.
// Endpoint may finish at any destination edge AFTER accepting the request,
// emits arbitrary reply data, and retains its transaction until retire.
// No fairness, reset, metastability, or physical bundled-data delay model.
module formal_rpc_contract #(
    parameter integer REQUEST_BITS=8, REPLY_BITS=8
)(
    input wire src_clk, dst_clk, src_valid, src_reply_ready, dst_ready,
    input wire endpoint_finish,
    input wire [REQUEST_BITS-1:0] src_data,
    input wire [REPLY_BITS-1:0] endpoint_data
);
    wire src_ready, src_reply_valid, dst_valid, dst_reply_ready;
    wire dst_retire, dst_occupied;
    wire [REQUEST_BITS-1:0] dst_data;
    wire [REPLY_BITS-1:0] src_reply_data;
    reg have=0, answered=0, sent=0;
    reg [REPLY_BITS-1:0] answer=0;
    // After its first handshake the endpoint may drop VALID or keep it high
    // (executor_core's bad-input reply is held). Neither may duplicate delivery.
    wire dst_reply_valid=have && answered && (!sent || endpoint_finish);
    wire [REPLY_BITS-1:0] dst_reply_data=answer;
    rpc_cdc #(.REQUEST_BITS(REQUEST_BITS),.REPLY_BITS(REPLY_BITS)) dut(.*);

    // Separate monitors; neither changes the DUT or assumes its correctness.
    reg outstanding=0;
    reg [REQUEST_BITS-1:0] expected_request=0;
    always @(posedge src_clk) begin
        if(src_valid && src_ready) begin
            assert(!outstanding);
            outstanding<=1;
            expected_request<=src_data;
        end
        if(src_reply_valid) begin
            assert(outstanding);
            assert(src_reply_data==answer);
            assert(have && sent);
            if(src_reply_ready) outstanding<=0;
        end
    end
    always @(posedge dst_clk) begin
        if(dst_valid && dst_ready) begin
            assert(!have);
            assert(dst_data==expected_request);
            have<=1;
        end
        if(have && !answered && endpoint_finish) begin
            answer<=endpoint_data;
            answered<=1;
        end
        if(dst_reply_ready) assert(have);
        if(dst_reply_valid && dst_reply_ready) sent<=1;
        if(dst_retire) begin
            assert(have && sent);
            assert(!outstanding);
            have<=0;
            answered<=0;
            sent<=0;
        end
    end
endmodule

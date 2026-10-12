// No runtime reset. At most ONE coalesced invalidation per 4-xi edge.
// The 64-bit saturation point is unreachable in the declared ten-year mission;
// see contract_check.py. Beyond that horizon saturation is conservatively FAST.
// This comparison is a component, NOT yet a pipelined LOW/freeze integration.
module generation_guard #(
    parameter integer BITS=64
)(
    input wire clk, loss, err_event, invalidate,
    input wire candidate_valid,
    input wire [BITS-1:0] candidate_generation,
    output reg [BITS-1:0] generation=0,
    output wire permitted, exhausted
);
    reg previous_loss=0;
    wire change=err_event || invalidate || (loss && !previous_loss);
    assign exhausted=&generation;
    assign permitted=candidate_valid && !loss && !err_event && !invalidate &&
                     !exhausted && candidate_generation==generation;
    always @(posedge clk) begin
        previous_loss<=loss;
        if(change && !exhausted) generation<=generation+1'b1;
    end
endmodule

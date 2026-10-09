// Local veto at FREEZE, not at an already committed SRAM grant.
// Matching generation is necessary, never sufficient scientific permission.
module predecision_guard #(
    parameter integer GEN_BITS=16
)(
    input wire clk, loss, err_event,
    input wire candidate_valid,
    input wire [GEN_BITS-1:0] candidate_generation,
    output reg [GEN_BITS-1:0] generation=0,
    output wire permitted, exhausted
);
    reg previous_loss=0;
    assign exhausted = &generation;
    assign permitted = candidate_valid && !loss && !err_event && !exhausted
                     && candidate_generation == generation;
    always @(posedge clk) begin
        previous_loss <= loss;
        if ((err_event || (loss && !previous_loss)) && !exhausted)
            generation <= generation + 1'b1;
    end
endmodule

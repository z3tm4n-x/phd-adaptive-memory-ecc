module formal_guard(input wire clk, loss, err_event, candidate_valid,
                    input wire [15:0] candidate_generation);
    wire [15:0] generation;
    wire permitted, exhausted;
    predecision_guard dut(.*);
    reg [15:0] expected_generation=0;
    reg was_lost=0;
    wire invalidating_event=err_event || (loss && !was_lost);
    wire expected_permission=candidate_valid && !loss && !err_event
          && (expected_generation != 16'hffff)
          && (candidate_generation == expected_generation);
    always @(posedge clk) begin
        assert(generation==expected_generation);
        assert(permitted==expected_permission);
        assert(exhausted==(expected_generation==16'hffff));
        was_lost<=loss;
        case({expected_generation==16'hffff,invalidating_event})
            2'b01: expected_generation<=expected_generation+16'd1;
            default: expected_generation<=expected_generation;
        endcase
    end
endmodule

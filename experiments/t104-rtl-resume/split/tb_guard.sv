`timescale 1ns/1ps
module tb_guard;
    reg clk=0, loss=0, err_event=0, candidate_valid=1;
    reg [15:0] candidate_generation=0;
    wire [15:0] generation;
    wire permitted,exhausted;
    integer i, expected=0;
    predecision_guard dut(.*);
    initial begin
        // All reachable generation values, including exhaustion; no force.
        for(i=0;i<65540;i=i+1) begin
            candidate_generation=16'(expected); err_event=0;
            #1;
            if(permitted !== (expected<65535)) $fatal(1,"fresh generation");
            candidate_generation=16'(expected+1); #1;
            if(permitted) $fatal(1,"future/stale generation");
            candidate_generation=16'(expected); err_event=1; #1;
            if(permitted) $fatal(1,"same-edge ERR veto");
            clk=1; if(expected<65535) expected=expected+1; #1;
            if(generation!==16'(expected)) $fatal(1,"saturation");
            clk=0;
        end
        $display("PASS guard generations=65536 saturation=5"); $finish;
    end
endmodule

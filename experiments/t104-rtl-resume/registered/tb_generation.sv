`timescale 1ns/1ps
module tb_generation;
    reg clk=0; always #2 clk=~clk;
    reg loss=0,err_event=0,invalidate=0,candidate_valid=1;
    reg [63:0] candidate_generation=0;
    wire [63:0] generation;
    wire permitted,exhausted;
    generation_guard dut(.*);
    integer i;
    initial begin
        @(negedge clk);
        for(i=0;i<70000;i=i+1) begin
            candidate_generation=i; err_event=0; #0.1;
            if(!permitted || exhausted || generation!=i) $fatal(1,"lost fresh generation %0d",i);
            err_event=1; loss=(i%3==0); invalidate=(i%7==0); #0.1;
            if(permitted) $fatal(1,"same-edge invalidation ignored");
            @(posedge clk); #0.1;
            if(generation!=i+1 || exhausted || permitted) $fatal(1,"stale/coalescing error");
            @(negedge clk); loss=0; invalidate=0;
        end
        err_event=0; candidate_generation=0; #0.1;
        if(permitted) $fatal(1,"old token replayed");
        candidate_generation=70000; #0.1;
        if(!permitted) $fatal(1,"unbounded FAST at old saturation");
        $display("PASS generation 70000 coalesced invalidations, no reset"); $finish;
    end
endmodule

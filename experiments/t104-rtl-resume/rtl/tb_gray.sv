`timescale 1ns/1ps
// Addressed regression of the actual core at every binary carry boundary.
// The injected time is a test hook, NOT information supplied by an application.
module tb_gray;
    reg clk=0;
    always #2 clk=~clk;
    reg [63:0] injected=0;
    wire [63:0] time_gray;
    executor_core dut(.clk(clk),.soft_reset(1'b0),.loss(1'b0),.recover(1'b0),
        .start_ok(1'b0),.cfg_wr(1'b0),.cfg_commit(1'b0),.cfg_address(4'd0),
        .cfg_data(32'd0),.request_valid(2'd0),.request_payload(512'd0),
        .retire(2'd0),.command_valid(1'b0),.command_integrity(1'b0),
        .command_payload(384'd0),.dq_in(16'd0),.err_in(1'b0),.time_gray(time_gray));
    integer bit_n, cases=0, j;
    reg [63:0] previous_binary=0, previous_gray=0, delta, expected;
    task check;
        input [63:0] tick;
        begin
            @(negedge clk); injected=tick<<2;
            #0.1;
            if(time_gray!==previous_gray) $fatal(1,"Gray changed between edges");
            @(posedge clk); #0.1;
            // Independent bit-by-bit Gray definition, not the RTL shift/XOR.
            expected=0;
            for(j=0;j<62;j=j+1) expected[j]=injected[j+2]^((j==61)?1'b0:injected[j+3]);
            if(time_gray!==expected) $fatal(1,"Gray value/latency changed");
            if(tick==previous_binary+1) begin
                delta=time_gray^previous_gray;
                if(delta==0 || (delta&(delta-1))!=0) $fatal(1,"non-unit Gray transition");
            end
            previous_binary=tick; previous_gray=time_gray; cases=cases+1;
        end
    endtask
    initial begin
        force dut.now=injected;
        force dut.running=1'b1;
        check(0);
        for(bit_n=1;bit_n<62;bit_n=bit_n+1) begin
            check((64'd1<<bit_n)-1);
            check(64'd1<<bit_n);
            check((64'd1<<bit_n)+1);
        end
        check(64'h3fffffffffffffff);
        $display("T104_GRAY_PASS cases=%0d",cases);
        $finish;
    end
endmodule

`timescale 1ns/1ps
// Real core register-update/compare path. Invalid-mask offers deliberately
// create error replies, letting the endpoint retire each test transaction.
module tb_spacing;
    reg clk=0;
    always #2 clk=~clk;
    reg [1:0] request_valid=0,retire=0;
    reg [511:0] request_payload=0;
    wire [1:0] request_ready;
    executor_core dut(.clk(clk),.soft_reset(1'b0),.loss(1'b0),.recover(1'b0),
        .start_ok(1'b0),.cfg_wr(1'b0),.cfg_commit(1'b0),.cfg_address(4'd0),
        .cfg_data(32'd0),.request_valid(request_valid),.request_payload(request_payload),
        .request_ready(request_ready),.retire(retire),.command_valid(1'b0),
        .command_integrity(1'b0),.command_payload(384'd0),.dq_in(16'd0),.err_in(1'b0));
    integer cases=0,k;
    reg expected;
    task check;
        input [63:0] previous,current;
        begin
            @(negedge clk); request_payload=0; request_payload[223:160]=previous;
            request_valid=1; retire=0;
            #0.1; if(!request_ready[0]) $fatal(1,"test endpoint not ready");
            @(posedge clk); #0.1;
            @(negedge clk); request_valid=0; retire=1;
            @(posedge clk); #0.1;
            @(negedge clk); retire=0; request_payload[223:160]=current;
            #0.1;
            expected=!(current>=previous && current-previous>=64'd5508);
            if(dut.close0!==expected) $fatal(1,"spacing previous=%h current=%h",previous,current);
            cases=cases+1;
        end
    endtask
    initial begin
        force dut.now=64'hffffffffffffffff;
        force dut.running=1'b1;
        check(0,5507); check(0,5508); check(0,5509);
        check(10000,9999); check(10000,15507); check(10000,15508);
        check(64'hffffffffffffea7b,64'hffffffffffffffff);
        check(64'hffffffffffffea7c,64'hffffffffffffffff);
        check(64'hffffffffffffffff,64'hffffffffffffffff);
        check(64'hffffffffffffffff,5507);
        for(k=13;k<64;k=k+1) begin
            check((64'd1<<k)-5508,64'd1<<k);
            check((64'd1<<k)-5507,64'd1<<k);
            check(64'd1<<k,(64'd1<<k)-1);
        end
        $display("T104_SPACING_PASS cases=%0d",cases);
        $finish;
    end
endmodule

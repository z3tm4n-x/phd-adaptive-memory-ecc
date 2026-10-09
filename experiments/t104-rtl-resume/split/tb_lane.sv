`timescale 1ns/1ps
module tb_lane;
    parameter integer PHASE=0;
    parameter integer STRESS=1;
    reg fast_clk=0, slow_clk=0, rst_s=1, rst_f=1, loss=0;
    always #2 fast_clk=~fast_clk;
    initial begin #(PHASE); forever #10 slow_clk=~slow_clk; end
    wire req_ready, resp_valid, qready;
    reg req_valid=0, resp_ready=0;
    reg [120:0] req_data=0;
    wire [96:0] resp_data;
    wire [18:0] word_out;
    wire ce,oe,we,drive,alias_high,busy,err_due,loss_fast,grant,release_op,fault;
    wire [1:0] be;
    wire [15:0] dq_out,gen;
    wire [120:0] granted;
    wire [7:0] age;
    integer sent=0, received=0, fast_edges=0, slow_edges=0, last_accept=-1000;
    integer malformed_offers=0;
    reg malformed=0;
    reg [63:0] active_id=0;
    wire [15:0] dq_in=alias_high ? 16'hc3a5 : 16'h5a3c;
    wire err_in=active_id[0];
    operation_lane dut(.fast_clk(fast_clk),.slow_clk(slow_clk),
        .startup_rst_slow(rst_s),.startup_rst_fast(rst_f),.soft_loss_slow(loss),
        .request_valid(req_valid),.request_ready(req_ready),.request_data(req_data),
        .response_valid(resp_valid),.response_ready(resp_ready),.response_data(resp_data),
        .dq_in(dq_in),.err_in(err_in),.word_out(word_out),.ce(ce),.oe(oe),.we(we),
        .drive(drive),.alias_high(alias_high),.byte_enable(be),.dq_out(dq_out),
        .fast_busy(busy),.err_due(err_due),.loss_fast(loss_fast),.generation(gen),
        .queues_ready_slow(qready),.grant_debug(grant),.release_debug(release_op),
        .grant_data_debug(granted),.age_debug(age),.protocol_fault(fault));
    initial begin
        repeat(10) @(negedge slow_clk); rst_s=0;
    end
    initial begin
        repeat(50) @(negedge fast_clk); rst_f=0;
    end
    always @(negedge slow_clk) begin
        slow_edges=slow_edges+1;
        req_valid=!rst_s && qready && sent<360 && (STRESS || slow_edges-last_accept>=280);
        req_data={64'(sent),4'((sent/6)%15+1),32'(32'hf0a50000+sent),
                  19'((sent*174763)%524288),2'((sent/2)%3)};
        // Long stall deliberately OUTSIDE the bounded-latency input contract.
        malformed=req_valid && malformed_offers<2;
        if(malformed) begin
            if(malformed_offers==0) req_data[1:0]=3;
            else req_data[56:53]=0;
        end
        resp_ready=!rst_s && !(STRESS && slow_edges>40 && slow_edges<240)
                     && slow_edges%11!=0 && slow_edges%11!=1;
        loss=(slow_edges%137>=30 && slow_edges%137<36);
    end
    always @(posedge slow_clk) begin
        if(malformed) begin
            if(req_ready) $fatal(1,"malformed request accepted");
            malformed_offers=malformed_offers+1;
        end
        if(req_valid && req_ready) begin
            $display("ACCEPT %0t %031h",$time,req_data); sent=sent+1;
            last_accept=slow_edges;
        end
        if(resp_valid && resp_ready) begin
            $display("REPLY %0t %025h",$time,resp_data); received=received+1;
        end
        if(received==360) begin
            $display("PASS lane phase=%0d stress=%0d accepted=%0d replied=%0d invalid=%0d",PHASE,STRESS,sent,received,malformed_offers);
            $finish;
        end
    end
    always @(posedge fast_clk) begin
        fast_edges=fast_edges+1;
        if(grant) begin
            active_id=granted[120:57];
            $display("GRANT %0t %031h",$time,granted);
        end
        if(release_op) $display("RELEASE %0t %0d",$time,active_id);
        #0.001;
        if(busy || dut.backend.done)
            $display("PIN %0t %0d %0d %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h",
                $time,active_id,age,busy,ce,oe,we,drive,alias_high,be,dq_out,
                dut.backend.sample,dut.backend.flag,dut.backend.done,
                dut.backend.commit_pulse,dut.backend.pending,dut.backend.read_data,
                word_out,err_due,loss_fast);
        if(fault) $fatal(1,"unexpected protocol fault");
        if(fast_edges>1000000) $fatal(1,"timeout");
    end
endmodule

// Pin-referenced observer. No DUT phase, round number or injected history.
`timescale 1ns/1ps
module timing_tb #(parameter CHECK_LOCAL=1);
    reg clk=0, reset=1, err=0, report_ok=1;
    reg [15:0] dq_in=16'h1234;
    wire [2:0] addr;
    wire selected, oe_n, we_n, drive, sealed;
    wire [15:0] dq_out;
    wire [3:0] count;
    wire [8:0] step;
    native8 #(.CHECK_LOCAL(CHECK_LOCAL)) dut (
        .clk(clk), .reset(reset), .err_in(err), .dq_in(dq_in),
        .release_ok(1'b1), .report_ok(report_ok), .install_ok(1'b1),
        .addr(addr), .selected(selected), .oe_n(oe_n), .we_n(we_n),
        .drive(drive), .dq_out(dq_out), .sealed(sealed), .count(count), .step(step)
    );

    // Same timestamp: input and its combinational fanout settle in the
    // active region, then the clock rises. No claim about analog setup.
    always begin #5; #0; clk=!clk; end
    initial begin @(negedge clk); reset=0; end

    integer arrival, repair, aperture;
    initial begin
        if (!$value$plusargs("arrival=%d",arrival) ||
            !$value$plusargs("repair=%d",repair) ||
            !$value$plusargs("aperture=%d",aperture)) $fatal(1,"missing stimulus");
    end
    event start_pass, start_last;
    time origin, first_read;
    integer scan=-1;
    reg previous_read0=0, previous_read=0, tracking=0;
    wire reading=selected && !oe_n;
    wire reading0=reading && addr==0;

    always @(posedge clk) begin
        #0.001;  // settle registered outputs and pin decodes; $time rounds to the ns edge
        if (reading0 && !previous_read0) begin
            scan=scan+1;
            if (scan==0) first_read=$time;
            if (scan==1280) begin
                origin=$time;
                tracking=1;
                $display("ORIGIN %0d",$time-first_read);
                ->start_pass;
            end
        end
        if (tracking && $time-origin < 2800) begin
            if (reading && !previous_read && addr==7) ->start_last;
            $display("PIN %0d %0d %b %b %b %b %0d %b %b %0d %b %0d %0d %0d",
                $time-origin,addr,selected,oe_n,we_n,drive,dq_out,dut.hit,
                sealed,count,report_ok,dut.proposed,step,dut.gap);
        end else if (tracking && (selected || !oe_n || !we_n || drive)) begin
            // First actual port activity, including any stray access in a pause.
            $display("NEXT %0d %0d %b %b %b %b",$time-origin,addr,selected,oe_n,we_n,drive);
            $finish;
        end
        previous_read=reading;
        previous_read0=reading0;
    end

    initial begin
        @start_pass; @(negedge clk);  // origin + 5 ns
        report_ok=0;
        #(arrival-5);
        report_ok=1;
    end
    always @(posedge report_ok)
        if (tracking) $display("CONFIRM %0d",$time-origin);
    initial begin
        @start_last; @(negedge clk);  // last read + 5 ns
        if (aperture) begin
            dq_in=16'hbace; err=!repair;
            #50;                     // +55 ns
        end
        dq_in=16'h5aa5; err=repair;
        if (aperture) #10; else #70;  // leave the marker at +65 / +75 ns
        dq_in=16'hc33c; err=!repair;
        #150; err=0;
    end
    initial begin #3606500; $fatal(1,"missing scan or successor"); end
endmodule

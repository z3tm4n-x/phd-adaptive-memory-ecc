// One ordinary single-bit deposit in a reachable state of the unchanged native8.
// Time and verdict evidence are anchored to external SRAM reads, not DUT counters.
`timescale 1ns/1ps
module fault_tb #(parameter CHECK_LOCAL = 1);
    reg clk = 0, reset = 1;
    always #5 clk = !clk;
    wire [2:0] addr;
    wire sel, oe_n, we_n, drive, sealed;
    wire [15:0] dq_out;
    wire [3:0] count;
    wire [8:0] step;
    wire reading = sel && !oe_n && we_n && !drive;
    wire read_zero = reading && addr == 0;
    reg [37:0] wrong [0:3];
    function automatic [15:0] half(input [2:0] a);
        reg [31:0] data;
        begin
            data = 32'ha5bc3410 + 32'h00010001 * a[1:0];
            half = a[2] ? data[31:16] : data[15:0];
        end
    endfunction
    // Only the hidden position 37 is damaged in the registered memory input.
    // The correct decoded data is thus also the physically stored data half.
    wire err_in = reading ? (|wrong[addr[1:0]]) : 1'b1;
    wire [15:0] dq_in = reading ? half(addr) : 16'hdead;
    native8 #(.CHECK_LOCAL(CHECK_LOCAL)) dut(
        .clk(clk), .reset(reset), .err_in(err_in), .dq_in(dq_in),
        .release_ok(1'b1), .report_ok(1'b1), .install_ok(1'b1),
        .addr(addr), .selected(sel), .oe_n(oe_n), .we_n(we_n), .drive(drive),
        .dq_out(dq_out), .sealed(sealed), .count(count), .step(step)
    );

    // A fixed-width packed name also works in Icarus 12's case selector.
    reg [127:0] target;
    integer bitno, at_ns, prior_value, dirty, look_round, max_rounds;
    integer ns, scan, origin, read_start, successors, before_value, after_value;
    reg [2:0] read_addr, write_addr;
    reg old_we, was_read_zero, was_read;
    event reached_origin;
    initial begin
        @reached_origin;
        if (dirty) begin
            #2101;
            wrong[3][37] = 1;
            $display("MEM 2101 3 37");
        end
    end

    function automatic integer current_value;
        case (target)
            "count":            current_value = dut.count;
            "sealed":           current_value = dut.sealed;
            "seen":             current_value = dut.seen;
            "proposed":         current_value = dut.proposed;
            "gap":              current_value = dut.gap;
            "step":             current_value = dut.step;
            "remaining":        current_value = dut.remaining;
            "remaining_parity": current_value = dut.remaining_parity;
            "quiet":            current_value = dut.quiet;
            "hit":              current_value = dut.hit;
            "phase":            current_value = dut.phase;
            default:            current_value = -1;
        endcase
    endfunction
    task automatic deposit;
        begin
            before_value = current_value();
            if (before_value !== prior_value) $fatal(1,"wrong reachable state: %s %0d expected %0d",target,before_value,prior_value);
            case (target)
                "count":            dut.count[bitno] = ~dut.count[bitno];
                "sealed":           dut.sealed = ~dut.sealed;
                "seen":             dut.seen[bitno] = ~dut.seen[bitno];
                "proposed":         dut.proposed[bitno] = ~dut.proposed[bitno];
                "gap":              dut.gap[bitno] = ~dut.gap[bitno];
                "step":             dut.step[bitno] = ~dut.step[bitno];
                "remaining":        dut.remaining[bitno] = ~dut.remaining[bitno];
                "remaining_parity": dut.remaining_parity = ~dut.remaining_parity;
                "quiet":            dut.quiet[bitno] = ~dut.quiet[bitno];
                "hit":              dut.hit = ~dut.hit;
                "phase":            dut.phase[bitno] = ~dut.phase[bitno];
                default:            $fatal(1,"unregistered deposit target");
            endcase
            after_value = current_value();
            if (after_value !== (before_value ^ (1 << bitno))) $fatal(1,"deposit failed");
            $display("FAULT %0d %0s %0d %0d %0d",ns,target,bitno,before_value,after_value);
        end
    endtask

    reg [22:0] bus, last_bus;
    reg [31:0] ctl, last_ctl;
    task automatic observe;
        begin
            bus = {sel ? addr : 3'd0, sel, oe_n, we_n, drive, drive ? dq_out : 16'd0};
            ctl = {sealed,count,dut.proposed,step,dut.gap};
            if ((^bus === 1'bx) || (^ctl === 1'bx)) $fatal(1,"unresolved pin or register");
            if (ns==0 || bus!=last_bus)
                $display("BUS %0d %0d %0d %0d %0d %0d %0d",ns,sel ? addr : 0,sel,oe_n,we_n,drive,drive ? dq_out : 0);
            if (ns==0 || ctl!=last_ctl)
                $display("CTL %0d %0d %0d %0d %0d %0d",ns,sealed,count,dut.proposed,step,dut.gap);
            if (reading && (!was_read || read_addr!=addr)) begin
                read_start=ns;
                read_addr=addr;
                if (addr==0 && ns>(look_round-1280)*2800)
                    successors=successors+1;
            end
            if (ns==read_start+60 && ns<2800)
                $display("SAMPLE %0d %0d %0d %0d %0d %0d",ns,read_addr,err_in,dut.hit,dq_in,dq_out);
            if (old_we && !we_n) begin
                write_addr=addr;
                if (!sel || !drive || !oe_n) $fatal(1,"unqualified WE# falling edge");
            end
            if (!old_we && we_n) begin
                if (!sel || !drive || !oe_n || addr!==write_addr || dq_out!==half(addr))
                    $fatal(1,"unqualified or wrong-data write at %0d",ns);
                $display("WRITE %0d %0d %0d %0d",ns,addr,dq_out,wrong[addr[1:0]]);
                wrong[addr[1:0]]=0;
            end
            old_we=we_n;
            was_read=reading;
            last_bus=bus;
            last_ctl=ctl;
        end
    endtask

    initial begin
        for (integer w=0; w<4; w=w+1) wrong[w]=0;
        if (!$value$plusargs("reg=%s",target) || !$value$plusargs("bit=%d",bitno) ||
            !$value$plusargs("at=%d",at_ns) || !$value$plusargs("before=%d",prior_value) ||
            !$value$plusargs("dirty=%d",dirty) || !$value$plusargs("look=%d",look_round) ||
            !$value$plusargs("max_rounds=%d",max_rounds)) $fatal(1,"missing test parameters");
        @(posedge clk); #0.001;
        if (!read_zero) $fatal(1,"reset has no first pin read");
        origin=$time;
        @(negedge clk); reset=0;
        was_read_zero=1;
        scan=0;
        while (scan<1280) begin
            @(posedge clk); #0.001;
            if (read_zero && !was_read_zero) scan=scan+1;
            was_read_zero=read_zero;
        end
        if ($time-origin != 1280*2800) $fatal(1,"wrong time at physically reached origin");
        $display("ORIGIN %0d",$time-origin);
        origin=$time;
        ->reached_origin;
        read_start=-1000; read_addr=0; old_we=1; was_read=0; successors=0;
        for (ns=0; ns<=max_rounds*2800; ns=ns+5) begin
            if (ns>0) begin
                @(clk); #0.001;
            end
            if ($time-origin!=ns) $fatal(1,"observer lost external time");
            if (target!="none" && ns==at_ns) deposit();
            #0.001; // register and combinational pins settled at this model edge
            observe();
            if ((ns>=4*2800 && successors>=2) || ns==max_rounds*2800) begin
                $display("END %0d %0d %0d",ns,successors,wrong[3]);
                $finish;
            end
        end
    end
endmodule

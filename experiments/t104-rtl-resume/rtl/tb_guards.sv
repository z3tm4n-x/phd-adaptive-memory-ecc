// Addressed failure-path checks independent of Python vector generation.
module tb_guards;
    reg clk=0,cold=1,sreset=0,alarm=0,bad=0,busy=0,permit=1;
    reg [63:0] now=0;
    wire cfg_ok,phase_ok,fault_ok,slot_ok,exec_ok,skip_ok;
    wire cfg_bad,phase_bad,fault_bad,slot_bad;
    wire [63:0] cursor_ok;
    absolute_calendar #(.WORD_BITS(3),.INVERSE(3)) good (
        .clk(clk),.cold_init(cold),.soft_reset(sreset),.now(now),
        .skip_permitted(permit),.alarm(alarm),.phase_bad(bad),.backend_busy(busy),
        .phase_valid(phase_ok),.fault(fault_ok),.config_ok(cfg_ok),
        .slot_pulse(slot_ok),.execute_pulse(exec_ok),.skip_pulse(skip_ok),.cursor(cursor_ok)
    );
    absolute_calendar #(.WORD_BITS(3),.INVERSE(3),.APP_CHARGE(208)) incompatible (
        .clk(clk),.cold_init(cold),.soft_reset(sreset),.now(now),
        .skip_permitted(permit),.alarm(alarm),.phase_bad(bad),.backend_busy(busy),
        .phase_valid(phase_bad),.fault(fault_bad),.config_ok(cfg_bad),.slot_pulse(slot_bad)
    );
    task edge_once;
        begin #2 clk=1; #1; #1 clk=0; end
    endtask
    initial begin
        edge_once(); cold=0;
        if (!cfg_ok || cfg_bad || phase_bad || !fault_bad) $fatal(1,"bad tuple accepted");
        edge_once(); // absolute0 must execute initial slot, even if LOW asserted
        if (!slot_ok || !exec_ok || skip_ok) $fatal(1,"initial slot skipped");
        now=4; sreset=1; edge_once(); sreset=0;
        if (cursor_ok!=1) $fatal(1,"soft reset changed absolute cursor");
        now=8; edge_once();
        now=12; cold=1; edge_once(); cold=0;
        if (phase_ok || !fault_ok || cursor_ok!=1) $fatal(1,"re-init created a new mission");
        now=16; edge_once();
        if (slot_bad) $fatal(1,"invalid configuration produced service");
        $display("GUARDS_OK invalid_tuple initial_mandatory soft_reset repeated_init");
        $finish;
    end
endmodule

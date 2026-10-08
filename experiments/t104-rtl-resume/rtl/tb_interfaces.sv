`timescale 1ns/1ps
module tb_interfaces;
    reg clk=0;
    always #2 clk=~clk;
    reg wr=0,commit=0,start_ok=0;
    reg [3:0] address=0;
    reg [31:0] data=0;
    wire arm_due,locked,fault,compatible;
    service_config dut(.*);
    reg fvalid=0;
    reg [1:0] fkind=2;
    reg [18:0] fword=0;
    reg [31:0] fdata=32'h12345678;
    reg [3:0] fmask=15;
    reg [63:0] fid=1,ftime=100;
    reg link_ready=0,reply_valid=0,reply_ready=0;
    wire send,ffault;
    wire [255:0] payload;
    app_frontend frontend(.clk(clk),.soft_reset(1'b0),.now_floor(ftime),
        .valid(fvalid),.kind(fkind),.word_address(fword),.data(fdata),.byte_enable(fmask),
        .request_id(fid),.link_ready(link_ready),.reply_valid(reply_valid),.reply_ready(reply_ready),
        .send(send),.payload(payload),.fault(ffault));
    task step;
        begin @(posedge clk);#0.1; end
    endtask
    task put;
        input integer idx;
        input [31:0] value;
        begin @(negedge clk);wr=1;address=idx;data=value;step;end
    endtask
    initial begin
        // Missing fields, a historically valid but incompatible reserve208,
        // and absent startup qualification must never arm this executor.
        @(negedge clk);commit=1;step;
        if(locked || !fault) $fatal(1,"uninitialized commit accepted");
        @(negedge clk);commit=0;
        put(0,32'h00104114);put(1,524288);put(2,38);put(3,3);put(4,196);
        put(5,164);put(6,320);put(7,8);put(8,1312);put(9,208);put(10,208);put(11,104);
        @(negedge clk);wr=0;start_ok=1;commit=1;#0.1;
        if(compatible || arm_due) $fatal(1,"mixed service tuple");step;
        @(negedge clk);commit=0;
        put(9,240);
        @(negedge clk);wr=0;start_ok=0;commit=1;#0.1;
        if(!compatible || arm_due) $fatal(1,"unqualified startup");step;
        @(negedge clk);start_ok=1;#0.1;if(!arm_due) $fatal(1,"valid tuple rejected");step;
        if(!locked) $fatal(1,"not locked");
        @(negedge clk);commit=0;
        put(9,208);@(negedge clk);wr=0;
        if(!compatible || !locked) $fatal(1,"runtime rewrite changed tuple");
        commit=1;#0.1;if(arm_due) $fatal(1,"mission restarted");step;
        @(negedge clk);commit=0;
        // An offer waits externally while the sole source credit is busy.
        // Its first-VALID time must not move to the later READY edge.
        fvalid=1;step;
        @(negedge clk);ftime=240;link_ready=1;#0.1;
        if(!send || payload[223:160]!=100) $fatal(1,"first VALID overwritten by READY");step;
        @(negedge clk);fvalid=0;link_ready=0;step;
        // Mutating an unaccepted offer is diagnosed, not silently captured.
        @(negedge clk);fvalid=1;ftime=300;step;
        @(negedge clk);fdata=0;link_ready=1;#0.1;
        if(send) $fatal(1,"changed offer captured");step;
        if(!ffault) $fatal(1,"changed offer undetected");
        $display("INTERFACES_OK config/lock/start/first-VALID/stable-offer");$finish;
    end
endmodule

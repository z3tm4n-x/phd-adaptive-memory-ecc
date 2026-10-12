`timescale 1ns/1ps
module tb_core_errors;
    reg clk=0;
    always #2 clk=~clk;
    reg soft_reset=0,loss=0,recover=1,start_ok=1,cfg_wr=0,cfg_commit=0;
    reg [3:0] cfg_address=0;
    reg [31:0] cfg_data=0;
    reg [1:0] request_valid=0,retire=0;
    reg [511:0] request_payload=0;
    wire [1:0] request_ready,reply_valid;
    wire [193:0] reply_payload;
    reg command_valid=0,command_integrity=1;
    reg [383:0] command_payload=0;
    wire command_accepted;
    reg [15:0] dq_in=16'hcafe;
    reg err_in=0;
    wire ce,oe,we,drive,alias_high,busy,pending,flag,done,commit_pulse;
    wire [1:0] byte_enable,grant_kind;
    wire [15:0] dq_out;
    wire [2:0] word_out;
    wire [63:0] err_count,now,time_gray,slot_index;
    wire running,config_locked,config_compatible,phase_valid,fault;
    wire [3:0] queue_state;
    wire app_grant,grant_owner,slot_pulse,skip_pulse;
    executor_core #(.WORD_BITS(3),.INVERSE(3)) dut(.*);
    integer fd,n,t,expected_bad;
    reg [255:0] packet;
    reg [4095:0] filename;
    task put;
        input integer addr;
        input [31:0] value;
        begin @(negedge clk);cfg_wr=1;cfg_address=addr;cfg_data=value;@(posedge clk);#0.1;end
    endtask
    initial begin
        if(!$value$plusargs("input=%s",filename)) $fatal(1,"input");
        fd=$fopen(filename,"r");if(!fd) $fatal(1,"file");
        put(0,32'h00104114);put(1,8);put(2,38);put(3,3);put(4,196);put(5,164);
        put(6,320);put(7,8);put(8,1312);put(9,240);put(10,208);put(11,104);
        @(negedge clk);cfg_wr=0;cfg_commit=1;@(posedge clk);#0.1;
        @(negedge clk);cfg_commit=0;
        wait(now==4);@(negedge clk);
        command_payload={64'd10000,64'd100,64'd4,64'd4,64'd1,32'h00104114,32'd104};
        command_valid=1;@(posedge clk);#0.1;if(!command_accepted) $fatal(1,"permission");
        @(negedge clk);command_valid=0;
        while(!$feof(fd)) begin
            n=$fscanf(fd,"%d %h %d\n",t,packet,expected_bad);
            if(n!=3 && n!=-1) $fatal(1,"row");
            if(n==3) begin
                wait(now==t);@(negedge clk);
                if(!request_ready[0]) $fatal(1,"credit unavailable");
                request_payload[255:0]=packet;request_valid=1;
                @(posedge clk);#0.1;
                if((queue_state[1:0]==3)!=expected_bad) $fatal(1,"bad classification at%0d",t);
                if(t==1576 && (!dut.calendar.freeze_pulse || !dut.calendar.frozen_execute))
                    $fatal(1,"same-edge malformed command did not force future FAST");
                @(negedge clk);request_valid=0;
                wait(queue_state[1:0]==3);@(negedge clk);retire=1;
                @(negedge clk);retire=0;
            end
        end
        if(dut.last_id[0]!=2) $fatal(1,"replay rewound accepted ID");
        $display("CORE_ERRORS_OK CRC/address/kind/mask/replay/priority");$finish;
    end
    initial begin #60000;$fatal(1,"timeout");end
endmodule

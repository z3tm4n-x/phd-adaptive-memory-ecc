`timescale 1ns/1ps
module tb_integrated;
    parameter integer PHASE=0,STRESS=0,WB=4,CYCLES=300000;
    localparam integer INV=(WB%2)?(((1<<WB)+1)/3):((2*(1<<WB)+1)/3);
    reg fast_clk=0,slow_clk=0,rst=1,start=0,loss=0;
    reg [1:0] rv=0,rr=3;
    reg [241:0] requests=0;
    wire [1:0] ready,reply_valid,credits;
    wire [96:0] reply;
    reg [15:0] dq=16'h5a3c;
    reg err=0;
    wire [WB-1:0] word_out;
    wire ce,oe,we,drive,alias_high,busy,pending,ed,release_due,running;
    wire grant,app_grant,sp,skip,fp,fe,low,permit,fault;
    wire [1:0] be;
    wire [15:0] dout;
    wire [56:0] gd;
    wire [63:0] generation,processed;
    wire [33:0] sw,lw,rw;
    wire [31:0] frame;
    integrated_executor #(.WORD_BITS(WB),.INVERSE(INV),.NW(40),.NH(80),.NR(130),.PAIR_WINDOW(200)) dut(
        .fast_clk(fast_clk),.slow_clk(slow_clk),.startup_rst_fast(rst),.startup_rst_slow(rst),
        .qualified_start(start),.loss_slow(loss),.request_valid(rv),.request_ready(ready),
        .request_data(requests),.response_valid(reply_valid),.response_ready(rr),.response_data(reply),
        .dq_in(dq),.err_in(err),.word_out(word_out),.ce(ce),.oe(oe),.we(we),.drive(drive),
        .alias_high(alias_high),.byte_enable(be),.dq_out(dout),.running(running),.busy(busy),
        .pending(pending),.err_due(ed),.release_due(release_due),.grant_debug(grant),
        .app_grant_debug(app_grant),.grant_data_debug(gd),.slot_pulse(sp),.skip_pulse(skip),
        .freeze_pulse(fp),.frozen_execute(fe),.generation(generation),.processed_generation(processed),
        .rule_low(low),.candidate_permit(permit),.short_left(sw),.long_left(lw),.recovery_left(rw),
        .frame_id(frame),.credits_debug(credits),.fault(fault));
    always #2 fast_clk=~fast_clk;
    initial begin #PHASE; forever #10 slow_clk=~slow_clk; end
    integer i=0,slow_i=0,sent=0,received=0,offered=0;
    integer next_offer=60;
    integer grant_count=0,active=-1,age=0,active_app=0;
    integer started_time=-1;
    reg [120:0] packet;
    reg [63:0] ident;
    initial begin #400; rst=0; #200; start=1; end
    always @(negedge slow_clk) begin
        slow_i=slow_i+1;
        if(!rst) begin
            loss=STRESS==2 ? (slow_i>=200 && slow_i<2202 && slow_i%2==0) :
                (slow_i>=500 && slow_i<517) || (slow_i>=1300 && slow_i<1302);
            rr=STRESS==1 && (slow_i%201<70)?0:3;
            if(rv==0 && slow_i>=next_offer && offered<(STRESS==1?120:10)) begin
                ident=offered;
                packet={ident,4'((offered%15)+1),32'hca000000|32'(offered),
                         19'(offered%(1<<WB)),2'(1+(offered%2))};
                requests[offered%2*121+:121]=packet;
                rv=offered%2?2:1;
                $display("OFFER %0t %0d %h",$time,offered%2,packet);
                offered=offered+1;
                next_offer=slow_i+(STRESS==1?2:5001);
            end
        end
    end
    always @(posedge slow_clk) begin
        if(dut.rule.start && !dut.rule.started) $display("RULE_START %0t",$time);
        if(dut.event_valid) $display("HISTORY %0t %h",$time,dut.event_data);
        if(dut.candidates.beacon_valid && !dut.candidates.response_pending)
            $display("SEND %0t %h",$time,dut.candidates.next_payload);
        if(|(rv & ready)) begin
            $display("ACCEPT %0t %0d %h",$time,dut.owner,dut.chosen);
            sent=sent+1;
            #0.002;rv=0;
        end
        if(|(reply_valid & rr)) begin
            $display("REPLY %0t %0d %h",$time,reply_valid[1],reply);
            received=received+1;
        end
        #0.001;
        $display("RULE %0t %h %h %h %h %h %h %h",$time,processed,sw,lw,rw,low,dut.rule.healthy,dut.rule.fault);
        if(credits>2) $fatal(1,"credit limit");
    end
    always @(negedge fast_clk) begin
        i=i+1;
        err=STRESS==2 ? (i>=600 && i<13000) :
            (i>=2000 && i<5500 && i%97<31) || (i>=22000 && i<24000);
        dq=alias_high?16'hc3a5:16'h5a3c;
        if(i==CYCLES) begin
            if(sent!=received || offered!=received) $fatal(1,"loss sent=%0d received=%0d",sent,received);
            if(fault) $fatal(1,"integrated fault");
            $display("PASS integrated phase=%0d stress=%0d cycles=%0d requests=%0d grants=%0d",PHASE,STRESS,i,received,grant_count);
            $finish;
        end
    end
    always @(posedge fast_clk) begin
        if(dut.calendar.slot_due && started_time<0) started_time=i;
        if(dut.calendar.freeze_due)
            $display("FREEZE %0t %0d %0d %h %h %h",$time,i-started_time,
                     dut.calendar.freeze_pos,permit,dut.local_alarm,dut.calendar.must_execute);
        if(dut.calendar.slot_due)
            $display("SLOT %0t %0d %h %h %h",$time,i-started_time,dut.control_due,dut.control_word,busy);
        if(dut.history_change) $display("EVENT %0t %h",$time,{dut.generation_next,dut.uptime,dut.loss_fast,ed});
        if(dut.candidates.frame_pulse) $display("BEACON %0t %h",$time,frame);
        if(dut.app_waiting && !app_was_waiting) $display("ELIGIBLE %0t",$time);
        app_was_waiting=dut.app_waiting;
        if(dut.candidates.installed) $display("CANDIDATE %0t %h %h %h %h",$time,
            dut.candidates.installed_frame,generation,dut.candidates.payload,dut.candidates.expected_crc);
        if(ed && permit) $fatal(1,"same-edge stale LOW");
        if(grant) begin
            if(active>=0) $fatal(1,"overlapping operation");
            active=grant_count;grant_count=grant_count+1;age=0;active_app=app_grant;
            $display("GRANT %0t %0d %0d %h",$time,active,app_grant,gd);
        end
        #0.001;
        if(active>=0) begin
            $display("PIN %0t %0d %0d %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h",
                $time,active,age,busy,ce,oe,we,drive,alias_high,be,dout,
                dut.backend.sample,dut.backend.flag,dut.backend.done,dut.backend.commit_pulse,
                pending,dut.backend.read_data,word_out,ed,dq,err);
            if(dut.backend.done) begin $display("RELEASE %0t %0d %0d",$time,active,active_app);active=-1;end
            age=age+4;
        end
        if(fault && i>400) $fatal(1,"fault at fast cycle %0d",i);
    end
    reg app_was_waiting=0;
endmodule

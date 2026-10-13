`timescale 1ns/1ps
module tb_arm;
    import "DPI-C" function int calculate_batch(input bit [767:0] bank,output bit [255:0] answer);
    parameter integer PHASE=0,STRESS=0,WB=4,CYCLES=120000;
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
    reg [11:0] awaddr=0,araddr=0;reg awvalid=0,wvalid=0,arvalid=0;
    reg [31:0] wdata=0;reg [3:0] wstrb=0;reg bready=0,rready=0;
    wire awready,wready,arready,bvalid,rvalid;wire [1:0] bresp,rresp;
    wire [31:0] rdata;
    reg [767:0] snapshot;reg [255:0] program_answer;
    reg [31:0] readback;integer word,packet_number=0;
 task write_bus(input [11:0] addr,input [31:0] data,input [3:0] strobe,
                input integer skew,input [1:0] expected);
  begin
   // Independently delayed AW and W, no assumption of same-cycle arrival.
   fork
    begin
     repeat(skew==1?3:0) @(negedge slow_clk);
     @(negedge slow_clk);awaddr=addr;awvalid=1;
     do @(posedge slow_clk);while(!awready);
     @(negedge slow_clk);awvalid=0;
    end
    begin
     repeat(skew==2?4:0) @(negedge slow_clk);
     @(negedge slow_clk);wdata=data;wstrb=strobe;wvalid=1;
     do @(posedge slow_clk);while(!wready);
     @(negedge slow_clk);wvalid=0;
    end
   join
   wait(bvalid); #1;
   if(bresp!==expected) $fatal(1,"B response addr=%h actual=%h expected=%h",addr,bresp,expected);
   repeat(2) begin @(posedge slow_clk);#1;
    if(!bvalid || bresp!==expected) $fatal(1,"B changed under backpressure");end
   @(negedge slow_clk);bready=1;@(negedge slow_clk);bready=0;
  end
 endtask
 task read_bus(input [11:0] addr,output [31:0] value);
  begin
   @(negedge slow_clk);araddr=addr;arvalid=1;
   do @(posedge slow_clk);while(!arready);
   @(negedge slow_clk);arvalid=0;
   wait(rvalid);#1;value=rdata;
   if(rresp!==0) $fatal(1,"R response");
   repeat(2) begin @(posedge slow_clk);#1;
    if(!rvalid || rresp!==0 || rdata!==value) $fatal(1,"R changed under backpressure");end
   @(negedge slow_clk);rready=1;@(negedge slow_clk);rready=0;
  end
 endtask

    initial begin
        wait(running);repeat(12) @(posedge slow_clk);
        // STRESS=3/4: same legal application, stationary FAST/LOW price.
        // FAST does not need the software rule; keep mailbox unclaimed.
        while(STRESS!=3) begin
            write_bus(12'h004,1,15,packet_number%3,0);
            for(word=0;word<24;word=word+1) begin
                read_bus(12'h100+word*4,readback);snapshot[word*32+:32]=readback;
            end
            if(!calculate_batch(snapshot,program_answer)) $fatal(1,"C rejected history");
            $display("PROGRAM %0t %h %h",$time,snapshot,program_answer);
            for(word=0;word<8;word=word+1)
                write_bus(12'h200+word*4,program_answer[word*32+:32],15,word%3,0);
            write_bus(12'h008,1,15,0,0);
            read_bus(12'h000,readback);
            while(readback[2:0]!=0) read_bus(12'h000,readback);
            packet_number=packet_number+1;
        end
    end

    wire [31:0] frame;
    arm_executor #(.WORD_BITS(WB),.INVERSE(INV)) dut(
        .fast_clk(fast_clk),.slow_clk(slow_clk),.startup_rst_fast(rst),.startup_rst_slow(rst),
        .qualified_start(start),.loss_slow(loss),.request_valid(rv),.request_ready(ready),
        .request_data(requests),.response_valid(reply_valid),.response_ready(rr),.response_data(reply),
        .dq_in(dq),.err_in(err),.word_out(word_out),.ce(ce),.oe(oe),.we(we),.drive(drive),
        .alias_high(alias_high),.byte_enable(be),.dq_out(dout),.running(running),.busy(busy),
        .pending(pending),.err_due(ed),.release_due(release_due),.grant_debug(grant),
        .app_grant_debug(app_grant),.grant_data_debug(gd),.slot_pulse(sp),.skip_pulse(skip),
        .freeze_pulse(fp),.frozen_execute(fe),.generation(generation),.processed_generation(processed),
        .rule_low(low),.candidate_permit(permit),
        .frame_id(frame),.credits_debug(credits),.fault(fault),
        .s_axi_awaddr(awaddr),.s_axi_awvalid(awvalid),.s_axi_awready(awready),
        .s_axi_wdata(wdata),.s_axi_wstrb(wstrb),.s_axi_wvalid(wvalid),.s_axi_wready(wready),
        .s_axi_bresp(bresp),.s_axi_bvalid(bvalid),.s_axi_bready(bready),
        .s_axi_araddr(araddr),.s_axi_arvalid(arvalid),.s_axi_arready(arready),
        .s_axi_rdata(rdata),.s_axi_rresp(rresp),.s_axi_rvalid(rvalid),.s_axi_rready(rready));
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
            loss=STRESS>=3 ? 0 : STRESS==2 ? (slow_i>=200 && slow_i<2202 && slow_i%2==0) :
                (slow_i>=500 && slow_i<517) || (slow_i>=1300 && slow_i<1302);
            rr=(STRESS==1 && (slow_i%201<70)) ||
               (STRESS>=3 && slow_i%17<4)?0:3;
            if(rv==0 && slow_i>=next_offer && offered<(STRESS>=3?8:STRESS==1?30:4)) begin
                ident=offered;
                packet={ident,4'((offered%15)+1),32'hca000000|32'(offered),
                         19'(offered%(1<<WB)),2'(1+(offered%2))};
                requests[offered%2*121+:121]=packet;
                rv=offered%2?2:1;
                $display("OFFER %0t %0d %h",$time,offered%2,packet);
                offered=offered+1;
                next_offer=slow_i+(STRESS>=3?25001:STRESS==1?2:5001);
            end
        end
    end
    always @(posedge slow_clk) begin
        if(dut.mailbox.collector.start && !dut.mailbox.collector.started) $display("RULE_START %0t %h",$time,dut.slow_tick);
        if(dut.event_valid) $display("HISTORY %0t %h %h",$time,dut.event_data,dut.slow_tick);
        if(dut.candidates.pending && dut.candidates.channel_ready)
            $display("INTERVAL_SEND %0t %h %h",$time,dut.slow_tick,dut.candidates.sending);
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
        if(credits>2) $fatal(1,"credit limit");
    end
    always @(negedge fast_clk) begin
        i=i+1;
        err=STRESS>=3 ? 0 : STRESS==2 ? (i>=600 && i<13000) :
            (i>=2000 && i<5500 && i%97<31) || (i>=22000 && i<24000);
        dq=alias_high?16'hc3a5:16'h5a3c;
        if(i==CYCLES) begin
            if(sent!=received || offered!=received) $fatal(1,"loss sent=%0d received=%0d",sent,received);
            if(fault) $fatal(1,"integrated fault");
            $display("PASS ARM integrated phase=%0d stress=%0d cycles=%0d requests=%0d grants=%0d",PHASE,STRESS,i,received,grant_count);
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
        if(dut.app_waiting && !app_was_waiting) $display("ELIGIBLE %0t",$time);
        app_was_waiting=dut.app_waiting;
        if(dut.candidates.installed) $display("INSTALLED %0t %h %h",$time,
            generation,dut.candidates.guard.payload);
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

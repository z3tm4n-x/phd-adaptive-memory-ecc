`timescale 1ns/1ps
module tb_calendar;
    parameter integer WB=3;
    localparam integer INVERSE=(WB%2) ? (((1<<WB)+1)/3) : ((2*(1<<WB)+1)/3);
    reg clk=0, cold=1, soft_reset_value=0, permit=0, alarm=0, bad=0, busy=0;
    reg [63:0] now=0;
    wire gp,gf,gcfg,ge,ga,gs,gex,gsk,gfr,gfe,gaw;
    wire rp,rf,re,ra,rs,rex,rsk,rfr,rfe,raw,sd,fd;
    wire [WB-1:0] gw,rw;
    wire [63:0] si,fi,cur;
    wire [WB-1:0] sw;
    integer i,seed=104;
    absolute_calendar #(.WORD_BITS(WB),.INVERSE(INVERSE)) gold(
        .clk(clk),.cold_init(cold),.soft_reset(soft_reset_value),.now(now),.skip_permitted(permit),
        .alarm(alarm),.phase_bad(bad),.backend_busy(busy),.phase_valid(gp),.fault(gf),
        .config_ok(gcfg),.execute_due(ge),.app_due(ga),.word_due(gw),
        .slot_pulse(gs),.execute_pulse(gex),.skip_pulse(gsk),.freeze_pulse(gfr),
        .frozen_execute(gfe),.app_window(gaw),.slot_index(si),.frozen_index(fi),
        .slot_word(sw),.cursor(cur));
    relative_calendar #(.WORD_BITS(WB),.INVERSE(INVERSE)) dut(
        .clk(clk),.cold_init(cold),.soft_reset(soft_reset_value),.skip_permitted(permit),
        .alarm(alarm),.phase_bad(bad),.backend_busy(busy),.phase_valid(rp),.fault(rf),
        .execute_due(re),.app_due(ra),.word_due(rw),.slot_due(sd),.freeze_due(fd),
        .slot_pulse(rs),.execute_pulse(rex),.skip_pulse(rsk),.freeze_pulse(rfr),
        .frozen_execute(rfe),.app_window(raw));
    initial begin
        #1; clk=1; #1; clk=0; cold=0;
        for(i=0;i<120000;i=i+1) begin
            now=64'(i)*4;
            permit=(i%17!=0);
            alarm=($unsigned($random(seed))%701==0);
            soft_reset_value=(i%1999==0);
            // Save a long healthy prefix, then exercise sticky phase fault.
            bad=(i==95001); cold=(i==110000);
            busy=(i>96000 && i%997==0);
            #1;
            if({ge,ga,gw,gp,gf} !== {re,ra,rw,rp,rf})
                $fatal(1,"pre-edge mismatch WB=%0d tick=%0d",WB,i);
            clk=1; #1;
            if({gs,gex,gsk,gfr,gfe,gaw,gp,gf} !== {rs,rex,rsk,rfr,rfe,raw,rp,rf})
                $fatal(1,"post-edge mismatch WB=%0d tick=%0d",WB,i);
            clk=0;
        end
        $display("PASS relative_calendar WB=%0d cycles=%0d",WB,i); $finish;
    end
endmodule

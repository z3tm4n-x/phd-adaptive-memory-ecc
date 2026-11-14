// Digital boundary test. Primitive models below are test fixtures; the actual
// AMD IP, clock primitives and ICAP are instantiated in the placed board top.
`timescale 1ns/1ps
module IBUF(input I, output O);assign O=I;endmodule
module BUFG(input I, output O);assign O=I;endmodule
module IOBUF(inout IO,input I,T,output O);assign IO=T?1'bz:I;assign O=IO;endmodule
module MMCME2_BASE #(parameter CLKIN1_PERIOD=10.0, CLKFBOUT_MULT_F=10.0, CLKOUT0_DIVIDE_F=10.0,
    CLKOUT1_DIVIDE=20,DIVCLK_DIVIDE=1,REF_JITTER1=0.005)(
    input CLKIN1,CLKFBIN,PWRDWN,RST,output CLKFBOUT,CLKOUT0,LOCKED,output reg CLKOUT1=0);
    assign CLKOUT0=CLKIN1;assign CLKFBOUT=CLKIN1;assign LOCKED=1;
    always @(posedge CLKIN1)CLKOUT1<=!CLKOUT1;
endmodule
module ICAPE2 #(parameter ICAP_WIDTH="X32")(input CLK,CSIB,RDWRB,input [31:0] I,output [31:0] O);
    assign O=0;
endmodule
module FRAME_ECCE2 #(parameter FARSRC="EFAR")(output CRCERROR,ECCERROR,ECCERRORSINGLE,
   output [25:0] FAR,output [4:0] SYNBIT,output [12:0] SYNDROME,output SYNDROMEVALID,output [6:0] SYNWORD);
   assign {CRCERROR,ECCERROR,ECCERRORSINGLE,FAR,SYNBIT,SYNDROME,SYNDROMEVALID,SYNWORD}=0;
endmodule
module sem_core(input icap_clk,icap_grant,fecc_crcerr,fecc_eccerr,fecc_eccerrsingle,fecc_syndromevalid,
   input [31:0] icap_o,input [25:0] fecc_far,input [12:0] fecc_syndrome,input [4:0] fecc_synbit,
   input [6:0] fecc_synword,input monitor_rxempty,monitor_txfull,input [7:0] monitor_rxdata,
   output icap_csib,icap_rdwrb,output [31:0] icap_i,
   output reg status_observation=0,status_correction=0,status_uncorrectable=0);
   assign {icap_csib,icap_rdwrb,icap_i}={1'b1,1'b1,32'b0};
endmodule
module sem_connection #(parameter ADAPTIVE=1);
    reg clk=0;always #5 clk=!clk;
    wire [19:0] addr;tri [15:0] dq; wire cs,oe,we;
    reg err=0;
    assign dq=(!cs&&!oe)?16'h5ac3:16'hzzzz;
    bank_board #(.PROTECTED(1),.ADAPTIVE(ADAPTIVE)) b(.ref100(clk),.sram_err(err),.sram_dq(dq),
        .sram_a(addr),.sram_ce_n(cs),.sram_oe_n(oe),.sram_we_n(we));
    task step;begin @(posedge clk);#1;end endtask
    integer i;
    initial begin
        repeat(16) begin step;if(!b.cold||!cs||!we)$fatal(1,"service before SEM ready");end
        @(negedge b.cfg_i); b.mitigation.monitor.sem.status_observation=1;
        wait(b.active_owner);#1;
        if(b.cold||cs||oe||addr!=0||b.sem_loss)$fatal(1,"cold start");
        for(i=1;i<=24;i=i+1)begin
            @(negedge clk);err=(i==6);
            if(i==3)begin b.mitigation.monitor.sem.status_observation=0;b.mitigation.monitor.sem.status_correction=1;end
            if(i==13)begin b.mitigation.monitor.sem.status_observation=1;b.mitigation.monitor.sem.status_correction=0;end
            if(i==21)begin b.mitigation.monitor.sem.status_observation=0;b.mitigation.monitor.sem.status_uncorrectable=1;end
            step;
            if(b.cold||we!==(i<11||i>=16)||(i<20&&(cs||addr!=0))||
               (i>=10&&i<18&&dq!==16'h5ac3))$fatal(1,"interrupted mandatory write %d",i);
            if(b.sem_loss!==((i>=4&&i<14)||i>=22))$fatal(1,"status crossing %d",i);
            if(i==20&&(!cs||b.active_owner||b.core.count!=1))$fatal(1,"uncommitted repair");
            if(i==24&&(!b.active_owner||cs||addr!=1))$fatal(1,"runtime restart or stalled port");
        end
        $display("SEM_LINK adaptive=%0d commissioning_wait=1 correction_spans_write=1 captured=1 committed=1 first_next_address=1 fail_status=1 runtime_cold=0",ADAPTIVE);
        $finish;
    end
endmodule

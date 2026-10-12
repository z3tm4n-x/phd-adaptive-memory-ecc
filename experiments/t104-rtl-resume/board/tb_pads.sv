`timescale 1ns/1ps
// Digital-only model of documented IOBUF truth table; not UNISIM or analog IO.
module IOBUF #(parameter IOSTANDARD="DEFAULT", DRIVE=12, SLEW="SLOW")
    (input I,T, output O, inout IO);
    assign IO=T ? 1'bz : I; assign O=IO;
endmodule
module IBUF #(parameter IOSTANDARD="DEFAULT")(input I,output O); assign O=I; endmodule
module tb_pads;
    reg [19:0] physical_address=0;
    reg ce=0,oe=0,we=0,drive=0,sram_err=0,memory_drive=0;
    reg [1:0] byte_enable=0;
    reg [15:0] dq_out=0,memory_data=0;
    wire [15:0] dq_in,sram_dq;
    wire [19:0] sram_a;
    wire err_in,sram_ce_n,sram_oe_n,sram_we_n,sram_lb_n,sram_ub_n;
    assign sram_dq=memory_drive ? memory_data : 16'hzzzz;
    sram_pads dut(.*);
    integer i,j,count=0;
    initial begin
        for(i=0;i<128;i=i+1) begin
            {sram_err,ce,oe,we,drive,byte_enable}=i;
            for(j=0;j<32;j=j+1) begin
                physical_address=(20'h81a23*j)^20'h54321;
                dq_out=(16'h1937*j)^16'ha55a;
                memory_data=~dq_out; memory_drive=!drive;
                #1;
                if(sram_a!==physical_address || err_in!==sram_err ||
                   {sram_ce_n,sram_oe_n,sram_we_n,sram_lb_n,sram_ub_n}!==
                   {~ce,~oe,~we,~byte_enable[0],~byte_enable[1]} ||
                   sram_dq!==(drive ? dq_out : memory_data) || dq_in!==sram_dq)
                    $fatal(1,"PAD_MISMATCH case=%0d",count);
                count=count+1;
            end
        end
        drive=0;memory_drive=0;#1;
        if(sram_dq!==16'hzzzz) $fatal(1,"PAD_MISMATCH tristate");
        $display("PADS_PASS cases=%0d",count);$finish;
    end
endmodule

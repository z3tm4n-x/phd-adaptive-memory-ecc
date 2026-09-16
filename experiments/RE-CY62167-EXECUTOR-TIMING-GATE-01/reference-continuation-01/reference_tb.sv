`timescale 1ns/1ps
module reference_tb;
 logic clk200=0;
 always #2.5 clk200=~clk200;
 logic hard_reset=1,soft_reset=0,qualified=1,transfer_ok=1;
 logic cmd_valid=0,trusted_valid=1;
 logic [1:0] cmd_kind;
 logic [18:0] cmd_addr=19'd123;
 logic [31:0] trusted_data;
 wire ce_tick,cmd_ready,busy,ack,invalid,fault,quiesced;
 wire [18:0] addr; wire [47:0] dq;
 logic [2:0] err;
 wire ce_n,oe_n,we_n;
 logic [47:0] memory_bus;
 assign dq=(!ce_n&&!oe_n)?memory_bus:48'bz;
 reference_slot dut(.*);
 integer file,count=0,scan,j,kind_i,err_i,write_i,fault_i,mode_i;
 logic [47:0] initial_bus,expected_bus;
 string vectors;
 initial begin
   if(!$value$plusargs("vectors=%s",vectors)) $fatal(1,"missing vectors");
   file=$fopen(vectors,"r");
   if(file==0) $fatal(1,"cannot open vectors");
   while(!$feof(file)) begin
     scan=$fscanf(file,"%h %h %d %d %d %d %d\n",initial_bus,expected_bus,kind_i,err_i,write_i,fault_i,mode_i);
     if(scan==7) begin
       hard_reset=1; soft_reset=0; qualified=1; transfer_ok=1; cmd_valid=0;
       trusted_valid=mode_i!=4; trusted_data=initial_bus[31:0];
       repeat(3) @(negedge clk200);
       hard_reset=0; memory_bus=initial_bus; err=3'(err_i); cmd_kind=2'(kind_i);
       while(!ce_tick) @(negedge clk200);
       cmd_valid=1;
       @(posedge clk200); #1; cmd_valid=0;
       if(!busy || addr!=123 || ack) $fatal(1,"start %0d",count);
       for(j=1;j<=24;j=j+1) begin
         repeat(2) @(posedge clk200);
         #1;
         if(mode_i==2 && j==14) begin
           hard_reset=1; @(posedge clk200); #1;
           if(busy || ack || !we_n || !oe_n || !ce_n) $fatal(1,"hard reset");
           j=25;
         end else begin
           if(j<24 && ack) $fatal(1,"early ack");
           if(j==8 && kind_i!=0 && !oe_n) $fatal(1,"OE at latch");
           if(j==9) begin memory_bus=~initial_bus; err=0; end
           if(j==14 && mode_i==1) soft_reset=1;
           if(j==18 && mode_i==3) transfer_ok=0;
           if(j>=12 && j<21 && write_i && mode_i!=4 && dq!==expected_bus)
             $fatal(1,"write image case %0d tick %0d got %h expected %h",count,j,dq,expected_bus);
           if(j>=13 && j<19 && we_n!==(write_i==0 || mode_i==4)) $fatal(1,"WE pulse %0d",count);
           if(j==24) begin
             if(busy || !we_n || !oe_n || !ce_n) $fatal(1,"unsafe fence");
             if(ack!==(fault_i==0 && mode_i<2)) $fatal(1,"fence ack %0d",count);
             if(fault!==(fault_i!=0)) $fatal(1,"fault %0d",count);
             if(mode_i==1 && !quiesced) $fatal(1,"quiesce");
             if((mode_i==3 || mode_i==4) && !invalid) $fatal(1,"invalid");
           end
         end
       end
       count=count+1;
     end
   end
   $display("PASS reference_slot vectors=%0d",count);
   $finish;
 end
 initial begin #10000000; $fatal(1,"timeout"); end
endmodule

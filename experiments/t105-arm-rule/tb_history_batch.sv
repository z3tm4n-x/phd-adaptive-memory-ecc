`timescale 1ns/1ps
module tb_history_batch;
 reg clk=0;always #10 clk=!clk;
 reg start=0,event_valid=0,history_fault=0,snapshot_request=0,snapshot_ack=0;
 reg [129:0] event_data=0;
 wire snapshot_valid,fault;wire [767:0] snapshot;wire [63:0] tick;
 history_batch dut(.*);
 integer f,o,rc,q,st,cl,ack;reg [130:0] record;
 reg was_valid=0;reg [767:0] held;
 string input_path,output_path;
 initial begin
  if(!$value$plusargs("INPUT=%s",input_path) || !$value$plusargs("OUTPUT=%s",output_path))
   $fatal(1,"paths required");
  f=$fopen(input_path,"r");o=$fopen(output_path,"w");if(!f||!o)$fatal;
  #1;
  while(!$feof(f)) begin
   rc=$fscanf(f,"%d %d %h %d %d\n",q,st,record,cl,ack);
   if(rc==5) begin
    start=st;event_valid=record[130];event_data=record[129:0];
    snapshot_request=cl;snapshot_ack=ack;
    @(posedge clk);#1;
    if(fault)$fatal(1,"collector fault at %0d",q);
    if(snapshot_valid && !was_valid) begin
     $fdisplay(o,"%0d %0192h",q,snapshot);held=snapshot;
    end
    if(snapshot_valid && was_valid && snapshot!==held) $fatal(1,"snapshot torn");
    was_valid=snapshot_valid;
    @(negedge clk);
   end
  end
  $fclose(f);$fclose(o);$display("HISTORY_BATCH_OK");$finish;
 end
endmodule

`timescale 1ns/1ps
module tb_time_format;
 longint unsigned stamp[0:4];
 integer i;
 initial begin
  stamp[0]=64'd670;
  stamp[1]=64'd90775751724002;
  stamp[2]=64'd202376233820426;
  stamp[3]=64'd202379545401958;
  stamp[4]=64'd363900000000002;
  for(i=0;i<5;i=i+1) begin
   $display("FORMAT %0d %0t %0d",stamp[i],stamp[i],64'd1000*stamp[i]);
  end
  $finish;
 end
endmodule

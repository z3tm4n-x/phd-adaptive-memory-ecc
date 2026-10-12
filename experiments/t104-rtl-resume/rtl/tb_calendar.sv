module tb_calendar;
    reg clk=0,cold_init=1,soft_reset=0,skip_permitted=0,alarm=0,phase_bad=0,backend_busy=0;
    reg [63:0] now=0;
    wire phase_valid,fault,config_ok,slot_pulse,execute_pulse,skip_pulse;
    wire execute_due,app_due;
    wire [2:0] word_due;
    wire freeze_pulse,frozen_execute,app_window;
    wire [63:0] slot_index,frozen_index,cursor;
    wire [2:0] slot_word;
    absolute_calendar #(.WORD_BITS(3),.INVERSE(3)) dut(.*);
    integer fd,n,row=0;
    reg [4095:0] vector_path;
    reg es,ee,ek,ef,efe,ea;
    reg [63:0] ej,efj;
    reg [2:0] ew;
    initial begin
        #2 clk=1; #1; #1 clk=0; cold_init=0;
        if (!$value$plusargs("vectors=%s",vector_path)) $fatal(1,"missing vectors");
        fd=$fopen(vector_path,"r");
        if (!fd) $fatal(1,"cannot open vectors");
        while (!$feof(fd)) begin
            n=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                      now,skip_permitted,alarm,soft_reset,es,ee,ek,ef,efe,ea,ej,efj,ew);
            if (n!=13) $fatal(1,"bad calendar vector");
            #1;
            if (execute_due !== ee || app_due !== ea || (es && word_due !== ew))
                $fatal(1,"calendar PRE-EDGE row%0d now%0d",row,now);
            #1 clk=1; #1;
            if ({slot_pulse,execute_pulse,skip_pulse,freeze_pulse,app_window} !== {es,ee,ek,ef,ea}
                || (slot_pulse && (slot_index!==ej || slot_word!==ew))
                || (freeze_pulse && (frozen_execute!==efe || frozen_index!==efj))
                || fault || !phase_valid || !config_ok)
                $fatal(1,"calendar row%0d time%0d slot%0d expected%0d pulses%h/%h freeze%0d/%0d fault%0d",
                       row,now,slot_index,ej,{slot_pulse,execute_pulse,skip_pulse,freeze_pulse,app_window},
                       {es,ee,ek,ef,ea},frozen_execute,efe,fault);
            #1 clk=0; row=row+1;
        end
        $display("CALENDAR_OK rows=%0d",row); $finish;
    end
endmodule

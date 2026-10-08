module tb_permission;
    reg clk=0,cold_init=1,soft_reset=0,loss=0,err_event=0,recover=0;
    reg [63:0] now=0;
    reg cmd_valid=0,cmd_integrity=1;
    reg [31:0] cmd_mission=104,cmd_config=32'h00104114;
    reg [63:0] cmd_sequence=0,cmd_issued=0,cmd_not_before=0,cmd_deadline=0,cmd_expires=0;
    wire command_ack,command_accepted,permit_at_edge,active,shadow,healthy,overflow;
    wire [63:0] err_count,last_sequence;
    permission_gate dut(.*);
    integer fd,n,row=0;
    reg [4095:0] vector_path;
    reg ep,ea,es,eh,eack,eaccepted;
    reg [63:0] ec,eq;
    initial begin
        #2 clk=1; #1; #1 clk=0; cold_init=0;
        if (!$value$plusargs("vectors=%s",vector_path)) $fatal(1,"missing vectors");
        fd=$fopen(vector_path,"r");
        if (!fd) $fatal(1,"cannot open vectors");
        while (!$feof(fd)) begin
            n=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                now,soft_reset,loss,err_event,recover,cmd_valid,cmd_integrity,cmd_mission,cmd_config,
                cmd_sequence,cmd_issued,cmd_not_before,cmd_deadline,cmd_expires,
                ep,ea,es,eh,eack,eaccepted,ec,eq);
            if (n!=22) $fatal(1,"bad permission row%0d n%0d",row,n);
            #1;
            if (permit_at_edge !== ep)
                $fatal(1,"permission PRE-EDGE row%0d now%0d got%0d expected%0d",row,now,permit_at_edge,ep);
            #1 clk=1; #1;
            if ({active,shadow,healthy,command_ack,command_accepted} !== {ea,es,eh,eack,eaccepted}
                || err_count !== ec || last_sequence !== eq || overflow)
                $fatal(1,"permission row%0d now%0d got%h expected%h count%0d/%0d seq%0d/%0d",
                       row,now,{active,shadow,healthy,command_ack,command_accepted},
                       {ea,es,eh,eack,eaccepted},err_count,ec,last_sequence,eq);
            #1 clk=0; row=row+1;
        end
        $display("PERMISSION_OK rows=%0d",row); $finish;
    end
endmodule

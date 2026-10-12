`timescale 1ns/1ps
module tb_executor;
    parameter integer WORD_BITS=3, INVERSE=3;
    parameter integer CPU_HALF=5, X_HALF=4, CMD_PHASE=1;
    localparam integer WORDS=1<<WORD_BITS;
    reg mem_clk=0,cpu_clk=0,x_clk=0,command_clk=0;
    always #2 mem_clk=~mem_clk;
    always #(CPU_HALF) cpu_clk=~cpu_clk;
    initial begin #1; forever #(X_HALF) x_clk=~x_clk; end
    initial begin #(CMD_PHASE); forever #5 command_clk=~command_clk; end
    reg soft_reset=0,loss=0,recover=1,start_ok=1;
    reg cfg_wr=0,cfg_commit=0;
    reg [3:0] cfg_address=0;
    reg [31:0] cfg_data=0;
    reg [1:0] app_valid=0,app_reply_ready=3;
    reg [3:0] app_kind=0;
    reg [2*WORD_BITS-1:0] app_word=0;
    reg [63:0] app_data=0;
    reg [7:0] app_mask=0;
    reg [127:0] app_id=0;
    wire [1:0] app_ready,app_reply_valid;
    wire [193:0] app_reply_payload;
    reg cmd_valid=0,cmd_reply_ready=1;
    reg [415:0] cmd_payload=0;
    wire cmd_ready,cmd_reply_valid;
    wire [31:0] cmd_reply_payload;
    reg [15:0] dq_in=0;
    reg err_in=0;
    wire ce,oe,we,drive,alias_high,busy,pending,flag,done,commit_pulse;
    wire [1:0] byte_enable;
    wire [15:0] dq_out;
    wire [WORD_BITS-1:0] word_out;
    wire [63:0] now,err_count;
    wire running,phase_valid,fault;
    wire [3:0] queue_state;
    executor #(.WORD_BITS(WORD_BITS),.INVERSE(INVERSE)) dut(.*);
    reg [31:0] memory [0:WORDS-1];
    reg [37:0] errors [0:WORDS-1];
    // Bounded fixtures only: full-W run uses sparse low word count model below
    // and does not allocate radiation birth tables for an entire device.
    reg signed [63:0] birth [0:WORDS*38-1];
    integer fd,commands_fd,out,n,k,byte_n,scenario;
    integer offered_t,port_id,op,w,mask,id;
    reg [31:0] data_value;
    integer cmd_t;
    reg [415:0] command_value;
    real origin=0;
    integer duration=400000;
    reg [4095:0] input_name,command_name,output_name;
    integer operations=0;
    reg [63:0] operation_start=0;
    reg [1:0] operation_kind=0;
    reg [WORD_BITS-1:0] operation_word=0;
    reg old_we=0,old_drive=0,old_alias=0;
    reg [1:0] old_be=0;
    reg [15:0] old_dout=0;
    reg [63:0] edge_time;
    reg pre_go,pre_app,pre_owner;
    reg [1:0] pre_kind;
    reg [WORD_BITS-1:0] pre_word;
    reg [31:0] pre_data;
    reg [3:0] pre_mask;
    reg pre_reset,pre_loss,pre_command,pre_integrity;
    reg [383:0] pre_command_data;
    reg [32:0] packed_pins;
    integer bit_index;
    task cfg;
        input integer index;
        input [31:0] value;
        begin
            @(negedge mem_clk); cfg_wr=1;cfg_address=index;cfg_data=value;
            @(posedge mem_clk); #0.1;
        end
    endtask
    initial begin
        if(!$value$plusargs("input=%s",input_name)) $fatal(1,"input");
        if(!$value$plusargs("commands=%s",command_name)) $fatal(1,"commands");
        if(!$value$plusargs("output=%s",output_name)) $fatal(1,"output");
        if(!$value$plusargs("scenario=%d",scenario)) scenario=0;
        if(!$value$plusargs("duration=%d",duration)) duration=400000;
        out=$fopen(output_name,"w"); fd=$fopen(input_name,"r");
        commands_fd=$fopen(command_name,"r");
        if(!out || !fd || !commands_fd) $fatal(1,"files");
        for(k=0;k<WORDS;k=k+1) begin memory[k]=32'h10000000+k;errors[k]=0;end
        for(k=0;k<WORDS*38;k=k+1) birth[k]=0;
        errors[0][32]=1; // one initially dirty word; memory is NOT reset by arm
        birth[32]=-1;
        cfg(0,32'h00104114);cfg(1,WORDS);cfg(2,38);cfg(3,3);cfg(4,196);
        cfg(5,164);cfg(6,320);cfg(7,8);cfg(8,1312);cfg(9,240);cfg(10,208);cfg(11,104);
        @(negedge mem_clk);cfg_wr=0;cfg_commit=1;
        @(posedge mem_clk);origin=$realtime+4;#0.1;
        if(!running) $fatal(1,"start rejected");
        @(negedge mem_clk);cfg_commit=0;
        fork
            begin
                while(!$feof(fd)) begin
                    n=$fscanf(fd,"%d %d %d %d %h %d %d\n",offered_t,port_id,op,w,data_value,mask,id);
                    if(n!=7 && n!=-1) $fatal(1,"request row");
                    if(n==7) begin
                    if(origin+offered_t>$realtime) #(origin+offered_t-$realtime);
                    if(port_id==0) @(negedge cpu_clk); else @(negedge x_clk);
                    app_kind[2*port_id+:2]=op;app_word[WORD_BITS*port_id+:WORD_BITS]=w;
                    app_data[32*port_id+:32]=data_value;app_mask[4*port_id+:4]=mask;
                    app_id[64*port_id+:64]=id;app_valid[port_id]=1;
                    $fdisplay(out,"O %.3f %d %d %d %h %d %d",$realtime-origin,port_id,op,w,data_value,mask,id);
                    if(port_id==0) begin @(posedge cpu_clk);while(!app_ready[0]) @(posedge cpu_clk);end
                    else begin @(posedge x_clk);while(!app_ready[1]) @(posedge x_clk);end
                    $fdisplay(out,"A %.3f %d %d",$realtime-origin,port_id,id);
                    #0.1;app_valid[port_id]=0;
                    end
                end
            end
            begin
                while(!$feof(commands_fd)) begin
                    n=$fscanf(commands_fd,"%d %h\n",cmd_t,command_value);
                    if(n!=2 && n!=-1) $fatal(1,"command row");
                    if(n==2) begin
                    if(origin+cmd_t>$realtime) #(origin+cmd_t-$realtime);
                    @(negedge command_clk);cmd_payload=command_value;cmd_valid=1;
                    @(posedge command_clk);while(!cmd_ready) @(posedge command_clk);
                    $fdisplay(out,"C %.3f %h",$realtime-origin,command_value);
                    #0.1;cmd_valid=0;
                    end
                end
            end
            begin
                if(scenario==2) begin
                    wait(dut.core.active_app && busy && dut.core.backend.age==100);
                    @(negedge mem_clk);soft_reset=1;
                    @(negedge mem_clk);soft_reset=0;
                end
                if(scenario==3) begin
                    app_reply_ready=0;
                    wait(|app_reply_valid);#180;app_reply_ready=3;
                end
            end
            begin
                if(origin+duration>$realtime) #(origin+duration-$realtime);
                #1;
                if(app_valid || cmd_valid) $fatal(1,"driver still pending");
                $fdisplay(out,"END %d %d %h %h",operations,fault,queue_state,err_count);
                $fclose(out);$display("INTEGRATED_DONE scenario=%0d operations=%0d fault=%0d",scenario,operations,fault);
                $finish;
            end
        join
    end
    always @(negedge mem_clk) if(running) begin
        dq_in=alias_high ? memory[word_out][31:16] : memory[word_out][15:0];
        err_in=|errors[word_out];
    end
    always @(posedge mem_clk) if(running) begin
        edge_time=now;
        pre_go=dut.core.go;pre_app=dut.core.app_grant;pre_owner=dut.core.grant_owner;
        pre_kind=dut.core.grant_kind;pre_word=dut.core.backend.word_in;
        pre_data=dut.core.backend.data_in;pre_mask=dut.core.backend.byte_enable_in;
        pre_reset=soft_reset;pre_loss=loss;pre_command=dut.core.command_valid;
        pre_integrity=dut.core.command_integrity;pre_command_data=dut.core.command_payload;
        if(dut.request_valid[0] && dut.request_ready[0]) $fdisplay(out,"D %d 0 %h",now,dut.requests[255:0]);
        if(dut.request_valid[1] && dut.request_ready[1]) $fdisplay(out,"D %d 1 %h",now,dut.requests[511:256]);
        if(pre_go) begin
            operations=operations+1;
            operation_start=now;operation_kind=pre_kind;operation_word=pre_word;
            if(scenario==0 && operations%2==0) begin
                bit_index=operations%38;
                errors[pre_word][bit_index]=~errors[pre_word][bit_index];
                birth[pre_word*38+bit_index]=now-1;
                $fdisplay(out,"I %d %d %d",now-1,pre_word,bit_index);
            end
        end
        #0.01;
        if(old_we && !we) begin
            if(!old_drive) $fatal(1,"write without driven data");
            for(bit_index=0;bit_index<38;bit_index=bit_index+1)
                if(birth[operation_word*38+bit_index]<$signed(operation_start))
                    errors[operation_word][bit_index]=0;
            if(operation_kind==2) begin
                for(byte_n=0;byte_n<2;byte_n=byte_n+1)
                    if(old_be[byte_n]) memory[operation_word][16*old_alias+8*byte_n+:8]=old_dout[8*byte_n+:8];
            end
            $fdisplay(out,"W %d %d %d %h %d %h",edge_time,operation_word,old_alias,old_dout,old_be,memory[operation_word]);
        end
        old_we=we;old_drive=drive;old_alias=alias_high;old_dout=dq_out;old_be=byte_enable;
        packed_pins={dut.core.backend.err_due,dut.core.backend.rejected,dut.core.backend.accepted,
                     dut.core.backend.ready,pending,commit_pulse,done,flag,dut.core.backend.sample,
                     dq_out,byte_enable,alias_high,drive,we,oe,ce,busy};
        $fdisplay(out,"P %d %d %d %d %d %h %d %h %d %h %h %d %h %d %d %d %d %d %d %d %h",
            edge_time,pre_go,pre_kind,pre_owner,pre_word,pre_data,pre_mask,dq_in,err_in,
            packed_pins,dut.core.backend.read_data,err_count,queue_state,fault,
            dut.core.slot_pulse,dut.core.slot_index,dut.core.skip_pulse,pre_reset,pre_loss,
            pre_command,pre_command_data);
        if(pre_command) $fdisplay(out,"V %d %d %d",edge_time,pre_integrity,dut.core.command_accepted);
    end
    always @(posedge cpu_clk) if(app_reply_valid[0]) begin
        $fdisplay(out,"R %.3f 0 %h %d",$realtime-origin,app_reply_payload[96:0],app_reply_ready[0]);
    end
    always @(posedge x_clk) if(app_reply_valid[1]) begin
        $fdisplay(out,"R %.3f 1 %h %d",$realtime-origin,app_reply_payload[193:97],app_reply_ready[1]);
    end
    always @(posedge command_clk) if(cmd_reply_valid && cmd_reply_ready)
        $fdisplay(out,"K %.3f %h",$realtime-origin,cmd_reply_payload);
    initial begin #2000000;$fatal(1,"timeout");end
endmodule

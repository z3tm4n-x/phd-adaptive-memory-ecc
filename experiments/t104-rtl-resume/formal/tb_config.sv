`timescale 1ns/1ps
module tb_config;
    parameter integer WORD_BITS=19, INVERSE=174763;
    reg clk=0,wr=0,commit=0,start_ok=0;
    reg [3:0] address=0;
    reg [31:0] data=0;
    wire [3:0] observed;
    reg [3:0] before_edge,after_edge;
    integer file_id,read_count,cases=0;
    reg [4095:0] vector_path;
    service_config #(.WORD_BITS(WORD_BITS),.INVERSE(INVERSE)) dut(
        .clk(clk),.wr(wr),.commit(commit),.start_ok(start_ok),
        .address(address),.data(data),.arm_due(observed[0]),
        .locked(observed[1]),.fault(observed[2]),.compatible(observed[3]));
    initial begin
        if(!$value$plusargs("vectors=%s",vector_path)) $fatal(1,"vectors required");
        file_id=$fopen(vector_path,"r");
        if(!file_id) $fatal(1,"cannot open vectors");
        while(!$feof(file_id)) begin
            clk=0;
            read_count=$fscanf(file_id,"%h %h %h %h %h %h %h\n",
                wr,commit,start_ok,address,data,before_edge,after_edge);
            if(read_count!=7) $fatal(1,"bad vector row");
            #1;
            if(observed!==before_edge) $fatal(1,"CONFIG_MISMATCH pre case=%0d got=%h expected=%h",cases,observed,before_edge);
            clk=1; #1;
            if(observed!==after_edge) $fatal(1,"CONFIG_MISMATCH post case=%0d got=%h expected=%h",cases,observed,after_edge);
            cases=cases+1;
        end
        $display("T104_CONFIG_PASS cases=%0d",cases);
        $finish;
    end
endmodule

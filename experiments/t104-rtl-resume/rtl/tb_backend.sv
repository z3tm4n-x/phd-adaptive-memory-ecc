module tb_backend;
    reg clk=0, cold_init=1, soft_reset=0, go=0, err_in=0;
    reg [1:0] kind=0;
    reg [18:0] word_in=0;
    reg [31:0] data_in=0;
    reg [3:0] byte_enable_in=15;
    reg [15:0] dq_in=0;
    wire ready,busy,accepted,rejected,fault,ce,oe,we,drive,alias_high;
    wire [18:0] word_out;
    wire [1:0] byte_enable;
    wire [15:0] dq_out;
    wire sample,flag,err_due,done,release_due,commit_pulse,pending;
    wire [31:0] read_data;
    wire [7:0] age;
    wire [1:0] kind_active;
    wire [32:0] packed_actual = {err_due,rejected,accepted,ready,pending,commit_pulse,
                                done,flag,sample,dq_out,byte_enable,alias_high,drive,we,oe,ce,busy};
    e_backend dut(.*);
    integer fd,n,row=0;
    reg [4095:0] vector_path;
    reg [32:0] expected;
    reg [31:0] expected_read;
    reg [18:0] expected_word;
    reg [7:0] expected_age;
    initial begin
        if (!$value$plusargs("vectors=%s",vector_path)) $fatal(1,"missing vectors");
        fd=$fopen(vector_path,"r");
        if (!fd) $fatal(1,"cannot open vectors");
        while (!$feof(fd)) begin
            n=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                cold_init,soft_reset,go,kind,word_in,data_in,byte_enable_in,dq_in,err_in,
                expected,expected_read,expected_word,expected_age);
            if (n!=13) $fatal(1,"bad vector row %0d n%0d",row,n);
            #2 clk=1; #1;
            if (packed_actual !== expected || read_data !== expected_read
                || word_out !== expected_word || age !== expected_age)
                $fatal(1,"row%0d got%h want%h data%h/%h word%h/%h age%0d/%0d",
                       row,packed_actual,expected,read_data,expected_read,word_out,expected_word,age,expected_age);
            #1 clk=0;
            row=row+1;
        end
        $display("BACKEND_OK rows=%0d",row);
        $finish;
    end
endmodule

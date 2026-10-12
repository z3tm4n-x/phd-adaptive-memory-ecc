// Top-level inputs let SAT -set-def-inputs explicitly quantify defined Boolean
// samples. Anyseq internal nets are not covered by that option in Yosys0.52.
module formal_backend(
    input wire clk, cold_init, soft_reset, go, err_in,
    input wire [1:0] kind,
    input wire [18:0] word_in,
    input wire [31:0] data_in,
    input wire [3:0] byte_enable_in,
    input wire [15:0] dq_in
);
    wire ready,busy,accepted,rejected,fault,ce,oe,we,drive,alias_high;
    wire [18:0] word_out;
    wire [1:0] byte_enable;
    wire [15:0] dq_out;
    wire sample,flag,err_due,done,release_due,commit_pulse,pending;
    wire [31:0] read_data;
    wire [7:0] age;
    wire [1:0] kind_active;
    e_backend dut(.*);
    reg past_valid = 0;
    reg [1:0] accepted_kind = 0;
    always @(posedge clk) begin
        past_valid <= 1;
        if (go && ready && !cold_init && kind != 3 && byte_enable_in != 0)
            accepted_kind <= kind;
        assert(!(drive && oe));
        assert(!we || (busy && drive && ce));
        assert(!pending || busy);
        assert(!done || (!busy && !drive && !we && !oe));
        assert(!flag || (busy && age == 64));
        assert(!commit_pulse || (busy && (age == 132 || age == 200)));
        assert(!busy || age <= 212);
        assert(!busy || kind_active==accepted_kind);
        if (past_valid && $past(busy)) begin
            assert(word_out == $past(word_out));
            assert(age == $past(age) + 4);
            assert(!accepted);
            if ($past(age) >= 60 && $past(age) < 148)
                assert(read_data[15:0] == $past(read_data[15:0]));
            if ($past(age) < 88) assert(busy);
            if ($past(pending) && $past(age) < 144) assert(busy);
            if (accepted_kind == 1 && $past(age) < 180) assert(busy);
            if (accepted_kind == 2 && $past(age) < 212) assert(busy);
        end
        if (past_valid && $past(flag)) assert(!flag);
        if (past_valid && we && $past(we)) assert(dq_out == $past(dq_out));
    end
endmodule

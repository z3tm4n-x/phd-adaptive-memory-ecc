// Combinational unsigned64 equivalence, including overflow and reverse time.
// Separate mathematical miter; full-core regression is still required.
module spacing(input wire [63:0] previous, current);
    wire old_close=current<previous || current-previous<64'd5508;
    wire [64:0] exact_next={1'b0,previous}+65'd5508;
    wire new_close=previous>64'hffffffffffffea7b || current<(previous+64'd5508);
    always @* begin
        assert(new_close==old_close);
        assert(new_close==(exact_next>{1'b0,current}));
    end
endmodule

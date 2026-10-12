// Same input history, no assumptions, four external signals and a proved
// representation relation. proof_match ports are added only to build copies.
module config_equivalence #(
    parameter integer WORD_BITS=19, INVERSE=174763
)(input wire clk, wr, commit, start_ok,
  input wire [3:0] address, input wire [31:0] data);
    wire [3:0] old_out, new_out;
    wire [11:0] old_match, new_match;
    config_gold #(.WORD_BITS(WORD_BITS),.INVERSE(INVERSE)) gold(
        .clk(clk),.wr(wr),.commit(commit),.start_ok(start_ok),
        .address(address),.data(data),.arm_due(old_out[0]),
        .locked(old_out[1]),.fault(old_out[2]),.compatible(old_out[3]),
        .proof_match(old_match));
    service_config #(.WORD_BITS(WORD_BITS),.INVERSE(INVERSE)) dut(
        .clk(clk),.wr(wr),.commit(commit),.start_ok(start_ok),
        .address(address),.data(data),.arm_due(new_out[0]),
        .locked(new_out[1]),.fault(new_out[2]),.compatible(new_out[3]),
        .proof_match(new_match));
    genvar i;
    generate for(i=0;i<4;i=i+1) begin: external_equivalence
        always @* assert(old_out[i]==new_out[i]);
    end
    for(i=0;i<12;i=i+1) begin: representation_invariant
        always @* assert(old_match[i]==new_match[i]);
    end endgenerate
endmodule

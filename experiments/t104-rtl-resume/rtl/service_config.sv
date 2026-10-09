// Memory-domain initialization port, NOT an asynchronous MMIO bus.
// All fields must be written; commit locks them for the one mission.
module service_config #(parameter integer WORD_BITS=19, INVERSE=174763)(
    input wire clk, wr, commit, start_ok,
    input wire [3:0] address,
    input wire [31:0] data,
    output wire arm_due,
    output reg locked, fault,
    output wire compatible
);
    // Only field equality is observable; retain it on the write edge instead
    // of putting twelve 32-bit comparisons on the arm/cold_init fast path.
    // Zero means either unwritten or a nonmatching LAST permitted write.
    reg [11:0] field_match=0;
    initial begin locked=0; fault=0; end
    assign compatible = (&field_match) && WORD_BITS>=3 && WORD_BITS<=19
        && ((64'd3*INVERSE)%(64'd1<<WORD_BITS)==1);
    assign arm_due = commit && !wr && !locked && compatible && start_ok;
    always @(posedge clk) begin
        if (wr) begin
            if (locked || address>=12 || commit) fault<=1;
            else case(address)
                0: field_match[0]<=data==32'h00104114;
                1: field_match[1]<=data==(32'd1<<WORD_BITS);
                2: field_match[2]<=data==38;
                3: field_match[3]<=data==3;
                4: field_match[4]<=data==196;
                5: field_match[5]<=data==164;
                6: field_match[6]<=data==320;
                7: field_match[7]<=data==8;
                8: field_match[8]<=data==1312;
                9: field_match[9]<=data==240;
                10: field_match[10]<=data==208;
                11: field_match[11]<=data==104;
            endcase
        end
        if (commit) begin
            if (arm_due) locked<=1;
            else fault<=1;
        end
    end
endmodule

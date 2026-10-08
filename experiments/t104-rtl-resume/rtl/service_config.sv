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
    reg [31:0] fields [0:11];
    initial begin locked=0; fault=0; end
    reg [11:0] written=0;
    integer i;
    initial for (i=0;i<12;i=i+1) fields[i]=0;
    assign compatible = written==12'hfff && WORD_BITS>=3 && WORD_BITS<=19
        && ((64'd3*INVERSE)%(64'd1<<WORD_BITS)==1)
        && fields[0]==32'h00104114 && fields[1]==(32'd1<<WORD_BITS)
        && fields[2]==38 && fields[3]==3 && fields[4]==196 && fields[5]==164
        && fields[6]==320 && fields[7]==8 && fields[8]==1312
        && fields[9]==240 && fields[10]==208 && fields[11]==104;
    assign arm_due = commit && !wr && !locked && compatible && start_ok;
    always @(posedge clk) begin
        if (wr) begin
            if (locked || address>=12 || commit) fault<=1;
            else begin fields[address]<=data; written[address]<=1; end
        end
        if (commit) begin
            if (arm_due) locked<=1;
            else fault<=1;
        end
    end
endmodule

// Explicit 8-bit increments with parallel prefix enables, not a 64-bit ripple.
// At most one coalesced event per edge; mission uptime also uses this counter.
module segmented_counter(input wire clk,inc,output reg [63:0] value=0,
                         output wire [63:0] next_value,
                         output wire exhausted);
    // Registered byte maxima avoid reconstructing a 56-bit carry prefix on
    // the event edge. The invariant maximum[k] == (&value[k*8+:8]) is proved.
    reg [7:0] maximum=0;
    assign exhausted=&maximum;
    genvar k;
    generate for(k=0;k<8;k=k+1) begin: chunks
        wire carry;
        if(k==0) assign carry=inc && !exhausted;
        else assign carry=inc && !exhausted && (&maximum[k-1:0]);
        assign next_value[k*8+:8]=value[k*8+:8]+carry;
        always @(posedge clk) begin
            value[k*8+:8]<=next_value[k*8+:8];
            maximum[k]<=carry ? value[k*8+:8]==8'hfe : maximum[k];
        end
    end endgenerate
endmodule

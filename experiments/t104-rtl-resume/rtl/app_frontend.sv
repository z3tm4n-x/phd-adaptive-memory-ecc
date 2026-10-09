// Source-domain first-VALID accounting, stable offer check and backpressure
// watchdog. now_floor comes from the synchronized protected Gray timebase.
// One source may hold an unaccepted offer externally, not a third queue entry.
module app_frontend #(parameter integer WORD_BITS=19)(
    input wire clk, soft_reset,
    input wire [63:0] now_floor,
    input wire valid,
    input wire [1:0] kind,
    input wire [WORD_BITS-1:0] word_address,
    input wire [31:0] data,
    input wire [3:0] byte_enable,
    input wire [63:0] request_id,
    input wire link_ready, reply_valid, reply_ready,
    output wire send,
    output wire [255:0] payload,
    output reg fault
);
    localparam integer OFFER_BITS=160;
    initial fault=0;
    wire [31:0] extended_word={{(32-WORD_BITS){1'b0}},word_address};
    wire [OFFER_BITS-1:0] offer={request_id,data,extended_word,24'd0,byte_enable,2'd0,kind};
    reg waiting=0;
    reg [OFFER_BITS-1:0] held=0;
    reg [63:0] first=0;
    reg [3:0] blocked_cycles=0;
    wire changed = waiting && (!valid || offer!=held);
    wire valid_request = (kind==1 || kind==2) && byte_enable!=0;
    assign send = valid && link_ready && valid_request && !changed;
    // Low->high little-endian words: meta32(kind1:0,mask7:4),address32,data32,
    // id64,first-VALID lower bound64; then CRC32 over these28 bytes.
    wire [223:0] content={waiting ? first : (valid ? now_floor : 64'd0),offer};
    function [31:0] crc224;
        input [223:0] bits;
        reg [31:0] c;
        integer i;
        begin
            c=32'hffffffff;
            for(i=0;i<224;i=i+1)
                c=(c>>1)^((c[0]^bits[i]) ? 32'hedb88320 : 32'd0);
            crc224=~c;
        end
    endfunction
    assign payload = {crc224(content),content};
    always @(posedge clk) begin
        if (soft_reset || changed || (valid && !valid_request)) fault<=1;
        if (!waiting && valid && !send) begin
            waiting<=1; first<=now_floor; held<=offer;
        end
        if (send) waiting<=0;
        if (reply_valid && !reply_ready) begin
            // T_CPU<=10.0001ns; at most9 complete waiting cycles fit100ns.
            if (blocked_cycles<15) blocked_cycles<=blocked_cycles+1;
            if (blocked_cycles>=9) fault<=1;
        end else blocked_cycles<=0;
    end
endmodule

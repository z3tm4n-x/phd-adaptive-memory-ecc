// Request arrives after3 synchronizer edges. Capture on4, CRC chunks on5/6/7,
// permission gate consumes at8. No field is published before complete CRC.
// Payload low->high: mission32,config32,sequence64,issued64,not_before64,
// deadline64,expires64; then standard reflected CRC32 over48 little-endian bytes.
module command_receiver(
    input wire clk,
    input wire in_valid,
    input wire [415:0] in_data,
    output wire in_ready,
    output wire command_valid, integrity,
    output wire [383:0] command,
    input wire accepted,
    output wire reply_valid,
    output wire [31:0] reply_data,
    input wire reply_ready, retire
);
    reg [2:0] stage=0;
    reg [415:0] saved=0;
    reg [31:0] crc=32'hffffffff;
    function [31:0] update_crc;
        input [31:0] old;
        input [127:0] bytes;
        reg [31:0] c;
        integer i;
        begin
            c=old;
            for(i=0;i<128;i=i+1)
                c=(c>>1)^((c[0]^bytes[i]) ? 32'hedb88320 : 32'd0);
            update_crc=c;
        end
    endfunction
    assign in_ready = stage==0;
    assign command_valid = stage==4;
    assign command = saved[383:0];
    assign integrity = (~crc)==saved[415:384];
    assign reply_valid = stage==5;
    assign reply_data = {31'd0,accepted};
    always @(posedge clk) begin
        case(stage)
            0: if(in_valid) begin saved<=in_data; crc<=32'hffffffff; stage<=1; end
            1: begin crc<=update_crc(crc,saved[127:0]); stage<=2; end
            2: begin crc<=update_crc(crc,saved[255:128]); stage<=3; end
            3: begin crc<=update_crc(crc,saved[383:256]); stage<=4; end
            4: stage<=5;
            5: if(reply_ready) stage<=6;
            6: if(retire) stage<=0;
            default: stage<=6;
        endcase
    end
endmodule

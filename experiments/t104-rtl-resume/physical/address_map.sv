// DESIGN SCENARIO, not the proprietary address-to-ECC-word relation.
// W32_seq + H_low: byte=4*word+2*half+lane; x16 address=byte>>1.
module address_map(input wire [18:0] word_index,input wire half,
                   output wire [19:0] address);
    assign address={word_index,half};
endmodule

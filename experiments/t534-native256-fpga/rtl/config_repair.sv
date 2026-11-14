// PG036 repair mode; board commissioning must grant exclusive access to ICAP.
module config_repair(input wire clk,output wire ready,loss);
    wire observation,correction,uncorrectable;
    wire csb,rwb,crc_err,ecc_err,single,syndrome_valid;
    wire [31:0] wdata,rdata;
    wire [12:0] syndrome;
    wire [25:0] far_addr;
    wire [4:0] syn_bit;
    wire [6:0] syn_word;
    ICAPE2 #(.ICAP_WIDTH("X32")) port(.CLK(clk),.CSIB(csb),.RDWRB(rwb),.I(wdata),.O(rdata));
    FRAME_ECCE2 #(.FARSRC("EFAR")) check_frame(.CRCERROR(crc_err),.ECCERROR(ecc_err),
        .ECCERRORSINGLE(single),.FAR(far_addr),.SYNBIT(syn_bit),.SYNDROME(syndrome),
        .SYNDROMEVALID(syndrome_valid),.SYNWORD(syn_word));
    sem_core sem(.icap_clk(clk),.icap_grant(1'b1),.icap_csib(csb),.icap_rdwrb(rwb),
        .icap_o(rdata),.icap_i(wdata),.fecc_crcerr(crc_err),.fecc_eccerr(ecc_err),
        .fecc_eccerrsingle(single),.fecc_syndromevalid(syndrome_valid),.fecc_far(far_addr),
        .fecc_syndrome(syndrome),.fecc_synbit(syn_bit),.fecc_synword(syn_word),
        .status_observation(observation),.status_correction(correction),
        .status_uncorrectable(uncorrectable),.monitor_rxempty(1'b1),.monitor_rxdata(8'b0),
        .monitor_txfull(1'b0));
    assign ready=observation;
    assign loss=!observation || correction || uncorrectable;
endmodule

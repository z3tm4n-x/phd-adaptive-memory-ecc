// Dedicated frame path. A request for frame f prepares f+2; no per-slot CDC.
// A candidate labels processed history, not the concurrently observed fast ID.
module candidate_link(
    input wire fast_clk,slow_clk,rst_fast,rst_slow,
    input wire frame_pulse,input wire [31:0] frame_id,
    input wire [63:0] processed_generation,input wire rule_low,
    input wire [63:0] generation,input wire invalidate,input wire loss,
    input wire [31:0] freeze_frame,
    output wire permit,
    output reg fault=0,
    output reg installed=0,output reg [31:0] installed_frame=0,
    output wire candidate_busy
);
    reg beacon_pending=0;
    reg [31:0] beacon=0;
    reg beacon_capture=0;
    reg [31:0] beacon_snapshot=0,target_snapshot=2;
    wire beacon_ready,beacon_valid;
    wire [31:0] received_frame;
    reg response_pending=0;
    reg [159:0] response=0;
    wire response_ready,candidate_valid,candidate_ready;
    wire [159:0] candidate_data;
    reg [127:0] payload=0;
    reg [31:0] expected_crc=0;
    reg [31:0] crc_pipe[0:15];
    reg [17:0] check_valid=0;
    reg checking=0,uninterrupted=0,crc_good=0;
    (* MAX_FANOUT=16 *) reg receipt=0;
    reg [159:0] snapshot=0;
    reg [3:0] generation_equal=0;
    reg [3:0] target_equal=0;
    reg [31:0] expected_target=2;
    // Four direct-mapped lines. The index already stores tag[1:0]; only
    // tag[3:2] needs state. Upper tag bits are zero by target_equal on every
    // installation. Do not infer a4x32 RAM plus a32-bit freeze comparison.
    reg [1:0] cache_tag[0:3];
    reg [3:0] cache_low=0;
    reg prepared_permit=0;
    integer i;
    initial begin
        for(i=0;i<4;i=i+1) cache_tag[i]=0;
        for(i=0;i<16;i=i+1) crc_pipe[i]=0;
    end
    function [31:0] crc128;
        input [127:0] data;
        reg [31:0] c; integer k;
        begin
            c=32'hffffffff;
            for(k=0;k<128;k=k+1) c=(c>>1)^((c[0]^data[k])?32'hedb88320:32'd0);
            crc128=~c;
        end
    endfunction
    function [31:0] crc_byte;
        input [31:0] c0; input [7:0] b;
        reg [31:0] c; integer k;
        begin
            c=c0;
            for(k=0;k<8;k=k+1) c=(c>>1)^((c[0]^b[k])?32'hedb88320:32'd0);
            crc_byte=c;
        end
    endfunction
    wire [127:0] next_payload={31'd0,rule_low,processed_generation,28'd0,received_frame[3:0]+4'd2};
    // Four-bit local FRAME tag, distinct from the nonreset64-bit generation.
    // The complete flight is <1us; a tag repeats after16 frames (>25us).
    // A still-pending beacon at a later frame faults. This diagnostic is not
    // a one-frame watchdog for an already accepted in-flight packet.
    wire [31:0] beacon_target={28'd0,frame_id[3:0]+4'd2};
    handshake_channel #(.WIDTH(32)) requests(
        .src_clk(fast_clk),.dest_clk(slow_clk),.src_rst(rst_fast),.dest_rst(rst_slow),
        .in_valid(beacon_pending),.in_ready(beacon_ready),.in_data(beacon),
        .out_valid(beacon_valid),.out_ready(!response_pending),.out_data(received_frame));
    handshake_channel #(.WIDTH(160)) candidates(
        .src_clk(slow_clk),.dest_clk(fast_clk),.src_rst(rst_slow),.dest_rst(rst_fast),
        .in_valid(response_pending),.in_ready(response_ready),.in_data(response),
        .out_valid(candidate_valid),.out_ready(candidate_ready),.out_data(candidate_data));
    always @(posedge slow_clk) begin
        if(response_pending && response_ready) response_pending<=0;
        if(beacon_valid && !response_pending) begin
            response<={crc128(next_payload),next_payload}; response_pending<=1;
        end
    end
    // checking is set on the acceptance edge, before receipt is observed.
    // Re-testing receipt here forms a redundant feedback path through the
    // high-fanout payload enable. Keep that enable outside the ready loop.
    assign candidate_ready=!checking;
    assign candidate_busy=checking || receipt;
    // No wide generation comparison in the freeze→decision path. Every
    // intervening ERR clears valid leases, including the installation edge.
    // Tag/lease lookup is before freeze. Immediate invalidation is still
    // combinational on the publication edge and clears the prepared bit.
    assign permit=prepared_permit && !invalidate && !loss && !fault;
    always @(posedge fast_clk) begin
        installed<=0;
        prepared_permit<=cache_low[freeze_frame[1:0]] &&
            cache_tag[freeze_frame[1:0]]==freeze_frame[3:2] &&
            freeze_frame[31:4]==0 && !invalidate && !loss && !fault;
        beacon_snapshot<=frame_id;target_snapshot<=beacon_target;
        beacon_capture<=frame_pulse && (!beacon_pending || beacon_ready);
        snapshot<=candidate_data;
        receipt<=candidate_valid && candidate_ready;
        if(candidate_valid && candidate_ready) checking<=1;
        check_valid<={check_valid[16:0],receipt};
        // Always-clocked CRC pipeline: no shared reset/enable spanning all
        // CRC bits, no data-dependent byte mux. Payload stays fixed until
        // the final valid bit. These cycles are all before target freeze.
        crc_pipe[0]<=crc_byte(32'hffffffff,payload[7:0]);
        for(i=1;i<16;i=i+1) crc_pipe[i]<=crc_byte(crc_pipe[i-1],payload[i*8+:8]);
        crc_good<=~crc_pipe[15]==expected_crc && payload[127:97]==0;
        if(beacon_pending && beacon_ready) beacon_pending<=0;
        if(frame_pulse) begin
            if(beacon_pending && !beacon_ready) fault<=1;
            uninterrupted<=0;
        end
        if(beacon_capture) begin
            beacon<=beacon_snapshot;beacon_pending<=1;expected_target<=target_snapshot;
        end
        if(receipt) begin
            payload<=snapshot[127:0]; expected_crc<=snapshot[159:128];
            uninterrupted<=!invalidate && !loss;
        end
        begin
            // These short comparisons are always clocked. Validity comes
            // from check_valid/uninterrupted, not a broad checking enable.
            generation_equal<={payload[95:80]==generation[63:48],
                              payload[79:64]==generation[47:32],
                              payload[63:48]==generation[31:16],
                              payload[47:32]==generation[15:0]};
            target_equal<={payload[31:24]==expected_target[31:24],
                           payload[23:16]==expected_target[23:16],
                           payload[15:8]==expected_target[15:8],
                           payload[7:0]==expected_target[7:0]};
        end
        if(check_valid[17]) begin
            checking<=0;
            // Future modulo16. Transport liveness is a separate obligation;
            // no arbitrary-delay or out-of-contract reset is permitted.
            if(!crc_good) fault<=1;
            else if((&target_equal) && !frame_pulse &&
                    (&generation_equal) && uninterrupted && !invalidate && !loss) begin
                cache_tag[payload[1:0]]<=payload[3:2];
                cache_low[payload[1:0]]<=payload[96];
                installed<=1; installed_frame<=payload[31:0];
            end
        end
        if(invalidate || loss) begin cache_low<=0; uninterrupted<=0; end
    end
endmodule

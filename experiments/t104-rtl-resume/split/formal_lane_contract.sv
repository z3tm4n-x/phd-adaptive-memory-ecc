// Inserted as assertions only into a build copy of operation_lane by the checker.
// Vendor boundary abstraction: arbitrary forward valid/data, arbitrary return
// capacity and loss, sampled on each fast edge. No FIFO implementation proof.
reg proof_owed=0, proof_launched=0, proof_released=0;
reg [120:0] proof_packet=0;
reg proof_past=0, proof_stalled=0;
reg [96:0] proof_reply=0;
always @(posedge fast_clk) begin
    assert(phase==0 || phase==1 || phase==2 || phase==4 || phase==8 || phase==16);
    if(phase==0) assert(protocol_fault && !fast_busy && !reply_pending);
    assert((phase==1)==!proof_owed);
    assert((phase==8)==fast_busy);
    if(proof_owed && phase!=2) begin
        assert(staged==proof_packet);
    end
    if(phase==2) assert(snapshot==proof_packet);
    if(phase==2) assert(!proof_launched && !proof_released);
    if(phase==8 || phase==16) begin
        assert(proof_launched);
        assert(active_id==proof_packet[120:57]);
    end
    if(forward_valid && forward_ready) begin
        assert(!proof_owed);
        proof_owed<=1; proof_launched<=0; proof_released<=0;
        proof_packet<=forward_data;
    end
    if(grant_debug) begin
        assert(staged[1:0]!=3 && staged[56:53]!=0);
        assert(proof_owed && !proof_launched && !fast_busy);
        assert(staged==proof_packet);
        proof_launched<=1;
    end
    if(fast_busy) begin
        assert(proof_launched && !proof_released);
        assert(word_out==proof_packet[20:2]);
    end
    if(release_debug) begin
        assert(proof_owed && proof_launched && !proof_released);
        proof_released<=1;
    end
    if(reply_pending) begin
        assert(proof_owed && proof_launched && proof_released && !fast_busy);
        assert(reply_hold[96:33]==proof_packet[120:57]);
    end
    if(reply_pending && return_ready) proof_owed<=0;
    if(proof_past && proof_stalled) assert(reply_pending && reply_hold==proof_reply);
    proof_past<=1;
    proof_stalled<=reply_pending && !return_ready;
    proof_reply<=reply_hold;
end

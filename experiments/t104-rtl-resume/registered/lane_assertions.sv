// Compositional cutpoint: arbitrary ordered-channel boundary values/capacity.
// Does NOT prove vendor ordering or end-to-end delay. No additional assumes.
reg proof_owed=0,proof_launched=0,proof_released=0;
reg [56:0] proof_packet=0;
reg proof_past=0,proof_stalled=0;
reg [32:0] proof_reply=0;
always @(posedge fast_clk) begin
    assert((receive_idle && !receipt)==!proof_owed);
    if(protocol_fault) assert(!receive_idle && !fast_busy && !reply_pending && !launch);
    if(receipt) begin
        assert(snapshot==proof_packet && proof_owed && !proof_launched && !proof_released);
        assert(!forward_ready);
    end
    if(proof_owed && !receipt) assert(staged==proof_packet);
    if(forward_valid && forward_ready) begin
        assert(!proof_owed);
        proof_owed<=1; proof_launched<=0; proof_released<=0; proof_packet<=forward_data;
    end
    if(grant_debug) begin
        assert(staged[1:0]!=3 && staged[56:53]!=0);
        assert(proof_owed && !proof_launched && !fast_busy);
        assert(staged==proof_packet && !receive_idle);
        proof_launched<=1;
    end
    if(fast_busy) begin
        assert(proof_launched && !proof_released);
        assert(word_out==proof_packet[20:2]);
        assert(!receive_idle && !launch);
    end
    if(release_debug) begin
        assert(proof_owed && proof_launched && !proof_released);
        proof_released<=1;
    end
    if(reply_pending) assert(proof_owed && proof_launched && proof_released && !fast_busy);
    if(reply_pending && return_ready) proof_owed<=0;
    if(proof_past && proof_stalled) assert(reply_pending && reply_hold==proof_reply);
    proof_past<=1; proof_stalled<=reply_pending && !return_ready; proof_reply<=reply_hold;
end

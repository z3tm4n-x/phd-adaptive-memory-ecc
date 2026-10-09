// Calendar microsequence only; policy/time/config live in the slow domain.
// Same 4-xi slot/freeze instants as cc0ce6d, no 64-bit time in this block.
module relative_calendar #(
    parameter integer WORD_BITS=19, INVERSE=174763
)(
    input wire clk, cold_init, soft_reset, skip_permitted, alarm, phase_bad,
    input wire backend_busy,
    output reg phase_valid=1, fault=0,
    output wire execute_due, app_due,
    output reg [WORD_BITS-1:0] word_due=0,
    output wire slot_due, freeze_due,
    output reg slot_pulse=0, execute_pulse=0, skip_pulse=0,
    output reg freeze_pulse=0, frozen_execute=0, app_window=0
);
    reg booted=0;
    reg [6:0] start_wait=0, freeze_wait=2;
    reg [8:0] app_wait=328;
    reg [2:0] start_pos=0, freeze_pos=2;
    reg [1:0] start_ring=0, freeze_ring=2, freeze_mod3=2;
    reg [WORD_BITS:0] warmup_left=(1<<WORD_BITS)-2;
    reg [3:0] decisions=4'b1111, valid_decisions=4'b0011;
    wire must_execute=warmup_left!=0 || freeze_mod3==0;
    wire decide=must_execute || !skip_permitted || alarm || soft_reset
               || !phase_valid || phase_bad || fault;
    assign slot_due=booted && start_wait==0;
    assign freeze_due=booted && freeze_wait==0;
    assign execute_due=slot_due && !backend_busy
                       && (decisions[start_ring] || !valid_decisions[start_ring]);
    assign app_due=booted && app_wait==0 && !backend_busy;
    always @(posedge clk) begin
        slot_pulse<=0; execute_pulse<=0; skip_pulse<=0;
        freeze_pulse<=0; app_window<=0;
        if (cold_init && !booted) booted<=1;
        else if (booted) begin
            if (cold_init || phase_bad) begin phase_valid<=0; fault<=1; end
            if (freeze_due) begin
                freeze_wait <= freeze_pos==7 ? 104 : 40;
                freeze_pos<=freeze_pos+1'b1; freeze_ring<=freeze_ring+1'b1;
                freeze_mod3<=freeze_mod3==2 ? 0 : freeze_mod3+1'b1;
                if (warmup_left!=0) warmup_left<=warmup_left-1'b1;
                decisions[freeze_ring]<=decide; valid_decisions[freeze_ring]<=1;
                freeze_pulse<=1; frozen_execute<=decide;
            end else freeze_wait<=freeze_wait-1'b1;
            if (slot_due) begin
                start_wait<=start_pos==7 ? 104 : 40;
                start_pos<=start_pos+1'b1; start_ring<=start_ring+1'b1;
                word_due<=word_due+INVERSE;
                slot_pulse<=1;
                if (!valid_decisions[start_ring]) begin phase_valid<=0; fault<=1; end
                if (decisions[start_ring] || !valid_decisions[start_ring]) begin
                    if (!backend_busy) execute_pulse<=1;
                    else begin phase_valid<=0; fault<=1; end
                end else skip_pulse<=1;
                valid_decisions[start_ring]<=0;
            end else start_wait<=start_wait-1'b1;
            if (app_wait==0) begin app_wait<=391; app_window<=1; end
            else app_wait<=app_wait-1'b1;
        end
    end
endmodule

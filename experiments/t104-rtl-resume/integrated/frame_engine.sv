// Same deterministic schedule as the independent absolute Calendar reference.
// Four local decisions suffice for lead320 at c164. Candidate FRAME leases are
// separate, prepared two frames ahead, and never alter committed slot bits.
module frame_engine #(
    parameter integer WORD_BITS=19,INVERSE=174763
)(
    input wire clk,start,permit,alarm,backend_busy,
    output wire control_due,app_due,slot_due,freeze_due,
    output wire control_prepare,app_prepare,
    output reg [WORD_BITS-1:0] word_due,
    output reg running,fault,
    output wire frame_pulse,
    output reg [31:0] frame_id,freeze_frame,
    output reg [2:0] slot_pos,freeze_pos,
    output reg slot_pulse,skip_pulse,freeze_pulse,frozen_execute
);
    initial begin
        word_due=0;running=0;fault=0;frame_id=0;freeze_frame=0;slot_pos=0;freeze_pos=2;
        slot_pulse=0;skip_pulse=0;freeze_pulse=0;frozen_execute=0;
    end
    reg [6:0] start_wait=0,freeze_wait=2;
    reg [8:0] app_wait=328;
    reg [1:0] start_ring=0,freeze_ring=2,freeze_mod3=2;
    reg [WORD_BITS:0] warmup_left=(1<<WORD_BITS)-2;
    reg [3:0] decisions=4'b1111,valid_decisions=4'b0011;
    reg slot_tick=0,freeze_tick=0,app_tick=0,frame_tick=0;
    reg execute_slot=1;
    wire must_execute=warmup_left!=0 || freeze_mod3==0;
    assign slot_due=slot_tick;
    assign freeze_due=freeze_tick;
    assign frame_pulse=frame_tick;
    // A frozen bit is available 320xi before its slot. Select it in advance;
    // no ring mux is allowed on the backend GO edge. Never sample live LOW
    // here: that would revoke an already committed skip after a new ERR.
    assign control_due=slot_due && execute_slot;
    assign app_due=app_tick;
    assign control_prepare=running && start_wait==1;
    assign app_prepare=running && app_wait==1;
    always @(posedge clk) begin
        slot_pulse<=0; skip_pulse<=0; freeze_pulse<=0;
        execute_slot<=decisions[start_ring] || !valid_decisions[start_ring];
        if(start && !running) begin running<=1;slot_tick<=1;frame_tick<=1;end
        else if(running) begin
            slot_tick<=start_wait==1;
            freeze_tick<=freeze_wait==1;
            app_tick<=app_wait==1;
            frame_tick<=start_wait==1 && slot_pos==0;
            if(freeze_due) begin
                freeze_wait<=freeze_pos==7 ? 104 : 40;
                // A local lease tag, NOT mission time or error generation.
                // A frame transfer finishes <1us; a tag repeats after16
                // frames (>25us). In-contract transfer bounds are checked
                // separately; blockage faults, but is not priced as normal.
                if(freeze_pos==7) freeze_frame<=(freeze_frame+1'b1)&32'hf;
                freeze_pos<=freeze_pos+1'b1; freeze_ring<=freeze_ring+1'b1;
                freeze_mod3<=freeze_mod3==2 ? 0 : freeze_mod3+1'b1;
                if(warmup_left!=0) warmup_left<=warmup_left-1'b1;
                decisions[freeze_ring]<=must_execute || !permit || alarm || fault;
                valid_decisions[freeze_ring]<=1;
                freeze_pulse<=1; frozen_execute<=must_execute || !permit || alarm || fault;
            end else freeze_wait<=freeze_wait-1'b1;
            if(slot_due) begin
                start_wait<=slot_pos==7 ? 104 : 40;
                slot_pos<=slot_pos+1'b1; start_ring<=start_ring+1'b1;
                word_due<=word_due+INVERSE;
                slot_pulse<=1;
                if(!valid_decisions[start_ring] || (control_due && backend_busy)) fault<=1;
                if(!decisions[start_ring] && valid_decisions[start_ring]) skip_pulse<=1;
                valid_decisions[start_ring]<=0;
            end else start_wait<=start_wait-1'b1;
            if(app_wait==0) app_wait<=391;
            else app_wait<=app_wait-1'b1;
            // Frame number changes at its first edge, not the final slot.
            if(start_wait==1 && slot_pos==0) frame_id<=(frame_id+1'b1)&32'hf;
        end
    end
endmodule

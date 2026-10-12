// T119 two-stage ERR rule. Only COMPLETED history is published in generation.
// Tick timers are conservative T135 counts; ERR pairing uses source timestamps
// so queue jitter cannot hide a close pair. Timestamp units: fast 4-xi edges.
module slow_rule #(
    parameter [33:0] NW=34'd4500045002,NH=34'd9000090002,NR=34'd9015504896,
    parameter [63:0] PAIR_WINDOW=64'd22500225010
)(
    input wire clk,start,event_valid,
    input wire [129:0] event_data,
    input wire history_fault,
    output reg [63:0] processed_generation,
    output wire low,
    output reg [33:0] short_left,long_left,recovery_left,
    output reg healthy,started,
    output reg fault
);
    initial begin
        processed_generation=0;short_left=0;long_left=0;recovery_left=NR;
        healthy=1;started=0;fault=0;
    end
    wire [63:0] event_generation=event_data[129:66];
    wire [63:0] timestamp=event_data[65:2];
    wire event_loss=event_data[1], event_err=event_data[0];
    reg [63:0] last_err=0;
    reg seen_err=0;
    assign low=started && healthy && !history_fault && !fault &&
               short_left==0 && long_left==0 && recovery_left==0 && !event_valid;
    always @(posedge clk) begin
        if(start && !started) begin started<=1; recovery_left<=NR; end
        if(started) begin
            if(short_left!=0) short_left<=short_left-1'b1;
            if(long_left!=0) long_left<=long_left-1'b1;
            if(recovery_left!=0) recovery_left<=recovery_left-1'b1;
        end
        if(history_fault) fault<=1;
        if(event_valid) begin
            // One generation per coalesced event; missing/reordered history
            // quarantines LOW, never assigns the latest fast number blindly.
            if(event_generation!=processed_generation+64'd1) fault<=1;
            processed_generation<=event_generation;
            healthy<=!event_loss;
            if(!event_loss && !healthy) begin
                // Compare with the post-tick hold: equality must renew NR,
                // not silently shorten a recovery by one slow cycle.
                if(recovery_left<=NR) recovery_left<=NR;
            end
            if(event_err) begin
                short_left<=NW;
                if(seen_err && timestamp>=last_err && timestamp-last_err<=PAIR_WINDOW)
                    long_left<=NH;
                last_err<=timestamp; seen_err<=1;
            end
        end
    end
endmodule

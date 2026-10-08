// Memory-domain atomic permission gate. Not the scientific LOW producer.
// cmd_valid means the complete, stable payload has ALREADY crossed the CDC.
// cmd_integrity is supplied by an integrity checker; it is not a CRC theorem.
module permission_gate #(
    parameter [31:0] MISSION_ID = 104,
    parameter [31:0] CONFIG_ID = 32'h00104114
)(
    input wire clk, cold_init, soft_reset, loss, err_event, recover,
    input wire [63:0] now,
    input wire cmd_valid, cmd_integrity,
    input wire [31:0] cmd_mission, cmd_config,
    input wire [63:0] cmd_sequence, cmd_issued, cmd_not_before, cmd_deadline, cmd_expires,
    output reg command_ack, command_accepted,
    output wire permit_at_edge,
    output reg active, shadow, healthy,
    output reg overflow,
    output reg [63:0] err_count, last_sequence
);
    initial begin
        command_ack=0; command_accepted=0; active=0; shadow=0; healthy=1;
        overflow=0; err_count=0; last_sequence=0;
    end
    reg begun = 0, revoked_valid = 0;
    reg [63:0] revoked = 0;
    reg [63:0] active_expires = 0;
    reg [63:0] shadow_not_before = 0, shadow_deadline = 0;
    reg [63:0] shadow_expires = 0, shadow_issued = 0;
    wire alarm_now = soft_reset || loss || err_event || (cold_init && begun);
    wire overflow_now = overflow || (err_event && err_count == 64'hffffffffffffffff);
    // Alarm is a final, same-edge veto, not a payload property. Keep it out
    // of the command-validation cone and the nested state-update enables.
    wire usable_channel = (healthy || recover) && !overflow_now;
    wire payload_good = cmd_integrity && cmd_mission == MISSION_ID && cmd_config == CONFIG_ID
        && cmd_sequence > last_sequence && (!revoked_valid || cmd_issued > revoked)
        && cmd_issued <= now && cmd_issued <= cmd_not_before
        && cmd_not_before <= cmd_deadline && cmd_deadline < cmd_expires
        && now <= cmd_deadline;
    wire bad_payload = cmd_valid && !payload_good;
    wire command_blocked = bad_payload || (cmd_valid && !usable_channel);
    wire shadow_late = shadow && now > shadow_deadline;
    wire shadow_due = shadow && now >= shadow_not_before && !shadow_late
                     && (!revoked_valid || shadow_issued > revoked);
    // The calendar consumes this combinational pre-edge view. Therefore an
    // on-deadline command can affect the SAME edge; an alarm wins at that edge.
    assign permit_at_edge = !alarm_now && usable_channel && !bad_payload && !shadow_late
        && ((active && now < active_expires) || shadow_due
            || (cmd_valid && now >= cmd_not_before));

    always @(posedge clk) begin
        command_ack <= cmd_valid;
        command_accepted <= cmd_valid && payload_good && usable_channel && !alarm_now;
        if (cold_init && !begun) begin
            begun <= 1; active <= 0; shadow <= 0; healthy <= 1;
            overflow <= 0; err_count <= 0; last_sequence <= 0;
            revoked_valid <= 0; revoked <= 0;
            active_expires <= 0; shadow_not_before <= 0; shadow_deadline <= 0;
            shadow_expires <= 0; shadow_issued <= 0;
            command_ack <= 0; command_accepted <= 0;
        end else if (begun) begin
            if (err_event) begin
                if (err_count == 64'hffffffffffffffff) overflow <= 1;
                else err_count <= err_count + 1;
            end
            if (alarm_now || command_blocked || shadow_late) begin
                active <= 0; shadow <= 0; healthy <= 0;
                revoked <= now; revoked_valid <= 1;
                command_accepted <= 0;
            end else begin
                if (recover) healthy <= 1;
                if (active && now >= active_expires) active <= 0;
                if (shadow_due && usable_channel) begin
                    active <= 1; active_expires <= shadow_expires; shadow <= 0;
                end
                // This branch already establishes !alarm and, whenever
                // cmd_valid, both payload_good and usable_channel.
                if (cmd_valid) begin
                    last_sequence <= cmd_sequence;
                    if (now < cmd_not_before) begin
                        shadow <= 1;
                        shadow_not_before <= cmd_not_before;
                        shadow_deadline <= cmd_deadline;
                        shadow_expires <= cmd_expires; shadow_issued <= cmd_issued;
                    end else begin
                        active <= 1; active_expires <= cmd_expires; shadow <= 0;
                    end
                end
            end
        end
    end
endmodule

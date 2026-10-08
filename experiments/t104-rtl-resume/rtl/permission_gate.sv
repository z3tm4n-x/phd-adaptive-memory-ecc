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
    wire channel_good = (healthy || recover) && !alarm_now && !overflow_now;
    wire valid_payload = cmd_integrity && cmd_mission == MISSION_ID && cmd_config == CONFIG_ID
        && cmd_sequence > last_sequence && (!revoked_valid || cmd_issued > revoked)
        && cmd_issued <= now && cmd_issued <= cmd_not_before
        && cmd_not_before <= cmd_deadline && cmd_deadline < cmd_expires
        && now <= cmd_deadline && channel_good;
    wire bad_command = cmd_valid && !valid_payload;
    wire shadow_late = shadow && now > shadow_deadline;
    wire shadow_due = shadow && now >= shadow_not_before && !shadow_late
                     && (!revoked_valid || shadow_issued > revoked);
    // The calendar consumes this combinational pre-edge view. Therefore an
    // on-deadline command can affect the SAME edge; an alarm wins at that edge.
    assign permit_at_edge = channel_good && !bad_command && !shadow_late
        && ((active && now < active_expires) || shadow_due
            || (cmd_valid && valid_payload && now >= cmd_not_before));

    always @(posedge clk) begin
        command_ack <= cmd_valid;
        command_accepted <= cmd_valid && valid_payload;
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
            if (alarm_now || bad_command || shadow_late) begin
                active <= 0; shadow <= 0; healthy <= 0;
                revoked <= now; revoked_valid <= 1;
                command_accepted <= 0;
            end else begin
                if (recover) healthy <= 1;
                if (active && now >= active_expires) active <= 0;
                if (shadow_due && channel_good) begin
                    active <= 1; active_expires <= shadow_expires; shadow <= 0;
                end
                if (cmd_valid && valid_payload) begin
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

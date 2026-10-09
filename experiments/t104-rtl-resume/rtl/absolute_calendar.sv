// Absolute schedule, independent of backend duration and application load.
// now is a protected, free-running 64-bit xi timebase supplied by integration.
// skip_permitted must come from the atomic command/health gate, NOT raw CPU LOW.
// This module never generates a scientific LOW decision.
module absolute_calendar #(
    parameter integer WORD_BITS = 19,
    parameter integer KA = 3,
    parameter integer INVERSE = 174763, // inverse(3) modulo 2^19
    parameter integer G = 196, C = 164, LEAD = 320,
    parameter integer BATCH = 8, APP_OFFSET = 1312, APP_CHARGE = 240
)(
    input wire clk, cold_init, soft_reset,
    input wire [63:0] now,
    input wire skip_permitted, alarm, phase_bad, backend_busy,
    output reg phase_valid,
    output reg fault,
    output wire config_ok,
    output wire execute_due, app_due,
    output wire [WORD_BITS-1:0] word_due,
    output reg slot_pulse, execute_pulse, skip_pulse,
    output reg freeze_pulse, frozen_execute, app_window,
    output reg [63:0] slot_index, frozen_index,
    output reg [WORD_BITS-1:0] slot_word,
    output reg [63:0] cursor
);
    initial begin
        phase_valid=1; fault=0; slot_pulse=0; execute_pulse=0; skip_pulse=0;
        freeze_pulse=0; frozen_execute=0; app_window=0; slot_index=0;
        frozen_index=0; slot_word=0; cursor=0;
    end
    localparam [63:0] WORDS = 64'd1 << WORD_BITS;
    localparam [63:0] FRAME = BATCH * G;
    localparam [63:0] WRAP_GAP = BATCH * G - (BATCH - 1) * C;
    assign config_ok = WORD_BITS >= 3 && WORD_BITS <= 19 && KA == 3
                    && ((64'd3 * INVERSE) % WORDS == 1)
                    && G == 196 && C == 164 && LEAD == 320 && BATCH == 8
                    && APP_OFFSET == 1312 && APP_CHARGE == 240;
    reg booted = 0, seen_edge = 0;
    reg [63:0] last_time = 0;
    reg [63:0] next_start = 0, next_freeze = 8, next_app = APP_OFFSET;
    reg [63:0] freeze_cursor = 2;
    reg [2:0] start_pos = 0, freeze_pos = 2;
    reg [1:0] freeze_mod3 = 2;
    reg [WORD_BITS-1:0] address_cursor = 0;
    reg [3:0] decisions = 4'b1111;
    reg [3:0] valid_decisions = 4'b0011;
    wire time_ok = !seen_edge ? now == 0 : (now >= last_time && now-last_time == 4);
    wire must_execute = freeze_cursor < WORDS || freeze_mod3 == 0;
    wire decide_execute = must_execute || !skip_permitted || alarm || soft_reset
                        || !phase_valid || phase_bad || !time_ok || fault;
    // These pre-edge grants, not the post-edge telemetry pulses, drive the
    // backend. Connecting execute_pulse to go would delay every start by4xi.
    assign execute_due = booted && config_ok && now == next_start && !backend_busy
                        && (decisions[cursor[1:0]] || !valid_decisions[cursor[1:0]]);
    assign app_due = booted && config_ok && now == next_app && !backend_busy;
    assign word_due = address_cursor;

    always @(posedge clk) begin
        slot_pulse <= 0; execute_pulse <= 0; skip_pulse <= 0;
        freeze_pulse <= 0; app_window <= 0;
        if (cold_init && !booted) begin
            booted <= 1; seen_edge <= 0; last_time <= 0;
            next_start <= 0; next_freeze <= 8; next_app <= APP_OFFSET;
            cursor <= 0; freeze_cursor <= 2; start_pos <= 0; freeze_pos <= 2;
            freeze_mod3 <= 2; address_cursor <= 0;
            decisions <= 4'b1111; valid_decisions <= 4'b0011;
            phase_valid <= config_ok; fault <= !config_ok;
        end else if (booted && config_ok) begin
            seen_edge <= 1; last_time <= now;
            // A second hardware init is NOT a new mission. Preserve phase and
            // committed operations, expose loss of qualification explicitly.
            if (phase_bad || !time_ok || cold_init) begin
                phase_valid <= 0; fault <= 1;
            end
            if (now == next_freeze) begin
                freeze_pulse <= 1; frozen_index <= freeze_cursor;
                frozen_execute <= decide_execute;
                decisions[freeze_cursor[1:0]] <= decide_execute;
                valid_decisions[freeze_cursor[1:0]] <= 1;
                if (next_freeze > 64'hffffffffffffffff-WRAP_GAP
                    || freeze_cursor == 64'hffffffffffffffff) begin
                    phase_valid <= 0; fault <= 1;
                end else begin
                    freeze_cursor <= freeze_cursor + 1;
                    freeze_mod3 <= freeze_mod3 == 2 ? 0 : freeze_mod3 + 1;
                    next_freeze <= next_freeze + (freeze_pos == 7 ? WRAP_GAP : C);
                    freeze_pos <= freeze_pos + 1;
                end
            end
            if (now == next_start) begin
                slot_pulse <= 1; slot_index <= cursor; slot_word <= address_cursor;
                if (!valid_decisions[cursor[1:0]]) begin
                    fault <= 1; phase_valid <= 0;
                end
                // A committed skip is not revoked by a later alarm/reset.
                if (decisions[cursor[1:0]] || !valid_decisions[cursor[1:0]]) begin
                    if (!backend_busy) execute_pulse <= 1;
                    else begin fault <= 1; phase_valid <= 0; end
                end else skip_pulse <= 1;
                valid_decisions[cursor[1:0]] <= 0;
                if (next_start > 64'hffffffffffffffff-WRAP_GAP
                    || cursor == 64'hffffffffffffffff) begin
                    phase_valid <= 0; fault <= 1;
                end else begin
                    cursor <= cursor + 1;
                    address_cursor <= address_cursor + INVERSE;
                    next_start <= next_start + (start_pos == 7 ? WRAP_GAP : C);
                    start_pos <= start_pos + 1;
                end
            end
            if (now == next_app) begin
                app_window <= 1;
                if (next_app > 64'hffffffffffffffff-FRAME) begin
                    phase_valid <= 0; fault <= 1;
                end else next_app <= next_app + FRAME;
            end
        end
    end
endmodule

// T534. Address calendar derived from native64/core.sv at 03e12c9. All pin controls are registered.
// Cold is a commissioning input, asserted only before the first modeled read.
module scan_engine #(parameter ADAPTIVE=1, parameter PARTNER_PIN=5) (
    input wire clk, cold, loss,
    input wire err_in,
    input wire [15:0] dq_in,
    input wire app_request, input wire [16:0] app_address,
    output reg app_grant, app_valid, output reg [15:0] app_data,
    (* DONT_TOUCH="TRUE", IOB="FALSE" *) output reg [16:0] address,
    output wire select_n, oe_n, we_n,
    output reg drive,
    output wire [16:0] pad_address,
    output wire pad_select_n, pad_oe_n, pad_we_n,
    output wire [15:0] dq_out,
    (* DONT_TOUCH="TRUE" *) output reg [15:0] repair_image,
    output wire [15:0] pad_t_n,
    output wire capture_check, output wire captured_err,
    output reg protect_owner,
    output wire [3:0] issued,
    output wire [9:0] quiet,
    output reg sealed, report_send, output reg [17:0] count,
    output reg [35:0] epoch,
    output wire accepted_zero, command_strobe,
    output reg execution_fault
);
    reg running, active;
    (* DONT_TOUCH="TRUE", IOB="FALSE" *) reg selected, reading, writing;
    assign select_n=!selected; assign oe_n=!reading; assign we_n=!writing;
    (* DONT_TOUCH="TRUE" *) reg [7:0] phase_a, phase_inv;
    (* DONT_TOUCH="TRUE" *) reg phase_parity;
    wire phase_error = (phase_a != ~phase_inv) || (phase_parity != ^phase_a);
    wire [7:0] phase = (phase_parity == ^phase_a) ? phase_a : ~phase_inv;
    reg [15:0] frame;
    reg [7:0] wait_rounds;
    reg wait_parity;
    reg installed;
    wire [3:0] policy_level;
    // The current scan starts with FAST prearmed. An older slow command
    // may not authorize skips if this scan's installation pulse is lost.
    assign issued=(installed || command_strobe) ? policy_level : 4'd0;
    wire wrap_frame = phase == 139;
    // Fixed uses the exact 61,735-frame period, including quiet frames.
    wire last_scan_frame = frame == 16'd32767;
    wire last_period_frame = ADAPTIVE ? last_scan_frame : frame == 16'd61734;
    wire wrap_round = wrap_frame && last_period_frame;
    wire wait_ok = wait_parity == ^wait_rounds;
    wire next_active = active ? issued == 0 : (wait_rounds <= 1 || !wait_ok);
    wire [7:0] reload_wait = (8'd1 << issued) - 1'b1;
    wire [7:0] next_wait = active ? reload_wait :
                           (wait_rounds == 0 || !wait_ok ? 8'd0 : wait_rounds - 1'b1);
    wire scan_start = !running || (wrap_round && (!ADAPTIVE || next_active));
    wire common_end = epoch[6:0] == 0;
    wire cut = active && last_scan_frame && phase == 109;
    wire install = active && last_scan_frame && phase == 129;
    wire new_frame = !running || wrap_frame;
    wire [7:0] next_phase = new_frame ? 8'd0 : phase+1'b1;
    wire next_frame_active = ADAPTIVE ? (wrap_round ? next_active : active)
                                      : (wrap_round || (!last_scan_frame && active));
    wire start_visit = (new_frame && (!running || next_frame_active)) ||
                       (active && (phase == 23 || phase == 51 || phase == 75));
    wire [1:0] launch_lane = new_frame ? 2'd0 : phase == 23 ? 2'd1 :
                             phase == 51 ? 2'd2 : 2'd3;
    wire [14:0] launch_frame = (!running || wrap_round) ? 15'd0 :
                               (wrap_frame ? frame + 1'b1 : frame);

    // Exchange the partner pin at the outer boundary only. Logical address
    // and completion count retain calendar order in all four builds.
    function automatic [16:0] bus_map(input [16:0] j);
        begin
            bus_map=j;
            bus_map[PARTNER_PIN]=j[16];
            bus_map[16]=j[PARTNER_PIN];
        end
    endfunction

    // A shifted token is independent of the frame phase. Capture requires
    // both witnesses; a missing capture invalidates this service.
    reg [19:0] visit_token;
    reg sampled, committed, damaged;
    // Complementary obligations are derived from a single captured ERR.
    // In a protected build each service replica has its own capture register.
    (* DONT_TOUCH="TRUE" *) reg sampled_err;
    assign captured_err=sampled_err;
    assign capture_check=^repair_image;
    (* DONT_TOUCH="TRUE" *) reg repair_a, repair_b;
    reg [17:0] seen;
    reg scan_bad, app_owner;
    wire sample_phase = phase == 5 || phase == 29 || phase == 57 || phase == 81;
    wire capture = protect_owner && visit_token[5] && sample_phase;
    wire missed_sample = protect_owner && visit_token[5] && !sample_phase;
    wire owes_write = repair_a || !repair_b;
    wire complete_read = protect_owner && visit_token[9] && !owes_write;
    wire complete_write = protect_owner && visit_token[19] && owes_write;
    reg [16:0] app_candidate;
    wire app_begin = phase==101 && app_request && !protect_owner;
    wire release_visit = complete_read || complete_write;
    wire addressed = seen == {1'b0,address};
    wire write_committed = committed && we_n && !drive;
    wire good_release = sampled && !damaged && addressed && !select_n &&
                        (!owes_write || write_committed) && !sealed;
    wire witness_disagrees = protect_owner && sampled && !visit_token[6] && (repair_a == repair_b);
    wire extra_write = !we_n && !owes_write;
    wire broken = phase_error || missed_sample || witness_disagrees || extra_write ||
                  (release_visit && !good_release);
    wire history_fault;
    generate if (ADAPTIVE) begin: adaptive
    native_rule policy (
        .clk(clk), .cold(cold), .scan_start(scan_start), .common_end(common_end),
        .cut(cut), .install(install), .epoch(epoch),
        .packet(report_send), .packet_complete(sealed), .packet_epoch(epoch),
        .packet_count(count), .sealed(sealed),
        .scan_bad(scan_bad && !scan_start), .actual_count(count),
        .loss(loss || broken || (!active && !wait_ok) || (wrap_round && active && !installed) ||
              (protect_owner && visit_token[6] && sampled_err)),
        .issued(policy_level), .quiet(quiet), .accepted_zero(accepted_zero),
        .command_strobe(command_strobe), .history_fault(history_fault)
    );

    end else begin: fixed
        assign policy_level=0;
        assign quiet=0;
        assign accepted_zero=0;
        assign command_strobe=0;
        assign history_fault=0;
    end endgenerate

    always @(posedge clk) begin
        if (cold) begin
            running<=0; active<=1; phase_a<=0; phase_inv<=8'hff; phase_parity<=0;
            frame<=0; epoch<=0;
            installed<=0;
            wait_rounds<=0; wait_parity<=0; visit_token<=0;
            address<=0; selected<=0; reading<=0; writing<=0; drive<=0;
            protect_owner<=0; app_owner<=0; app_grant<=0; app_valid<=0;
            sampled<=0;
            repair_a<=0;repair_b<=1;
            committed<=0; damaged<=0; seen<=0; count<=0; sealed<=0;
            scan_bad<=0; report_send<=0; execution_fault<=0;
        end else begin
            running<=1;
            report_send<=0; app_grant<=0; app_valid<=0;
            if(command_strobe) installed<=1;
            phase_a<=next_phase; phase_inv<=~next_phase; phase_parity<=^next_phase;
            if (running && wrap_frame) frame<=wrap_round ? 16'd0 : frame+1'b1;
            if (!ADAPTIVE && wrap_frame && last_scan_frame) active<=0;
            if (wrap_round && running) begin
                active<=ADAPTIVE ? next_active : 1'b1; epoch<=epoch+1'b1;
                wait_rounds<=next_wait; wait_parity<=^next_wait;
            end
            if (scan_start) begin
                installed<=0;
                seen<=0; count<=0; sealed<=0; scan_bad<=0;
            end
            visit_token<={visit_token[18:0],start_visit};
            if (start_visit) begin
                address<={launch_frame,launch_lane}; protect_owner<=1;
                selected<=1; reading<=1; writing<=0; drive<=0;
                sampled<=0;
                committed<=0; damaged<=0;
            end
            if (capture) begin
                sampled<=1;
            end
            if (protect_owner && visit_token[6]) begin
                reading<=0;repair_a<=sampled_err;repair_b<=!sampled_err;
            end
            if (broken || history_fault || (ADAPTIVE && !active && !wait_ok)) execution_fault<=1;
            if (broken) begin scan_bad<=1; damaged<=1; end
            // The rule samples the old scan_bad and any current broken/loss
            // on this edge. Its validity decision is then latched in invalid.
            // Consume the closed scan's flag; later faults still set it anew.
            if (cut) scan_bad<=0;
            if (protect_owner && visit_token[9] && owes_write) drive<=1;
            if (protect_owner && visit_token[10] && owes_write) writing<=1;
            if (protect_owner && visit_token[15] && !we_n && drive && !select_n) begin
                writing<=0; committed<=1;
            end
            if (protect_owner && visit_token[17]) drive<=0;
            if (release_visit) begin
                protect_owner<=0; selected<=0; reading<=0; writing<=0; drive<=0;
                if (good_release) begin
                    seen<=seen+1'b1;
                    count<=count+{17'd0,owes_write};
                    if (&address) begin
                        sealed<=!scan_bad && !broken;
                        report_send<=!scan_bad && !broken;
                    end
                end
            end

            // Only reads are admitted for the long-lived payload. The
            // application never changes the protection report or the repair.
            if (phase==100) app_candidate<=app_address;
            if (app_begin) begin
                app_grant<=1; app_owner<=1; address<=app_candidate;
                selected<=1; reading<=1;
            end
            if (app_owner && phase==108) reading<=0;
            if (app_owner && phase==111) begin selected<=0; app_valid<=1; end
            if (phase==125) app_owner<=0;
        end
    end
    // Capture exactly once at +60 ns; hold this image through WE# rising.
    reg drive_next=0;
    // Independent idle values allow the address pad FF to reload each edge.
    // During every owned transaction its D equals the registered witness.
    // Inputs to the final I/O FFs. Vote these before the original edge;
    // moving a register past that edge would change the SRAM contract.
    assign pad_address=cold ? 17'd0 : start_visit ? bus_map({launch_frame,launch_lane}) :
                     app_begin ? bus_map(app_candidate) : (protect_owner || app_owner) ? bus_map(address) : 17'd0;
    assign pad_select_n=cold || !(start_visit || app_begin || (selected && !release_visit && !(app_owner && phase==111)));
    assign pad_oe_n=cold || !(start_visit || app_begin || (reading && !release_visit && !(protect_owner && visit_token[6]) && !(app_owner && phase==108)));
    assign pad_we_n=cold || !(!release_visit && !start_visit && ((protect_owner && visit_token[10] && owes_write) ||
                    (writing && !(protect_owner && visit_token[15] && drive && selected))));
    assign dq_out=repair_image;
    assign pad_t_n={16{!drive_next}};
    always @(posedge clk) begin
        if (capture) sampled_err<=err_in;
        if (capture || (app_owner && phase==107)) repair_image<=dq_in;
        if (app_owner && phase==108) app_data<=repair_image;
        if(cold || visit_token[16]) drive_next<=0;
        else if(protect_owner && visit_token[8]) drive_next<=owes_write;
    end
endmodule

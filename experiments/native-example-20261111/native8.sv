// Native local-register demonstrator: eight x16 addresses in two frames.
module native8 #(parameter CHECK_LOCAL = 1) (
    input wire clk, reset, err_in,
    input wire [15:0] dq_in,
    input wire release_ok, report_ok, install_ok,
    output wire [2:0] addr,
    output wire selected, oe_n, we_n, drive,
    output reg [15:0] dq_out,
    output reg sealed,
    output reg [3:0] count,
    output reg [8:0] step
);
    reg [7:0] phase, round_phase;
    reg frame, active, hit;
    reg [8:0] gap, remaining, proposed;
    reg remaining_parity;
    reg [3:0] seen;
    reg poisoned, started, spoiled, any_err;
    reg [9:0] quiet;
    wire common_end = round_phase == 0;
    wire [9:0] next_quiet = !started || spoiled ? 10'd0 :
                            (quiet < 596 ? quiet+10'd1 : quiet);

    wire [1:0] lane = phase < 24 ? 0 : phase < 52 ? 1 : phase < 76 ? 2 : 3;
    wire [7:0] age = phase - (lane==0 ? 8'd0 : lane==1 ? 8'd24 :
                              lane==2 ? 8'd52 : 8'd76);
    localparam [7:0] SAMPLE_TICK=6, READ_RELEASE_TICK=10, WRITE_RELEASE_TICK=20;
    localparam [7:0] CUT_TICK=110, INSTALL_TICK=130;  // in the second frame
    assign addr = {frame,lane};
    assign selected = active && (age<READ_RELEASE_TICK || (hit && age<WRITE_RELEASE_TICK));
    assign oe_n = !(active && age<7);
    assign drive = active && hit && age>=READ_RELEASE_TICK && age<18;
    assign we_n = !(drive && age>=11 && age<16);
    // Pins decode the current tick. A clocked update entering tick k
    // sees k-1 before the phase register advances on that same edge.
    wire sample_visit = active && (age == SAMPLE_TICK - 8'd1);
    wire release_visit = active && (hit ? age == WRITE_RELEASE_TICK - 8'd1 :
                                          age == READ_RELEASE_TICK - 8'd1);
    wire cut_report = active && frame && (phase == CUT_TICK - 8'd1);
    wire install_command = active && frame && (phase == INSTALL_TICK - 8'd1);
    wire good_zero = report_ok && sealed && !poisoned && count==0 &&
                     (!CHECK_LOCAL || !any_err);

    function automatic allowed_gap(input [8:0] value);
        case (value)
            1, 2, 4, 8, 16, 32, 64, 128, 256: allowed_gap=1;
            default: allowed_gap=0;
        endcase
    endfunction
    wire valid_proposal = !CHECK_LOCAL || allowed_gap(proposed);
    wire valid_installed = !CHECK_LOCAL || allowed_gap(gap);
    wire valid_wait = !CHECK_LOCAL || ((^remaining)==remaining_parity);
    wire [8:0] initial_wait = valid_installed ? gap-9'd1 : 9'd0;
    wire [8:0] shorter_wait = remaining==0 ? 9'd0 : remaining-9'd1;

    function automatic [8:0] quiet_step(input [9:0] cells);
        if      (cells>=596) quiet_step=256;
        else if (cells>=298) quiet_step=128;
        else if (cells>=149) quiet_step=64;
        else if (cells>=75)  quiet_step=32;
        else if (cells>=38)  quiet_step=16;
        else if (cells>=19)  quiet_step=8;
        else if (cells>=10)  quiet_step=4;
        else if (cells>=5)   quiet_step=2;
        else                 quiet_step=1;
    endfunction

    always @(posedge clk) begin
        if (reset) begin
            phase<=0; frame<=0; round_phase<=0; active<=1; hit<=0;
            gap<=1; remaining<=0; remaining_parity<=0; step<=1; proposed<=1;
            seen<=0; count<=0; sealed<=0; poisoned<=0; dq_out<=0;
            started<=0; spoiled<=0; quiet<=0; any_err<=0;
        end else begin
            if (phase==139) begin
                phase<=0;
                frame<=!frame;
                if (frame) begin
                    round_phase<=round_phase+1'b1;
                    if (active) begin
                        active<=gap==1 || !valid_installed;
                        remaining<=initial_wait; remaining_parity<=^initial_wait;
                        if (!valid_installed) begin
                            step<=1; quiet<=0; spoiled<=!common_end;
                        end
                    end else begin
                        active<=!valid_wait || remaining<=1;
                        if (valid_wait) begin
                            remaining<=shorter_wait; remaining_parity<=^shorter_wait;
                        end else begin
                            remaining<=0; remaining_parity<=0; step<=1;
                            quiet<=0; spoiled<=!common_end;
                        end
                    end
                    gap<=1;  // preinstalled fast on the next active scan
                    seen<=0; count<=0; sealed<=0; poisoned<=0; any_err<=0;
                end
            end else phase<=phase+1'b1;
            if (active && age==0) hit<=0;
            if (sample_visit) begin
                hit<=err_in; dq_out<=dq_in;
                if (err_in) any_err<=1;
            end
            if (release_visit) begin
                if (!release_ok || {1'b0,addr}!=seen || sealed) begin
                    poisoned<=1; sealed<=0;
                end else begin
                    seen<=seen+1'b1;
                    count<=count+hit;
                    if (addr==7 && !poisoned) sealed<=1;
                end
            end
            if (cut_report) begin // cut at L-300 ns
                if (!good_zero) begin
                    proposed<=1; quiet<=0; spoiled<=!common_end;
                end else if (common_end) begin
                    proposed<=quiet_step(next_quiet);
                    quiet<=next_quiet; spoiled<=0;
                end else proposed<=step;
                if (common_end) started<=1;
            end
            if (install_command) begin // install 200 ns later
                if (install_ok && valid_proposal) begin step<=proposed; gap<=proposed; end
                else begin step<=1; gap<=1; quiet<=0; spoiled<=!common_end; end
            end
        end
    end
endmodule

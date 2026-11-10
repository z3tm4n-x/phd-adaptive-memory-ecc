`timescale 1ns/1ps
// Behavioural adapter for the reduced controller, not a routed production top.
// tick is a local 10ns clock index. It is not a radiation/environment input.
module native #(parameter A=8)(
    input wire clk, input wire [63:0] tick,
    input wire err_pin, input wire [15:0] dq_pin,
    // Physical interface and observation-channel test boundary.
    input wire [31:0] pin_address, input wire write_exec_ok,
    input wire token_drop, token_repeat,
    input wire rx_valid, rx_complete, input wire [63:0] rx_epoch,
    input wire [31:0] rx_count, input wire install_lost,
    input wire app_probe,
    output wire [31:0] requested_address, output wire other_ready
);
    localparam L=A/4*140, CUT=L-30, INSTALL=CUT+20;
    wire [63:0] round_no=tick/L;
    wire [31:0] rt=tick%L, phase=tick%140;
    reg [63:0] next_round=0, active_round=64'hffff_ffff_ffff_ffff;
    wire beginning=(round_no==next_round && rt==0);
    wire active=(active_round==round_no || beginning);
    wire launch=active && (phase==0 || phase==24 || phase==52 || phase==76);
    assign requested_address=4*(rt/140)+(phase==24?1:phase==52?2:phase==76?3:0);

    reg locked=0,sampled=0,hit=0,wrote=0;
    reg [31:0] addr=0; reg [63:0] tag=0, start_tick=0;
    reg [15:0] image=0;
    wire [63:0] age=tick-start_tick;
    wire sample=locked && age==6, write_end=locked && hit && age==16;
    wire release_event=locked && age==(hit?20:10);
    // Owner INCLUDING turnaround/release, not just the WE low pulse.
    // No management requester feeds the port. 'other_ready' is availability
    // to the arbiter, not permission to exceed the application's envelope.
    wire read_owner=launch || (locked && age<10);
    wire repair_owner=locked && hit && age>=10 && age<20;
    assign other_ready=!launch && (!locked || release_event);
    wire app_grant=other_ready && app_probe && phase==102;
    wire writing=locked && hit && age>=11 && age<16;

    // Dense ascending traversal: the next expected address and pass epoch suffice.
    // Ignored old reports and repeated RELEASE tokens are different interfaces.
    reg [31:0] seen=0, count=0, last_addr=0;
    reg [63:0] last_tag=0;
    reg sealed=0, poison=0;
    reg got=0, conflict=0; reg [31:0] packet_count=0;
    wire packet_here=rx_valid && rx_complete && rx_epoch==round_no && active && rt<=CUT;
    wire disagree=packet_here && got && packet_count!=rx_count;
    wire timely=(got || packet_here) && !conflict && !disagree && sealed && !poison;
    wire [31:0] taken_count=got?packet_count:rx_count;
    reg [31:0] step=1, chosen=1, temp_step;
    reg [63:0] last_bad=0, chosen_bad=0, temp_bad;
    reg cut_bad=0; reg [31:0] cut_count=0;
    wire cutting=active && rt==CUT, installing=active && rt==INSTALL;

    always @(posedge clk) begin
        if(beginning) begin
            active_round<=round_no;next_round<=round_no+1; // preinstalled FAST
            seen<=0;count<=0;sealed<=0;poison<=0;got<=0;conflict<=0;
        end
        if(launch) begin
            if(locked) $fatal(1,"overlapping native transactions");
            locked<=1;start_tick<=tick;addr<=pin_address;tag<=round_no;
            sampled<=0;hit<=0;wrote<=0;
        end
        if(sample) begin sampled<=1;hit<=err_pin;image<=dq_pin;end
        if(write_end) wrote<=write_exec_ok;
        if(release_event) begin
            locked<=0;last_tag<=tag;last_addr<=addr;
            if(!token_drop) begin
                if(!sampled || (hit && !wrote) || tag!=round_no || addr!=seen || sealed) begin
                    poison<=1;sealed<=0;
                end else begin
                    seen<=seen+1;count<=count+hit;
                    if(seen==A-1 && !poison) sealed<=1; // count includes this release
                end
            end
        end
        if(token_repeat && active && last_tag==round_no) begin
            // Replay of the last completion cannot advance the cursor.
            if(last_addr!=seen) begin poison<=1;sealed<=0;end
        end
        if(packet_here) begin
            if(!got) begin got<=1;packet_count<=rx_count;end
            else if(disagree) conflict<=1;
        end
        if(cutting) begin
            cut_bad<=!timely;cut_count<=timely?taken_count:0;
            $native_choose(L*10,round_no,timely && taken_count!=0,!timely,
                           step,last_bad,temp_step,temp_bad);
            chosen<=temp_step;chosen_bad<=temp_bad;
        end
        if(installing) begin
            if(install_lost) begin
                $native_choose(L*10,round_no,1'b0,1'b1,step,last_bad,temp_step,temp_bad);
                step<=1;last_bad<=temp_bad; // preset stands, expired command never retried
            end else begin
                step<=chosen;last_bad<=chosen_bad;next_round<=round_no+chosen;
            end
        end
    end
endmodule

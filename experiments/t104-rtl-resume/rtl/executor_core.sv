// Single memory-clock arbiter with two per-source credits. The requests and
// retire pulses here have ALREADY crossed the RPC bridge. No input can bypass
// the absolute calendar or cancel a pending backend operation.
module executor_core #(
    parameter integer WORD_BITS=19,
    parameter integer INVERSE=174763
)(
    input wire clk, soft_reset, loss, recover, start_ok,
    input wire cfg_wr, cfg_commit,
    input wire [3:0] cfg_address,
    input wire [31:0] cfg_data,
    input wire [1:0] request_valid,
    input wire [511:0] request_payload,
    output wire [1:0] request_ready,
    input wire [1:0] retire,
    output wire [1:0] reply_valid,
    output wire [193:0] reply_payload,
    input wire command_valid, command_integrity,
    input wire [383:0] command_payload,
    output wire command_accepted,
    input wire [15:0] dq_in,
    input wire err_in,
    output wire ce, oe, we, drive, alias_high,
    output wire [1:0] byte_enable,
    output wire [15:0] dq_out,
    output wire [WORD_BITS-1:0] word_out,
    output wire busy, pending, flag, done, commit_pulse,
    output wire [63:0] err_count,
    output reg [63:0] now,
    output wire [63:0] time_gray,
    output reg running,
    output wire config_locked, config_compatible, phase_valid,
    output wire fault,
    output wire [3:0] queue_state,
    output wire app_grant,
    output wire [1:0] grant_kind,
    output wire grant_owner,
    output wire [63:0] slot_index,
    output wire slot_pulse, skip_pulse
);
    wire arm, config_fault, calendar_fault, backend_fault, config_ok;
    initial begin now=0; running=0; end
    reg time_fault=0, queue_fault=0;
    service_config #(.WORD_BITS(WORD_BITS),.INVERSE(INVERSE)) configuration(
        .clk(clk),.wr(cfg_wr),.commit(cfg_commit),.start_ok(start_ok),
        .address(cfg_address),.data(cfg_data),.arm_due(arm),.locked(config_locked),
        .fault(config_fault),.compatible(config_compatible));
    // Gray encode the core-edge counter, not a binary multi-bit CDC bus.
    reg [63:0] published_time=0;
    assign time_gray=(published_time>>2)^((published_time>>2)>>1);
    always @(posedge clk) begin
        if (arm) begin running<=1; now<=0; end
        else if(running) begin
            published_time<=now;
            if(now>64'hfffffffffffffffb) time_fault<=1;
            else now<=now+4;
        end
    end
    wire permit, healthy, overflow, err_due, release_due;
    wire command_ack, active, shadow;
    wire [63:0] last_sequence;
    wire new_queue_loss;
    wire alarm = loss || time_fault || config_fault || queue_fault || new_queue_loss;
    permission_gate gate(
        .clk(clk),.cold_init(arm),.soft_reset(soft_reset),.loss(alarm),
        .err_event(err_due),.recover(recover),.now(now),
        .cmd_valid(command_valid && running),.cmd_integrity(command_integrity),
        .cmd_mission(command_payload[31:0]),.cmd_config(command_payload[63:32]),
        .cmd_sequence(command_payload[127:64]),.cmd_issued(command_payload[191:128]),
        .cmd_not_before(command_payload[255:192]),.cmd_deadline(command_payload[319:256]),
        .cmd_expires(command_payload[383:320]),.command_ack(command_ack),
        .command_accepted(command_accepted),.permit_at_edge(permit),
        .active(active),.shadow(shadow),.healthy(healthy),.overflow(overflow),
        .err_count(err_count),.last_sequence(last_sequence));
    wire control_due, app_due, execute_pulse, freeze_pulse, frozen_execute, app_window;
    wire [63:0] frozen_index, cursor;
    wire [WORD_BITS-1:0] control_word, slot_word;
    absolute_calendar #(.WORD_BITS(WORD_BITS),.INVERSE(INVERSE)) calendar(
        .clk(clk),.cold_init(arm),.soft_reset(soft_reset),.now(now),
        .skip_permitted(permit),.alarm(alarm || err_due),.phase_bad(time_fault),
        .backend_busy(busy),.phase_valid(phase_valid),.fault(calendar_fault),
        .config_ok(config_ok),.execute_due(control_due),.app_due(app_due),
        .word_due(control_word),.slot_pulse(slot_pulse),.execute_pulse(execute_pulse),
        .skip_pulse(skip_pulse),.freeze_pulse(freeze_pulse),.frozen_execute(frozen_execute),
        .app_window(app_window),.slot_index(slot_index),.frozen_index(frozen_index),
        .slot_word(slot_word),.cursor(cursor));
    // EMPTY0 / QUEUED1 / ACTIVE2 / REPLY3. REPLY remains occupied until the
    // SOURCE consumes it and its acknowledgement has crossed back.
    reg [1:0] state [0:1];
    reg [223:0] request [0:1];
    reg [63:0] last_id [0:1];
    reg [1:0] seen_id=0;
    reg [1:0] error_reply=0;
    reg [63:0] last_offer=0;
    reg seen_offer=0;
    reg active_app=0, owner=0;
    reg [31:0] result [0:1];
    integer i;
    initial for(i=0;i<2;i=i+1) begin
        state[i]=0; request[i]=0; last_id[i]=0; result[i]=0;
    end
    function [31:0] crc224;
        input [223:0] bits;
        reg [31:0] c;
        integer k;
        begin
            c=32'hffffffff;
            for(k=0;k<224;k=k+1)
                c=(c>>1)^((c[0]^bits[k]) ? 32'hedb88320 : 32'd0);
            crc224=~c;
        end
    endfunction
    wire [255:0] p0=request_payload[255:0], p1=request_payload[511:256];
    wire [1:0] capture=request_valid & request_ready;
    function bad_request;
        input [255:0] value;
        input seen;
        input [63:0] previous;
        begin
            bad_request=crc224(value[223:0])!=value[255:224]
                || (value[1:0]!=1 && value[1:0]!=2)
                || value[7:4]==0 || (value[31:0]&32'hffffff0c)!=0
                || value[63:32]>=(32'd1<<WORD_BITS) || value[223:160]>now
                || (seen && value[159:96]<=previous);
        end
    endfunction
    wire [1:0] bad={bad_request(p1,seen_id[1],last_id[1]),bad_request(p0,seen_id[0],last_id[0])};
    // Allow48xi timestamp uncertainty; do NOT reject a conforming near-boundary
    // stream merely because the two Gray samples have different phase lag.
    wire close0=seen_offer && (p0[223:160]<last_offer || p0[223:160]-last_offer<5508);
    wire close1=seen_offer && (p1[223:160]<last_offer || p1[223:160]-last_offer<5508);
    // Same-edge loss priority: do not wait for the sticky diagnostic register
    // before a freeze decision at this edge.
    assign new_queue_loss=|(capture & bad) || (&capture)
                          || (capture[0] && close0) || (capture[1] && close1);
    assign request_ready={running && state[1]==0,running && state[0]==0};
    assign queue_state={state[1],state[0]};
    wire queued0=state[0]==1, queued1=state[1]==1;
    // Timestamps are conservative lower bounds; CPU wins exact ties.
    assign grant_owner=!queued0 || (queued1 && request[1][223:160]<request[0][223:160]);
    assign app_grant=running && app_due && !control_due && (queued0 || queued1);
    wire [223:0] chosen=request[grant_owner];
    assign grant_kind=control_due ? 2'd0 : chosen[1:0];
    wire go=running && (control_due || app_grant);
    wire [31:0] read_data;
    wire accepted, rejected, ready, sample;
    wire [7:0] age;
    e_backend #(.WORD_BITS(WORD_BITS)) backend(
        .clk(clk),.cold_init(arm),.soft_reset(soft_reset),.go(go),.kind(grant_kind),
        .word_in(control_due ? control_word : chosen[32+:WORD_BITS]),
        .data_in(control_due ? 32'd0 : chosen[95:64]),
        .byte_enable_in(control_due ? 4'hf : chosen[7:4]),
        .dq_in(dq_in),.err_in(err_in),.ready(ready),.busy(busy),
        .accepted(accepted),.rejected(rejected),.fault(backend_fault),
        .word_out(word_out),.ce(ce),.oe(oe),.we(we),.drive(drive),
        .alias_high(alias_high),.byte_enable(byte_enable),.dq_out(dq_out),
        .sample(sample),.flag(flag),.err_due(err_due),.done(done),
        .release_due(release_due),.commit_pulse(commit_pulse),.pending(pending),
        .read_data(read_data),.age(age));
    // Reply payload: request ID64, data32, bad-input bit. A normal reply is
    // latched into the return CDC on the SAME edge as the physical release.
    genvar p;
    generate for(p=0;p<2;p=p+1) begin: replies
        assign reply_valid[p]=(release_due && active_app && owner==p)
                             || (state[p]==3 && error_reply[p]);
        assign reply_payload[p*97+:97]={error_reply[p],
            state[p]==2 ? read_data : result[p],request[p][159:96]};
    end endgenerate
    assign fault=config_fault || calendar_fault || backend_fault || time_fault
                 || queue_fault || overflow;
    reg [255:0] incoming;
    reg malformed;
    always @(posedge clk) begin
        for(i=0;i<2;i=i+1) begin
            if(capture[i]) begin
                incoming=i==0 ? p0 : p1;
                malformed=bad[i];
                request[i]<=incoming[223:0]; result[i]<=0;
                state[i]<=malformed ? 3 : 1;
                error_reply[i]<=malformed;
                if(malformed) queue_fault<=1;
                // A rejected/replayed packet cannot rewind the high-water ID.
                if(!malformed) begin last_id[i]<=incoming[159:96]; seen_id[i]<=1; end
                // This necessary monitor is not an envelope certificate.
                if(i==0 ? close0 : close1) queue_fault<=1;
                last_offer<=incoming[223:160]; seen_offer<=1;
            end
            if(retire[i]) begin
                if(state[i]!=3) queue_fault<=1;
                else begin state[i]<=0; error_reply[i]<=0; end
            end
        end
        if(&capture) queue_fault<=1; // simultaneous CPU/X violates joint b=1
        if(go) begin
            active_app<=app_grant;
            if(app_grant) begin owner<=grant_owner; state[grant_owner]<=2; end
        end
        if(release_due && active_app) begin
            state[owner]<=3; result[owner]<=read_data;
        end
        if(rejected) queue_fault<=1;
        if(soft_reset && running) queue_fault<=1;
    end
endmodule

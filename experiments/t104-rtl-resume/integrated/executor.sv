// Complete functional two-domain executor, with separate application, history
// and candidate paths. SRAM E is the proven registered backend, unchanged.
module integrated_executor #(
    parameter integer WORD_BITS=19,INVERSE=174763,
    parameter [33:0] NW=34'd4500045002,NH=34'd9000090002,NR=34'd9015504896,
    parameter [63:0] PAIR_WINDOW=64'd22500225010
)(
    input wire fast_clk,slow_clk,startup_rst_fast,startup_rst_slow,
    input wire qualified_start,loss_slow,
    input wire [1:0] request_valid,
    output wire [1:0] request_ready,
    input wire [241:0] request_data,
    output wire [1:0] response_valid,input wire [1:0] response_ready,
    output wire [96:0] response_data,
    input wire [15:0] dq_in,input wire err_in,
    output wire [WORD_BITS-1:0] word_out,
    output wire ce,oe,we,drive,alias_high,
    output wire [1:0] byte_enable,output wire [15:0] dq_out,
    output wire running,busy,pending,err_due,release_due,
    output wire grant_debug,app_grant_debug,
    output wire [56:0] grant_data_debug,
    output wire slot_pulse,skip_pulse,freeze_pulse,frozen_execute,
    output wire [63:0] generation,processed_generation,
    output wire rule_low,candidate_permit,
    output wire [33:0] short_left,long_left,recovery_left,
    output wire [31:0] frame_id,
    output wire [1:0] credits_debug,
    output wire fault
);
    // Slow application admission: two total credits including returned-but-
    // unconsumed replies. CPU wins simultaneous offers; aggregate envelope
    // still applies to first VALID, not to the arbitrarily delayed handshake.
    wire [120:0] req0=request_data[120:0],req1=request_data[241:121];
    wire owner=!request_valid[0];
    wire [120:0] chosen=owner?req1:req0;
    wire legal=(chosen[1:0]==1 || chosen[1:0]==2) && chosen[56:53]!=0 &&
               chosen[20:2]<(20'd1<<WORD_BITS);
    reg [1:0] credits=0;
    wire running_slow;
    wire forward_capacity,id_capacity,id_valid,returned_valid;
    wire [64:0] id_data;
    wire [32:0] returned_data;
    wire can_accept=running_slow && !startup_rst_slow && credits<2 && forward_capacity && id_capacity && legal;
    assign request_ready={can_accept && owner,can_accept && !owner};
    wire capture=|(request_valid & request_ready);
    wire consume=returned_valid && id_valid && response_ready[id_data[64]];
    assign response_valid={returned_valid && id_valid && id_data[64],
                           returned_valid && id_valid && !id_data[64]};
    assign response_data={id_data[63:0],returned_data};
    assign credits_debug=credits;
    always @(posedge slow_clk) begin
        case({capture,consume})
            2'b10:credits<=credits+1'b1;
            2'b01:credits<=credits-1'b1;
            default:credits<=credits;
        endcase
    end
    wire forward_valid,forward_ready,fw_wbusy,fw_rbusy;
    wire [56:0] forward_data;
    wire id_wbusy,id_rbusy;
    async_queue #(.WIDTH(57)) app_requests(
        .wr_clk(slow_clk),.rd_clk(fast_clk),.rst(startup_rst_slow),.rd_rst(startup_rst_fast),
        .in_valid(capture),.in_ready(forward_capacity),.in_data(chosen[56:0]),
        .out_valid(forward_valid),.out_ready(forward_ready),.out_data(forward_data),
        .wr_busy(fw_wbusy),.rd_busy(fw_rbusy));
    slow_queue #(.WIDTH(65)) app_ids(.clk(slow_clk),.rst(startup_rst_slow),
        .in_valid(capture),.in_ready(id_capacity),.in_data({owner,chosen[120:57]}),
        .out_valid(id_valid),.out_ready(consume),.out_data(id_data),
        .wr_busy(id_wbusy),.rd_busy(id_rbusy));
    reg [56:0] app_snapshot=0,app_command=0,backend_command=57'h1e0000000000000;
    reg app_receipt=0,app_waiting=0,app_prepared=0;
    reg active_app=0,observed_err=0,reply_pending=0;
    reg [32:0] reply=0;
    wire return_ready,return_wbusy,return_rbusy;
    async_queue #(.WIDTH(33),.SLOW_SOURCE(0)) app_responses(
        .wr_clk(fast_clk),.rd_clk(slow_clk),.rst(startup_rst_fast),.rd_rst(startup_rst_slow),
        .in_valid(reply_pending),.in_ready(return_ready),.in_data(reply),
        .out_valid(returned_valid),.out_ready(consume),.out_data(returned_data),
        .wr_busy(return_wbusy),.rd_busy(return_rbusy));
    assign forward_ready=!app_waiting && !app_receipt;
    wire start_fast,loss_fast;
    xpm_cdc_single #(.DEST_SYNC_FF(3),.SRC_INPUT_REG(1),.INIT_SYNC_FF(1)) start_cdc(
        .src_clk(slow_clk),.src_in(qualified_start),.dest_clk(fast_clk),.dest_out(start_fast));
    xpm_cdc_single #(.DEST_SYNC_FF(3),.SRC_INPUT_REG(1),.INIT_SYNC_FF(1)) loss_cdc(
        .src_clk(slow_clk),.src_in(loss_slow),.dest_clk(fast_clk),.dest_out(loss_fast));
    // The recovery timer begins after the actual calendar start, never a
    // few CDC cycles before mission t0. This only extends the initial hold.
    xpm_cdc_single #(.DEST_SYNC_FF(3),.SRC_INPUT_REG(1),.INIT_SYNC_FF(1)) running_cdc(
        .src_clk(fast_clk),.src_in(running),.dest_clk(slow_clk),.dest_out(running_slow));

    // Generation packet is emitted on the same edge as the local veto. A
    // loss FALL is also a history change (recovery), with no mission reset.
    reg previous_loss=0,history_overflow=0;
    wire history_change=running && (err_due || loss_fast!=previous_loss);
    wire [63:0] generation_next,uptime;
    wire generation_full,uptime_full;
    segmented_counter version(.clk(fast_clk),.inc(history_change),.value(generation),
        .next_value(generation_next),.exhausted(generation_full));
    segmented_counter timestamp(.clk(fast_clk),.inc(running),.value(uptime),
        .next_value(),.exhausted(uptime_full));
    wire event_ready,event_valid,event_wbusy,event_rbusy;
    wire [129:0] event_data;
    reg event_capture=0,event_write=0;
    reg [65:0] event_snapshot=0;
    reg [129:0] event_staged=0;
    // Two registers BEFORE the FIFO, never inside E. At event_capture the
    // generation register already includes exactly the captured event edge.
    // Consecutive events are pipelined, not coalesced across distinct edges.
    always @(posedge fast_clk) begin
        event_capture<=history_change;
        event_snapshot<={uptime,loss_fast,err_due};
        event_write<=event_capture;
        event_staged<={generation,event_snapshot};
    end
    event_fifo history(.wr_clk(fast_clk),.rd_clk(slow_clk),.rst(startup_rst_fast),
        .in_valid(event_write),.in_ready(event_ready),.in_data(event_staged),
        .out_valid(event_valid),.out_ready(1'b1),.out_data(event_data),
        .wr_busy(event_wbusy),.rd_busy(event_rbusy));
    always @(posedge fast_clk) begin
        if(running) previous_loss<=loss_fast;
        if(event_write && !event_ready) history_overflow<=1;
    end
    wire history_fault_slow,rule_fault,rule_fault_fast;
    xpm_cdc_single #(.DEST_SYNC_FF(3),.SRC_INPUT_REG(1),.INIT_SYNC_FF(1)) history_fault_cdc(
        .src_clk(fast_clk),.src_in(history_overflow),.dest_clk(slow_clk),.dest_out(history_fault_slow));
    slow_rule #(.NW(NW),.NH(NH),.NR(NR),.PAIR_WINDOW(PAIR_WINDOW)) rule(
        .clk(slow_clk),.start(running_slow),.event_valid(event_valid),.event_data(event_data),
        .history_fault(history_fault_slow),.processed_generation(processed_generation),
        .low(rule_low),.short_left(short_left),.long_left(long_left),.recovery_left(recovery_left),
        .healthy(),.started(),.fault(rule_fault));
    xpm_cdc_single #(.DEST_SYNC_FF(3),.SRC_INPUT_REG(1),.INIT_SYNC_FF(1)) rule_fault_cdc(
        .src_clk(slow_clk),.src_in(rule_fault),.dest_clk(fast_clk),.dest_out(rule_fault_fast));

    wire [WORD_BITS-1:0] control_word;
    wire control_due,app_due,control_prepare,app_prepare,frame_pulse;
    wire [31:0] freeze_frame;
    wire calendar_fault,candidate_fault;
    wire local_alarm=loss_fast || history_change || history_overflow || rule_fault_fast ||
                     generation_full || uptime_full;
    candidate_link candidates(.fast_clk(fast_clk),.slow_clk(slow_clk),
        .rst_fast(startup_rst_fast),.rst_slow(startup_rst_slow),
        .frame_pulse(frame_pulse),.frame_id(frame_id),
        .processed_generation(processed_generation),.rule_low(rule_low),
        .generation(generation),.invalidate(local_alarm),.loss(loss_fast),
        .freeze_frame(freeze_frame),.permit(candidate_permit),.fault(candidate_fault),
        .installed(),.installed_frame(),.candidate_busy());
    frame_engine #(.WORD_BITS(WORD_BITS),.INVERSE(INVERSE)) calendar(
        .clk(fast_clk),.start(start_fast && !startup_rst_fast),
        .permit(candidate_permit),.alarm(local_alarm || candidate_fault),.backend_busy(busy),
        .control_due(control_due),.app_due(app_due),.slot_due(),.freeze_due(),
        .control_prepare(control_prepare),.app_prepare(app_prepare),.word_due(control_word),
        .running(running),.fault(calendar_fault),.frame_pulse(frame_pulse),.frame_id(frame_id),
        .freeze_frame(freeze_frame),.slot_pos(),.freeze_pos(),.slot_pulse(slot_pulse),
        .skip_pulse(skip_pulse),.freeze_pulse(freeze_pulse),.frozen_execute(frozen_execute));
    assign app_grant_debug=app_due && app_prepared && !busy;
    assign grant_debug=control_due || app_grant_debug;
    assign grant_data_debug=backend_command;
    wire [31:0] read_data;
    wire backend_fault;
    reg application_fault=0;
    reg overlap_fault=0,outbox_fault=0;
    always @(posedge fast_clk) begin
        // Diagnostic pipeline is outside the atomic operation. It never
        // changes acceptance or suppresses a pending correction/response.
        overlap_fault<=grant_debug && busy;
        outbox_fault<=release_due && active_app && reply_pending && !return_ready;
        if(overlap_fault || outbox_fault) application_fault<=1;
        app_snapshot<=forward_data;
        app_receipt<=forward_valid && forward_ready;
        if(app_receipt) begin app_command<=app_snapshot; app_waiting<=1; end
        if(control_prepare) backend_command<={4'hf,32'd0,{{(19-WORD_BITS){1'b0}},control_word},2'd0};
        if(app_prepare) begin
            app_prepared<=app_waiting && !reply_pending;
            if(app_waiting && !reply_pending) backend_command<=app_command;
        end
        if(app_due) app_prepared<=0;
        if(grant_debug) begin
            active_app<=app_grant_debug; observed_err<=0;
            if(app_grant_debug) app_waiting<=0;
        end
        if(err_due) observed_err<=1;
        if(reply_pending && return_ready) reply_pending<=0;
        if(release_due && active_app) begin
            reply<={read_data,observed_err}; reply_pending<=1;
        end
    end
    e_backend_registered #(.WORD_BITS(WORD_BITS),.PREVALIDATED(1)) backend(
        .clk(fast_clk),.cold_init(1'b0),.soft_reset(1'b0),.go(grant_debug),
        .kind(backend_command[1:0]),.word_in(backend_command[2+:WORD_BITS]),
        .data_in(backend_command[52:21]),.byte_enable_in(backend_command[56:53]),
        .dq_in(dq_in),.err_in(err_in),.ready(),.busy(busy),.accepted(),.rejected(),
        .fault(backend_fault),.word_out(word_out),.ce(ce),.oe(oe),.we(we),.drive(drive),
        .alias_high(alias_high),.byte_enable(byte_enable),.dq_out(dq_out),
        .sample(),.flag(),.err_due(err_due),.done(),.release_due(release_due),
        .commit_pulse(),.pending(pending),.read_data(read_data),.kind_active(),.age());
    assign fault=history_overflow || rule_fault_fast || calendar_fault || candidate_fault ||
                 application_fault || backend_fault || generation_full || uptime_full;
endmodule

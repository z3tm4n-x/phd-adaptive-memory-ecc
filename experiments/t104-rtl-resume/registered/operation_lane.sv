// Registered SRAM lane. Wide transaction IDs NEVER enter the fast domain.
// Two ordered slow queues join an ID with its returned result exactly once.
// Request {id64,mask4,data32,word19,kind2}; response {id64,data32,observed_ERR}.
// No LOW/calendar integration is claimed by this component.
module operation_lane(
    input wire fast_clk, slow_clk, startup_rst_slow, startup_rst_fast,
    input wire soft_loss_slow,
    input wire request_valid, output wire request_ready,
    input wire [120:0] request_data,
    output wire response_valid, input wire response_ready,
    output wire [96:0] response_data,
    input wire [15:0] dq_in, input wire err_in,
    output wire [18:0] word_out,
    output wire ce, oe, we, drive, alias_high,
    output wire [1:0] byte_enable, output wire [15:0] dq_out,
    output wire fast_busy, err_due, loss_fast,
    output wire [63:0] generation,
    output wire queues_ready_slow,
    output wire grant_debug, release_debug,
    output wire [56:0] grant_data_debug,
    output wire [7:0] age_debug,
    output reg protocol_fault=0
);
    wire forward_valid,forward_ready,forward_wr_busy,forward_rd_busy;
    wire [56:0] forward_data;
    wire return_ready,return_wr_busy,return_rd_busy;
    wire returned_valid,returned_ready;
    wire [32:0] returned_data;
    wire id_ready,id_valid,id_wr_busy,id_rd_busy;
    wire [63:0] id_data;
    reg receive_idle=1, receipt=0, launch=0, reply_pending=0;
    reg [56:0] snapshot=0,staged=0;
    reg [32:0] reply_hold=0;
    reg observed_err=0;
    wire [31:0] read_data;
    wire backend_ready,backend_fault;
    wire [1:0] kind_active;
    wire request_legal=request_data[1:0]!=3 && request_data[56:53]!=0;
    wire request_capacity;
    wire staged_legal=staged[1:0]!=3 && staged[56:53]!=0;
    assign request_ready=request_capacity && id_ready && request_legal;

    async_queue #(.WIDTH(57)) requests(
        .wr_clk(slow_clk),.rd_clk(fast_clk),.rst(startup_rst_slow),.rd_rst(startup_rst_fast),
        .in_valid(request_valid && request_legal && id_ready),.in_ready(request_capacity),
        .in_data(request_data[56:0]),.out_valid(forward_valid),.out_ready(forward_ready),
        .out_data(forward_data),.wr_busy(forward_wr_busy),.rd_busy(forward_rd_busy));
    slow_queue #(.WIDTH(64)) ids(
        .clk(slow_clk),.rst(startup_rst_slow),
        .in_valid(request_valid && request_legal && request_capacity),.in_ready(id_ready),
        .in_data(request_data[120:57]),.out_valid(id_valid),.out_ready(response_valid && response_ready),
        .out_data(id_data),.wr_busy(id_wr_busy),.rd_busy(id_rd_busy));
    async_queue #(.WIDTH(33),.SLOW_SOURCE(0)) responses(
        .wr_clk(fast_clk),.rd_clk(slow_clk),.rst(startup_rst_fast),.rd_rst(startup_rst_slow),
        .in_valid(reply_pending),.in_ready(return_ready),.in_data(reply_hold),
        .out_valid(returned_valid),.out_ready(returned_ready),.out_data(returned_data),
        .wr_busy(return_wr_busy),.rd_busy(return_rd_busy));
    assign response_valid=returned_valid && id_valid;
    assign returned_ready=response_ready && id_valid;
    assign response_data={id_data,returned_data};
    assign queues_ready_slow=!forward_wr_busy && !return_rd_busy && !id_wr_busy && !id_rd_busy;
    xpm_cdc_single #(.DEST_SYNC_FF(3),.SRC_INPUT_REG(1),.INIT_SYNC_FF(1),
                     .SIM_ASSERT_CHK(1)) loss_crossing(
        .src_clk(slow_clk),.src_in(soft_loss_slow),.dest_clk(fast_clk),.dest_out(loss_fast));
    generation_guard guard(.clk(fast_clk),.loss(loss_fast),.err_event(err_due),.invalidate(1'b0),
        .candidate_valid(1'b0),.candidate_generation(64'd0),.generation(generation),
        .permitted(),.exhausted());
    // Receipt cuts the channel's acknowledgement path before the controller.
    // Its one-cycle overlap with receive_idle is blocked explicitly: no second pop.
    assign forward_ready=receive_idle && !receipt && !return_wr_busy;
    assign grant_debug=launch;
    assign grant_data_debug=staged;
    always @(posedge fast_clk) begin
        snapshot<=forward_data;
        receipt<=forward_valid && forward_ready;
        launch<=0;
        if(receipt) begin
            receive_idle<=0;
            staged<=snapshot;
            if(snapshot[1:0]!=3 && snapshot[56:53]!=0) launch<=1;
            else protocol_fault<=1;
        end
        if(grant_debug) observed_err<=0;
        if(err_due) observed_err<=1;
        if(release_debug) begin reply_hold<={read_data,observed_err}; reply_pending<=1; end
        if(reply_pending && return_ready) begin receive_idle<=1; reply_pending<=0; end
    end
    // Legal-go invariant is proved by prove_lane.py, specialization separately
    // compared with the full-input reference. No second mask decode after grant.
    e_backend_registered #(.PREVALIDATED(1)) backend(.clk(fast_clk),.cold_init(1'b0),.soft_reset(loss_fast),
        .go(grant_debug),.kind(staged[1:0]),.word_in(staged[20:2]),.data_in(staged[52:21]),
        .byte_enable_in(staged[56:53]),.dq_in(dq_in),.err_in(err_in),.ready(backend_ready),
        .busy(fast_busy),.accepted(),.rejected(),.fault(backend_fault),.word_out(word_out),
        .ce(ce),.oe(oe),.we(we),.drive(drive),.alias_high(alias_high),.byte_enable(byte_enable),
        .dq_out(dq_out),.sample(),.flag(),.err_due(err_due),.done(),.release_due(release_debug),
        .commit_pulse(),.pending(),.read_data(read_data),.kind_active(kind_active),.age(age_debug));
endmodule

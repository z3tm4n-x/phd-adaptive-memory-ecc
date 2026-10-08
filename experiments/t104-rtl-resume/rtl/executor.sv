// Conditional T104/T114 executor. Core clock period4xi, each source clock
// <=10.0001ns; clocks must keep running. Board pins and protected startup are
// outside this generic module. This is not the scientific rule producer.
module executor #(parameter integer WORD_BITS=19, INVERSE=174763)(
    input wire mem_clk, cpu_clk, x_clk, command_clk,
    input wire soft_reset, loss, recover, start_ok,
    input wire cfg_wr, cfg_commit,
    input wire [3:0] cfg_address,
    input wire [31:0] cfg_data,
    input wire [1:0] app_valid,
    input wire [3:0] app_kind,
    input wire [2*WORD_BITS-1:0] app_word,
    input wire [63:0] app_data,
    input wire [7:0] app_mask,
    input wire [127:0] app_id,
    output wire [1:0] app_ready,
    output wire [1:0] app_reply_valid,
    output wire [193:0] app_reply_payload,
    input wire [1:0] app_reply_ready,
    input wire cmd_valid,
    input wire [415:0] cmd_payload,
    output wire cmd_ready, cmd_reply_valid,
    output wire [31:0] cmd_reply_payload,
    input wire cmd_reply_ready,
    input wire [15:0] dq_in,
    input wire err_in,
    output wire ce, oe, we, drive, alias_high,
    output wire [1:0] byte_enable,
    output wire [15:0] dq_out,
    output wire [WORD_BITS-1:0] word_out,
    output wire busy, pending, flag, done, commit_pulse,
    output wire [63:0] now, err_count,
    output wire running, phase_valid, fault,
    output wire [3:0] queue_state
);
    wire [63:0] gray_time;
    wire [1:0] request_valid, request_ready, reply_valid, retire;
    wire [511:0] requests;
    wire [193:0] replies;
    wire [1:0] source_fault;
    (* ASYNC_REG="TRUE" *) reg [2:0] fault_cpu=0, fault_x=0;
    // Asynchronous host soft_reset is not accepted: this input is memory-domain.
    // Loss is delivered directly to the gate; no operational CDC toggle reset.
    always @(posedge mem_clk) begin
        fault_cpu<={fault_cpu[1:0],source_fault[0]};
        fault_x<={fault_x[1:0],source_fault[1]};
    end
    genvar p;
    generate for(p=0;p<2;p=p+1) begin: ports
        wire clock_source = p==0 ? cpu_clk : x_clk;
        (* ASYNC_REG="TRUE" *) reg [63:0] gt1=0, gt2=0, gt3=0;
        reg [63:0] decoded;
        integer j;
        always @(posedge clock_source) begin gt1<=gray_time; gt2<=gt1; gt3<=gt2; end
        always @* begin
            decoded[63]=gt3[63];
            for(j=62;j>=0;j=j-1) decoded[j]=decoded[j+1]^gt3[j];
        end
        wire [255:0] payload;
        wire link_ready, send, response_ready, occupied;
        app_frontend #(.WORD_BITS(WORD_BITS)) frontend(
            .clk(clock_source),.soft_reset(1'b0),.now_floor(decoded<<2),
            .valid(app_valid[p]),.kind(app_kind[p*2+:2]),
            .word_address(app_word[p*WORD_BITS+:WORD_BITS]),.data(app_data[p*32+:32]),
            .byte_enable(app_mask[p*4+:4]),.request_id(app_id[p*64+:64]),
            .link_ready(link_ready),.reply_valid(app_reply_valid[p]),
            .reply_ready(app_reply_ready[p]),.send(send),.payload(payload),
            .fault(source_fault[p]));
        // Only send denotes capture; malformed offers do not receive READY.
        assign app_ready[p]=send;
        rpc_cdc #(.REQUEST_BITS(256),.REPLY_BITS(97)) bridge(
            .src_clk(clock_source),.dst_clk(mem_clk),.src_valid(send),.src_data(payload),
            .src_ready(link_ready),.src_reply_valid(app_reply_valid[p]),
            .src_reply_data(app_reply_payload[p*97+:97]),.src_reply_ready(app_reply_ready[p]),
            .dst_valid(request_valid[p]),.dst_data(requests[p*256+:256]),
            .dst_ready(request_ready[p]),.dst_reply_valid(reply_valid[p]),
            .dst_reply_data(replies[p*97+:97]),.dst_reply_ready(response_ready),
            .dst_retire(retire[p]),.dst_occupied(occupied));
    end endgenerate
    wire receiver_valid, receiver_ready, receiver_reply, receiver_reply_ready, receiver_retire;
    wire command_valid, command_integrity, command_accepted, cmd_occupied;
    wire [415:0] command_input;
    wire [383:0] command;
    wire [31:0] command_result;
    rpc_cdc #(.REQUEST_BITS(416),.REPLY_BITS(32)) command_bridge(
        .src_clk(command_clk),.dst_clk(mem_clk),.src_valid(cmd_valid),.src_data(cmd_payload),
        .src_ready(cmd_ready),.src_reply_valid(cmd_reply_valid),.src_reply_data(cmd_reply_payload),
        .src_reply_ready(cmd_reply_ready),.dst_valid(receiver_valid),.dst_data(command_input),
        .dst_ready(receiver_ready),.dst_reply_valid(receiver_reply),.dst_reply_data(command_result),
        .dst_reply_ready(receiver_reply_ready),.dst_retire(receiver_retire),.dst_occupied(cmd_occupied));
    command_receiver receiver(.clk(mem_clk),.in_valid(receiver_valid),.in_data(command_input),
        .in_ready(receiver_ready),.command_valid(command_valid),.integrity(command_integrity),
        .command(command),.accepted(command_accepted),.reply_valid(receiver_reply),
        .reply_data(command_result),.reply_ready(receiver_reply_ready),.retire(receiver_retire));
    wire core_fault, config_locked, config_compatible, app_grant, grant_owner;
    wire [1:0] grant_kind;
    wire [63:0] slot_index;
    wire slot_pulse, skip_pulse;
    executor_core #(.WORD_BITS(WORD_BITS),.INVERSE(INVERSE)) core(
        .clk(mem_clk),.soft_reset(soft_reset),.loss(loss||fault_cpu[2]||fault_x[2]),
        .recover(recover),.start_ok(start_ok),.cfg_wr(cfg_wr),.cfg_commit(cfg_commit),
        .cfg_address(cfg_address),.cfg_data(cfg_data),.request_valid(request_valid),
        .request_payload(requests),.request_ready(request_ready),.retire(retire),
        .reply_valid(reply_valid),.reply_payload(replies),.command_valid(command_valid),
        .command_integrity(command_integrity),.command_payload(command),
        .command_accepted(command_accepted),.dq_in(dq_in),.err_in(err_in),
        .ce(ce),.oe(oe),.we(we),.drive(drive),.alias_high(alias_high),
        .byte_enable(byte_enable),.dq_out(dq_out),.word_out(word_out),.busy(busy),
        .pending(pending),.flag(flag),.done(done),.commit_pulse(commit_pulse),
        .err_count(err_count),.now(now),.time_gray(gray_time),.running(running),
        .config_locked(config_locked),.config_compatible(config_compatible),
        .phase_valid(phase_valid),.fault(core_fault),.queue_state(queue_state),
        .app_grant(app_grant),.grant_kind(grant_kind),.grant_owner(grant_owner),
        .slot_index(slot_index),.slot_pulse(slot_pulse),.skip_pulse(skip_pulse));
    assign fault=core_fault||fault_cpu[2]||fault_x[2];
endmodule

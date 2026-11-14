// Selected ZedBoard/FMC demonstration. CY62167GE30's CE2 and BYTE are high.
module bank_board #(parameter ADAPTIVE=1, PROTECTED=0) (
    input wire ref100, sram_err,
    inout wire [15:0] sram_dq,
    output wire [19:0] sram_a,
    output wire sram_ce_n, sram_oe_n, sram_we_n, sram_ub_n, sram_lb_n,
    (* IOB="TRUE" *) output reg locked_led, fault_led
);
    wire clk, ref_i, fb_i, fb, clk_i, cfg_i, locked;
    IBUF input_buffer(.I(ref100),.O(ref_i));
    MMCME2_BASE #(.CLKIN1_PERIOD(10.0),.CLKFBOUT_MULT_F(10.0),
        .CLKOUT0_DIVIDE_F(10.0),.CLKOUT1_DIVIDE(20),.DIVCLK_DIVIDE(1),.REF_JITTER1(0.005)) mmcm(
        .CLKIN1(ref_i),.CLKFBIN(fb),.CLKFBOUT(fb_i),.CLKOUT0(clk_i),.CLKOUT1(cfg_i),
        .PWRDWN(1'b0),.RST(1'b0),.LOCKED(locked));
    BUFG feedback(.I(fb_i),.O(fb));
    BUFG clock_buffer(.I(clk_i),.O(clk));
    // Qualified clean memory and valid reference clock before configuration.
    // Only configuration starts a new mission; no run-time reset pin.
    (* SHREG_EXTRACT="NO" *) reg [3:0] startup=0;
    (* ASYNC_REG="TRUE" *) reg [1:0] lock_sync=0;
    always @(posedge clk) begin
        lock_sync<={lock_sync[0],locked};
        if(lock_sync[1]) startup<={startup[2:0],1'b1};
    end
    wire sem_ready,sem_loss;
    if(PROTECTED) begin: mitigation
        wire cfg_clk, observing, contaminated;
        BUFG config_clock(.I(cfg_i),.O(cfg_clk));
        config_repair monitor(.clk(cfg_clk),.ready(observing),.loss(contaminated));
        // Status levels span at least a 50 MHz cycle. Related clocks are timed.
        (* ASYNC_REG="TRUE" *) reg [1:0] observation_sync=0, loss_sync=2'b11;
        always @(posedge clk) begin
            observation_sync<={observation_sync[0],observing};
            loss_sync<={loss_sync[0],contaminated};
        end
        assign sem_ready=observation_sync[1];
        assign sem_loss=loss_sync[1];
    end else begin
        assign sem_ready=1; assign sem_loss=0;
    end
    // The mission starts only after configuration observation and clean RAM
    // commissioning. Once started a SEM event must never cold-reset history.
    reg commissioned=0;
    always @(posedge clk) if(startup[3] && sem_ready) commissioned<=1;
    wire cold=!commissioned;
    wire [15:0] dq_in,dq_out,app_data;
    wire [16:0] address;
    wire app_grant, app_valid;
    wire [15:0] pad_t_n;
    wire [3:0] issued;
    wire active_owner;
    wire fault_status;
    assign sram_a={3'b0,address};
    assign sram_lb_n=0;
    assign sram_ub_n=0;
    genvar b;
    generate for(b=0;b<16;b=b+1) begin: io
        IOBUF dq(.IO(sram_dq[b]),.I(dq_out[b]),.O(dq_in[b]),.T(pad_t_n[b]));
    end endgenerate

    // Read-only fabric client. Hold request until a reserved slot accepts it.
    // Minimum inter-grant time exceeds the 1,000,020 ns application envelope.
    reg [16:0] app_rest=0;
    reg [16:0] app_addr=0;
    reg observed=0;
    always @(posedge clk) begin
        if(app_grant) begin app_rest<=17'd100003; app_addr<=app_addr+1'b1; end
        else if(app_rest!=0) app_rest<=app_rest-1'b1;
        if(app_valid) observed<=^app_data;
    end
    controller #(.ADAPTIVE(ADAPTIVE),.PROTECTED(PROTECTED)) core(.clk(clk),.cold(cold),
         .external_loss(sem_loss),.dq_in(dq_in),.err_in(sram_err),
         .app_request(app_rest==0),.app_addr(app_addr),.app_grant(app_grant),.app_valid(app_valid),
         .app_data(app_data),.pad_addr(address),.cs(sram_ce_n),.oe(sram_oe_n),.we(sram_we_n),
         .data(dq_out),.t_n(pad_t_n),.issued(issued),.owner(active_owner),.fault(fault_status));
    always @(posedge clk) begin
        locked_led<=observed ^ (^issued) ^ active_owner;
        fault_led<=fault_status || sem_loss;
    end
endmodule

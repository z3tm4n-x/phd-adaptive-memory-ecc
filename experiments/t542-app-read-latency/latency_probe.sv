// Observation boundary for the two accepted configurations. The source of an
// external request is separate from bank_board's unmodified internal client.
`timescale 1ns/1ns
module latency_probe #(parameter ADAPTIVE=1, BUILTIN=1)(
    input wire clk, reset_core, sem_ok, req, err, preload,
    input wire [16:0] request_addr, input wire [15:0] read_data,
    input wire [9:0] prefix_z,input wire [3:0] prefix_level,input wire [35:0] prefix_epoch,
    output wire cold, request_line, grant, valid, owner, cs, oe, we, drive, running, active,
    output wire [16:0] source_addr, pad_addr, candidate,
    output wire [15:0] app_data, capture_data, driven_data,
    output wire [7:0] phase, output wire [3:0] installed,
    output wire consumed_parity
);
    // Only the clean history before the long scan is loaded. Address, phase,
    // frame, repair, application, sampling, grant and data are never seeded.
    `define OBSERVE(C) \
      assign phase=C.lane[0].u.phase; \
      assign candidate=C.lane[0].u.app_candidate; \
      assign capture_data=C.lane[0].u.repair_image; \
      assign running=C.lane[0].u.running; \
      assign active=C.lane[0].u.active; \
      if(ADAPTIVE) for(genvar j=0;j<3;j=j+1) begin: prefix \
        always @(posedge preload) begin \
          C.lane[j].u.epoch<=prefix_epoch; \
          C.lane[j].u.adaptive.policy.initialized<=1; \
          C.lane[j].u.adaptive.policy.issued<=prefix_level; \
          C.lane[j].u.adaptive.policy.quiet<=prefix_z; \
          C.lane[j].u.adaptive.policy.quiet_inv<=~prefix_z; \
        end \
      end

    if(BUILTIN) begin: board_client
        tri [15:0] pads;
        wire [19:0] address;
        assign pads=(!cs && !oe)?read_data:16'hzzzz;
        bank_board #(.ADAPTIVE(ADAPTIVE),.PROTECTED(1)) b(
          .ref100(clk),.sram_err(err),.sram_dq(pads),.sram_a(address),
          .sram_ce_n(cs),.sram_oe_n(oe),.sram_we_n(we));
        // Only the vendor primitive/SEM fixtures are substituted in this run.
        always @(sem_ok) b.mitigation.monitor.sem.status_observation=sem_ok;
        assign pad_addr=address[16:0];
        assign cold=b.cold;assign request_line=b.core.app_request;assign source_addr=b.app_addr;
        assign grant=b.app_grant;assign valid=b.app_valid;assign owner=b.active_owner;
        assign app_data=b.app_data;assign driven_data=pads;assign drive=(b.pad_t_n==0);
        assign installed=b.issued;assign consumed_parity=b.observed;
        `OBSERVE(b.core)
    end else begin: external_client
        wire [15:0] t_n;
        controller #(.ADAPTIVE(ADAPTIVE),.PROTECTED(1)) d(
          .clk(clk),.cold(reset_core),.external_loss(1'b0),.err_in(err),.dq_in(read_data),
          .app_request(req),.app_addr(request_addr),.cs(cs),.oe(oe),.we(we),
          .pad_addr(pad_addr),.data(driven_data),.t_n(t_n),.app_grant(grant),.app_valid(valid),
          .app_data(app_data),.owner(owner),.issued(installed));
        assign cold=reset_core;assign request_line=req;assign source_addr=request_addr;
        assign drive=(t_n==0);assign consumed_parity=0;
        `OBSERVE(d)
    end
    `undef OBSERVE
endmodule

// Test-only deposits at stable idle points. All transactions and decisions
// run in the unchanged controller; probes do not supply a production input.
`timescale 1ns/1ns
module harness #(parameter ADAPTIVE=1, PROTECTED=0) (
    input wire clk,cold,loss,err,req,input wire [15:0] dq,input wire [16:0] app,
    input wire edit,input wire [3:0] action,input wire [9:0] prefix,
    input wire [3:0] prior_level,input wire [35:0] prefix_epoch,
    output wire cs,oe,we,owner,sealed,pkt,zero,strobe,fault,grant,valid,
    output wire [16:0] addr,output wire [15:0] data,t_n,app_data,
    output wire [9:0] z,output wire [3:0] issued,output wire [17:0] count,
    output wire [35:0] epoch,output wire [2:0] err_trace,output wire [15:0] image0
);
    controller #(.ADAPTIVE(ADAPTIVE),.PROTECTED(PROTECTED)) dut(.clk(clk),.cold(cold),
        .external_loss(loss),.err_in(err),.dq_in(dq),.app_request(req),.app_addr(app),
        .cs(cs),.oe(oe),.we(we),.pad_addr(addr),.data(data),.t_n(t_n),.app_grant(grant),
        .app_valid(valid),.app_data(app_data),.owner(owner),.sealed(sealed),.sent(pkt),
        .zero(zero),.strobe(strobe),.fault(fault),.count(count),.issued(issued),.quiet(z));
    assign epoch=dut.lane[0].u.epoch;
    assign image0=dut.lane[0].u.repair_image;
    if (PROTECTED)
        assign err_trace={dut.lane[2].u.sampled_err,dut.lane[1].u.sampled_err,dut.lane[0].u.sampled_err};
    else assign err_trace={2'b0,dut.lane[0].u.sampled_err};

    for(genvar i=0;i<(PROTECTED?3:1);i=i+1) begin: examiner
        always @(posedge edit) begin
            case(action)
                1: dut.lane[i].u.epoch<=prefix_epoch;
                2: begin // skip only the idle interior of a dormant basal round
                    dut.lane[i].u.frame<=32767;
                    dut.lane[i].u.phase_a<=139;
                    dut.lane[i].u.phase_inv<=~8'd139;
                    dut.lane[i].u.phase_parity<=^8'd139;
                end
                3: begin // between clean frame 0 and final frame at phase 136
                    dut.lane[i].u.frame<=32766;
                    if(dut.lane[i].u.active) dut.lane[i].u.seen<=131068;
                end
                4: if(i==0) dut.lane[i].u.sampled_err<=0;
                5: if(i==0) dut.lane[i].u.repair_image<=dut.lane[i].u.repair_image ^ 16'h1;
                7: dut.lane[i].u.report_send<=0;
                8: dut.lane[i].u.report_send<=1;
                default: ;
            endcase
        end
        if(ADAPTIVE) begin
            always @(posedge edit) begin
                if(action==1) begin
                    dut.lane[i].u.adaptive.policy.initialized<=1;
                    dut.lane[i].u.adaptive.policy.quiet<=prefix;
                    dut.lane[i].u.adaptive.policy.quiet_inv<=~prefix;
                    dut.lane[i].u.adaptive.policy.issued<=prior_level;
                end
                if(action==9 && i==0)
                    dut.lane[i].u.adaptive.policy.issued<=dut.lane[i].u.adaptive.policy.issued ^ 4'd2;
            end
        end
    end
endmodule

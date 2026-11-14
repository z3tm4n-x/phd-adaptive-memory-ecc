// Three independent engines vote only at the common outward interface.
module controller #(parameter ADAPTIVE=1, PROTECTED=0, PARTNER_PIN=5) (
    input wire clk,cold,external_loss, input wire err_in, input wire [15:0] dq_in,
    input wire app_request,input wire [16:0] app_addr,
    (* IOB="TRUE", DONT_TOUCH="TRUE" *) output reg [16:0] pad_addr,
    (* IOB="TRUE", DONT_TOUCH="TRUE" *) output reg cs,oe,we,
    (* IOB="TRUE", DONT_TOUCH="TRUE" *) output reg [15:0] data,t_n,
    output wire app_grant,app_valid, output wire [15:0] app_data,
    output wire owner,sealed,sent,zero,strobe,fault,output wire [17:0] count,
    output wire [3:0] issued,output wire [9:0] quiet
);
    localparam LANES=PROTECTED ? 3 : 1;
    localparam WIDTH=17+3+32+2+16+6+18+4+10;
    wire [WIDTH-1:0] bus[0:LANES-1];
    wire [10:0] witness[0:LANES-1];
    wire mismatch;
    for(genvar i=0;i<LANES;i=i+1) begin: lane
        wire [16:0] a; wire sel,read_n,write_n,g,v,own,seal,pkt,z,cmd,bad;
        wire [15:0] d,t,app; wire [17:0] cnt; wire [3:0] period; wire [9:0] history;
        wire stored_err,data_parity;
        // KEEP_HIERARCHY and separate out-of-context instances are checked in
        // the placed netlist. Digital TMR is conditional on fault containment.
        (* KEEP_HIERARCHY="TRUE" *) scan_engine #(.ADAPTIVE(ADAPTIVE),.PARTNER_PIN(PARTNER_PIN)) u (
            .clk(clk),.cold(cold),.loss(external_loss || mismatch),.err_in(err_in),.dq_in(dq_in),
            .app_request(app_request),.app_address(app_addr),.app_grant(g),.app_valid(v),.app_data(app),
            .pad_address(a),.pad_select_n(sel),.pad_oe_n(read_n),.pad_we_n(write_n),.dq_out(d),
            .pad_t_n(t),.protect_owner(own),.sealed(seal),.report_send(pkt),.accepted_zero(z),
            .command_strobe(cmd),.execution_fault(bad),.count(cnt),.issued(period),.quiet(history),
            .captured_err(stored_err),.capture_check(data_parity));
        assign bus[i]={a,sel,read_n,write_n,d,t,g,v,app,own,seal,pkt,z,cmd,bad,cnt,period,history};
        // The fixed controller never uses a history or a period decision.
        assign witness[i]={own,sel,read_n,write_n,pkt,stored_err,data_parity,period};
    end
    wire [WIDTH-1:0] voted;
    if(PROTECTED) begin: triple
        assign voted=(bus[0]&bus[1])|(bus[0]&bus[2])|(bus[1]&bus[2]);
        // Register discrepancy before diagnostic use. A true ERR is acted on
        // locally at the original edge without waiting for this comparison.
        reg disagree=0;
        always @(posedge clk) disagree<=!cold && ((witness[0]!=witness[1])||(witness[0]!=witness[2]));
        assign mismatch=disagree;
    end else begin
        assign voted=bus[0]; assign mismatch=0;
    end
    wire voted_fault;
    wire [51:0] pad_d;
    assign {pad_d,app_grant,app_valid,app_data,owner,sealed,sent,
            zero,strobe,voted_fault,count,issued,quiet}=voted;
    always @(posedge clk) {pad_addr,cs,oe,we,data,t_n}<=pad_d;
    assign fault=voted_fault||mismatch;
endmodule

// T104 registered 4-xi microsequence. Age is an observation, NEVER a control.
// Identical edge contract to ../rtl/e_backend.sv; preparation precedes go.
// Semantic enables; the board layer inverts active-low SRAM outputs.
module e_backend_registered #(
    parameter integer WORD_BITS=19,
    parameter integer PREVALIDATED=0 // only if wrapper proves every go legal
)(
    input wire clk, cold_init, soft_reset, go,
    input wire [1:0] kind,
    input wire [WORD_BITS-1:0] word_in,
    input wire [31:0] data_in,
    input wire [3:0] byte_enable_in,
    input wire [15:0] dq_in, input wire err_in,
    output wire ready,
    output reg busy, accepted, rejected, fault,
    output reg [WORD_BITS-1:0] word_out,
    output reg ce, oe, we, drive, alias_high,
    output reg [1:0] byte_enable,
    output reg [15:0] dq_out,
    output reg sample, flag, err_due, done, release_due,
    output reg commit_pulse, pending,
    output wire [31:0] read_data,
    output wire [1:0] kind_active,
    output reg [7:0] age
);
    initial begin
        busy=0; accepted=0; rejected=0; fault=0; word_out=0;
        ce=0; oe=0; we=0; drive=0; alias_high=0; byte_enable=3; dq_out=0;
        sample=0; flag=0; err_due=0; done=0; release_due=0;
        commit_pulse=0; pending=0; age=0;
    end
    localparam [1:0] CONTROL=0, READ32=1, WRITE32=2;
    reg [53:0] step=0; // bit k: current elapsed time is 4*k xi
    reg [1:0] op=0;
    reg [31:0] requested=0;
    reg [3:0] mask=15;
    reg [15:0] low_data=0, high_data=0;
    reg captured_err=0;
    wire repairing=op==WRITE32 || (op==CONTROL && captured_err);
    assign ready=!busy;
    assign read_data={high_data,low_data};
    assign kind_active=op;

    always @(posedge clk) begin
        accepted<=0; rejected<=0; done<=0;
        sample<=0; flag<=err_due; err_due<=0; commit_pulse<=0;
        release_due<=0;
        if(cold_init && !busy) begin
            op<=0; requested<=0; mask<=15; age<=0; step<=0;
            low_data<=0; high_data<=0; captured_err<=0;
            word_out<=0; fault<=0; alias_high<=0; byte_enable<=3;
            ce<=0; oe<=0; we<=0; drive<=0; dq_out<=0; pending<=0;
        end else begin
            if(soft_reset || cold_init) fault<=1;
            if(busy) begin
                step<={step[52:0],1'b0};
                age<=age+8'd4;
                if(step[0]) begin ce<=1; oe<=1; end // age 4
                if(step[14]) begin // age 60, coherent full-word observation
                    low_data<=dq_in; captured_err<=err_in; sample<=1;
                    err_due<=op!=READ32 && err_in;
                    pending<=op==WRITE32 || (op==CONTROL && err_in);
                end
                if(step[15]) begin oe<=0; ce<=repairing; end // age 64
                // Announce release one edge BEFORE it, independently of age.
                if((step[21] && op==CONTROL && !repairing) ||
                   (step[35] && op==CONTROL && repairing) ||
                   (step[44] && op==READ32) || (step[52] && op==WRITE32))
                    release_due<=1;
                if(step[22]) begin // age 92
                    if(repairing) begin
                        we<=1; drive<=1;
                        dq_out<={op==WRITE32 && mask[1] ? requested[15:8] : low_data[15:8],
                                 op==WRITE32 && mask[0] ? requested[7:0] : low_data[7:0]};
                    end
                    if(op==READ32) alias_high<=1;
                end
                if(step[23] && op==READ32) begin ce<=1; oe<=1; end // age 96
                if(step[32] && repairing) begin // age 132, first write committed
                    we<=0; ce<=0; commit_pulse<=1;
                end
                if(step[34]) begin drive<=0; dq_out<=0; end // age 140
                if(step[36] && op==WRITE32) begin // age 148, second alias
                    alias_high<=1; byte_enable<=mask[3:2];
                end
                if(step[37]) begin // age 152
                    if(op==WRITE32) begin ce<=1; drive<=1; dq_out<=requested[31:16]; end
                    if(op==READ32) begin high_data<=dq_in; sample<=1; end
                end
                if(step[38] && op==READ32) begin ce<=0; oe<=0; end // age 156
                if(step[39] && op==WRITE32) we<=1; // age 160
                if(step[49] && op==WRITE32) begin // age 200
                    ce<=0; we<=0; commit_pulse<=1;
                end
                if(step[51]) begin drive<=0; dq_out<=0; end // age 208
                if(release_due) begin
                    busy<=0; done<=1; pending<=0;
                    ce<=0; oe<=0; we<=0; drive<=0; dq_out<=0;
                end
            end else begin
                step<=0; alias_high<=0;
                if(go) begin
                    if(!PREVALIDATED && (kind==3 || byte_enable_in==0)) begin rejected<=1; fault<=1; end
                    else begin
                        busy<=1; accepted<=1; age<=0; step<=54'b1;
                        op<=kind; word_out<=word_in; requested<=data_in; mask<=byte_enable_in;
                        captured_err<=0; low_data<=0; high_data<=0; byte_enable<=3;
                    end
                end
            end
        end
    end
endmodule

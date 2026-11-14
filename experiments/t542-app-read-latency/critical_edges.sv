// Second simulator, no probe wrapper. Check only public pins and app signals.
`timescale 1ns/1ps
module critical_edges #(parameter ADAPTIVE = 0);
    localparam [16:0] OLD = 17'h10020, NEW_ADDR = 17'h10001;
    // Address bits 5 and 16 are exchanged by the accepted implementation.
    localparam [16:0] OLD_PAD = 17'h10020, NEW_PAD = 17'h00021;
    localparam [15:0] OLD_DATA = 16'ha55a, NEW_DATA = 16'h3c69;

    reg clk = 0, cold = 1, req = 0;
    reg [16:0] src = OLD;
    wire grant, valid, cs, oe, we;
    wire [16:0] pad;
    wire [15:0] returned;
    wire [15:0] dq = cs || oe ? 16'hzzzz :
                     pad == OLD_PAD ? OLD_DATA : pad == NEW_PAD ? NEW_DATA : 16'hd3d3;

    always #5 clk = !clk;
    controller #(.ADAPTIVE(ADAPTIVE), .PROTECTED(1)) dut(
        .clk(clk), .cold(cold), .external_loss(1'b0), .err_in(1'b1), .dq_in(dq),
        .app_request(req), .app_addr(src), .pad_addr(pad), .cs(cs), .oe(oe), .we(we),
        .app_grant(grant), .app_valid(valid), .app_data(returned));

    integer t;
    reg expect_grant, expect_valid;
    initial begin
        repeat (3) @(posedge clk);
        for (t = 0; t <= 674; t = t + 1) begin
            @(negedge clk);
            cold = 0;
            case (t)
                100: src = NEW_ADDR;        // Prepared before snapshot.
                102: req = 1;
                103: begin req = 0; src = OLD; end
                242: begin src = NEW_ADDR; req = 1; end // Late simultaneous address and request.
                243: begin req = 0; src = OLD; end
                382: src = NEW_ADDR;        // Too late for this slot; suppress grant.
                383: req = 1;
                523: begin req = 0; src = OLD; end
                661: begin req = 1; src = NEW_ADDR; end // Simultaneous, on snapshot edge.
                663: begin req = 0; src = OLD; end
            endcase
            @(posedge clk); #1;
            expect_grant = t == 102 || t == 242 || t == 522 || t == 662;
            expect_valid = t == 112 || t == 252 || t == 532 || t == 672;
            if (grant !== expect_grant || valid !== expect_valid)
                $fatal(1, "unexpected grant/valid at tick %0d", t);
            if (expect_grant) begin
                if (src !== NEW_ADDR || {cs,oe,we} !== 3'b001 ||
                    pad !== (t == 242 ? OLD_PAD : NEW_PAD))
                    $fatal(1, "wrong SRAM operation at tick %0d", t);
                $display("GRANT A=%0d tick=%0d request=%h pad=%h", ADAPTIVE,t,src,pad);
            end
            if (expect_valid) begin
                if ({cs,oe,we} !== 3'b111 || returned !== (t == 252 ? OLD_DATA : NEW_DATA))
                    $fatal(1, "incorrect data at tick %0d", t);
                $display("VALID A=%0d tick=%0d value=%h", ADAPTIVE,t,returned);
            end
        end
        $display("PASS A=%0d grants=4 valid=4 wrong_when_late=1 deferred_correct=1", ADAPTIVE);
        $finish(0);
    end
endmodule

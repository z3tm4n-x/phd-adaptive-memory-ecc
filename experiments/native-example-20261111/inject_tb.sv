// Directed corruptions are deposited in the actual RTL state after capture.
`timescale 1ns/1ps
module inject_tb #(parameter CHECK_LOCAL=1);
    reg clk=0, reset=1, err=0, release_ok=1, report_ok=1, install_ok=1;
    always #5 clk=!clk;
    wire [2:0] addr;
    wire sel,oe_n,we_n,drive,sealed;
    wire [15:0] dq;
    wire [3:0] count;
    wire [8:0] step;
    wire reading=sel && !oe_n;
    reg was_reading=0, was_we_n=1;
    native8 #(.CHECK_LOCAL(CHECK_LOCAL)) d(clk,reset,err,16'h5aa5,release_ok,report_ok,install_ok,
              addr,sel,oe_n,we_n,drive,dq,sealed,count,step);
    integer sc, r, k, reads, writes, expected, next_start, checked;
    initial begin
        if (!$value$plusargs("case=%d",sc)) $fatal(1,"case required");
        @(posedge clk); @(negedge clk); reset=0;
        reads=0; writes=0; next_start=-1; checked=0;
        for (r=0;r<=1284;r=r+1) begin
            for (k=0;k<280;k=k+1) begin
                // Final release and a controller SEU at the first promotion.
                err=(sc==1 || sc==4) && r==1280 && addr==7;
                if ((sc==6 || sc==7) && r==1280 && addr==7) err=1;
                release_ok=!(sc==2 && r==1280 && addr==7);
                report_ok=!(sc==3 && r==1280);
                install_ok=!(sc==5 && r==1280);
                #1;
                if (r>1280 && next_start<0 && (sel || !oe_n || !we_n || drive)) begin
                    if (k!=0 || addr!==0 || !reading || !we_n || drive)
                        $fatal(1,"first subsequent bus activity is not a scan start");
                    next_start=r;
                end
                if (r==1280) begin
                    if (reading && !was_reading) begin
                        if (addr!==reads[2:0]) $fatal(1,"out-of-sequence read");
                        reads=reads+1;
                    end
                    if (!we_n && was_we_n) begin
                        writes=writes+1;
                        if(addr!==7 || dq!==16'h5aa5 || !drive || !sel || !oe_n)
                            $fatal(1,"incorrect repair");
                    end
                    if (k==237 && (sc==1 || sc==4 || sc==6 || sc==7) &&
                        (count!==1 || sealed!==1))
                        $fatal(1,"last repair not sealed");
                    if(k==245 && sc==4) d.count[0]=1'b0; // actual 1 -> 0
                    if(k==265 && sc==6) d.proposed[1]=1'b1; // 1 -> 3 before latch
                    if (k==271) begin
                        expected=sc==0 || sc==8 || (sc==4 && !CHECK_LOCAL) ? 2 :
                                 (sc==6 && !CHECK_LOCAL) ? 3 : 1;
                        if(step!==expected || d.gap!==expected) $fatal(1,"wrong installed step");
                        checked=1;
                    end
                    if (k==275 && sc==7) d.gap[1]=1'b1; // after install, before use
                end
                if(r==1281 && k==20 && sc==8) d.remaining[1]=1'b1;
                was_reading=reading;
                was_we_n=we_n;
                @(negedge clk);
            end
        end
        if(!checked || reads!=8 || writes!=((sc==1 || sc==4 || sc==6 || sc==7)?1:0))
            $fatal(1,"incorrect scan totals");
        expected=sc==8 ? (CHECK_LOCAL ? 1282 : 1284) :
                 (sc==0 || (sc==4 && !CHECK_LOCAL)) ? 1282 :
                 ((sc==6 || sc==7) && !CHECK_LOCAL) ? 1283 : 1281;
        if(next_start!=expected) $fatal(1,"physical next start %d expected %d",next_start,expected);
        $display("case=%0d reads=%0d writes=%0d next_start=%0d",sc,reads,writes,next_start);
        $finish;
    end
endmodule

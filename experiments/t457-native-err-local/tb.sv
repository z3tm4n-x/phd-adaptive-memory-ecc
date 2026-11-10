`timescale 1ns/1ps
// The testbench owns injection truth, address partners and perturbations;
// the controller sees DQ/ERR, transaction identity, reports and local time.
module tb;
    parameter A=8;
    localparam L=140*(A/4), CUT=L-30, INS=CUT+20;
    reg clk=0; reg [63:0] tick=0, end_tick;
    integer scenario, literal, mixed;
    wire [63:0] r=tick/L;
    wire [31:0] rt=tick%L;
    wire [31:0] reqaddr; wire other_ready;
    // Default pairs (0,4),(1,5),(2,6),(3,7); alternative last two
    // addresses 3 and 7 have distinct outside partners (model only).
    function integer word_of(input integer a);
        word_of=(mixed && a==7)?4:a%4;
    endfunction
    function integer half_of(input integer a);
        half_of=(a>=4 && !(mixed && a==7));
    endfunction
    reg [37:0] bits[0:4], recent=0;
    reg [31:0] data[0:4];
    wire repeated=(scenario==6 && r==0 && rt==L-64);
    wire [31:0] pinaddr=repeated?reqaddr-1:reqaddr;
    wire [31:0] word=word_of(d.addr);
    wire err_pin=bits[word]!=0;
    wire [15:0] dq_pin=half_of(d.addr)?data[word][31:16]:data[word][15:0];
    wire write_ok=!(scenario==8 && r==0 && d.addr==7);
    wire drop_tok=(scenario==5 && r==0 && d.addr==7);
    wire dup_tok=(scenario==7 && r==0 && rt==12);
    reg rx_valid,rx_complete;reg [63:0] rx_epoch;reg [31:0] rx_count;
    wire install_lost=(scenario==13 && r==1280);
    wire app_probe=(r==0 && rt==L-38) || (r==152577 && rt==102);
    native #(.A(A)) d(clk,tick,err_pin,dq_pin,pinaddr,write_ok,drop_tok,dup_tok,
        rx_valid,rx_complete,rx_epoch,rx_count,install_lost,app_probe,reqaddr,other_ready);

    integer i;
    reg [63:0] rd=0,wr=0,excluded=0,app=0,idle_ticks=0,idle_excluded=0,control_excluded=0;
    reg [63:0] jumped=0,npass=0,nswitch=0;
    integer app_left=0, oldstep, cut_lock=0, cut_app=0;
    reg was_sealed, was_cut, was_install, was_launch, was_release, in_pass;
    task inject(input integer parent, input integer w, input integer b);
        begin
            bits[w][b]=!bits[w][b];
            if(d.locked && word_of(d.addr)==w) recent[b]=bits[w][b];
            $display("J %0d %0d %0d %0d",tick,parent,w,b);
        end
    endtask

    initial begin
        if(!$value$plusargs("case=%d",scenario) || !$value$plusargs("end=%d",end_tick)
            || !$value$plusargs("literal=%d",literal) || !$value$plusargs("mixed=%d",mixed))
            $fatal(1,"need case/end/literal/mixed");
        for(i=0;i<5;i=i+1) begin bits[i]=0; data[i]=32'ha5bc3410+32'h00010001*i;end
        rx_valid=0;rx_complete=0;rx_epoch=0;rx_count=0;
        #1;
        while(tick<end_tick) begin
            // Only after a literal, free idle frame. No scheduled report,
            // injection, cut, install or probe in the skipped interior.
            // One entire maximum 255L pause is run literally in case 14.
            if(!literal && rt==140 && r>d.active_round && r<d.next_round &&
               !(scenario==14 && r>=152577) && !d.locked && app_left==0) begin : skip
                reg [63:0] finish;
                finish=d.next_round*L; if(finish>end_tick) finish=end_tick;
                if(!other_ready || d.read_owner || d.repair_owner) $fatal(1,"nonempty gap");
                $display("Z %0d %0d",tick,finish);
                jumped=jumped+finish-tick;idle_ticks=idle_ticks+finish-tick;
                #(10*(finish-tick)); tick=finish; #0;
            end
            if(tick<end_tick) begin
                if((scenario==1 || scenario==5 || scenario==6 || scenario==8 || scenario==16 ||
                    scenario==18) && r==0 && rt==L-65) inject(1,word_of(7),37);
                if(scenario==15 && r==1280 && rt==L-65) inject(1,word_of(7),21);
                if(scenario==17 && r<38 && rt==L-65) inject(r,word_of(7),r);
                if(scenario==2 && r==0 && rt==22) begin inject(1,1,0);inject(1,2,33);end
                if(scenario==2 && r==0 && rt==185) begin inject(2,2,21);inject(2,3,37);end
                if(scenario==3 && r==0 && rt==2) inject(1,0,35);
                if(scenario==4 && r==0 && rt==L-57) inject(1,word_of(7),32);
                if(scenario==23 && r==0 && rt==2) inject(1,0,12);
                if(scenario==23 && r==0 && rt==12) inject(2,0,12);
                #1;
                rx_valid=0;rx_complete=d.sealed;rx_epoch=d.active_round;rx_count=d.count;
                if(d.active && d.sealed) begin
                    rx_valid=(rt==CUT-10);
                    if(scenario==9 && r==0) rx_valid=(rt==CUT-10 || rt==CUT);
                    if(scenario==10 && (r==1282 || r==1283)) rx_valid=0;
                    if(scenario==11 && r==1282) rx_valid=(rt==CUT+1);
                    if(scenario==11 && r==1283) begin rx_valid=(rt==CUT-1);rx_epoch=1282;end
                    if(scenario==12 && r==1280) rx_valid=(rt==CUT);
                    if(scenario==18 && r==0) rx_valid=0;
                    if(scenario==14 && r==152832) rx_valid=0;
                    if(scenario==19 && r==1280) rx_valid=(rt==CUT-1);
                    if(scenario==20 && r==1280 && rt==CUT) begin rx_valid=1;rx_count=1;end
                    if(scenario==21 && (r==1024 || r==1280)) rx_valid=(rt==CUT-10 || rt==CUT);
                    if(scenario==22 && r==1280) rx_valid=(rt==CUT+1);
                    if(scenario==23 && r>=1) rx_valid=0;
                end
                #1;
                was_launch=d.launch;was_release=d.release_event;was_cut=d.cutting;
                was_install=d.installing;was_sealed=d.sealed;oldstep=d.step;in_pass=d.active;
                if(d.beginning) begin npass=npass+1;$display("B %0d %0d",tick,r);end
                if(d.launch) begin $display("G %0d %0d %0d %0d",tick,r,reqaddr,pinaddr);recent=0;end
                if(d.sample) $display("S %0d %0d %0d %0d",tick,d.addr,err_pin,dq_pin);
                if(d.write_end) begin
                    $display("W %0d %0d %0d %0d",tick,d.addr,d.image,write_ok);
                    if(write_ok) bits[word]=bits[word]&recent;
                end
                if(d.release_event) $display("R %0d %0d %0d %0d %0d",tick,d.addr,d.hit,d.wrote,drop_tok);
                if(dup_tok) $display("D %0d %0d",tick,d.last_addr);
                if(rx_valid) $display("P %0d %0d %0d %0d",tick,rx_epoch,rx_count,rx_complete);
                if(d.app_grant) begin app_left=10;$display("A %0d",tick);end
                if(was_cut) begin cut_lock=0;cut_app=0;end
                if(in_pass && rt>=CUT && rt<INS) begin
                    cut_lock=cut_lock+!other_ready;cut_app=cut_app+(app_left>0);
                end
                if(app_left>0) begin if(!other_ready) $fatal(1,"application/protection collision");
                    app=app+1;app_left=app_left-1;end
                if(!other_ready) excluded=excluded+1;
                if(d.read_owner) rd=rd+1;
                if(d.repair_owner) wr=wr+1;
                if(!in_pass) begin idle_ticks=idle_ticks+1;
                    if(!other_ready) idle_excluded=idle_excluded+1;end
                if(tick%140>=126 && tick%140<130 && !other_ready) control_excluded=control_excluded+1;
                if($time!=tick*10+3) $fatal(1,"10ns model clock phase drift");
                clk=1;#1;
                if(!was_sealed && d.sealed) $display("F %0d %0d %0d %0d",tick,r,d.seen,d.count);
                if(was_cut) $display("C %0d %0d %0d %0d %0d %0d %0d %0d",
                                      tick,r,d.seen,d.count,d.sealed,d.cut_bad,d.cut_count,d.chosen);
                if(was_install) begin
                    if(oldstep!=d.step) nswitch=nswitch+1;
                    $display("K %0d %0d %0d %0d %0d %0d %0d %0d",tick,r,d.step,d.last_bad,d.next_round,install_lost,cut_lock,cut_app);
                end
                clk=0;tick=tick+1;#7;
            end
        end
        $display("END %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d",
          tick,rd,wr,excluded,app,idle_ticks,idle_excluded,control_excluded,
          npass,nswitch,jumped,d.locked,d.sealed);
        $finish;
    end
endmodule

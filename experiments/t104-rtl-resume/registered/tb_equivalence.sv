`timescale 1ns/1ps
module tb_equivalence;
    reg clk=0; always #2 clk=~clk;
    reg cold_init=0, soft_reset=0, go=0;
    reg [1:0] kind=0;
    reg [18:0] word_in=0;
    reg [31:0] data_in=0;
    reg [3:0] byte_enable_in=15;
    reg [15:0] dq_in=0;
    reg err_in=0;
    wire [99:0] old_trace,new_trace;
    // Full 100-bit observable vector, including idle/rejection/reset behavior.
    // Bit count is checked independently by explicit concatenation widths.
    wire [18:0] ow,nw; wire [15:0] od,nd; wire [31:0] ordata,nrdata;
    wire [1:0] obe,nbe,ok,nk; wire [7:0] oa,na;
    wire [19:0] ob,nb;
    e_backend old_e(.clk(clk),.cold_init(cold_init),.soft_reset(soft_reset),.go(go),
      .kind(kind),.word_in(word_in),.data_in(data_in),.byte_enable_in(byte_enable_in),
      .dq_in(dq_in),.err_in(err_in),.word_out(ow),.dq_out(od),.read_data(ordata),
      .byte_enable(obe),.kind_active(ok),.age(oa),
      .ready(ob[0]),.busy(ob[1]),.accepted(ob[2]),.rejected(ob[3]),.fault(ob[4]),
      .ce(ob[5]),.oe(ob[6]),.we(ob[7]),.drive(ob[8]),.alias_high(ob[9]),
      .sample(ob[10]),.flag(ob[11]),.err_due(ob[12]),.done(ob[13]),
      .release_due(ob[14]),.commit_pulse(ob[15]),.pending(ob[16]));
    e_backend_registered new_e(.clk(clk),.cold_init(cold_init),.soft_reset(soft_reset),.go(go),
      .kind(kind),.word_in(word_in),.data_in(data_in),.byte_enable_in(byte_enable_in),
      .dq_in(dq_in),.err_in(err_in),.word_out(nw),.dq_out(nd),.read_data(nrdata),
      .byte_enable(nbe),.kind_active(nk),.age(na),
      .ready(nb[0]),.busy(nb[1]),.accepted(nb[2]),.rejected(nb[3]),.fault(nb[4]),
      .ce(nb[5]),.oe(nb[6]),.we(nb[7]),.drive(nb[8]),.alias_high(nb[9]),
      .sample(nb[10]),.flag(nb[11]),.err_due(nb[12]),.done(nb[13]),
      .release_due(nb[14]),.commit_pulse(nb[15]),.pending(nb[16]));
    assign old_trace={ow,od,ordata,obe,ok,oa,ob[16:0],4'b0};
    assign new_trace={nw,nd,nrdata,nbe,nk,na,nb[16:0],4'b0};
    integer edges=0, transactions=0;
    reg [31:0] rng=32'h91375a21;
    task tick;
      begin @(posedge clk); #0.1;
        if(old_trace !== new_trace) begin
          $display("DIFF edge=%0d age=%0d kind=%0d flags %h/%h data %h/%h",edges,oa,ok,ob[16:0],nb[16:0],ordata,nrdata);
          $fatal(1,"registered E mismatch");
        end
        edges=edges+1; @(negedge clk);
      end
    endtask
    integer k,m,e,i,t;
    initial begin
      // All kinds/masks/ERR, including malformed requests and every pending phase.
      for(k=0;k<4;k=k+1) for(m=0;m<16;m=m+1) for(e=0;e<2;e=e+1) begin
        cold_init=1; tick(); cold_init=0; kind=k; byte_enable_in=m;
        word_in=transactions*937; data_in=32'hc17ed312 ^ transactions;
        err_in=e; dq_in=16'h5a3c; go=1; tick(); go=0;
        for(i=0;i<60;i=i+1) begin
          soft_reset=(i%7==0); cold_init=(i%13==0 && i<54);
          dq_in=dq_in+16'h139; tick();
        end
        soft_reset=0; cold_init=0; transactions=transactions+1;
      end
      // Deterministic unrestricted streams: also simultaneous go/complete/reset.
      for(t=0;t<300000;t=t+1) begin
        rng=rng^(rng<<13); rng=rng^(rng>>17); rng=rng^(rng<<5);
        go=rng[0]; cold_init=&rng[4:1]; soft_reset=rng[5]; kind=rng[7:6];
        byte_enable_in=rng[11:8]; err_in=rng[12]; dq_in=rng[31:16];
        data_in=rng; word_in=rng[18:0]; tick();
      end
      $display("PASS registered equivalence edges=%0d cases=%0d",edges,transactions); $finish;
    end
endmodule

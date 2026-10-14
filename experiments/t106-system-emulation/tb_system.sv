`timescale 1ns/1ps
// New test model only. arm_executor and its dependencies are unmodified.
module tb_system;
 import "DPI-C" function void system_next(output int op,addr,value,delay);
 import "DPI-C" function void system_reply(input int response,value,tick);
 import "DPI-C" function string system_folder();
 reg fast_clk=0,slow_clk=0,rst=1,start=0,loss=0;
 always #2 fast_clk=~fast_clk;
 always #10 slow_clk=~slow_clk;
 reg [1:0] rv=0,rr=3;reg [241:0] requests=0;
 wire [1:0] ready,reply_valid,credits;wire [96:0] reply;
 reg [15:0] dq=0;reg err=0;
 wire [18:0] word_out;wire ce,oe,we,drive,alias_high,busy,pending,ed,release_due,running;
 wire grant,app_grant,sp,skip,fp,fe,low,permit,fault;
 wire [1:0] be;wire [15:0] dout;wire [56:0] gd;
 wire [63:0] generation,processed;wire [31:0] frame;
 reg [11:0] awaddr=0,araddr=0;reg awvalid=0,wvalid=0,arvalid=0;
 reg [31:0] wdata=0;reg [3:0] wstrb=15;reg bready=1,rready=1;
 wire awready,wready,arready,bvalid,rvalid;wire [1:0] bresp,rresp;wire [31:0] rdata;
 arm_executor dut(
 .fast_clk(fast_clk),.slow_clk(slow_clk),.startup_rst_fast(rst),.startup_rst_slow(rst),
 .qualified_start(start),.loss_slow(loss),.request_valid(rv),.request_ready(ready),
 .request_data(requests),.response_valid(reply_valid),.response_ready(rr),.response_data(reply),
 .dq_in(dq),.err_in(err),.word_out(word_out),.ce(ce),.oe(oe),.we(we),.drive(drive),
 .alias_high(alias_high),.byte_enable(be),.dq_out(dout),.running(running),.busy(busy),
 .pending(pending),.err_due(ed),.release_due(release_due),.grant_debug(grant),
 .app_grant_debug(app_grant),.grant_data_debug(gd),.slot_pulse(sp),.skip_pulse(skip),
 .freeze_pulse(fp),.frozen_execute(fe),.generation(generation),.processed_generation(processed),
 .rule_low(low),.candidate_permit(permit),.frame_id(frame),.credits_debug(credits),.fault(fault),
 .s_axi_awaddr(awaddr),.s_axi_awvalid(awvalid),.s_axi_awready(awready),
 .s_axi_wdata(wdata),.s_axi_wstrb(wstrb),.s_axi_wvalid(wvalid),.s_axi_wready(wready),
 .s_axi_bresp(bresp),.s_axi_bvalid(bvalid),.s_axi_bready(bready),
 .s_axi_araddr(araddr),.s_axi_arvalid(arvalid),.s_axi_arready(arready),
 .s_axi_rdata(rdata),.s_axi_rresp(rresp),.s_axi_rvalid(rvalid),.s_axi_rready(rready));

 // Full address domain; six hidden check positions are NOT a claimed code matrix.
 reg [31:0] data_mem[0:524287];reg [37:0] errors[0:524287];
 reg [37:0] recent=0;reg [31:0] decoded;reg exceeded=0;
 integer trace,inf,appf,k,rc,op,addr,value,delay,slow_cycles=0;
 integer active=-1,serial=0,age=0,active_word=0,active_kind=0;
 integer offered=0,accepted=0,received=0;
 integer inj_time,inj_word,inj_bit,inj_parent,offer_time,offer_owner;
 reg [120:0] offer_packet;
 time t0=0;integer horizon=1200000;reg finished=0;
 string folder;
 initial begin
  folder=system_folder();
  trace=$fopen({folder,"/trace.txt"},"w");
  inf=$fopen({folder,"/injections.txt"},"r");
  appf=$fopen({folder,"/application.txt"},"r");
  if(!trace || !inf || !appf) $fatal(1,"input/output files");
  for(k=0;k<524288;k=k+1) begin data_mem[k]=32'ha5a50000^k;errors[k]=0;end
  rc=$fscanf(inf,"%d %d %d %d\n",inj_time,inj_word,inj_bit,inj_parent);
  if(rc!=4) inj_time=-1;
  rc=$fscanf(appf,"%d %d %h\n",offer_time,offer_owner,offer_packet);
  if(rc!=3) offer_time=-1;
  #400;rst=0;
  forever begin
   system_next(op,addr,value,delay);
   if(op==2) begin
    if(!finished) $fatal(1,"early stop");
    $fdisplay(trace,"END %0t %0d %0d %0d %0d %0d",$time,offered,accepted,received,active,exceeded);
    $fclose(trace);system_reply(0,received,slow_cycles);$finish;
   end
   if(op==3) begin
    @(negedge slow_clk);start=1;
    $fdisplay(trace,"QUALIFIED %0t",$time);
   end else if(op==4) begin
    repeat(delay) @(negedge slow_clk);
   end else if(op==0) begin
    @(negedge slow_clk);araddr=addr;arvalid=1;
    do @(posedge slow_clk);while(!arready);
    @(negedge slow_clk);arvalid=0;
    wait(rvalid);value=rdata;
    @(negedge slow_clk);
   end else if(op==1) begin
    @(negedge slow_clk);awaddr=addr;wdata=value;awvalid=1;wvalid=1;
    do @(posedge slow_clk);while(!(awready && wready));
    @(negedge slow_clk);awvalid=0;wvalid=0;
    wait(bvalid);
    @(negedge slow_clk);
   end else $fatal(1,"unknown bridge op");
   system_reply(op==0?rresp:op==1?bresp:0,op==0?value:finished,slow_cycles);
  end
 end

 always @(negedge slow_clk) if(t0 && !finished) begin
  rr=(($time-t0)%340<80)?0:3;
  if(rv==0 && offer_time>=0 && $time-t0>=offer_time) begin
   requests[offer_owner*121+:121]=offer_packet;rv=offer_owner?2:1;
   $fdisplay(trace,"OFFER %0t %0d %h",$time,offer_owner,offer_packet);offered=offered+1;
   rc=$fscanf(appf,"%d %d %h\n",offer_time,offer_owner,offer_packet);
   if(rc!=3) offer_time=-1;
  end
 end
 always @(posedge slow_clk) begin
  slow_cycles<=slow_cycles+1;
  if(!finished) begin
  if(dut.mailbox.collector.start && !dut.mailbox.collector.started)
   $fdisplay(trace,"RULE_START %0t %h",$time,dut.slow_tick);
  if(dut.event_valid) $fdisplay(trace,"HISTORY %0t %h %h",$time,dut.event_data,dut.slow_tick);
  if(dut.mailbox.collector.cut) $fdisplay(trace,"CUT %0t %h",$time,dut.slow_tick);
  if(dut.mailbox.decision_valid && dut.mailbox.decision_ready)
   $fdisplay(trace,"PROGRAM %0t %h %h",$time,dut.mailbox.snapshot,dut.mailbox.decision);
  if(|(rv & ready) && !finished) begin
   $fdisplay(trace,"ACCEPT %0t %0d %h",$time,dut.owner,dut.chosen);
   accepted=accepted+1;#0.002;rv=0;
  end
  if(|(reply_valid & rr) && !finished) begin
   $fdisplay(trace,"REPLY %0t %0d %h",$time,reply_valid[1],reply);received=received+1;
  end
  if(credits>2) $fatal(1,"credits");
  end
 end
 always @(negedge fast_clk) begin
  if(t0 && !finished) begin
   while(inj_time>=0 && $time-t0>=inj_time) begin
    errors[inj_word]=errors[inj_word]^(38'd1<<inj_bit);
    if(active>=0 && inj_word==active_word) recent[inj_bit]=errors[inj_word][inj_bit];
    if($countones(errors[inj_word])>1) exceeded=1;
    $fdisplay(trace,"INJECT %0t %0d %0d %0d %h %0d",$time,inj_parent,inj_word,inj_bit,errors[inj_word],exceeded);
    rc=$fscanf(inf,"%d %d %d %d\n",inj_time,inj_word,inj_bit,inj_parent);
    if(rc!=4) inj_time=-1;
   end
  end
  // Explicit diagnostic output after SEC exceedance; not guaranteed data.
  decoded=data_mem[word_out];
  if($countones(errors[word_out])>1) decoded=decoded^errors[word_out][31:0];
  dq=alias_high?decoded[31:16]:decoded[15:0];err=errors[word_out]!=0;
 end
 always @(posedge fast_clk) begin
  if(t0 && !finished && $time-t0>=horizon) begin
   finished=1;$fdisplay(trace,"HORIZON %0t %0d %0d %0d %0d",$time,active,busy,credits,pending);
  end
  if(!finished) begin
   if(dut.calendar.slot_due && !t0) begin t0=$time;$fdisplay(trace,"T0 %0t",$time);end
   if(dut.calendar.freeze_due)
    $fdisplay(trace,"FREEZE %0t %0d %h %h %h",$time,($time-t0),permit,dut.local_alarm,dut.calendar.must_execute);
   if(dut.calendar.slot_due)
    $fdisplay(trace,"SLOT %0t %0d %h %h %h",$time,($time-t0),dut.control_due,dut.control_word,busy);
   if(dut.history_change) $fdisplay(trace,"EVENT %0t %h",$time,{dut.generation_next,dut.uptime,dut.loss_fast,ed});
   if(grant) begin
    if(active>=0) $fatal(1,"lock overlap");
    active=serial;serial=serial+1;age=0;active_word=gd[20:2];active_kind=gd[1:0];recent=0;
    $fdisplay(trace,"GRANT %0t %0d %0d %h",$time,active,app_grant,gd);
   end
   #0.001;
   if(active>=0) begin
    if(dut.backend.sample)
     $fdisplay(trace,"OBSERVE %0t %0d %h %h %h %h",$time,active,alias_high,dq,err,errors[active_word]);
    $fdisplay(trace,"PIN %0t %0d %0d %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h",
      $time,active,age,busy,ce,oe,we,drive,alias_high,be,dout,
      dut.backend.sample,dut.backend.flag,dut.backend.done,dut.backend.commit_pulse,
      pending,dut.backend.read_data,word_out,ed,dq,err);
    if(dut.backend.commit_pulse) begin
     errors[active_word]=errors[active_word]&recent;
     if(active_kind==2) begin
      if(be[0]) data_mem[active_word][alias_high*16+:8]=dout[7:0];
      if(be[1]) data_mem[active_word][alias_high*16+8+:8]=dout[15:8];
     end
     $fdisplay(trace,"WRITE %0t %0d %h %h %h %h %h",$time,active,alias_high,dout,be,data_mem[active_word],errors[active_word]);
    end
    if(dut.backend.done) begin $fdisplay(trace,"RELEASE %0t %0d",$time,active);active=-1;end
    age=age+4;
   end
   if(fault) $fatal(1,"DUT fault");
   if(ed && permit) $fatal(1,"stale LOW");
  end
 end
endmodule

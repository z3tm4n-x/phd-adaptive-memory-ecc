`timescale 1ns/1ps
// New test model only. arm_executor and its dependencies are unmodified.
module tb_burst_v2;
 import "DPI-C" function void system_next(output int op,addr,value,delay);
 import "DPI-C" function void system_reply(input int response,value,input longint unsigned tick);
 import "DPI-C" function string system_folder();
 import "DPI-C" function string system_trace_path();
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
 integer trace,inf,appf,k,rc,op,addr,value,delay;
 longint unsigned slow_cycles=0;
 longint active=-1,serial=0;integer age=0,active_word=0,active_kind=0;
 integer offered=0,accepted=0,received=0;
 longint inj_time,offer_time;integer inj_word,inj_bit,inj_parent,offer_owner;
 reg [120:0] offer_packet;
 time t0=0;longint unsigned offset=0,horizon=1200000;reg finished=0;
 longint unsigned false_begin=0,false_end=0,loss_begin=0,loss_end=0;
 integer cfg,jumpfile,fixed_mode; longint unsigned jump_ns,shift_words,skip_done,new_seq;
 reg [767:0] new_packet;reg [255:0] new_decision;
 wire jump_safe=running && !busy && !pending && active<0 && credits==0 &&
  !rv && !dut.app_waiting && !dut.app_receipt && !dut.app_prepared && !dut.reply_pending &&
  !dut.forward_valid && !dut.id_valid && !dut.returned_valid &&
  !dut.event_valid && !dut.event_capture && !dut.event_write &&
  (fixed_mode || dut.mailbox.collector.event_count==0) && !dut.mailbox.snapshot_valid &&
  !dut.mailbox.validating && !dut.mailbox.decision_valid && !dut.mailbox.aw_have && !dut.mailbox.w_have &&
  !dut.candidates.pending && dut.candidates.channel_ready && !dut.candidates.received_valid &&
  !dut.candidates.guard.captured && !dut.candidates.guard.checking &&
  !(dut.calendar.warmup_active && permit) && dut.backend.op==0 && !dut.backend.sampled_err && !dut.backend.second_seen && !fault && !awvalid && !arvalid;
 // Stand-only sparse index. Full arrays remain allocated/addressable.
 integer dirty_words[0:65535],dirty_count=0,di,dw;
 reg dirty_listed[0:524287];
 longint unsigned next_dirty,rel_now,first_index,visit_index,visit_time;
 longint unsigned data_sum,error_sum;integer error_positions,z;
 function automatic longint unsigned slot_time(input longint unsigned j);
  slot_time=(j/8)*1568+(j%8)*164;
 endfunction
 task automatic find_dirty;
  begin
   rel_now=($time+offset)-t0;
   first_index=(rel_now/1568)*8;
   while(slot_time(first_index)<rel_now) first_index=first_index+1;
   next_dirty=64'hffffffffffffffff;di=0;
   while(di<dirty_count) begin
    dw=dirty_words[di];
    if(errors[dw]==0) begin
     dirty_listed[dw]=0;dirty_count=dirty_count-1;dirty_words[di]=dirty_words[dirty_count];
    end else begin
     visit_index=(64'd3*dw)%524288;
     if(visit_index<first_index)
      visit_index=visit_index+((first_index-visit_index+524287)/524288)*524288;
     visit_time=slot_time(visit_index);
     if(visit_time<next_dirty) next_dirty=visit_time;
     di=di+1;
    end
   end
  end
 endtask
 string folder;
 initial begin
  folder=system_folder();
  cfg=$fopen({folder,"/accel.txt"},"r");
  rc=$fscanf(cfg,"%d %d %d %d %d %d\n",horizon,false_begin,false_end,loss_begin,loss_end,fixed_mode);$fclose(cfg);
  if(rc!=6) $fatal(1,"acceleration config");
  trace=$fopen(system_trace_path(),"w");
  inf=$fopen({folder,"/injections.txt"},"r");
  appf=$fopen({folder,"/application.txt"},"r");
  if(!trace || !inf || !appf) $fatal(1,"input/output files");
  for(k=0;k<524288;k=k+1) begin data_mem[k]=32'ha5a50000^k;errors[k]=0;dirty_listed[k]=0;end
  rc=$fscanf(inf,"%d %d %d %d\n",inj_time,inj_word,inj_bit,inj_parent);
  if(rc!=4) inj_time=-1;
  rc=$fscanf(appf,"%d %d %h\n",offer_time,offer_owner,offer_packet);
  if(rc!=3) offer_time=-1;

  #400;rst=0;
  forever begin
   system_next(op,addr,value,delay);
   if(op==2) begin
    if(!finished) $fatal(1,"early stop");
    $fdisplay(trace,"END %0d %0d %0d %0d %0d %0d",(64'd1000*($time+offset)),offered,accepted,received,active,exceeded);
    $fclose(trace);system_reply(0,received,slow_cycles);$finish;
   end
   if(op==8) begin
    find_dirty();
    system_reply(0,next_dirty==64'hffffffffffffffff ? 32'hffffffff : next_dirty-rel_now,slow_cycles);
   end else if(op==7) begin
    system_reply(0,t0,slow_cycles);
   end else if(op==6) begin
    system_reply(0,{28'd0,loss,low,permit,jump_safe},slow_cycles);
   end else if(op==5) begin
    if(!jump_safe || delay<=0 || delay%2) $fatal(1,"unsafe/nonperiodic jump");
    jump_ns=64'd188160*delay;shift_words=(64'd320*delay)%524288;
    find_dirty();
    if((inj_time>=0 && inj_time<rel_now+jump_ns) ||
       (offer_time>=0 && offer_time<rel_now+jump_ns) || next_dirty<rel_now+jump_ns)
      $fatal(1,"nonempty input/dirty word inside jump");
    if(dut.backend.op!=0 || dut.backend.sampled_err || dut.backend.second_seen)
      $fatal(1,"jump must follow a clean completed control");
    if(dut.uptime>64'hffffffffffffffff-jump_ns/4 ||
       dut.slow_tick>64'hffffffffffffffff-jump_ns/20)
      $fatal(1,"jump would overflow mission time");
    if((false_begin && ($time+offset)-t0<false_begin && ($time+offset)-t0+jump_ns>=false_begin) ||
       (false_end && ($time+offset)-t0<false_end && ($time+offset)-t0+jump_ns>=false_end) ||
       (loss_begin && ($time+offset)-t0<loss_begin && ($time+offset)-t0+jump_ns>=loss_begin) ||
       (loss_end && ($time+offset)-t0<loss_end && ($time+offset)-t0+jump_ns>=loss_end))
      $fatal(1,"external input inside jump");
    if(dut.candidates.active && dut.candidates.allowed &&
       dut.slow_tick<dut.candidates.after_tick &&
       dut.slow_tick+jump_ns/20>=dut.candidates.after_tick)
      $fatal(1,"deadline inside jump");
    jumpfile=$fopen({folder,"/jump.txt"},"r");
    rc=$fscanf(jumpfile,"%d %h %h\n",skip_done,new_packet,new_decision);$fclose(jumpfile);
    if(rc!=3) $fatal(1,"jump input");
    new_seq=dut.mailbox.collector.packet_seq+delay;
    if(!fixed_mode && (new_packet[63:0]!=new_seq || new_decision[63:0]!=new_seq ||
       new_packet[191:128]!=generation || new_decision[127:64]!=generation ||
       new_packet[255:192]!=dut.mailbox.snapshot[255:192]+jump_ns/20))
      $fatal(1,"jump sequence/time/generation");
    $fdisplay(trace,"JUMP %0d %0d %0d %0d %0d %0d %h %h",
      (64'd1000*($time+offset)),jump_ns,delay,skip_done,permit,dut.calendar.word_due,new_packet,new_decision);
    offset=offset+jump_ns;
    dut.timestamp.value=dut.timestamp.value+jump_ns/4;
    for(k=0;k<8;k=k+1) dut.timestamp.maximum[k]=(&dut.timestamp.value[k*8+:8]);
    dut.mailbox.collector.tick=dut.mailbox.collector.tick+jump_ns/20;
    if(!fixed_mode) begin
    dut.mailbox.collector.packet_seq=new_seq;
    dut.mailbox.collector.snapshot=new_packet;
    dut.mailbox.stored_sequence=new_seq;
    dut.mailbox.shadow=new_decision;dut.mailbox.checking=new_decision;
    dut.mailbox.decision=new_decision;dut.mailbox.crc=~new_decision[255:224];
    dut.candidates.after_tick=new_decision[191:128];
    end
    dut.calendar.word_due=dut.calendar.word_due+shift_words;
    dut.backend_command[20:2]=dut.backend_command[20:2]+shift_words;
    dut.backend.word_out=dut.backend.word_out+shift_words;
    // Every represented operation is a clean control; materialize its last
    // sample. The memory itself and every live error position are preserved.
    dut.backend.dq_sample=data_mem[dut.backend.word_out][15:0];
    dut.backend.first_copy=data_mem[dut.backend.word_out][15:0];
    dut.backend.low_write=data_mem[dut.backend.word_out][15:0];
    decoded=data_mem[dut.backend.word_out];dq=decoded[15:0];err=0;
    if(dut.calendar.warmup_left<=64'd960*delay) begin
     dut.calendar.warmup_left=0;dut.calendar.warmup_active=0;
    end else dut.calendar.warmup_left=dut.calendar.warmup_left-64'd960*delay;
    dut.event_snapshot[65:2]=dut.event_snapshot[65:2]+jump_ns/4;
    dut.event_staged[65:2]=dut.event_staged[65:2]+jump_ns/4;
    serial=serial+skip_done;
    system_reply(0,0,slow_cycles);
   end else if(op==3) begin
    @(negedge slow_clk);start=1;
    $fdisplay(trace,"QUALIFIED %0d",(64'd1000*($time+offset)));
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
   if(op!=5 && op!=6 && op!=7 && op!=8) system_reply(op==0?rresp:op==1?bresp:0,op==0?value:finished,slow_cycles);
  end
 end

 always @(negedge slow_clk) if(t0 && !finished) begin
  rr=((($time+offset)-t0)%340<80)?0:3;
  loss=loss_begin!=0 && ($time+offset)-t0>=loss_begin && ($time+offset)-t0<loss_end;
  if(rv==0 && offer_time>=0 && ($time+offset)-t0>=offer_time) begin
   requests[offer_owner*121+:121]=offer_packet;rv=offer_owner?2:1;
   $fdisplay(trace,"OFFER %0d %0d %h",(64'd1000*($time+offset)),offer_owner,offer_packet);offered=offered+1;
   rc=$fscanf(appf,"%d %d %h\n",offer_time,offer_owner,offer_packet);
   if(rc!=3) offer_time=-1;
  end
 end
 always @(posedge slow_clk) begin
  slow_cycles<=slow_cycles+1;
  if(!finished) begin
  if(dut.mailbox.collector.start && !dut.mailbox.collector.started)
   $fdisplay(trace,"RULE_START %0d %h",(64'd1000*($time+offset)),dut.slow_tick);
  if(dut.event_valid) $fdisplay(trace,"HISTORY %0d %h %h",(64'd1000*($time+offset)),dut.event_data,dut.slow_tick);
  if(dut.mailbox.collector.cut) $fdisplay(trace,"CUT %0d %h",(64'd1000*($time+offset)),dut.slow_tick);
  if(dut.mailbox.decision_valid && dut.mailbox.decision_ready)
   $fdisplay(trace,"PROGRAM %0d %h %h",(64'd1000*($time+offset)),dut.mailbox.snapshot,dut.mailbox.decision);
  if(|(rv & ready) && !finished) begin
   $fdisplay(trace,"ACCEPT %0d %0d %h",(64'd1000*($time+offset)),dut.owner,dut.chosen);
   accepted=accepted+1;#0.002;rv=0;
  end
  if(|(reply_valid & rr) && !finished) begin
   $fdisplay(trace,"REPLY %0d %0d %h",(64'd1000*($time+offset)),reply_valid[1],reply);received=received+1;
  end
  if(credits>2) $fatal(1,"credits");
  end
 end
 always @(negedge fast_clk) begin
  if(t0 && !finished) begin
   while(inj_time>=0 && ($time+offset)-t0>=inj_time) begin
    if(!dirty_listed[inj_word]) begin
     if(dirty_count>=65536) $fatal(1,"stand sparse capacity");
     dirty_words[dirty_count]=inj_word;dirty_count=dirty_count+1;dirty_listed[inj_word]=1;
    end
    errors[inj_word]=errors[inj_word]^(38'd1<<inj_bit);
    if(active>=0 && inj_word==active_word) recent[inj_bit]=errors[inj_word][inj_bit];
    if($countones(errors[inj_word])>1) exceeded=1;
    $fdisplay(trace,"INJECT %0d %0d %0d %0d %h %0d",(64'd1000*($time+offset)),inj_parent,inj_word,inj_bit,errors[inj_word],exceeded);
    rc=$fscanf(inf,"%d %d %d %d\n",inj_time,inj_word,inj_bit,inj_parent);
    if(rc!=4) inj_time=-1;
   end
  end
  // Explicit diagnostic output after SEC exceedance; not guaranteed data.
  decoded=data_mem[word_out];
  if($countones(errors[word_out])>1) decoded=decoded^errors[word_out][31:0];
  dq=alias_high?decoded[31:16]:decoded[15:0];err=errors[word_out]!=0 ||
   (false_begin!=0 && ($time+offset)-t0>=false_begin && ($time+offset)-t0<false_end);
 end
 reg previous_permit=0,previous_low=0,previous_loss_pin=0;
 always @(posedge fast_clk) begin
  if(permit!=previous_permit || low!=previous_low || loss!=previous_loss_pin) begin
   $fdisplay(trace,"PERMISSION %0d %h %h %h %h %h %h",(64'd1000*($time+offset)),permit,low,loss,generation,processed,dut.candidates.after_tick);
   previous_permit=permit;previous_low=low;previous_loss_pin=loss;
  end
  if(t0 && !finished && ($time+offset)-t0>=horizon) begin
   finished=1;$fdisplay(trace,"HORIZON %0d %0d %0d %0d %0d",(64'd1000*($time+offset)),active,busy,credits,pending);
   data_sum=0;error_sum=0;error_positions=0;
   for(z=0;z<524288;z=z+1) begin
    data_sum=data_sum+(64'd1+z)*data_mem[z];
    error_sum=error_sum+(64'd1+2*z)*errors[z];
    error_positions=error_positions+$countones(errors[z]);
   end
   $fdisplay(trace,"STATE %0d %h %h %0d %0d",(64'd1000*($time+offset)),data_sum,error_sum,error_positions,exceeded);
  end
  if(!finished) begin
   if(dut.calendar.slot_due && !t0) begin t0=($time+offset);$fdisplay(trace,"T0 %0d",(64'd1000*($time+offset)));end
   if(dut.calendar.freeze_due)
    $fdisplay(trace,"FREEZE %0d %0d %h %h %h",(64'd1000*($time+offset)),(($time+offset)-t0),permit,dut.local_alarm,dut.calendar.must_execute);
   if(dut.calendar.slot_due)
    $fdisplay(trace,"SLOT %0d %0d %h %h %h",(64'd1000*($time+offset)),(($time+offset)-t0),dut.control_due,dut.control_word,busy);
   if(dut.history_change) $fdisplay(trace,"EVENT %0d %h",(64'd1000*($time+offset)),{dut.generation_next,dut.uptime,dut.loss_fast,ed});
   if(grant) begin
    if(active>=0) $fatal(1,"lock overlap");
    active=serial;serial=serial+1;age=0;active_word=gd[20:2];active_kind=gd[1:0];recent=0;
    $fdisplay(trace,"GRANT %0d %0d %0d %h",(64'd1000*($time+offset)),active,app_grant,gd);
   end
   #0.001;
   if(active>=0) begin
    if(dut.backend.sample)
     $fdisplay(trace,"OBSERVE %0d %0d %h %h %h %h",(64'd1000*($time+offset)),active,alias_high,dq,err,errors[active_word]);
    $fdisplay(trace,"PIN %0d %0d %0d %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h",
      (64'd1000*($time+offset)),active,age,busy,ce,oe,we,drive,alias_high,be,dout,
      dut.backend.sample,dut.backend.flag,dut.backend.done,dut.backend.commit_pulse,
      pending,dut.backend.read_data,word_out,ed,dq,err);
    if(dut.backend.commit_pulse) begin
     errors[active_word]=errors[active_word]&recent;
     if(active_kind==2) begin
      if(be[0]) data_mem[active_word][alias_high*16+:8]=dout[7:0];
      if(be[1]) data_mem[active_word][alias_high*16+8+:8]=dout[15:8];
     end
     $fdisplay(trace,"WRITE %0d %0d %h %h %h %h %h",(64'd1000*($time+offset)),active,alias_high,dout,be,data_mem[active_word],errors[active_word]);
    end
    if(dut.backend.done) begin $fdisplay(trace,"RELEASE %0d %0d",(64'd1000*($time+offset)),active);active=-1;end
    age=age+4;
   end
   if(fault) $fatal(1,"DUT fault");
   if(ed && permit) $fatal(1,"stale LOW");
  end
 end
endmodule

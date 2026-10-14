// Single-master AXI4-Lite peripheral, 50MHz. This is protocol logic, not
// an ARM latency model. AW and W are independently held. Partial writes
// cannot publish: all 32 bytes and the final CRC/commit must be present.
module rule_mailbox(
 input wire clk,start,event_valid,input wire [129:0] event_data,
 input wire history_fault,
 input wire [11:0] s_axi_awaddr,input wire s_axi_awvalid,output wire s_axi_awready,
 input wire [31:0] s_axi_wdata,input wire [3:0] s_axi_wstrb,
 input wire s_axi_wvalid,output wire s_axi_wready,
 output reg [1:0] s_axi_bresp=0,output reg s_axi_bvalid=0,input wire s_axi_bready,
 input wire [11:0] s_axi_araddr,input wire s_axi_arvalid,output wire s_axi_arready,
 output reg [31:0] s_axi_rdata=0,output reg [1:0] s_axi_rresp=0,
 output reg s_axi_rvalid=0,input wire s_axi_rready,
 output reg decision_valid=0,input wire decision_ready,output reg [255:0] decision=0,
 output wire [63:0] tick,output wire fault
);
 wire snapshot_valid,collector_fault;
 wire [767:0] snapshot;
 reg snapshot_request=0,snapshot_ack=0,protocol_fault=0,start_seen=0;
 reg aw_have=0,w_have=0;
 reg [11:0] awaddr=0;
 reg [31:0] wdata=0;reg [3:0] wstrb=0;
 reg [255:0] shadow=0,checking=0;
 reg [31:0] written=0,crc=0;
 reg [2:0] word_index=0;
 reg validating=0;
 reg [63:0] stored_sequence=0;
 assign fault=collector_fault || protocol_fault;
 history_batch collector(.clk(clk),.start(start),.event_valid(event_valid),.event_data(event_data),
  .history_fault(history_fault||protocol_fault),.snapshot_request(snapshot_request),
  .snapshot_ack(snapshot_ack),.snapshot_valid(snapshot_valid),.snapshot(snapshot),
  .tick(tick),.fault(collector_fault));
 assign s_axi_awready=!aw_have && !s_axi_bvalid && !validating && !decision_valid;
 assign s_axi_wready=!w_have && !s_axi_bvalid && !validating && !decision_valid;
 assign s_axi_arready=!s_axi_rvalid;
 function [31:0] crc_word;
  input [31:0] initial_crc;input [31:0] b;
  reg [31:0] c;integer k;
  begin c=initial_crc;for(k=0;k<32;k=k+1)
   c=(c>>1)^((c[0]^b[k])?32'hedb88320:32'd0);
   crc_word=c;
  end
 endfunction
 wire [31:0] crc_next=crc_word(crc,checking[word_index*32+:32]);
 wire content_good=checking[63:0]==snapshot[63:0] &&
   checking[127:64]==snapshot[191:128] &&
   (checking[223:192]==0 || checking[223:192]==1 || checking[223:192]==2) &&
   (checking[223:192]!=1 || checking[191:128]>=snapshot[255:192]);
 integer b;
 always @(posedge clk) begin
  snapshot_request<=0;snapshot_ack<=0;
  if(start) start_seen<=1;
  if(s_axi_bvalid && s_axi_bready) s_axi_bvalid<=0;
  if(s_axi_rvalid && s_axi_rready) s_axi_rvalid<=0;
  if(decision_valid && decision_ready) begin
   decision_valid<=0;snapshot_ack<=1;written<=0;
   stored_sequence<=decision[63:0];
  end
  if(s_axi_awvalid && s_axi_awready) begin awaddr<=s_axi_awaddr;aw_have<=1;end
  if(s_axi_wvalid && s_axi_wready) begin wdata<=s_axi_wdata;wstrb<=s_axi_wstrb;w_have<=1;end
  if(aw_have && w_have && !s_axi_bvalid && !validating && !decision_valid) begin
   aw_have<=0;w_have<=0;s_axi_bresp<=0;s_axi_bvalid<=1;
   if(awaddr[1:0]!=0) s_axi_bresp<=2;
   else if(awaddr==12'h004) begin
    if(wstrb!=15 || wdata!=1 || snapshot_valid || !start_seen) s_axi_bresp<=2;
    else begin snapshot_request<=1;written<=0;end
   end else if(awaddr==12'h00c) begin
    if(wstrb!=15 || wdata!=1) s_axi_bresp<=2;
    else protocol_fault<=1;
   end else if(awaddr>=12'h200 && awaddr<12'h220) begin
    for(b=0;b<4;b=b+1) if(wstrb[b]) begin
     shadow[awaddr[4:2]*32+b*8+:8]<=wdata[b*8+:8];
     written[awaddr[4:2]*4+b]<=1;
    end
   end else if(awaddr==12'h008) begin
    if(wstrb!=15 || wdata!=1 || !snapshot_valid || written!=32'hffffffff) s_axi_bresp<=2;
    else begin
     checking<=shadow;crc<=32'hffffffff;word_index<=0;
     validating<=1;s_axi_bvalid<=0;
    end
   end else s_axi_bresp<=2;
  end
  if(validating) begin
   crc<=crc_next;word_index<=word_index+1'b1;
   if(word_index==6) begin
    validating<=0;s_axi_bvalid<=1;
    if(~crc_next==checking[255:224] && content_good) begin
     decision<=checking;decision_valid<=1;s_axi_bresp<=0;
    end else begin s_axi_bresp<=2;protocol_fault<=1;end
   end
  end
  if(s_axi_arvalid && s_axi_arready) begin
   s_axi_rvalid<=1;s_axi_rresp<=0;s_axi_rdata<=0;
   if(s_axi_araddr[1:0]!=0) s_axi_rresp<=2;
   else if(s_axi_araddr==0)
    s_axi_rdata<={27'd0,fault,start_seen,decision_valid,validating,snapshot_valid};
   else if(s_axi_araddr==12'h010) s_axi_rdata<=stored_sequence[31:0];
   else if(s_axi_araddr==12'h014) s_axi_rdata<=stored_sequence[63:32];
   else if(s_axi_araddr>=12'h100 && s_axi_araddr<12'h160 && snapshot_valid)
    s_axi_rdata<=snapshot[(s_axi_araddr-12'h100)*8+:32];
   else s_axi_rresp<=2;
  end
 end
endmodule

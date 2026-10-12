// Same visible edge contract as registered/e_backend_registered.sv.
// All pin enables are prepared one cycle BEFORE the pin event. Native
// active-low pin registers avoid an inverter between FF and OLOGIC.
module e_backend_registered #(
 parameter integer WORD_BITS=19,PREVALIDATED=0
)(
 input wire clk,cold_init,soft_reset,go,
 input wire [1:0] kind,input wire [WORD_BITS-1:0] word_in,
 input wire [31:0] data_in,input wire [3:0] byte_enable_in,
 input wire [15:0] dq_in,input wire err_in,
 output wire ready,output reg busy,accepted,rejected,fault,
 (* IOB="TRUE" *) output reg [WORD_BITS-1:0] word_out,
 output wire ce,oe,we,drive,
 (* IOB="TRUE" *) output reg alias_high,
 output wire [1:0] byte_enable,
 (* IOB="TRUE" *) output reg [15:0] dq_out,
 output reg sample,flag,output wire err_due,
 output reg done,release_due,commit_pulse,
 output wire pending,output wire [31:0] read_data,
 output wire [1:0] kind_active,output reg [7:0] age,
 // Synchronous I/O R/S pins have a substantially larger setup requirement
 // than D on this device. Preserve Boolean behavior, use the D input.
 (* IOB="TRUE", EXTRACT_RESET="no", EXTRACT_ENABLE="no" *) output reg pad_ce_n,pad_oe_n,pad_we_n,
 (* IOB="TRUE", EXTRACT_RESET="no", EXTRACT_ENABLE="no" *) output reg [1:0] pad_be_n,
 (* IOB="TRUE", DONT_TOUCH="TRUE" *) output reg [15:0] pad_t_n
);
 initial begin
  busy=0;accepted=0;rejected=0;fault=0;word_out=0;alias_high=0;dq_out=0;
  sample=0;flag=0;done=0;release_due=0;commit_pulse=0;age=0;
  pad_ce_n=1;pad_oe_n=1;pad_we_n=1;pad_be_n=0;pad_t_n=16'hffff;
 end
 reg [53:0] step=0;
 reg [1:0] op=0;
 reg is_control=1,is_read=0,is_write=0;
 reg [31:0] requested=0;
 reg [3:0] mask=15;
 // Semantic observability retains the original idle value. Physical byte
 // enables are restored while CE is inactive, before the next operation.
 reg [1:0] semantic_be_n=0;
 // One physical input sample register per pin, shared between the aliases.
 // No early sampling: updates at the exact old60/152 edges only.
 (* IOB="TRUE" *) reg [15:0] dq_sample=0;
 (* IOB="TRUE" *) reg sampled_err=0;
 reg first_seen=0,second_seen=0,first_pulse=0;
 reg [15:0] first_copy=0,low_write=0;
 reg read_on=0,first_capture=0,second_capture=0;
 reg read_off=0,first_write=0,first_commit=0,first_drive_off=0;
 reg second_alias=0,second_drive=0,second_we=0,second_commit=0,second_drive_off=0;
 reg release_arm=0;
 reg drive_level=0;
 reg alias_level=0;
 reg first_read_level=0,first_repair_level=0;
 reg second_read_level=0,second_write_level=0;
 reg [15:0] dq_level=0;
 wire accept=go && !busy && !(cold_init && !busy) && (PREVALIDATED || (kind!=3 && byte_enable_in!=0));
 wire repairing=is_write || (is_control && sampled_err);
 assign ready=!busy;
 assign ce=!pad_ce_n;assign oe=!pad_oe_n;assign we=!pad_we_n;
 assign drive=!pad_t_n[0];assign byte_enable=~semantic_be_n;
 assign read_data={second_seen?dq_sample:16'd0,first_seen?(second_seen?first_copy:dq_sample):16'd0};
 assign err_due=first_pulse && sampled_err;
 assign pending=busy && first_seen && repairing;
 assign kind_active=op;

 // Pure sampling FFs can occupy ILOGIC. Other state never causes a pin to
 // be sampled at a different instant; masks below reproduce init/read_data.
 always @(posedge clk) begin
  if(first_capture || second_capture) dq_sample<=dq_in;
  if(first_capture) sampled_err<=err_in;
  if(!second_seen) first_copy<=dq_sample;
  // OLOGIC tristate FF has no fabric feedback; its level is prepared one
  // edge earlier in fabric, then copied identically at all sixteen pads.
  pad_t_n<={16{!drive_level}};
  dq_out<=dq_level;
  // Prepare the alias one edge early, just like DQ/T. The pad FF has no
  // busy-driven reset/enable path. Clearing follows the old idle edge.
  alias_high<=alias_level;
  if((step[21] && is_read) || (step[35] && is_write)) alias_level<=1;
  if(release_due || (cold_init && !busy)) alias_level<=0;
  // Encode the active windows before the pad edge. No complex CE/SET
  // extraction on remote OLOGIC. At64 the just-captured ERR is still used
  // on the SAME edge as in the reference, not delayed or resampled.
  pad_ce_n<=!(first_read_level ||
    (first_repair_level && (is_write || sampled_err)) ||
    second_read_level || second_write_level);
  pad_oe_n<=!(first_read_level || second_read_level);
  if(accept) first_read_level<=1;
  if(step[14]) begin first_read_level<=0;first_repair_level<=!is_read;end
  if(step[31]) first_repair_level<=0;
  if(step[22] && is_read) second_read_level<=1;
  if(step[37]) second_read_level<=0;
  if(step[36] && is_write) second_write_level<=1;
  if(step[48]) second_write_level<=0;
  if(cold_init && !busy) begin
   first_read_level<=0;first_repair_level<=0;second_read_level<=0;second_write_level<=0;
  end
  if((step[21] && repairing) || (step[36] && is_write)) drive_level<=1;
  if(step[21] && repairing) dq_level<=low_write;
  if(step[36] && is_write) dq_level<=requested[31:16];
  if(step[33] || step[50] || release_arm || (cold_init && !busy)) begin
   drive_level<=0;dq_level<=0;
  end
 end
 always @(posedge clk) begin
  accepted<=0;rejected<=0;done<=0;sample<=first_capture || second_capture;
  // Command type is known well before sampling. Prequalify this pulse,
  // never delay ERR after its capture/publication edge.
  first_pulse<=first_capture && !is_read;flag<=err_due;commit_pulse<=0;
  // One-hot phase is an observation/control source; no wide age comparator.
  step<={step[52:0],1'b0};
  read_on<=step[22] && is_read;
  first_capture<=step[13];second_capture<=step[36] && is_read;
  read_off<=step[14];first_write<=step[21] && repairing;
  first_commit<=step[31] && repairing;
  first_drive_off<=step[33];second_alias<=step[35] && is_write;
  second_drive<=step[36] && is_write;
  second_we<=step[38] && is_write;
  second_commit<=step[48] && is_write;
  second_drive_off<=step[50];
  release_arm<=(step[20] && is_control && !repairing) ||
               (step[34] && is_control && repairing) ||
               (step[43] && is_read) || (step[51] && is_write);
  release_due<=release_arm;
  if(busy) age<=age+8'd4;
  if(soft_reset || (cold_init && busy)) fault<=1;
  if(first_capture) first_seen<=1;
  if(second_capture) second_seen<=1;
  if(step[16]) low_write<={is_write && mask[1]?requested[15:8]:dq_sample[15:8],
                          is_write && mask[0]?requested[7:0]:dq_sample[7:0]};
  if(first_write) pad_we_n<=0;
  if(first_commit || second_commit) begin pad_we_n<=1;commit_pulse<=1;end
  if(second_alias) begin pad_be_n<=~mask[3:2];semantic_be_n<=~mask[3:2];end
  if(second_we) pad_we_n<=0;
  if(release_due) begin
   // All three pins are already inactive at the proved release boundary.
   // Do not re-route the broad release signal into remote I/O set pins.
   busy<=0;done<=1;
   step<=0;
  end
  if(!busy) begin
   pad_be_n<=0;
   if(go && !accept) begin rejected<=1;fault<=1;end
  end
  if(accept) begin
   busy<=1;accepted<=1;age<=0;step<=1;read_on<=1;
   op<=kind;is_control<=kind==0;is_read<=kind==1;is_write<=kind==2;
   word_out<=word_in;requested<=data_in;mask<=byte_enable_in;
   first_seen<=0;second_seen<=0;semantic_be_n<=0;
  end
  if(cold_init && !busy) begin
   busy<=0;accepted<=0;rejected<=0;fault<=0;age<=0;step<=0;
   op<=0;is_control<=1;is_read<=0;is_write<=0;requested<=0;mask<=15;
   first_seen<=0;second_seen<=0;first_pulse<=0;sample<=0;
   word_out<=0;pad_be_n<=0;semantic_be_n<=0;
   pad_we_n<=1;
   read_on<=0;first_capture<=0;second_capture<=0;read_off<=0;
   first_write<=0;first_commit<=0;first_drive_off<=0;second_alias<=0;
   second_drive<=0;second_we<=0;second_commit<=0;second_drive_off<=0;release_arm<=0;
  end
 end
endmodule

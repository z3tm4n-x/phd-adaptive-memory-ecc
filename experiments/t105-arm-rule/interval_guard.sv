// The fast side receives a precomputed Boolean only AFTER the slow-side
// deadline. It does not implement NW/NH/NR, pairing or the history filter.
// Generation changes must coincide with invalidate, as in accepted B.
module interval_guard(
 input wire clk,valid,input wire [64:0] data,output wire ready,
 input wire [63:0] generation,input wire invalidate,loss,
 output wire permit,output reg installed=0
);
 reg captured=0,checking=0,uninterrupted=0,cached=0;
 reg [64:0] payload=0;
 reg [3:0] equal_generation=0;
 assign ready=!captured && !checking;
 assign permit=cached && !invalidate && !loss;
 always @(posedge clk) begin
  installed<=0;
  captured<=valid && ready;
  if(valid && ready) begin payload<=data;uninterrupted<=!invalidate && !loss;end
  checking<=captured;
  equal_generation<={payload[64:49]==generation[63:48],
                     payload[48:33]==generation[47:32],
                     payload[32:17]==generation[31:16],
                     payload[16:1]==generation[15:0]};
  if(checking && (&equal_generation) && uninterrupted && !invalidate && !loss) begin
   cached<=payload[0];installed<=1;
  end
  if(invalidate || loss) begin cached<=0;uninterrupted<=0;end
 end
endmodule

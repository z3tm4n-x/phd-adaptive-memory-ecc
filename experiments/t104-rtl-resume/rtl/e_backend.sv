// New T104/T114 backend; no code from the accepted A / old executor.
// Pins below are active-high semantic enables. Board wrappers invert as needed.
// cold_init is qualified initialization only; soft_reset must NEVER clear pending.
module e_backend #(
    parameter integer WORD_BITS = 19
)(
    input wire clk, cold_init, soft_reset,
    input wire go,
    input wire [1:0] kind,             // 0 control E, 1 read32, 2 observed write32
    input wire [WORD_BITS-1:0] word_in,
    input wire [31:0] data_in,
    input wire [3:0] byte_enable_in,
    input wire [15:0] dq_in,
    input wire err_in,                 // coherent with dq_in, not an independent CDC
    output wire ready,
    output reg busy,
    output reg accepted, rejected,
    output reg fault,
    output reg [WORD_BITS-1:0] word_out,
    output wire ce, oe, we, drive, alias_high,
    output wire [1:0] byte_enable,
    output wire [15:0] dq_out,
    output wire sample, flag, err_due, done, commit_pulse, pending,
    output wire [31:0] read_data,
    output reg [7:0] age
);
    initial begin
        busy=0; accepted=0; rejected=0; fault=0; word_out=0; age=0;
    end
    localparam [1:0] CONTROL = 0, READ32 = 1, WRITE32 = 2;
    reg [1:0] op = 0;
    reg [31:0] requested = 0;
    reg [3:0] mask = 15;
    reg [15:0] low_data = 0, high_data = 0;
    reg captured_err = 0;
    reg completed = 0;
    wire repairing = op == WRITE32 || (op == CONTROL && captured_err);
    wire [7:0] end_age = op == WRITE32 ? 8'd216 : op == READ32 ? 8'd184 :
                         repairing ? 8'd148 : 8'd92;
    wire [7:0] next_age = age + 8'd4;
    wire alive = busy || completed;
    wire second_read = op == READ32 && age >= 92;
    wire second_write = op == WRITE32 && age >= 148;
    wire [15:0] merged_low = {
        (op == WRITE32 && mask[1]) ? requested[15:8] : low_data[15:8],
        (op == WRITE32 && mask[0]) ? requested[7:0] : low_data[7:0]
    };

    assign ready = !busy;
    assign alias_high = alive && (second_read || second_write);
    assign byte_enable = second_write ? mask[3:2] : 2'b11;
    assign ce = busy && ((age >= 4 && age < 64)
                     || (repairing && age >= 64 && age < 132)
                     || (second_read && age >= 96 && age < 156)
                     || (second_write && age >= 152 && age < 200));
    assign oe = busy && ((age >= 4 && age < 64)
                     || (second_read && age >= 96 && age < 156));
    assign we = busy && ((repairing && age >= 92 && age < 132)
                     || (second_write && age >= 160 && age < 200));
    assign drive = busy && ((repairing && age >= 92 && age < 140)
                        || (second_write && age >= 152 && age < 208));
    assign dq_out = drive ? (second_write ? requested[31:16] : merged_low) : 16'd0;
    assign sample = busy && (age == 60 || (op == READ32 && age == 152));
    assign flag = busy && age == 64 && op != READ32 && captured_err;
    // A same-clock consumer uses this BEFORE the edge that publishes flag.
    // Using flag at that edge would silently delay priority by one core cycle.
    assign err_due = busy && age == 60 && op != READ32 && captured_err;
    assign done = completed;
    assign commit_pulse = alive && ((repairing && age == 132)
                                || (op == WRITE32 && age == 200));
    assign pending = busy && repairing && age >= 60;
    assign read_data = {high_data, low_data};

    always @(posedge clk) begin
        accepted <= 0;
        rejected <= 0;
        completed <= 0;
        if (cold_init && !busy) begin
            op <= 0; requested <= 0; mask <= 15; age <= 0;
            low_data <= 0; high_data <= 0; captured_err <= 0;
            word_out <= 0; fault <= 0;
        end else begin
            if (soft_reset || cold_init) fault <= 1;
            if (busy) begin
                age <= next_age;
                if (next_age == 60) begin
                    low_data <= dq_in;
                    captured_err <= err_in;
                end
                if (op == READ32 && next_age == 152) high_data <= dq_in;
                if (next_age == end_age) begin
                    busy <= 0;
                    completed <= 1;
                end
            end else if (go) begin
                if (kind == 3 || byte_enable_in == 0) begin
                    rejected <= 1;
                    fault <= 1;
                end else begin
                    busy <= 1; accepted <= 1; age <= 0;
                    op <= kind; word_out <= word_in; requested <= data_in;
                    mask <= byte_enable_in; captured_err <= 0;
                    low_data <= 0; high_data <= 0;
                end
            end
        end
    end
endmodule

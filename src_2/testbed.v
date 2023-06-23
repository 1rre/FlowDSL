module GeneratedModule(
    input clk,
    input reset_n,
    input [31:0] in0,
    input [31:0] in1,
    output [31:0] out0
);
  reg [31:0] gen_0;
  reg [31:0] yy;
  reg [31:0] gen_1;
  reg [31:0] buffer_in0_1;
  reg [31:0] buffer_in0_2;
  reg [31:0] buffer_in0_3;
  reg [31:0] buffer_in0_4;
  reg [31:0] buffer_in0_5;
  reg [31:0] buffer_in0_6;
  reg [31:0] buffer_gen_0_1;
  reg [31:0] buffer_gen_0_2;
  initial begin
    gen_0 = 0;
    yy = 0;
    gen_1 = 0;
    buffer_in0_1 = 0;
    buffer_in0_2 = 0;
    buffer_in0_3 = 0;
    buffer_in0_4 = 0;
    buffer_in0_5 = 0;
    buffer_in0_6 = 0;
    buffer_gen_0_1 = 0;
    buffer_gen_0_2 = 0;
  end
  assign out0 = gen_1;
  always @(posedge clk) begin
    buffer_in0_1 <= in0;
    buffer_in0_2 <= buffer_in0_1;
    buffer_in0_3 <= buffer_in0_2;
    buffer_in0_4 <= buffer_in0_3;
    buffer_in0_5 <= buffer_in0_4;
    buffer_in0_6 <= buffer_in0_5;
    buffer_gen_0_1 <= gen_0;
    buffer_gen_0_2 <= buffer_gen_0_1;
    gen_0 <= buffer_in0_2 + gen_0;
    yy <= gen_0 + buffer_in0_6;
    gen_1 <= buffer_gen_0_2 + yy;
  end
endmodule


module main;
  reg [31:0] in0;
  reg clk;
  wire [31:0] out0;
  GeneratedModule g (
    .in0(in0),
    .clk(clk),
    .out0(out0)
  );
  initial forever begin
    clk = 0;
    #5;
    clk = 1;
    #5;
  end
  initial 
    begin
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      @(posedge clk);
      $finish ;
    end
endmodule 


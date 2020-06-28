module top (
clk,
in0,
in1,
out0,
out1,
out2
);

input clk;
input [1:0] in0;
input in1;
output out0;
output [7:0] out1;
output out2;

wire [7:0] w0;
wire w1;
m2 i2 (.clk(), .in({in0[1],in1,in0[0]}), .out(out2) );
endmodule

module m2(
clk,out,in
);

input clk;
input [2:0] in;
output out;
wire [2:0] w0;

buffer dmy_00 (.in0(in[0]), .in1(in[1]), .out(w0[0]));
buffer dmy_01 (.in0(in[2]), .in1(w0[0]), .out(out));


endmodule

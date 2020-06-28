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
m4 ddd (.clk(), .in(w1), .out(out2) );
m0 i0 (.clk(clk), .in0({in1,w0[7:1]}),.in1({in0[1],clk}), .out0(out1),.out1(out0));
m1 #(77) i1 (
.clk(clk), .in0(out1),.in1(in1), .out0(w1),.out1(w0[7:0])
);
m2 i2 (.clk(), .in(w1), .out(out2) );
endmodule

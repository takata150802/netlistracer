module m1(
clk,
in0,
in1,
out0,
out1
);

input clk;
input in0;
input in1;
output out0;
output [7:0] out1;

m2 i2(.clk(clk),.in(), .out(out0));
m2 i3(.clk(clk),.in(), .out(out1));
endmodule

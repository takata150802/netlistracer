module m2(
clk,out
);

input clk;
input in;
output out;

buffer dmy_m2 (.clk(), .in(in), .out(out));

endmodule

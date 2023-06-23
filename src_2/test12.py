from flow.flow.graph import Graph

# This requires 1 iteration of lower limits

gr = Graph()

in0 = gr.istream(32)
in1 = gr.istream(32)
#x = in0 + in1.offset(1)
#y = in0.offset(1) + in1.offset(2)
xx = (in0.offset(-1) + gr.forward_ref("xx").offset(-1)).offset(2)

yy = xx.offset(1) + in0.offset(-1)

out0 = gr.ostream(xx + yy, 32)

# Buffering twice - once to make offset and once after

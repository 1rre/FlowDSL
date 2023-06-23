from flow.flow.graph import Graph

# This requires 1 iteration of lower limits

gr = Graph()

in0 = gr.istream(32)
sl1 = in0[0:16]
sl2 = in0[16:32]
in1 = sl1 @ sl2 + in0

out0 = gr.ostream(in1, 32)

# Buffering twice - once to make offset and once after

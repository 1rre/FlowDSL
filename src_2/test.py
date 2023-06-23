from flow.flow.graph import Graph

# This requires 2 iterations of lower limits

gr = Graph()

avg_window = 4

# @ 0

avg_window = 4
in0 = gr.istream(32)
t_0 = in0 - in0.offset(-avg_window + 1)
total = t_0 + gr.forward_ref("total").offset(-1)
c1 = gr.const(avg_window)
div_t = total / c1
out0 = gr.ostream(div_t, 32)
from flow.flow.graph import Graph

# This requires 2 iterations of lower limits

gr = Graph()

avg_window = 4

# @ 0
in0 = gr.istream()
in0_off = in0#.offset(-4)
# I think this is a bug from offsetting by 0?
in0_off2 = in0_off.offset(avg_window)
t_0 = in0_off2 - in0_off
total_off = gr.forward_ref("total").offset(-1)
total = t_0 + total_off
c1 = gr.const(avg_window)
div_t = total // c1
out0 = gr.ostream(div_t)

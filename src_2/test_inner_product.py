from flow.flow.graph import Graph

# This requires 1 iteration of lower limits

gr = Graph()

in0 = gr.istream(32)
in1 = gr.istream(32)

current = in0 * in1

sum_out = gr.forward_ref("sum_out").offset(-1).with_reset(0) + current
#sum_out = +current

out0 = gr.ostream(sum_out, 32)

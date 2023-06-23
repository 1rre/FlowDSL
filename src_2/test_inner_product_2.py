from flow.flow.graph import Graph

# This requires 1 iteration of lower limits

gr = Graph()

in0 = gr.istream(32)
in1 = gr.istream(32)

base = in0 * in1

sum_c = (reset_n - gr.const(1)) * gr.forward_ref("sum_c").offset(-1) + base
sum_d =  reset_n * gr.forward_ref("sum_d").offset(-1) + base

sum = sum_c + sum_d

sum_out = reset_n * sum

out0 = gr.ostream(sum_out, 32)

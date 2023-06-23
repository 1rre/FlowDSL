from flow.flow.graph import Graph

# This does not resolve with iterations of lower limits
# This means an equivilance needs to be found/an error returned
# This is because it cannot be drawn as a graph

gr = Graph()
in0 = gr.istream()
in1 = gr.istream()

current = in0 * in1
sum_out = current + gr.forward_ref("sum_out").offset(-1)

out0 = gr.ostream(sum_out)
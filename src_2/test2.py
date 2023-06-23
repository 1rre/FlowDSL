from flow.flow.graph import Graph

# This requires 1 iteration of lower limits

gr = Graph()

in0 = gr.istream()
add1 = in0 + in0.offset(-1)
add2 = add1 + in0.offset(-2)
add3 = add2 + in0.offset(-3)
div0 = add3 // gr.const(4)

out0 = gr.ostream(div0, 32)

# Buffering twice - once to make offset and once after

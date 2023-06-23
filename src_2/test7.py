from flow.flow.graph import Graph

# This does not resolve with iterations of lower limits
# This means an equivilance needs to be found/an error returned
# This is because it cannot be drawn as a graph

gr = Graph()

in0 = gr.istream()
x = gr.forward_ref("y").offset(-1)
y = x.offset(1)
out0 = gr.ostream(x)
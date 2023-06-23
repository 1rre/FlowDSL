from flow.flow.graph import Graph

# This does not resolve with iterations of lower limits
# This means an equivilance needs to be found/an error returned
# This is because it cannot be drawn as a graph

gr = Graph()

in0 = gr.istream()
in1 = gr.istream()

quo_init = gr.const(0)

for i in range(1, 5):
  quo_init = in0 + quo_init

out0 = gr.ostream(in0 // quo_init)

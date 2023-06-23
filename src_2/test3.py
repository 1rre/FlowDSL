from flow.flow.graph import Graph

# This requires 1 iteration of lower limits

gr = Graph()

in0 = gr.istream()
x = in0 + gr.const(1)
y = x + x
z = y // x.offset(1)
out = gr.ostream(z)

gr.resolve()



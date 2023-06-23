from flow.flow.graph import Graph

# This requires 1 iteration of lower limits
# Note that x occurs before t = 0

gr = Graph()

in0 = gr.istream()
x = in0.offset(-1) + gr.const(1)
y = x + x
z = y // x
out = gr.ostream(z)

gr.resolve()

# REWRITTEN:
# in0 = gr.istream
# y = x.offset(1) + x.offset(1)
# z = y // x.offset(1)
# out = gr.ostream(z)

# Interestingly this can be optimised to just "out = 2"
# Is it worth a step for this?

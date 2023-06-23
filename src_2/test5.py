from flow.flow.graph import Graph

# This does not resolve with iterations of lower limits
# This means an equivilance needs to be found/an error returned
# This is because it cannot be drawn as a graph

gr = Graph()

in0 = gr.istream().offset(-2)
x = in0 + gr.forward_ref("z").offset(1)
y = x - in0.offset(1)
z = y - in0.offset(-1)
out0 = gr.ostream(z)

#f = input()
#x = f(t) + z(t+1)
#y = x(t) - f(t+1)
#z = y(t) - f(t-1)

#x = f(t) + y(t+1) - f(t)
#x = y(t+1)
#y = x(t) - f(t+1)
#y = y(t+1) - f(t+1)
#y(t+1) = y(t) + f(t+1)
#y = y(t-1) + f(t)
#z = y(t) - f(t-1)


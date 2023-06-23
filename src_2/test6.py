from flow.flow.graph import Graph

# This takes 2 iterations of lower limits
# This is a rewritten form of test 5

gr = Graph()

in0 = gr.istream()
y = gr.forward_ref("y").offset(-1) + in0.offset(-1)
z = y - in0.offset(-1)
out0 = gr.ostream(z)

gr.resolve()

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

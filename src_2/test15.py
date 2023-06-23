from flow.flow.graph import Graph
from flow.flow.node import Node

# This requires 1 iteration of lower limits

gr = Graph()

screen_width = 480

r_in = gr.istream(8)



def apply_kernel(
    gr: Graph, in0: Node, kernel: list[list[int]], divisor: int = None
) -> Node:
  assert len(kernel)  > 0
  assert len(kernel[0]) > 0
  mid_y = (len(kernel) + 1) // 2
  mid_x = (len(kernel[0]) + 1) // 2
  divisor = sum(map(sum, kernel))
  out = None
  for (i, x) in enumerate(kernel):
    for (j, y) in enumerate(x):
      if y != 0:
        offset_by = (i - mid_y) * screen_width + (j - mid_x)
        node = in0.offset(offset_by) * gr.const(y)
        if out != None:
          out = out + node
        else:
          out = node
  if out != None:
    if divisor:
      return out / gr.const(divisor)
    else:
      return out
  else:
    return gr.const(0)

def roberts_cross(in0: Node):
  a = apply_kernel(gr, in0, [[-1, 0], [0, -1]])
  b = apply_kernel(gr, in0, [[0, 1], [1, 0]])
  return abs(a) + abs(b)

r_out = gr.ostream(roberts_cross(r_in), 8)

# Buffering twice - once to make offset and once after

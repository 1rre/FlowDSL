from flow.flow.graph import Graph
from flow.flow.node import Node

# This requires 1 iteration of lower limits

gr = Graph()

screen_width = 640
screen_height = 480

r_in = gr.istream(8)
#g_in = gr.istream(8)
#b_in = gr.istream(8)

def roberts_cross(in0: Node) -> Node:
    last = in0.offset(-1)
    prev_row = in0.offset(-screen_height)
    prev_row_last = in0.offset(-screen_height - 1)
    gx = prev_row_last - in0
    gy = prev_row - last
    return abs(gx) + abs(gy)

r_out = gr.ostream(roberts_cross(r_in), 8)
#g_out = gr.ostream(roberts_cross(g_in), 8)
#b_out = gr.ostream(roberts_cross(b_in), 8)

# Buffering twice - once to make offset and once after

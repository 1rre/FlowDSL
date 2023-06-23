from xdsl.printer import Printer
from xdsl.dialects.builtin import StringAttr, ArrayAttr

from xdsl.ir import MLContext
from xdsl.parser import Parser

from flow.flow_initial.dialect.graph import *
from flow.flow_initial.dialect.node import *

printer = Printer()
graph_attr = GraphAttr(GraphSize(1, 1))
printer.print_attribute(graph_attr)
print()
ctx = MLContext()
ctx.register_attr(GraphAttr)
parser = Parser(ctx, '!flow_initial.graph<1, 1>')
param = parser.parse_attribute()
print(param)

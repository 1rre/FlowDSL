from xdsl.printer import Printer
from xdsl.dialects.builtin import StringAttr, IntAttr, ModuleOp

from xdsl.ir import MLContext, Block
from xdsl.irdl import RegionDef
from xdsl.parser import Parser

from flow.flow_initial.dialect.graph import *
from flow.flow_initial.dialect.node import *

printer = Printer()

graph_attr = GraphAttr(GraphSize(1, 1))

op1 = Const(
  result_types=[NodeAttr([StringAttr("Hello")])],
  attributes={"value": IntAttr(5)}
)

op2 = OStream(result_types=[NodeAttr([StringAttr("World")])])
op3 = Offset(operands=[op2], attributes={"value": IntAttr(5)}, result_types=[NodeAttr([StringAttr("Third")])])

op = ModuleOp(ops = [op1, op2, op3])


ctx = MLContext()

printer.print_op(op)

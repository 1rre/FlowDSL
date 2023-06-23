from xdsl.ir import MLContext, Block, OpResult
from flow.flow.graph import Graph
from xdsl.printer import Printer
from flow.flow2.deduplicator import Deduplicator
from flow.flow2.dialect.node import Flow2Node
from flow.flow_timed.offset_future import InputRetimer
from flow.util.flow_printer import FlowPrinter
from flow.flow2.reference_matching import ReferenceMatching
from flow.flow_timed.node_mapper import NodeMapper
from flow.hard_flow.to_hardware import ToHardware

from test11 import gr

try:
  print(gr.resolve())
  print()
except: pass

compiled = gr.to_xdsl()
printer = Printer()
printer.print_op(compiled)
print()
print()

ctx = MLContext()

names = list(gr.node_mappings.keys())
ReferenceMatching().apply(ctx, compiled)

Deduplicator(names, list(compiled.body.block.ops)).apply(ctx, compiled)


print(compiled)
print()
print()

nm = NodeMapper()
nm.apply(ctx, compiled)

it = InputRetimer(names, list(compiled.body.block.ops))
it.apply(ctx, compiled)
if len(it.mappings) > 0:
  NodeMapper().apply(ctx, compiled)

for op in list(compiled.body.block.ops):
  #assert not isinstance(op, Flow2Node), ""
  pass
  

print(compiled)
print()
print()

ToHardware().apply(ctx, compiled)

print(compiled)
print()
print()

printer2 = FlowPrinter()
printer2.print_module(compiled)

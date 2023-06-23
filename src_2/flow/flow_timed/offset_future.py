# Takes input flow2 and emits flow_timed
from xdsl.dialects import builtin
from xdsl.ir import MLContext, SSAValue, OpResult, Operation
import xdsl.ir as ir
from xdsl.passes import ModulePass
from xdsl.dialects.builtin import ModuleOp, StringAttr, IntAttr
from xdsl.pattern_rewriter import (
  PatternRewriter, RewritePattern, op_type_rewrite_pattern, PatternRewriteWalker
)
from typing import Annotated
from flow.flow2.dce import DeadCodeEliminator
from flow.flow2.dialect import node as v2
from flow.flow_timed import node as timed

def rewrite(op: ir.Operation):
  if isinstance(op, timed.Const):
    return v2.Const(op.operands, result_types=[v2.WNodeAttr([IntAttr(op.result.typ.width.data)])], attributes=op.attributes)
  if isinstance(op, timed.IStream):
    return v2.IStream(op.operands, result_types=[v2.WNodeAttr([IntAttr(op.result.typ.width.data)])], attributes=op.attributes)
  if isinstance(op, timed.OStream):
    return v2.OStream(op.operands, result_types=[v2.WNodeAttr([IntAttr(op.result.typ.width.data)])], attributes=op.attributes)
  if isinstance(op, timed.Offset):
    return v2.Offset(op.operands, result_types=[v2.NodeAttr()], attributes=op.attributes)
  if isinstance(op, timed.BinOp):
    return v2.BinOp(op.operands, result_types=[v2.NodeAttr()], attributes=op.attributes)
  if isinstance(op, timed.Unary):
    return v2.Unary(op.operands, result_types=[v2.NodeAttr()], attributes=op.attributes)
  if isinstance(op, timed.Concat):
    return v2.Concat(op.operands, result_types=[v2.NodeAttr()], attributes=op.attributes)
  return op

class Detimer(RewritePattern):
  @op_type_rewrite_pattern
  def match_and_rewrite(self, op: ir.Operation, rewriter: PatternRewriter):
    for opr in list(op.operands):
      new_opr = rewrite(opr.owner)
      if new_opr != opr.owner:
        rewriter.replace_op(opr.owner, new_opr)
    new_op = rewrite(op)
    if new_op != op:
      print(f"Detiming: {op}")
      rewriter.replace_op(op, new_op)

# TODO: Replace this before we get to timed?
class OffsetFuture(RewritePattern):
  names: list[str]
  ops: list[ir.Operation]
  done: set[ir.Operation] = set()
  mappings: list[bool]
  offset_total: int = 0
  def __init__(self, ops, mappings):
    self.mappings = mappings
    self.ops = ops
    for op in self.ops:
      if isinstance(op, timed.Offset):
        arg = op.operands[0].owner
        arg_time = arg.results[0].typ.time.data
        op_time = op.results[0].typ.time.data
        if arg_time < op_time:
          print(f"Arg time lt op time: {arg_time} vs {op_time} :: {op}")
          mappings.append(True)
          self.offset_total = max(self.offset_total, op_time - arg_time)
    RewritePattern.__init__(self)

  @op_type_rewrite_pattern
  def match_and_rewrite(self, op: ir.Operation, rewriter: PatternRewriter):
    if self.offset_total > 0 and isinstance(op, timed.IStream) and op not in self.done:
      in_cpy = timed.IStream([], [o.typ for o in op.results], op.attributes)
      rt = timed.NodeAttr([IntAttr(-self.offset_total)])
      new_offset = timed.Offset(in_cpy.results, attributes={"offset": IntAttr(-self.offset_total)}, result_types=[rt])
      rewriter.replace_op(op, [in_cpy, new_offset])
      self.done.add(in_cpy)

class InputRetimer(ModulePass):
  name = "flow_timed.retime_inputs"
  names: list[str]
  ops: list[ir.Operation]
  mappings = []
  def __init__(self, names: list[str], ops: list[ir.Operation]):
    self.names = names
    self.ops = ops
    ModulePass.__init__(self)

  def apply(self, ctx: MLContext, op: ModuleOp) -> None:
    ops = op.regions[0].ops
    PatternRewriteWalker(OffsetFuture(ops, self.mappings)).rewrite_module(op)
    print(ops)
    def is_flow2(x):
      return isinstance(x, v2.Flow2Node)
    if any(map(is_flow2, op.body.ops)):
      PatternRewriteWalker(Detimer()).rewrite_module(op)
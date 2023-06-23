

from xdsl.dialects import builtin
from xdsl.ir import MLContext, SSAValue, OpResult
import xdsl.ir as ir
from xdsl.passes import ModulePass
from xdsl.dialects.builtin import ModuleOp, StringAttr, IntAttr
from xdsl.pattern_rewriter import (
  PatternRewriter, RewritePattern, op_type_rewrite_pattern, PatternRewriteWalker
)
from typing import Annotated
from flow.flow2.dialect import node as v2
from flow.flow_initial.dialect import node as initial

class DeadCodeEliminator(RewritePattern):
  ops: list[ir.Operation]
  to_keep_out: set[ir.Operation] = set()
  to_keep: set[ir.Operation] = set()
  to_keep_in: set[ir.Operation] = set()

  def add_deps_out(self, op: ir.Operation):
    if op not in self.to_keep_out:  
      self.to_keep_out |= {op}
      for opr in op.operands:
        self.add_deps_out(opr.owner) # type: ignore

  def add_deps_in(self, op: ir.Operation):
    if op not in self.to_keep_in:
      self.to_keep_in |= {op}
      for use in op.result.uses:
        self.add_deps_in(use.operation) # type: ignore

  def __init__(self, ops: list[ir.Operation]):
    self.ops = ops
    self.to_keep_out = set()
    self.to_keep_in = set()
    for op in self.ops:
      if isinstance(op, v2.OStream):
        self.add_deps_out(op)
      if isinstance(op, v2.IStream) or isinstance(op, v2.Const):
        self.add_deps_in(op)
    self.to_keep = self.to_keep_in.intersection(self.to_keep_out)

  @op_type_rewrite_pattern
  def match_and_rewrite(self, op: ir.Operation, rewriter: PatternRewriter):
    if isinstance(op, v2.IStream) or isinstance(op, initial.IStream) or isinstance(op, ModuleOp): return
    if op not in self.to_keep:
      rewriter.erase_op(op, safe_erase=False)
      #op_opr = list(op.operands)
      #for i, opr in enumerate(op.operands):
      #  if opr.owner not in self.to_keep and opr.owner != op:
      #    no_op = v2.Const(attributes={"value": IntAttr(0)}, result_types=[v2.NodeAttr()])
      #    op_opr[i] = no_op.results[0]
      #    rts = list(r.typ for r in op.results)
      #    new_op = op.__class__(op_opr, rts, op.attributes)
      #    self.to_keep |= {new_op}
      #    rewriter.replace_op(op, new_op)
      #    op = new_op
      
      #if len(op.results[0].uses) == 0:
      #else:
      #  print("STILL IN USE:")
      #  print(op)
  
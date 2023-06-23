from xdsl.dialects import builtin
from xdsl.ir import MLContext, SSAValue, OpResult
from xdsl.irdl import VarOperand
import xdsl.ir as ir
from xdsl.passes import ModulePass
from xdsl.dialects.builtin import ModuleOp, StringAttr, IntAttr
from xdsl.pattern_rewriter import (
  PatternRewriter, RewritePattern, op_type_rewrite_pattern, PatternRewriteWalker
)
from typing import Annotated
from flow.flow2.dce import DeadCodeEliminator
from flow.flow2.dialect.node import *
import flow.flow2.dialect.node as v2
from flow.flow_initial.dialect import node as initial

class CheckNames(RewritePattern):
  mappings: dict[str, ir.Operation]
  def __init__(self, rootop):
    self.mappings = {}
    for op in rootop.body.ops:
      self.mappings[op.result.typ.uid.data] = op
    RewritePattern.__init__(self)

  @op_type_rewrite_pattern
  def match_and_rewrite(self, op: ir.Operation, rewriter: PatternRewriter):
    if isinstance(op, ModuleOp) or isinstance(op, Flow2Node): return
    
    can_update = True
    oprs = []
    for name, opr in sorted(op.attributes.items()):
      if isinstance(opr, StringAttr) and name[0:3] == 'opr':
        if opr.data not in self.mappings:
          can_update = False
          break
        oprs.append(self.mappings[opr.data].result)
      if isinstance(opr, ArrayAttr) and name[0:3] == 'opr':
        x = VarOperand()
        for opr2 in opr.data:
          if opr2.data not in self.mappings:
            can_update = False
            break
          x.append(self.mappings[opr2.data].result)
        if not can_update: break
        oprs.append(x)
          

    if not can_update: return

    match op.__class__:
      case initial.OStream | initial.IStream | initial.Const | initial.Slice:
        rt = WNodeAttr([op.result.typ.width])
      case _:
        rt = NodeAttr()

    attrs = dict(
      (k,v) for (k,v) in op.attributes.items()
            if k[0:3] != 'opr'
    )

    if op.result.typ.uid.data[0] != '#':
      attrs |= {'uid': op.result.typ.uid}

    new_op = getattr(v2, op.__class__.__name__)(oprs, [rt], attrs)
    self.mappings[op.result.typ.uid.data] = new_op
    rewriter.replace_op(op, new_op)

class ReferenceMatching(ModulePass):
  name = "flow2.match_reference"
  def __init__(self):
    ModulePass.__init__(self)

  def apply(self, ctx: MLContext, op: ModuleOp) -> None:
    PatternRewriteWalker(CheckNames(op)).rewrite_module(op)
    ops_l = []
    while list(op.body.ops) != ops_l:
      ops_l = list(op.body.ops)
      PatternRewriteWalker(DeadCodeEliminator(list(op.body.ops))).rewrite_module(op)
      
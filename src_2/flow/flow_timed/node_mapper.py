# Takes input flow2 and emits flow_timed
from xdsl.dialects import builtin
from xdsl.ir import MLContext, SSAValue, OpResult, Operation
from xdsl.irdl import VarOperand
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

def construct_timed(op: Operation, lo):
  if isinstance(op, v2.IStream):
    width = op.result.typ.width.data #type: ignore
    return timed.IStream(operands=op.operands, result_types=[timed.WNodeAttr([IntAttr(lo or 0), IntAttr(width)])], attributes=op.attributes) 
  elif isinstance(op, v2.OStream):
    width = op.result.typ.width.data #type: ignore
    return timed.OStream(operands=op.operands, result_types=[timed.WNodeAttr([IntAttr(lo or 0), IntAttr(width)])], attributes=op.attributes) 
  elif isinstance(op, v2.Offset):
    return timed.Offset(operands=op.operands, result_types=[timed.NodeAttr([IntAttr(lo or 0)])], attributes=op.attributes) 
  elif isinstance(op, v2.BinOp):
    return timed.BinOp(operands=op.operands, result_types=[timed.NodeAttr([IntAttr(lo or 0)])], attributes=op.attributes)
  elif isinstance(op, v2.Unary):
    return timed.Unary(operands=op.operands, result_types=[timed.NodeAttr([IntAttr(lo or 0)])], attributes=op.attributes)
  elif isinstance(op, v2.Resettable):
    return timed.Resettable(operands=op.operands, result_types=[timed.NodeAttr([IntAttr(lo or 0)])], attributes=op.attributes)
  elif isinstance(op, v2.Const):
    width = op.result.typ.width.data #type: ignore
    return timed.Const(operands=op.operands, result_types=[timed.ConstAttr([IntAttr(width)])], attributes=op.attributes)
  elif isinstance(op, v2.Slice):
    width = op.result.typ.width.data #type: ignore
    return timed.Slice(operands=op.operands, result_types=[timed.WNodeAttr([IntAttr(lo or 0), IntAttr(width)])], attributes=op.attributes)
  elif isinstance(op, v2.Concat):
    opr = VarOperand()
    for r in op.operands:
      opr.append(r)
    print(opr)
    return timed.Concat(operands=[opr], result_types=[timed.NodeAttr([IntAttr(lo or 0)])], attributes=op.attributes)
  else:
    return op

class SetTimes(RewritePattern):
  names: list[str]
  ops: list[ir.Operation]
  def __init__(self, mappings, rootop):
    self.node_mappings = mappings
    RewritePattern.__init__(self)
    self.rootop = rootop

  @op_type_rewrite_pattern
  def match_and_rewrite(self, op: ir.Operation, rewriter: PatternRewriter):
    opr_replace = []
    if isinstance(op, ModuleOp): return
    if isinstance(op, v2.IStream):
      self.node_mappings[op] = (0,0)
      #rewriter.replace_op(op, new_op)
    elif isinstance(op, v2.Const):
      # Defer on const to see when it's used
      # This is to stop setting upper/lower bounds based on const
      self.node_mappings[op] = (None, None)
    elif isinstance(op, v2.OStream):
      arg: Operation = op.operands[0].owner # type: ignore
      if arg in self.node_mappings:
        mapping = self.node_mappings[arg]
        self.node_mappings[op] = mapping
    elif isinstance(op, v2.Slice):
      if op.operands[0].owner in self.node_mappings:
        self.node_mappings[op] = self.node_mappings[op.operands[0].owner]
    elif isinstance(op, v2.Concat):
      def try_put(opr: Operation):
        if opr in self.node_mappings:  
          lo_opr, hi_opr = self.node_mappings[opr]
          if op in self.node_mappings:
            lo, hi = self.node_mappings[op]
          else: lo, hi = None, None
          if lo_opr != None:
            lo = max(lo or (lo_opr), (lo_opr))
          if hi_opr != None:
            hi = max(hi or (hi_opr), (hi_opr))
          self.node_mappings[op] = lo, hi
          if hi != None:
            self.node_mappings[opr] = lo_opr, (hi - 1)
            if lo_opr == (hi-1):
              new_op = construct_timed(opr, lo)
              if opr != new_op:
                self.node_mappings[new_op] = lo_opr, (hi - 1)
                rewriter.replace_op(opr, new_op)
                return True
      
      for opr in list(op.operands):
        try_put(opr.owner)
    
    elif isinstance(op, v2.BinOp) or isinstance(op, v2.Unary):
      def try_put(opr: Operation):
        if opr in self.node_mappings:  
          lo_opr, hi_opr = self.node_mappings[opr]
          if op in self.node_mappings:
            lo, hi = self.node_mappings[op]
          else: lo, hi = None, None
          if lo_opr != None:
            lo = max(lo or (lo_opr + 1), (lo_opr + 1))
          if hi_opr != None:
            hi = max(hi or (hi_opr + 1), (hi_opr + 1))
          self.node_mappings[op] = lo, hi
          if hi != None:
            self.node_mappings[opr] = lo_opr, (hi - 1)
            if lo_opr == (hi-1):
              new_op = construct_timed(opr, lo)
              if opr != new_op:
                self.node_mappings[new_op] = lo_opr, (hi - 1)
                rewriter.replace_op(opr, new_op)
                return True
      
      for opr in list(op.operands):
        try_put(opr.owner)
        
    elif isinstance(op, v2.Resettable):
      arg: Operation = op.operands[0].owner # type: ignore
      if arg in self.node_mappings:
        lo, hi = self.node_mappings[arg]
        self.node_mappings[op] = (lo, hi)

    elif isinstance(op, v2.Offset):
      arg: Operation = op.operands[0].owner # type: ignore
      if arg in self.node_mappings:
        lo, hi = self.node_mappings[arg]
        offset = op.attributes["offset"].data #type: ignore
        self.node_mappings[op] = (lo + offset, hi + offset)
        
    if isinstance(op, v2.Concat):
      print("Op is concat")
      print(op in self.node_mappings)
      print(op in self.rootop.body.ops)
      print(self.node_mappings[op])

    if op in self.node_mappings and op in self.rootop.body.ops:
      lo, hi = self.node_mappings[op]
      if lo == hi:
        new_op = construct_timed(op, lo)
        if op != new_op:
          self.node_mappings[new_op] = self.node_mappings[op]
          rewriter.replace_op(op, new_op)
          
class NodeMapper(ModulePass):
  name = "flow_timed.node_mapper"

  def apply(self, ctx: MLContext, op: ModuleOp) -> None:
    self.mappings = {}
    while True:
      mappings_last = self.mappings.copy()
      PatternRewriteWalker(SetTimes(self.mappings, op)).rewrite_module(op)
      if mappings_last == self.mappings:
        break
    
    PatternRewriteWalker(SetTimes(self.mappings, op)).rewrite_module(op)

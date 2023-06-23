

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
from flow.flow2.dialect.node import *

def reversable(op: str):
  return op in ['+', '*', '||', '&&', '^', '|', '&', '==', '!=']

# TODO: This identifies identical operations and merges them
class Deduplicate(RewritePattern):
  names: list[str]
  rootop: ModuleOp
  cse_binop: dict[Tuple[SSAValue, SSAValue, str], Operation]
  cse_offset: dict[Tuple[SSAValue, int], Operation]
  cse_const: dict[int, Operation]
  to_replace: dict[Operation, Operation]

  def generate_replace(self, skip = None):
    self.cse_binop = {}
    self.cse_const = {}
    self.cse_offset = {}
    self.to_replace = {}
    for op in self.rootop.body.ops:
      if op == skip: continue
      if isinstance(op, Offset):
        if (op.operands[0], op.attributes["offset"].data) in self.cse_offset:
          self.to_replace[op] = self.cse_offset[(op.operands[0], op.attributes["offset"].data)]
        self.cse_offset[op.operands[0], op.attributes["offset"].data] = op

      if isinstance(op, BinOp):
        if (op.operands[0], op.operands[1], op.attributes["op"].data) in self.cse_binop:
          self.to_replace[op] = self.cse_binop[(op.operands[0], op.operands[1], op.attributes["op"].data)]
        if reversable(op.attributes['op'].data):
          self.cse_binop[op.operands[1], op.operands[0], op.attributes["op"].data] = op
        self.cse_binop[op.operands[0], op.operands[1], op.attributes["op"].data] = op
      if isinstance(op, Const):
        if op.attributes["value"].data in self.cse_const:
          self.to_replace[op] = self.cse_const[op.attributes["value"].data]
        self.cse_const[op.attributes["value"].data] = op
        

      #if len(self.to_replace) > 0:
      #  print(f"Replacing (duplicate): {op}")
      #  return

  def __init__(self, names, rootop):

    self.names = names
    self.rootop = rootop
    
    self.generate_replace()
    RewritePattern.__init__(self)

  @op_type_rewrite_pattern
  def match_and_rewrite(self, op: ir.Operation, rewriter: PatternRewriter):
    if op in self.to_replace:
      opr = self.to_replace[op]
      for use in list(opr.results[0].uses):
        idx = use.operation.operands.index(opr.results[0])
        args = list(use.operation.operands)
        args[idx] = op.results[0]
        rt = [r.typ for r in use.operation.results]
        new = use.operation.__class__(args, rt, use.operation.attributes)
        rewriter.replace_op(use.operation, new)

      self.generate_replace(opr)
      
      rewriter.erase_op(opr)

# TODO: This identifies identical operations and merges them
class RewriteOffsets(RewritePattern):
  names: list[str]
  ops: list[ir.Operation]
  def __init__(self, names, ops):
    self.names = names
    self.ops = ops
    RewritePattern.__init__(self)

  @op_type_rewrite_pattern
  def match_and_rewrite(self, op: ir.Operation, rewriter: PatternRewriter):
    if isinstance(op, BinOp):
      if isinstance(op.operands[0].owner, Offset) and isinstance(op.operands[1].owner, Offset):
        #print(f"Rewrite offset:\n{op.operands[0].owner}\n{op.operands[1].owner}")
        offset_0 = op.operands[0].owner.attributes['offset'].data
        offset_1 = op.operands[1].owner.attributes['offset'].data
        if offset_0 > offset_1:
          offset_in = IntAttr(offset_1 - offset_0)
          offset_out = IntAttr(offset_0)
          #print(f"OIN: {offset_in}, OUT: {offset_out}")
          new_in0_in = op.operands[0].owner.operands[0]
          rt0 = [op.operands[0].typ]
          new_in0 = Offset([new_in0_in], rt0, {'offset': offset_in})
          new_in1 = op.operands[1].owner.operands[0]
          new_binop = BinOp([new_in0, new_in1], [op.result.typ], op.attributes)
          ofs_out = Offset([new_binop.result], [op.result.typ], {'offset': offset_out})
          rewriter.replace_op(op, [new_in0, new_binop, ofs_out], new_results=[ofs_out.result])
        elif offset_1 > offset_0:
          offset_in = IntAttr(offset_0 - offset_1)
          offset_out = IntAttr(offset_1)
          #print(f"OIN: {offset_in}, OUT: {offset_out}")
          new_in1_in = op.operands[1].owner.operands[0]
          rt1 = [op.operands[1].typ]
          new_in1 = Offset([new_in1_in], rt1, {'offset': offset_in})
          new_in0 = op.operands[0].owner.operands[0]
          new_binop = BinOp([new_in0, new_in1], [op.result.typ], op.attributes)
          ofs_out = Offset([new_binop.result], [op.result.typ], {'offset': offset_out})
          rewriter.replace_op(op, [new_in1, new_binop, ofs_out], new_results=[ofs_out.result])
        else:
          new_in0 = op.operands[0].owner.operands[0]
          new_in1 = op.operands[1].owner.operands[0]
          offset_out = IntAttr(offset_1)
          new_binop = BinOp([new_in0, new_in1], [op.result.typ], op.attributes)
          ofs_out = Offset([new_binop.result], [op.result.typ], {'offset': offset_out})
          rewriter.replace_op(op, [new_binop, ofs_out], new_results=[ofs_out.result])

class OffsetRenamer(RewritePattern):
  names: list[str]
  ops: list[ir.Operation]
  def __init__(self, names, ops):
    self.names = names
    self.ops = ops
    RewritePattern.__init__(self)

  @op_type_rewrite_pattern
  def match_and_rewrite(self, op: ir.Operation, rewriter: PatternRewriter):
    if isinstance(op, Offset):
      arg = op.operands[0]
      if op.attributes['offset'].data == 0 or isinstance(arg.owner, Const):
        rewriter.replace_op(op, [], new_results=[arg])
      elif arg.owner == op:
        #print("Self-owned")
        pass
      elif isinstance(arg.owner, Offset):
        offset = arg.owner.attributes["offset"].data + op.attributes["offset"].data # type: ignore
        node = arg.owner.operands[0] # type: ignore
        result_types = [res.typ for res in op.results]
        new_op = Offset(operands=[node], result_types=result_types, attributes={"offset": IntAttr(offset)})
        rewriter.replace_op(op, new_op)
        
class Deduplicator(ModulePass):
  name = "flow2.dedup"
  names: list[str]
  ops: list[ir.Operation]
  def __init__(self, names: list[str], ops: list[ir.Operation]):
    self.names = names
    self.ops = ops
    ModulePass.__init__(self)

  def apply(self, ctx: MLContext, op: ModuleOp) -> None:
    init = []
    while list(op.body.ops) != init:
      init = list(op.body.ops)
      PatternRewriteWalker(OffsetRenamer(self.names, op.regions[0].ops)).rewrite_module(op)
      PatternRewriteWalker(DeadCodeEliminator(list(op.regions[0].ops))).rewrite_module(op)
      PatternRewriteWalker(RewriteOffsets(self.names, list(op.regions[0].ops))).rewrite_module(op)
      PatternRewriteWalker(DeadCodeEliminator(list(op.body.ops))).rewrite_module(op)
      PatternRewriteWalker(Deduplicate(self.names, op)).rewrite_module(op)
      PatternRewriteWalker(DeadCodeEliminator(list(op.body.ops))).rewrite_module(op)


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
from math import ceil, log2

from flow.flow_timed import node
from flow.hard_flow import reg



class Bits(RewritePattern):
  bit_usage: dict[Operation, set[int]] = {}
  bit_avail: dict[Operation, set[int]] = {}

  def get_used_bits(self, op: ir.Operation, use: ir.Operation) -> set[int]:
    #print(f"gub: {op.name} => {use.name} ({isinstance(use, reg.Unary)})")
    if use not in self.bit_usage:
      return set()

    if isinstance(use, reg.OStream) or isinstance(use, reg.Offset) or isinstance(use, reg.Buffer) or isinstance(use, reg.Resettable):
      return self.bit_usage[use]

    if isinstance(use, reg.BinOp):
      match use.attributes["op"].data: # type: ignore
        case '/' | '%':
          # Note here, we're not gonna use more than 2 * use
          # We also need to think about the case of "0xFFFFFFFFFFFFFFFFF / 0xFFFFFFFFFFFF"
          # Only high bits will be used
          if use in self.bit_usage:
            opu = self.bit_usage[use]
          else:
            opu = set()
          
          # This is suboptimal
          return opu | self.bit_avail[op]
        case '&&' | '||' | '==' | '!=' | '>' | '>=' | '<=' | '<':
          # This is funny as it's theoretically infinite
          # Therefore it's probably better to do it though forward, rather than backward propagation
          # Assuming that the input is not cyclic, we can have 
          return set(self.bit_avail[op])
        case '*' | '-' | '+' | '|' | '&' | '^':
          # Note that here we will need to have some sort of overflow protection?
          return self.bit_usage[use]
    elif isinstance(use, reg.Unary):
      match use.attributes["op"].data: # type: ignore
        case '+' | '-' | 'abs' | '~':
          return self.bit_usage[use]
        case '!':
          return set(self.bit_avail[op])
    return set()
  
  def get_available_bits(self, op: ir.Operation, opr_avail: list[set[int]]):
    if isinstance(op, reg.Buffer) or isinstance(op, reg.Offset) or isinstance(op, reg.Resettable):
      return opr_avail[0]
    elif isinstance(op, reg.BinOp):
      match op.attributes["op"].data: # type: ignore
        case '/' | '%':
          return opr_avail[0].copy()
        case '&&' | '||' | '==' | '!=' | '>' | '>=' | '<=' | '<':
          return set(range(1))
        case '*':
          range1 = len(opr_avail[0])
          range2 = len(opr_avail[1])
          return set(range(range1 + range2))
        case '-' | '+':
          range1 = len(opr_avail[0])
          range2 = len(opr_avail[1])
          return set(range(max(range1, range2) + 1))
        case '|' | '&' | '^':
          return (opr_avail[0] | opr_avail[1])
    elif isinstance(op, reg.Unary):
      match op.attributes["op"].data: # type: ignore
        case '+':
          # This is theoretically infinite which may be an issue
          return opr_avail[0]
        case '-' | 'abs' | '~':
          return opr_avail[0]
        case '!':
          return set(range(1))
    return set()
  
  def trail_forwards(self, op: Operation, updating: set[Operation]):
    if op in updating: return

    if op not in self.bit_avail:
      self.bit_avail[op] = set() # type: ignore
    op_avail = []
    for opr in op.operands:
      if opr.owner in self.bit_avail:
        op_avail.append(self.bit_avail[opr.owner]) # type: ignore
      else:
        op_avail.append(set()) # type: ignore
    self.bit_avail[op] |= self.get_available_bits(op, op_avail)
    for opu in op.results[0].uses:
      self.trail_forwards(opu.operation, updating | {op}) # type: ignore


  def set_available_bits(self, ops: list[ir.Operation]):
    for op in ops:
      if isinstance(op, reg.IStream) or isinstance(op, reg.OStream):
        width = op.result.typ.width.data # type: ignore
        self.bit_avail[op] = set(range(width))
        self.trail_forwards(op, set())
      if isinstance(op, reg.Const):
        data = op.attributes["value"].data
        if data == 0:
          value = 1
        elif data < 0:
          value = ceil(log2(-data)) # type: ignore
        else:
          value = ceil(log2(data)) # type: ignore
        self.bit_avail[op] = set(range(value))
        self.trail_forwards(op, set())
      

    #for op in ops:
    #  if op not in self.bit_avail:
    #    self.bit_avail[op] = set()
    #  opr_avail: list[set[int]] = []
    #  for opr in op.operands:
    #    opro: ir.Operation = opr.owner # type: ignore
    #    if opro in self.bit_avail:
    #       avail = self.bit_avail[opro]
    #    else:
    #       avail: set[int] = set()
    #    opr_avail.append(avail)
    #  bit_use = self.get_available_bits(op, opr_avail)
    #  self.bit_avail[op] |= bit_use
          
  def trail_back(self, op: Operation, updating: set[Operation]):
    if op in updating: return
    if "uid" in (op.attributes):
      name = op.attributes["uid"].data
    else:
      name = "[unnamed]"

    for opr in op.operands:
      if opr.owner not in self.bit_usage:
        self.bit_usage[opr.owner] = set() # type: ignore
      ub = self.get_used_bits(opr.owner, op) # type: ignore
      self.bit_usage[opr.owner] |= ub # type: ignore
    
    for opr in op.operands:
      self.trail_back(opr.owner, updating | {op}) # type: ignore
  
  def set_used_bits(self, ops):
    for op in ops:
      if isinstance(op, reg.IStream) or isinstance(op, reg.OStream):
        width = op.result.typ.width.data # type: ignore
        self.bit_usage[op] = set(range(width))
        self.trail_back(op, set())
  
  def __init__(self, ops: list[ir.Operation]):
    self.set_available_bits(ops)
    self.set_used_bits(ops)


  @op_type_rewrite_pattern
  def match_and_rewrite(self, op: ir.Operation, rewriter: PatternRewriter):
    if len(op.results) > 0 and isinstance(op.results[0].typ, reg.ValueAttr):
      time = op.result.typ.time.data # type: ignore
      if op in self.bit_usage:
        width = len(self.bit_usage[op])
      else:
        width = 0
      # Max & Min don't work on empty sets
      if width != 0:
        width = max(self.bit_usage[op]) - min(self.bit_usage[op]) + 1
      new_result = [reg.RegAttr([IntAttr(time), IntAttr(width)])]
      if isinstance(op, reg.Concat):
        rewriter.replace_op(op, op.__class__([op.operands], new_result, op.attributes))
      else:
        rewriter.replace_op(op, op.__class__(op.operands, new_result, op.attributes))



class Compile(RewritePattern):
  @op_type_rewrite_pattern
  def match_and_rewrite(self, op: ir.Operation, rewriter: PatternRewriter):
    if isinstance(op, node.Const):
      #width = op.result.typ.width.data # type: ignore
      data = op.attributes["value"].data
      if data == 0:
        width = 1
      elif data < 0:
        width = ceil(log2(1 - data)) # type: ignore
      else:
        width = ceil(log2(1 + data)) # type: ignore
      new_op = reg.Const(operands=op.operands, result_types=[reg.ConstAttr([IntAttr(width)])], attributes=op.attributes)
      rewriter.replace_op(op, new_op)
    elif isinstance(op, node.IStream):
      time = op.result.typ.time.data # type: ignore
      width = op.result.typ.width.data # type: ignore
      new_op = reg.IStream(operands=op.operands, result_types=[reg.RegAttr([IntAttr(time), IntAttr(width)])], attributes=op.attributes)
      rewriter.replace_op(op, new_op)
    elif isinstance(op, node.OStream):
      time = op.result.typ.time.data # type: ignore
      width = op.result.typ.width.data # type: ignore
      new_op = reg.OStream(operands=op.operands, result_types=[reg.RegAttr([IntAttr(time), IntAttr(width)])], attributes=op.attributes)
      rewriter.replace_op(op, new_op)
    elif isinstance(op, node.Unary):
      time = op.result.typ.time.data # type: ignore
      new_op = reg.Unary(operands=op.operands, result_types=[reg.ValueAttr([IntAttr(time)])], attributes=op.attributes)
      rewriter.replace_op(op, new_op)
    elif isinstance(op, node.Slice):
      time = op.result.typ.time.data # type: ignore
      new_op = reg.Slice(operands=op.operands, result_types=[reg.ValueAttr([IntAttr(time)])], attributes=op.attributes)
      rewriter.replace_op(op, new_op)
    elif isinstance(op, node.Resettable):
      time = op.result.typ.time.data # type: ignore
      new_op = reg.Resettable(operands=op.operands, result_types=[reg.ValueAttr([IntAttr(time)])], attributes=op.attributes)
      rewriter.replace_op(op, new_op)

    elif isinstance(op, node.Concat):
      x_t = op.result.typ.time.data
      buffers: list[Operation] = []
      for opr in op.operands:
        right_t = opr.typ.time.data # type: ignore
        result_t = reg.ValueAttr([IntAttr(x_t - right_t)])
        if hasattr(op.operands[0].typ, "time"):
          buffer = reg.Buffer([opr], result_types=[result_t], attributes={"by": result_t})
          buffers.append(buffer)

      result_t = reg.ValueAttr([IntAttr(x_t)])
      new_op = reg.Concat([VarOperand(buffers.copy())], result_types=[result_t], attributes=op.attributes) # type: ignore
      buffers.append(new_op)
      rewriter.replace_op(op, buffers)
      
    elif isinstance(op, node.BinOp):
      # This assumes no consts, TODO: Fix
      left = op.operands[0].owner
      right = op.operands[1].owner

      if hasattr(op.operands[0].typ, "time"):
        left_t = op.operands[0].typ.time.data # type: ignore
      else:
        left_t = op.result.typ.time.data - 1 # type: ignore

      if hasattr(op.operands[1].typ, "time"):
        right_t = op.operands[1].typ.time.data # type: ignore
      else:
        right_t = op.result.typ.time.data - 1 # type: ignore
      
      # Inducing buffers
      buffers: list[Operation] = []
      if right_t > left_t:
        result_t = reg.ValueAttr([IntAttr(right_t)])
        left = reg.Buffer([left], result_types=[result_t], attributes={"by": IntAttr(right_t - left_t)}) # type: ignore
        buffers.append(left)
      
      if left_t > right_t:
        result_t = reg.ValueAttr([IntAttr(left_t)])
        right = reg.Buffer([right], result_types=[result_t], attributes={"by": IntAttr(left_t - right_t)}) # type: ignore
        buffers.append(right)
      
      ops = buffers
      # TODO: Replace this with t0
      result_t = reg.ValueAttr([IntAttr(max(right_t, left_t) + 1)])
      new_op = reg.BinOp([left, right], result_types=[result_t], attributes=op.attributes) # type: ignore
      ops.append(new_op)
      rewriter.replace_op(op, ops)

    elif isinstance(op, node.Offset):
      buffer = -op.attributes["offset"].data # type: ignore
      t_init = op.operands[0].typ.time.data - buffer # type: ignore
      rel = op.operands[0]
      offset = reg.Offset([rel], result_types=[reg.ValueAttr([IntAttr(t_init)])], attributes=op.attributes)
      rewriter.replace_op(op, offset)
  

class RemoveConstBuffer(RewritePattern):
  @op_type_rewrite_pattern
  def match_and_rewrite(self, op: ir.Operation, rewriter: PatternRewriter):
    if isinstance(op, reg.Buffer):
      if isinstance(op.operands[0].owner, reg.Const):
        for use in list(op.result.uses):
          new_args = list(use.operation.operands)
          new_args[new_args.index(op.result)] = op.operands[0]
          rts = [op.typ for op in use.operation.results]
          new_use = use.operation.__class__(new_args, rts, use.operation.attributes)
          rewriter.replace_op(use.operation, new_use)
        rewriter.erase_op(op)
  

class ToHardware(ModulePass):
  name = "hard_flow.to_hardware"
  def __init__(self):
    ModulePass.__init__(self)

  def apply(self, ctx: MLContext, op: ModuleOp) -> None:
    PatternRewriteWalker(Compile()).rewrite_module(op)
    # TODO: Type and timing check
    PatternRewriteWalker(Bits(list(op.regions[0].ops))).rewrite_module(op)
    n_ops = -1
    while n_ops != len(op.body.ops):
      n_ops = len(op.body.ops)
      PatternRewriteWalker(RemoveConstBuffer()).rewrite_module(op)


from typing import Annotated
from xdsl.irdl import (IRDLOperation, OpAttr, Operand, VarOperand, ParameterDef, AnyAttr, irdl_attr_definition, irdl_op_definition, BaseAttr, OptOpAttr)
from xdsl.dialects.builtin import StringAttr, IntAttr
from xdsl.ir import ParametrizedAttribute, TypeAttribute, OpResult

from ..flow2.dialect import node as v2

# We use these for some pre-timing rewrites

@irdl_attr_definition
class NodeAttr(ParametrizedAttribute, TypeAttribute):
  name = "flow_timed.node"
  time: ParameterDef[IntAttr]

@irdl_attr_definition
class WNodeAttr(ParametrizedAttribute, TypeAttribute):
  name = "flow_timed.wnode"
  time: ParameterDef[IntAttr]
  width: ParameterDef[IntAttr]
  
@irdl_attr_definition
class ConstAttr(ParametrizedAttribute, TypeAttribute):
  name = "flow_timed.const_t"
  width: ParameterDef[IntAttr]

@irdl_op_definition
class Const(IRDLOperation):
  name: str = "flow_timed.const"
  # Consts are untimed
  result: Annotated[OpResult, ConstAttr]
  uid: OptOpAttr[StringAttr]

@irdl_op_definition
class IStream(IRDLOperation):
  name: str = "flow_timed.istream"
  result: Annotated[OpResult, NodeAttr]
  uid: OptOpAttr[StringAttr]

@irdl_op_definition
class OStream(IRDLOperation):
  name: str = "flow_timed.ostream"
  node: Annotated[Operand, NodeAttr]
  result: Annotated[OpResult, NodeAttr]
  uid: OptOpAttr[StringAttr]

@irdl_op_definition
class Offset(IRDLOperation):
  name: str = "flow_timed.offset"
  offset: OpAttr[IntAttr]
  node: Annotated[Operand, NodeAttr]
  result: Annotated[OpResult, NodeAttr]
  uid: OptOpAttr[StringAttr]

@irdl_op_definition
class Slice(IRDLOperation):
  name: str = "flow_timed.slice"
  lo: OpAttr[IntAttr]
  hi: OpAttr[IntAttr]
  node: Annotated[Operand, NodeAttr]
  result: Annotated[OpResult, NodeAttr]
  
@irdl_op_definition
class Concat(IRDLOperation):
  name: str = "flow_timed.concat"
  node: Annotated[VarOperand, NodeAttr]
  result: Annotated[OpResult, NodeAttr]

@irdl_op_definition
class BinOp(IRDLOperation):
  name: str = "flow_timed.binop"
  result: Annotated[OpResult, NodeAttr]
  op: OpAttr[StringAttr]
  left: Annotated[Operand, NodeAttr]
  right: Annotated[Operand, NodeAttr]
  uid: OptOpAttr[StringAttr]
  
@irdl_op_definition
class Unary(IRDLOperation):
  name: str = "flow_timed.binop"
  result: Annotated[OpResult, NodeAttr]
  op: OpAttr[StringAttr]
  node: Annotated[Operand, NodeAttr]
  uid: OptOpAttr[StringAttr]

@irdl_op_definition
class Resettable(IRDLOperation):
  name: str = "flow_timed.binop"
  result: Annotated[OpResult, NodeAttr]
  to: OpAttr[IntAttr]
  node: Annotated[Operand, NodeAttr]
  uid: OptOpAttr[StringAttr]
  

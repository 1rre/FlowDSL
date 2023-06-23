from typing import Annotated
from xdsl.irdl import (IRDLOperation, OpAttr, Operand, ParameterDef, AnyAttr, irdl_attr_definition, irdl_op_definition, BaseAttr, OptOpAttr)
from xdsl.dialects.builtin import StringAttr, IntAttr
from xdsl.ir import ParametrizedAttribute, TypeAttribute, OpResult

@irdl_attr_definition
class RegAttr(ParametrizedAttribute, TypeAttribute):
  name = "hard_flow.reg"
  time: ParameterDef[IntAttr]
  width: ParameterDef[IntAttr]

@irdl_attr_definition
class ValueAttr(ParametrizedAttribute, TypeAttribute):
  name = "hard_flow.value"
#  width: ParameterDef[IntAttr]
  time: ParameterDef[IntAttr]

@irdl_op_definition
class Buffer(IRDLOperation):
  name = "hard_flow.buffer"
  of: Annotated[Operand, RegAttr | ValueAttr]
  by: OpAttr[IntAttr]
  uid: OptOpAttr[StringAttr]
  result: Annotated[OpResult, RegAttr]

@irdl_op_definition
class Offset(IRDLOperation):
  name = "hard_flow.offset"
  of: Annotated[Operand, RegAttr | ValueAttr]
  uid: OptOpAttr[StringAttr]
  result: Annotated[OpResult, RegAttr | ValueAttr]

@irdl_op_definition
class IStream(IRDLOperation):
  name = "hard_flow.istream"
  uid: OptOpAttr[StringAttr]
  result: Annotated[OpResult, RegAttr]

@irdl_op_definition
class OStream(IRDLOperation):
  name = "hard_flow.ostream"
  uid: OptOpAttr[StringAttr]
  of: Annotated[Operand, RegAttr | ValueAttr]
  result: Annotated[OpResult, RegAttr]

@irdl_attr_definition
class ConstAttr(ParametrizedAttribute, TypeAttribute):
  name = "hard_flow.const_t"
  width: ParameterDef[IntAttr]

@irdl_op_definition
class Const(IRDLOperation):
  name = "hard_flow.const"
  result: Annotated[OpResult, ConstAttr]
  uid: OptOpAttr[StringAttr]

@irdl_op_definition
class BinOp(IRDLOperation):
  name = "hard_flow.binop"
  op: OpAttr[StringAttr]
  left: Annotated[Operand, RegAttr | ValueAttr]
  right: Annotated[Operand, RegAttr | ValueAttr]
  uid: OptOpAttr[StringAttr]
  result: Annotated[OpResult, RegAttr | ValueAttr]

@irdl_op_definition
class Unary(IRDLOperation):
  name = "hard_flow.unary"
  op: OpAttr[StringAttr]
  node: Annotated[Operand, RegAttr | ValueAttr]
  uid: OptOpAttr[StringAttr]
  result: Annotated[OpResult, RegAttr | ValueAttr]

@irdl_op_definition
class Resettable(IRDLOperation):
  name = "hard_flow.resettable"
  to: OpAttr[IntAttr]
  node: Annotated[Operand, RegAttr | ValueAttr]
  uid: OptOpAttr[StringAttr]
  result: Annotated[OpResult, RegAttr | ValueAttr]


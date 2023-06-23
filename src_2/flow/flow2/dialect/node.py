from typing import Annotated, Tuple, TypeVar, Union
from xdsl.dialects.builtin import (AnyIntegerAttr, StringAttr, IntAttr)
from xdsl.ir import SSAValue, Dialect, OpResult, Attribute, TypeAttribute, ParametrizedAttribute, Data
from xdsl.irdl import (IRDLOperation, OpAttr, Operand, ParameterDef, AnyAttr, irdl_attr_definition, irdl_op_definition, BaseAttr, OptOpAttr)


@irdl_attr_definition
class NodeAttr(ParametrizedAttribute, TypeAttribute):
  name = "flow2.node"

@irdl_attr_definition
class WNodeAttr(ParametrizedAttribute, TypeAttribute):
  name = "flow2.wnode"
  width: ParameterDef[IntAttr]

class Flow2Node: pass

@irdl_op_definition
class Const(IRDLOperation, Flow2Node):
  name: str = "flow2.const"
  result: Annotated[OpResult, WNodeAttr]
  uid: OptOpAttr[StringAttr]


@irdl_op_definition
class IStream(IRDLOperation, Flow2Node):
  name: str = "flow2.istream"
  result: Annotated[OpResult, WNodeAttr]
  uid: OptOpAttr[StringAttr]

@irdl_op_definition
class OStream(IRDLOperation, Flow2Node):
  name: str = "flow2.ostream"
  node: Annotated[Operand, WNodeAttr]
  result: Annotated[OpResult, NodeAttr]
  uid: OptOpAttr[StringAttr]

@irdl_op_definition
class Offset(IRDLOperation, Flow2Node):
  name: str = "flow2.offset"
  offset: OpAttr[AnyIntegerAttr]
  node: Annotated[Operand, NodeAttr]
  result: Annotated[OpResult, NodeAttr]
  uid: OptOpAttr[StringAttr]
  
@irdl_op_definition
class Slice(IRDLOperation, Flow2Node):
  name: str = "flow2.slice"
  lo: OpAttr[IntAttr]
  hi: OpAttr[IntAttr]
  node: Annotated[Operand, WNodeAttr]
  result: Annotated[OpResult, NodeAttr]

@irdl_op_definition
class BinOp(IRDLOperation, Flow2Node):
  name: str = "flow2.binop"
  result: Annotated[OpResult, NodeAttr]
  left: Annotated[Operand, NodeAttr]
  right: Annotated[Operand, NodeAttr]
  op: OpAttr[StringAttr]
  uid: OptOpAttr[StringAttr]

@irdl_op_definition
class Unary(IRDLOperation, Flow2Node):
  name: str = "flow2.unary"
  result: Annotated[OpResult, NodeAttr]
  node: Annotated[Operand, NodeAttr]
  op: OpAttr[StringAttr]
  uid: OptOpAttr[StringAttr]

@irdl_op_definition
class Resettable(IRDLOperation, Flow2Node):
  name: str = "flow2.resettable"
  result: Annotated[OpResult, NodeAttr]
  node: Annotated[Operand, NodeAttr]
  to: OpAttr[IntAttr]
  uid: OptOpAttr[StringAttr]

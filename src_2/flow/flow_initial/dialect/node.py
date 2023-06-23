from dataclasses import dataclass
from typing import Annotated, Tuple, TypeVar, Union
from uuid import uuid4

from xdsl.dialects.builtin import (ArrayAttr, StringAttr, IntAttr)
from xdsl.ir import SSAValue, Dialect, OpResult, Attribute, TypeAttribute, ParametrizedAttribute, Data
from xdsl.irdl import (IRDLOperation, OpAttr, Operand, ParameterDef,
                       irdl_attr_definition, irdl_op_definition, BaseAttr)
from xdsl.parser import Parser
from xdsl.printer import Printer

# TODO: Maybe resolve between width and int vs float?
#@irdl_attr_definition
#class NodeType(ParametrizedAttribute, TypeAttribute):
#  name: str = "flow_initial.node"

  #id: ParameterDef[SymbolNameAttr]
  #time_atleast: ParameterDef[IntAttr]
  #time_atmost: ParameterDef[IntAttr]

class Node:
  varname: str
  atleast: int | None = None
  atmost: int | None = None

  def __init__(self, vn: str = str(uuid4())) -> None:
    self.varname = vn



@irdl_attr_definition
class NodeAttr(ParametrizedAttribute, TypeAttribute):
  name = "flow_initial.node"
  uid: ParameterDef[StringAttr]
  #time: ParameterDef[IntAttr]

@irdl_attr_definition
class WNodeAttr(ParametrizedAttribute, TypeAttribute):
  name = "flow_initial.wnode"
  width: ParameterDef[IntAttr]
  uid: ParameterDef[StringAttr]
  #time: ParameterDef[IntAttr]
  
#######################
## NODE DECLARATIONS ##
#######################

@irdl_op_definition
class Const(IRDLOperation):
  name: str = "flow_initial.const"
  result: Annotated[OpResult, NodeAttr]


@irdl_op_definition
class IStream(IRDLOperation):
  name: str = "flow_initial.istream"
  result: Annotated[OpResult, NodeAttr]

@irdl_op_definition
class OStream(IRDLOperation):
  name: str = "flow_initial.ostream"
  opr_0: OpAttr[StringAttr]
  result: Annotated[OpResult, NodeAttr]

@irdl_op_definition
class Offset(IRDLOperation):
  name: str = "flow_initial.offset"
  offset: OpAttr[IntAttr]
  opr_0: OpAttr[StringAttr]
  result: Annotated[OpResult, NodeAttr]

@irdl_op_definition
class Slice(IRDLOperation):
  name: str = "flow_initial.slice"
  lo: OpAttr[IntAttr]
  hi: OpAttr[IntAttr]
  opr_0: OpAttr[StringAttr]
  result: Annotated[OpResult, NodeAttr]


@irdl_op_definition
class Concat(IRDLOperation):
  name: str = "flow_initial.concat"
  opr_0: OpAttr[ArrayAttr[StringAttr]]
  result: Annotated[OpResult, NodeAttr]

@irdl_op_definition
class Unary(IRDLOperation):
  name: str = "flow_initial.unary"
  result: Annotated[OpResult, NodeAttr]
  op: OpAttr[StringAttr]
  opr_0: OpAttr[StringAttr]

@irdl_op_definition
class Resettable(IRDLOperation):
  name: str = "flow_initial.resettable"
  result: Annotated[OpResult, NodeAttr]
  to: OpAttr[IntAttr]
  opr_0: OpAttr[StringAttr]

@irdl_op_definition
class BinOp(IRDLOperation):
  name: str = "flow_initial.binop"
  result: Annotated[OpResult, NodeAttr]
  op: OpAttr[StringAttr]
  opr_0: OpAttr[StringAttr]
  opr_1: OpAttr[StringAttr]

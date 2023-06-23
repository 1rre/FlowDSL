from typing import Annotated

from xdsl.ir import Data, OpResult, Region
from xdsl.irdl import (irdl_attr_definition, irdl_op_definition, IRDLOperation,
                       OpAttr)
from xdsl.printer import Printer
from xdsl.parser import Parser
from xdsl.dialects.builtin import StringAttr, ArrayAttr, IntAttr, FloatAttr
from .node import *

################
## ATTRIBUTES ##
################

def parse_ids(parser: Parser):
  delim = parser.Delimiter.SQUARE
  return lambda: parser.parse_comma_separated_list(delim, parser.parse_str_literal) 

class GraphSize:
  n_inputs: int
  n_outputs: int
  def __init__(self, i, o) -> None:
    self.n_inputs = i
    self.n_outputs = o
  def __str__(self):
    return f"{self.n_inputs}, {self.n_outputs}"

@irdl_attr_definition
class GraphAttr(Data[GraphSize], Attribute, TypeAttribute):
  name: str = "flow_initial.graph"
  @staticmethod
  def parse_parameter(parser: Parser) -> GraphSize:
    delim = parser.Delimiter.NONE
    [inputs, outputs] = parser.parse_comma_separated_list(delim, parser.parse_int_literal)
    return GraphSize(inputs, outputs)
  
  def print_parameter(self, printer: Printer):
    printer.print(self.data)


################
## OPERATIONS ##
################

class NodeCondition:
  pass

class Graph:
  inputs: list[str]
  outputs: list[str]
  variables: list[str]
  conditions: list[NodeCondition]
  def __init__(self, inputs, outputs, variables) -> None:
    self.inputs = inputs
    self.outputs = outputs
    self.variables = variables
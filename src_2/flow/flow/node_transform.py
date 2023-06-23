from abc import abstractmethod
from xdsl.irdl import IRDLOperation
from typing import Callable

from flow.flow.tenative_mapping import NodeMapping
from ..flow_initial.dialect import graph

class NodeTransform:
  depends: dict[str, int]
  width: int = 32
  resettable: bool = False

  @abstractmethod
  def to_xdsl(self, name: str) -> IRDLOperation: pass

class ForwardRef(NodeTransform):
  def __init__(self, name: str):
    self.name = name

class NodeOffset(NodeTransform):
  node: str
  by: int

  def __init__(self, node, by):
    self.node = node
    self.by = by
    self.depends = {node: by}

  def __repr__(self) -> str:
    return f"{self.node}@{self.by}"
  
  def to_xdsl(self, name):
    rtn_type = graph.NodeAttr([
      graph.StringAttr(name),
      #graph.IntAttr(mapping.atmost or mapping.atleast or 0)
    ])
    attributes = {
      "opr_0": graph.StringAttr(self.node),
      "offset": graph.IntAttr(self.by)
    }
    return graph.Offset(attributes=attributes, result_types=[rtn_type])
    

class NodeConst(NodeTransform):
  depends = {}
  value: int
  
  def __init__(self, value, width):
    self.value = value
    self.width = width

  def __repr__(self) -> str:
    return f"{self.value}"

  def to_xdsl(self, name):
    rtn_type = graph.WNodeAttr([
      graph.IntAttr(self.width),
      graph.StringAttr(name),
      #graph.IntAttr(mapping.atmost or mapping.atleast or 0)
    ])
    attributes = {
      "value": graph.IntAttr(self.value)
    }
    return graph.Const(attributes=attributes, result_types=[rtn_type])

class NodeInput(NodeTransform):
  depends = {}
  def to_xdsl(self, name):
    rtn_type = graph.WNodeAttr([
      graph.IntAttr(self.width),
      graph.StringAttr(name),
      #graph.IntAttr(mapping.atmost or mapping.atleast or 0)
    ])
    return graph.IStream(result_types=[rtn_type])
  def __init__(self, width):
    self.width = width
  

class NodeOutput(NodeTransform):
  depends = {}
  node: str
  def __init__(self, node: str, width: int):
    self.depends[node] = 0
    self.node = node
    self.width = width
    
  def to_xdsl(self, name):
    rtn_type = graph.WNodeAttr([
      graph.IntAttr(self.width),
      graph.StringAttr(name)
    ])
    return graph.OStream(
      result_types=[rtn_type],
      attributes={"opr_0": graph.StringAttr(self.node)}
    )

# Unary
class NodeOp(NodeTransform):
  op: str
  node: str

  def __init__(self, op, node):
    self.op = op
    self.node = node
    self.depends = {node: 0}

  def __repr__(self) -> str:
    return f"{self.op}{self.node}"
  
  def to_xdsl(self, name: str):
    rtn_type = graph.NodeAttr([graph.StringAttr(name)])
    attributes = {
      "op": graph.StringAttr(self.op),
      "opr_0": graph.StringAttr(self.node)
    }
    return graph.Unary(
      result_types=[rtn_type],
      attributes=attributes
    )
  

class NodeResettable(NodeTransform):
  to: int
  node: str

  def __init__(self, to, node):
    self.to = to
    self.node = node
    self.depends = {node: 0}

  def __repr__(self) -> str:
    return f"reset({self.node}, {self.to})"
  
  def to_xdsl(self, name: str):
    rtn_type = graph.NodeAttr([graph.StringAttr(name)])
    attributes = {
      "to": graph.IntAttr(self.to),
      "opr_0": graph.StringAttr(self.node)
    }
    return graph.Resettable(
      result_types=[rtn_type],
      attributes=attributes
    )
  
class NodeConcat(NodeTransform):
  nodes: list[str]
  def __init__(self, nodes):
    self.nodes = list(node.name for node in nodes)
    self.depends = {node.name: 0 for node in nodes}
    
  def __repr__(self) -> str:
    return "{" + ", ".join(self.nodes) + "}"
  
  def to_xdsl(self, name: str) -> IRDLOperation:
    rtn_type = graph.NodeAttr([graph.StringAttr(name)])
    attributes = {
      "opr_0": graph.ArrayAttr([graph.StringAttr(node) for node in self.nodes])
    }
    return graph.Concat(
      result_types=[rtn_type],
      attributes=attributes
    )

class NodeSlice(NodeTransform):
  lo: int
  hi: int
  node: str
  def __init__(self, node, lo, hi):
    self.lo = lo
    self.hi = hi
    self.node = node
    self.depends = {node: 0}
    
  def __repr__(self) -> str:
    return f"{self.node}[{self.lo}:{self.hi}]"
  
  def to_xdsl(self, name: str) -> IRDLOperation:
    rtn_type = graph.WNodeAttr([
      graph.IntAttr(abs(self.hi - self.lo)),
      graph.StringAttr(name),
      #graph.IntAttr(mapping.atmost or mapping.atleast or 0)
    ])
    attributes = {
      "lo": graph.IntAttr(self.lo),
      "hi": graph.IntAttr(self.hi),
      "opr_0": graph.StringAttr(self.node)
    }
    return graph.Slice(
      result_types=[rtn_type],
      attributes=attributes
    )    

class NodeBinOp(NodeTransform):
  op: str
  l: str
  r: str

  def __init__(self, op, l, r):
    self.op = op
    self.l = l
    self.r = r
    self.depends = {l: 0, r: 0}

  def __repr__(self) -> str:
    return f"{self.l} {self.op} {self.r}"

  def to_xdsl(self, name: str):
    rtn_type = graph.NodeAttr([graph.StringAttr(name)])
    attributes = {
      "op": graph.StringAttr(self.op),
      "opr_0": graph.StringAttr(self.l),
      "opr_1": graph.StringAttr(self.r)
    }
    return graph.BinOp(
      result_types=[rtn_type],
      attributes=attributes
    )


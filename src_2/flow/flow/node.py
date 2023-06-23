from varname import varname
from .node_transform import *

# TODO: We need to go through and calculate offsets, rename offset nodes etc.
#       This may be in a different class?

class Node:
  name: str
  buffer: int
  width: int

  # mod is a Graph, but can't be typed due to circular dependency
  def __init__(self, mod, name: str, width: int, buffer: int = 0):
    self.name = name
    self.buffer = buffer
    self.mod = mod
    self.width = width

  def offset(self, by: int):
    try:
      vn = f"{varname(1)}"
    except:
      vn = f"#{self.mod.var_cnt}#"
      self.mod.var_cnt += 1
    vn = self.mod.insert_node(vn, NodeOffset(self.name, by))
    return Node(self.mod, vn, self.width, by)

  def __add__(self, other: "Node"):
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.mod.var_cnt}#"
      self.mod.var_cnt += 1
    width = max(self.width, other.width) + 1
    vn = self.mod.insert_node(vn, NodeBinOp("+", self.name, other.name))
    return Node(self.mod, vn, self.width, 0)
  
  def __sub__(self, other: "Node"):
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.mod.var_cnt}#"
      self.mod.var_cnt += 1
    width = max(self.width, other.width) + 1
    vn = self.mod.insert_node(vn, NodeBinOp("-", self.name, other.name))
    return Node(self.mod, vn, self.width, 0)

  def __truediv__(self, other: "Node"):
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.mod.var_cnt}#"
      self.mod.var_cnt += 1
    width = self.width
    vn = self.mod.insert_node(vn, NodeBinOp("/", self.name, other.name))
    return Node(self.mod, vn, self.width, 0)

  def __floordiv__(self, other: "Node"):
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.mod.var_cnt}#"
      self.mod.var_cnt += 1
    width = self.width
    vn = self.mod.insert_node(vn, NodeBinOp("/", self.name, other.name))
    return Node(self.mod, vn, self.width, 0)

  def __mul__(self, other: "Node"):
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.mod.var_cnt}#"
      self.mod.var_cnt += 1
    width = self.width + other.width
    vn = self.mod.insert_node(vn, NodeBinOp("*", self.name, other.name))
    return Node(self.mod, vn, self.width, 0)

  def __repr__(self):
    return f"{self.name}@{self.buffer}"
  
  def __matmul__(self, t: "Node"):
    return self.mod.concat(self, t)
  
  def __pos__(self):
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.mod.var_cnt}#"
      self.mod.var_cnt += 1
    vn = self.mod.insert_node(vn, NodeOp("+", self.name))
    return Node(self.mod, vn, self.width, 0)

  def __abs__(self) -> "Node":
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.mod.var_cnt}#"
      self.mod.var_cnt += 1
    vn = self.mod.insert_node(vn, NodeOp("abs", self.name))
    return Node(self.mod, vn, self.width, 0)
    
  
  def with_reset(self, to: int = 0) -> "Node":
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.mod.var_cnt}#"
      self.mod.var_cnt += 1
    vn = self.mod.insert_node(vn, NodeResettable(to, self.name))
    return Node(self.mod, vn, self.width, 0)


  def __getitem__(self, at: int | slice) -> "Node":
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.mod.var_cnt}#"
      self.mod.var_cnt += 1
    if isinstance(at, slice):
      node = NodeSlice(self.name, at.start, at.stop)
    elif isinstance(at, int):
      node = NodeSlice(self.name, at, at + 1)
    else:
      raise TypeError(at)
    vn = self.mod.insert_node(vn, node)
    return Node(self.mod, vn, abs(node.hi - node.lo), 0)
from flow.flow.tenative_mapping import NodeMapping
from .node import Node
from .node_transform import *
from varname import varname
from ..flow_initial.dialect import graph
from xdsl.ir import MLContext, Block
from xdsl.irdl import RegionDef
from xdsl.dialects.builtin import ModuleOp

class Graph:
  inputs: list[str]
  consts: dict[str, int|float]
  outputs: list[str]
  node_mappings: dict[str, NodeTransform]
  var_cnt = 1

  def __init__(self):
    self.node_mappings = {}
    self.outputs = []
    self.inputs = []

  def insert_node(self, vn: str, node: NodeTransform):
    vn_renamed = vn
    i = 0
    while vn_renamed in self.node_mappings and not isinstance(self.node_mappings[vn_renamed], ForwardRef):
      vn_renamed = f"{vn}${i}"
      i += 1
    self.node_mappings[vn_renamed] = node
    return vn_renamed

  def forward_ref(self, name: str):
    node = ForwardRef(name)
    vn = self.insert_node(name, node)
    return Node(self, vn, 0)
  
  def concat(self, *args: Node):
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.var_cnt}#"
      self.var_cnt += 1
    vn = self.insert_node(vn, NodeConcat(list(args)))
    return Node(self, vn, 0)

  def istream(self, width: int = 32):
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.var_cnt}#"
      self.var_cnt += 1
    vn = self.insert_node(vn, NodeInput(width))
    self.inputs.append(vn)
    return Node(self, vn, 0)

  def const(self, value: int, width: int = 32):
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.var_cnt}#"
      self.var_cnt += 1
    vn = self.insert_node(vn, NodeConst(value, width))
    return Node(self, vn, 0)

  def ostream(self, node: Node, width: int = 32):
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.var_cnt}#"
      self.var_cnt += 1
    self.insert_node(vn, NodeOutput(node.name, width))
    self.outputs.append(vn)
    return Node(self, vn, width, 0)
  
  def accumulate(self, node: Node):
    try:
      vn = f"{varname()}"
    except:
      vn = f"#{self.var_cnt}#"
      self.var_cnt += 1
    vn = self.insert_node(vn, NodeOp("+", node.name))
    return Node(self, vn, node.width, 0)
  
  def check_mapping(self, mapping: NodeMapping) -> bool:
    if mapping.atleast == None:
      for ref in mapping.refs:
        if ref.atleast != None:
          return False
      return True
    elif mapping.atmost == None:
      for ref in mapping.irefs:
        if ref.atmost != None:
          return False
      return True
    else:
      # Probably more comprehensive tests required here
      if mapping.atmost >= mapping.atleast:
        return True
      else:
        return False
      
  def setup_mappings(self):
    mappings = {node: NodeMapping(node) for node in self.inputs}

    for node in self.node_mappings.keys():
      mappings[node] = NodeMapping(node)

    for (node, transform) in self.node_mappings.items():
      for (dep, offset) in transform.depends.items():
        maybe_dep = mappings.get(dep)
        if maybe_dep == None:
          raise(UnboundLocalError(dep))
        if isinstance(self.node_mappings[node], NodeBinOp):
          mappings[node].refs[maybe_dep] = offset + 1
        else:
          mappings[node].refs[maybe_dep] = offset

    for node in self.inputs:
      mappings[node].atleast = 0
      mappings[node].atmost = 0

    for (node, mapping) in mappings.items():
      mapping.invert(mappings)
    
    return mappings
  
  def depths(self):
    mappings = self.setup_mappings()
    def run_iteration():
      # TODO: detect no of iterations
      for (node, mapping) in mappings.items():
        mapping.set_lower_limits()
      # TODO: Check if mapping is complete, and if not then recurse
      do_recurse = False
      for (node, mapping) in mappings.items():
        if self.check_mapping(mapping):
          pass
        else:
          do_recurse = True
      if do_recurse: run_iteration()
    
    run_iteration()

    for (node, mapping) in mappings.items():
      mapping.set_upper_limits()

    return mappings
  
  def resolve(self):
    depth_map: dict[str, NodeMapping] = self.depths()
    for (node, mapping) in depth_map.items():
      assert self.check_mapping(mapping), f"Mapping {node} does not resolve"
    return depth_map

  
  def mk_const(self, name: str, value: int | float):
    value_attr = graph.IntAttr(value) if isinstance(value, int) else graph.FloatAttr(value) # type: ignore
    return graph.Const(
      result_types=[],
      attributes={"value": value_attr}
    )

  def to_xdsl(self):
    #node_mapping = self.resolve()
    #node_mapping = self.setup_mappings()
    ops = list(
      node.to_xdsl(name,)
        for (name, node) in self.node_mappings.items()
    )
    block = Block(ops = ops)
    ops = RegionDef(blocks = [block])
    op = ModuleOp(ops)
    return op
  
  def to_xdsl_timing(self):
    ops = []
    block = Block(ops = ops)
    ops = RegionDef(blocks = [block])
    op = ModuleOp(ops)
    return op
    
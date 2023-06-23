
class NodeMapping:
  node: str
  refs: dict["NodeMapping", int]
  irefs: dict["NodeMapping", int]
  atleast: int | None = None
  atmost: int | None = None
  
  def __init__(self, node: str):
    self.node = node
    self.refs = {}
    self.irefs = {}

  def add_ref(self, to: "NodeMapping", offset: int):
    self.refs[to] = offset

  def invert(self, mappings: dict[str, "NodeMapping"]):
    for (_, mapping) in mappings.items():
      if self in mapping.refs.values():
        self.irefs[mapping] = mapping.refs[self]

  def set_lower_limits(self):
    for (ref, offset) in self.refs.items():
      if ref.atleast != None:
        if self.atleast == None:
          self.atleast = ref.atleast + offset
        else:
          self.atleast = max(ref.atleast + offset, self.atleast)
  
  def set_upper_limits(self):
    # TODO: Backfeed from mappings
    if (self.atleast != None):
      for (ref, offset) in self.refs.items():
        if ref.atmost == None:
          ref.atmost = self.atleast - offset
          ref.set_upper_limits()
        else:
          if (self.atleast - offset < ref.atmost):
            ref.atmost = self.atleast - offset
            ref.set_upper_limits()
    # TODO: Cascade forward

  def __repr__(self):
    return f"«{self.atleast} < {self.node} < {self.atmost}»"


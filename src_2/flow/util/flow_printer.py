from xdsl.printer import Printer
from xdsl.ir import SSAValue, Operation
from xdsl.dialects.builtin import ModuleOp
from  ..hard_flow import reg as node

def offset_by(name: str, by: int):
  # This is how many clock cycles we need to buffe
  if by == 0:
    return name
  elif by < 0:
    # TODO: Scan for this and work from there?
    print(f"Attempt to offset {name} into the future by {by}")
    raise ValueError
  else:
    return f"buffer_{name}_{by}"


class PrintContext:
  inputs: list[Operation]
  outputs: list[Operation]
  buffers: dict[str, set[int]]
  ssa_values: dict[SSAValue, str]
  module: ModuleOp
  widths: dict[Operation, int]
  max_t: int = 0


  cnt = 0

  def get_name(self, op: Operation) -> str:
    if op.results[0] in self.ssa_values:
      return self.ssa_values[op.results[0]]
    if isinstance(op, node.Offset):
      return self.get_name(op.operands[0].owner)
    if isinstance(op, node.Const):
      value = op.attributes["value"].data
      width = op.result.typ.width.data
      return f"{width}'d{value}"
    if "uid" in op.attributes:
      return op.attributes["uid"].data
    self.ssa_values[op.results[0]] = f'gen_{self.cnt}'
    print(f"Added ('gen_{self.cnt}'): {op}")
    self.cnt += 1
    return self.ssa_values[op.results[0]]



  def add_ssa_values(self, op: Operation):
    # Don't actually add inputs or outputs to the context
    for val in op.results:
      if not isinstance(val.owner, node.Buffer):
        self.ssa_values[val] = self.get_name(op)
        self.widths[val.owner] = val.typ.width.data

    if isinstance(op, node.IStream):
      self.inputs.append(op)
      self.widths[op] = op.result.typ.width.data # type: ignore
      
    elif isinstance(op, node.OStream):
      self.outputs.append(op)
      self.widths[op] = op.result.typ.width.data # type: ignore

    if isinstance(op, node.Const):
      return
    
    for val in op.operands:
      if not isinstance(val.owner, node.Buffer):
        self.widths[val.owner] = val.typ.width.data # type:  ignore
        self.ssa_values[val] = self.get_name(val.owner) # type: ignore
    

  def add_buffers(self, op: Operation):
    if len(op.results) != 1 or isinstance(op, node.Const):
      return
    elif isinstance(op, node.Buffer):
      dep_name = self.ssa_values[op.operands[0]]
      diff = op.attributes["by"].data # type: ignore
      self.buffers[dep_name] |= set(range(1, diff + 1))
      self.ssa_values[op.result] = offset_by(dep_name, diff)

  def pop_io(self, op: Operation):
    if isinstance(op, node.IStream) or isinstance(op, node.OStream):
      self.ssa_values.pop(op.result)

  def __init__(self, module: ModuleOp):
    self.inputs = []
    self.outputs = []
    self.ssa_values = {}
    self.buffers = {}
    self.widths = {}
    self.module = module
    module.walk(self.add_ssa_values)
    for (key, val) in self.ssa_values.items():
      self.buffers[val] = set()
      if isinstance(key.owner, node.Unary) and key.owner.attributes['op'].data == '+' or isinstance(key.owner, node.Resettable):
        self.max_t = max(key.typ.time.data, self.max_t)
    module.walk(self.add_buffers)
      
    #module.walk(self.pop_io)

class FlowPrinter:
  #def print_op_helper(self, context: PrintContext):
  #  def print_op(op: Operation):
  #    operands = ", ".join(list(context.ssa_values[opr] for opr in op.operands))
  #    results = ", ".join(list(context.ssa_values[res] for res in op.results))
  #    if isinstance(op, node.IStream):
  #      print("Found istream")
  #  return print_op
  def get_width(self, width):
    if width <= 0:
      raise IndexError(width)
    if width == 1:
      return ""
    else:
      return f"[{width-1}:0]"

  def print_helper(self, context: PrintContext):
    print("module GeneratedModule(")
    default_inputs = ["    input clk", "    input reset_n"]
    default_outputs = []
    inputs = list(f"    input {self.get_width(context.widths[input])} {context.get_name(input)}" for input in context.inputs)
    outputs = list(f"    output {self.get_width(context.widths[output])} {context.get_name(output)}" for output in context.outputs)
    print((",\n").join(default_inputs + inputs + outputs + default_outputs))
    print(");")

    initials = []
    io_names = list(context.get_name(io) for io in (context.inputs + context.outputs))
    declared = []
    for i in range(1, context.max_t + 1):
      initials.append(f"    buffer_reset_n_{i} = 0;")
      print(f"  reg buffer_reset_n_{i};") # type: ignore
  
    for (op, val) in context.ssa_values.items():
      if isinstance(op.owner, node.Buffer):
        owner = op.owner
        while isinstance(owner, node.Buffer) or isinstance(owner, node.Offset):
          owner = owner.operands[0].owner
        width = context.widths[owner]
        owner_name = context.ssa_values[owner.results[0]]
        for i in range(1, op.owner.attributes['by'].data + 1):
          if f"buffer_{owner_name}_{i}" not in declared:
            declared.append(f"buffer_{owner_name}_{i}")
            print(f"  reg {self.get_width(width)} buffer_{owner_name}_{i};") # type: ignore
            initials.append(f"    buffer_{owner_name}_{i} = 0;")
      elif (val not in io_names and not isinstance(op.owner, node.Offset)
                                and not isinstance(op.owner, node.Const)
                                and not isinstance(op.owner, node.Resettable)):
        print(f"  reg {self.get_width(context.widths[op.owner])} {val};") # type: ignore
        initials.append(f"    {val} = 0;") # type: ignore
        #print(f"  initial {val} = 0;")
        declared.append(val)
      elif isinstance(op.owner, node.Resettable):
        reset_to = op.owner.attributes['to'].data
        parent = context.ssa_values[op.owner.operands[0]]
        reset_time =  op.typ.time.data
        if reset_time < 0:
          reset_time = 0
        reset = offset_by("reset_n", reset_time)
        print(f"  wire {self.get_width(context.widths[op.owner])} {val} = {reset}? {parent} : {reset_to};") # type: ignore


    print("  initial begin")
    for initial in initials:
      print(initial)
    print("  end")

    for op in context.module.regions[0].block.ops:
      if isinstance(op, node.OStream):
        name = context.ssa_values[op.operands[0]]
        res = context.ssa_values[op.result]
        print(f"  assign {res} = {name};")

        
    print("  always @(posedge clk) begin")
    for (name, buffer) in context.buffers.items():
      last = name
      if len(buffer) > 0:
        parent = 0
        for (key, val) in context.ssa_values.items():
          if val == name and not(isinstance(key.owner, node.Const)):
            parent = key.typ.time.data
            break
        for n in sorted(list(buffer)):
          # Reset carried by buffer
          print(f"    buffer_{name}_{n} <= {last};")
          last = f"buffer_{name}_{n}"

    last = "reset_n"
    for i in range(1, context.max_t + 1):
      print(f"    buffer_reset_n_{i} <= {last};")
      last = f"buffer_reset_n_{i}"

    for op in context.module.regions[0].block.ops:
      if isinstance(op, node.Unary):
        time = op.result.typ.time.data
        nd = op.operands[0]
        node_name = context.ssa_values[nd]
        res = context.ssa_values[op.result]
        match op.attributes['op'].data:
          case '-' | '~' | '!':
            print(f"    {res} <= {op.attributes['op'].data} {node_name};")
          case 'abs':
            print(f"    {res} <= {node_name}[{op.result.typ.width.data-1}] ? -{node_name} : {node_name};")
          case '+':
            if hasattr(op.result.typ, "time"):
              reset = op.result.typ.time.data - 1
            else:
              reset = 0
            reset = offset_by("reset_n", reset)
            print(f"    {res} <= $unsigned($signed({res}) & $signed({reset})) + {node_name};")
      elif isinstance(op, node.BinOp):
        # TODO: Check Times
        o0_const = isinstance(op.operands[0].owner, node.Const)
        o1_const = isinstance(op.operands[1].owner, node.Const)

        #if not o0_const and not o1_const and op.operands[0].typ.time.data != op.operands[1].typ.time.data:
        #  print("// MISMATCH (OPERAND 0/OPERAND 1):")
        #  print(f"// {op.operands[0].owner}")
        #  print(f"// {op.operands[1].owner}")
        #  print()
        #if not o0_const and op.result.typ.time.data != op.operands[0].typ.time.data + 1:
        #  print("// MISMATCH (OPERAND 0/RESULT):")
        #  print(f"// {op.operands[0].owner}")
        #  print(f"// {op}")
        #  print()
        #if not o1_const and op.result.typ.time.data != op.operands[1].typ.time.data + 1:
        #  print("// MISMATCH (OPERAND 1/RESULT):")
        #  print(f"// {op.operands[1].owner}")
        #  print(f"// {op}")
        #  print()
        time = op.result.typ.time.data
        left = op.operands[0]
        left_name = context.ssa_values[left]
        if not isinstance(left.owner, node.Const) and left.typ.time.data < time - 1:
          left_name = f"buffer_{left_name}_{time - left.typ.time.data - 1}"
        
        right = op.operands[1]
        right_name = context.ssa_values[right]
        if not isinstance(right.owner, node.Const) and right.typ.time.data < time - 1:
          right_name = f"buffer_{right_name}_{time - right.typ.time.data - 1}"

        res = context.ssa_values[op.result]
        print(f"    {res} <= {left_name} {op.attributes['op'].data} {right_name};")
      #elif isinstance(op, node.Offset):

    print("  end")
    print("endmodule")

  def print_module(self, module: ModuleOp):
    context = PrintContext(module)
    self.print_helper(context)



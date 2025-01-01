from enum import Enum, auto

class OpCode(Enum):
    OP_CONSTANT = auto()
    OP_NIL = auto()
    OP_TRUE = auto()
    OP_FALSE = auto()
    OP_POP = auto()
    OP_GET_LOCAL = auto()
    OP_SET_LOCAL = auto()
    OP_GET_GLOBAL = auto()
    OP_DEFINE_GLOBAL = auto()
    OP_SET_GLOBAL = auto()
    OP_EQUAL = auto()
    OP_GREATER = auto()
    OP_LESS = auto()
    OP_ADD = auto()
    OP_SUBTRACT = auto()
    OP_MULTIPLY = auto()
    OP_DIVIDE = auto()
    OP_NOT = auto()
    OP_NEGATE = auto()
    OP_PRINT = auto()
    OP_JUMP = auto()
    OP_JUMP_IF_FALSE = auto()
    OP_LOOP = auto()
    OP_CALL = auto()
    OP_RETURN = auto()
    OP_GET_FIELD = auto()
    OP_SET_FIELD = auto()
    OP_STRUCT = auto()
    OP_BUILD_ARRAY = auto()
    OP_GET_INDEX = auto()
    OP_SET_INDEX = auto()
    OP_CLOSURE = auto()
    OP_GET_UPVALUE = auto()
    OP_SET_UPVALUE = auto()
    OP_CLOSE_UPVALUE = auto()
    OP_CLASS = auto()
    OP_METHOD = auto()
    OP_INHERIT = auto()
    OP_GET_SUPER = auto()
    
    # Error handling
    OP_TRY_BEGIN = auto()   # Push exception handler
    OP_TRY_END = auto()     # Pop exception handler
    OP_THROW = auto()       # Throw exception

class Chunk:
    def __init__(self):
        self.code = []
        self.lines = []
        self.constants = []

    def write(self, byte, line):
        self.code.append(byte)
        self.lines.append(line)

    def add_constant(self, value):
        self.constants.append(value)
        return len(self.constants) - 1

    def disassemble(self, name):
        print(f"== {name} ==")
        i = 0
        while i < len(self.code):
            i = self.disassemble_instruction(i)

    def disassemble_instruction(self, offset):
        print(f"{offset:04d} ", end="")
        if offset > 0 and self.lines[offset] == self.lines[offset - 1]:
            print("   | ", end="")
        else:
            print(f"{self.lines[offset]:4d} ", end="")
        
        instruction = self.code[offset]
        if isinstance(instruction, OpCode):
            # It's an enum member
            if instruction == OpCode.OP_CONSTANT:
                return self.constant_instruction("OP_CONSTANT", self.chunk_ref, offset)
            # ... incomplete disassembler logic, but that's fine for now
            print(f"{instruction.name}")
            return offset + 1
        elif isinstance(instruction, int): # Byte args
             # This simple disassembler assumes instruction at offset is OpCode
             # But bytecode is mixed list of OpCode enum and ints.
             # My VM reads self.chunk.code[ip].
             pass
        return offset + 1


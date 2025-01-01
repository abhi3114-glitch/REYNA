from enum import Enum, auto

class ObjType(Enum):
    STRING = auto()
    STRUCT = auto()
    INSTANCE = auto()
    FUNCTION = auto()
    NATIVE = auto()
    CLASS = auto()
    BOUND_METHOD = auto()
    ARRAY = auto()



# ... preserve others ...


class Obj:
    def __init__(self, type):
        self.type = type
        self.marked = False # For GC

    def __repr__(self):
        return f"<Obj {self.type.name}>"

class ObjString(Obj):
    def __init__(self, value):
        super().__init__(ObjType.STRING)
        self.value = value
    
    def __repr__(self):
        return f"'{self.value}'"

    def __str__(self):
        return self.value
    
    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return isinstance(other, ObjString) and self.value == other.value

class ObjStruct(Obj):
    def __init__(self, name):
        super().__init__(ObjType.STRUCT)
        self.name = name
    
    def __repr__(self):
        return f"<struct {self.name}>"

class ObjArray(Obj):
    def __init__(self, elements):
        super().__init__(ObjType.ARRAY)
        self.elements = elements
    def __repr__(self): return str(self.elements)
    def __str__(self): return str(self.elements)

class ObjInstance(Obj):
    def __init__(self, struct):
        super().__init__(ObjType.INSTANCE)
        self.struct = struct
        self.fields = {} # name -> value
    
    def __repr__(self):
        return f"<instance {self.struct.name}>"

class ObjFunction(Obj):
    def __init__(self, name, arity, chunk, upvalue_count=0):
        super().__init__(ObjType.FUNCTION)
        self.name = name
        self.arity = arity
        self.chunk = chunk
        self.upvalue_count = upvalue_count
    
    def __repr__(self):
        return f"<fn {self.name}>"

class ObjUpvalue(Obj):
    def __init__(self, location):
        super().__init__(ObjType.NATIVE) # Internal type
        self.location = location # Stack index (int) or None if closed
        self.closed = None # The value if closed
        self.next = None # For open upvalues list in VM

    def __repr__(self):
        return f"<upvalue loc={self.location} closed={self.closed}>"

class ObjClosure(Obj):
    def __init__(self, function):
        super().__init__(ObjType.FUNCTION)
        self.function = function
        self.upvalues = [] # List of ObjUpvalue
        
    def __repr__(self):
        return f"<closure {self.function.name}>"

class ObjNative(Obj):
    def __init__(self, fn, name):
        super().__init__(ObjType.NATIVE)
        self.fn = fn
        self.name = name
    
    def __repr__(self):
        return f"<native {self.name}>"

class ObjClass(Obj):
    def __init__(self, name):
        super().__init__(ObjType.CLASS)
        self.name = name
        self.methods = {}
    
    def __repr__(self):
        return f"<class {self.name}>"

class ObjBoundMethod(Obj):
    def __init__(self, receiver, method):
        super().__init__(ObjType.BOUND_METHOD)
        self.receiver = receiver
        self.method = method
    
    def __repr__(self):
        return str(self.method)




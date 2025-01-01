from reyna_chunk import OpCode
from token_type import TokenType
import reyna_vals as object
from reyna_gc import GC

class InterpretResult:
    OK = 0
    COMPILE_ERROR = 1
    RUNTIME_ERROR = 2

class CallFrame:
    def __init__(self, closure, ip, slots):
        self.closure = closure
        self.ip = ip
        self.slots = slots

class ExceptionHandler:
    def __init__(self, catch_ip, stack_depth, frame_depth):
        self.catch_ip = catch_ip     # IP to jump to on exception
        self.stack_depth = stack_depth  # Stack size when try was entered
        self.frame_depth = frame_depth  # Call frame depth when try was entered

class VM:
    def __init__(self):
        self.frames = []
        self.stack = []
        self.globals = {} 
        self.open_upvalues = [] # Linked list of open upvalues
        self.gc = GC(self) # Initialize GC
        self.exception_handlers = []  # Stack of exception handlers
        
        # Load Stdlib
        import stdlib
        stdlib.register_stdlib(self)
        import sys
        self.sys = sys

    def interpret(self, chunk):
        fn = object.ObjFunction("script", 0, chunk)
        closure = object.ObjClosure(fn)
        self.stack = [closure]
        self.frames = [CallFrame(closure, 0, 0)]
        return self.run()

    def read_byte(self):
        frame = self.frames[-1]
        b = frame.closure.function.chunk.code[frame.ip]
        frame.ip += 1
        return b

    def read_short(self):
        frame = self.frames[-1]
        b1 = frame.closure.function.chunk.code[frame.ip]
        b2 = frame.closure.function.chunk.code[frame.ip+1]
        frame.ip += 2
        return (b1 << 8) | b2

    def read_constant(self):
        frame = self.frames[-1]
        return frame.closure.function.chunk.constants[self.read_byte()]

    def run(self):
        while True:
            if not self.frames: return InterpretResult.OK
            
             # print(f"Stack: {self.stack}")
            try:
                # print(f"IP: {self.frames[-1].ip} Op: {self.frames[-1].closure.function.chunk.code[self.frames[-1].ip]}")
                pass
            except: pass
            instruction = self.read_byte()
            
            # Dispatch
            # print(f"OP: {instruction}")
            # self.sys.stdout.flush()
            if instruction == OpCode.OP_RETURN:
                result = self.pop() if self.stack else None
                self.close_upvalues(self.frames[-1].slots) # Close upvalues for this frame
                frame = self.frames.pop()
                if not self.frames:
                    return InterpretResult.OK
                
                # Clean up caller's stack to the point before the call
                while len(self.stack) > frame.slots:
                    self.pop()
                self.push(result)
                continue
            
            elif instruction == OpCode.OP_CONSTANT:
                constant = self.read_constant()
                self.push(constant)
            
            elif instruction == OpCode.OP_NIL: self.push(None)
            elif instruction == OpCode.OP_TRUE: self.push(True)
            elif instruction == OpCode.OP_FALSE: self.push(False)
            
            elif instruction == OpCode.OP_POP:
                if len(self.stack) > 0: self.pop()

            elif instruction == OpCode.OP_GET_LOCAL:
                slot = self.read_byte()
                val = self.stack[self.frames[-1].slots + slot]
                self.push(val)
                
            elif instruction == OpCode.OP_SET_LOCAL:
                slot = self.read_byte()
                self.stack[self.frames[-1].slots + slot] = self.peek(0)
            
            # ... globals ...

            elif instruction == OpCode.OP_JUMP_IF_FALSE:
                offset = self.read_short()
                if not self.is_truthy(self.peek(0)):
                    self.frames[-1].ip += offset
            elif instruction == OpCode.OP_JUMP:
                offset = self.read_short()
                self.frames[-1].ip += offset
            elif instruction == OpCode.OP_LOOP:
                offset = self.read_short()
                self.frames[-1].ip -= offset
                
            elif instruction == OpCode.OP_GET_GLOBAL:
                name_idx = self.read_byte()
                name = self.frames[-1].closure.function.chunk.constants[name_idx]
                if name in self.globals:
                    self.push(self.globals[name])
                else:
                    print(f"Undefined variable '{name}'.")
                    return InterpretResult.RUNTIME_ERROR
                    
            elif instruction == OpCode.OP_DEFINE_GLOBAL:
                name_idx = self.read_byte()
                name = self.frames[-1].closure.function.chunk.constants[name_idx]
                self.globals[name] = self.peek(0)
                self.pop()
                
            elif instruction == OpCode.OP_SET_GLOBAL:
                name_idx = self.read_byte()
                name = self.frames[-1].closure.function.chunk.constants[name_idx]
                if name in self.globals:
                     self.globals[name] = self.peek(0)
                else:
                    print(f"Undefined variable '{name}'.")
                    # return InterpretResult.RUNTIME_ERROR
            
            elif instruction == OpCode.OP_EQUAL:
                b = self.pop()
                a = self.pop()
                self.push(a == b)
                
            elif instruction == OpCode.OP_GREATER:
                b = self.pop()
                a = self.pop()
                self.push(a > b)
                
            elif instruction == OpCode.OP_LESS:
                b = self.pop()
                a = self.pop()
                self.push(a < b)

            elif instruction == OpCode.OP_ADD:
                b = self.pop()
                a = self.pop()
                if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    self.push(a + b)
                # Handle String concat
                elif isinstance(a, object.ObjString) or isinstance(b, object.ObjString):
                    str_a = a.value if isinstance(a, object.ObjString) else str(a)
                    str_b = b.value if isinstance(b, object.ObjString) else str(b)
                    
                    res = object.ObjString(str_a + str_b)
                    self.gc.allocate(res)
                    self.push(res)
                else:
                    # Fallback for maybe other objects?
                    # For now just try python add
                    try:
                        self.push(a + b)
                    except:
                        print(f"Runtime Error: Cannot add {type(a)} {type(b)}")
                        return InterpretResult.RUNTIME_ERROR

            elif instruction == OpCode.OP_SUBTRACT:
                b = self.pop()
                a = self.pop()
                self.push(a - b)
            elif instruction == OpCode.OP_MULTIPLY:
                b = self.pop()
                a = self.pop()
                self.push(a * b)
            elif instruction == OpCode.OP_DIVIDE:
                b = self.pop()
                a = self.pop()
                self.push(a / b)
            elif instruction == OpCode.OP_NOT:
                self.push(not self.pop())
            elif instruction == OpCode.OP_NEGATE:
                self.push(-self.pop())
            elif instruction == OpCode.OP_PRINT:
                val = self.pop()
                print(val)
                
            elif instruction == OpCode.OP_JUMP_IF_FALSE:
                offset = self.read_short()
                if not self.is_truthy(self.peek(0)):
                    self.frames[-1].ip += offset
            elif instruction == OpCode.OP_JUMP:
                offset = self.read_short()
                self.frames[-1].ip += offset
            elif instruction == OpCode.OP_LOOP:
                offset = self.read_short()
                self.frames[-1].ip -= offset
                
            elif instruction == OpCode.OP_GET_FIELD:
                name_idx = self.read_byte()
                name = self.frames[-1].closure.function.chunk.constants[name_idx]
                obj = self.pop()
                if isinstance(obj, object.ObjInstance):
                    if name in obj.fields:
                         self.push(obj.fields[name])
                    elif isinstance(obj.struct, object.ObjClass) and name in obj.struct.methods:
                         method = obj.struct.methods[name]
                         bound = object.ObjBoundMethod(obj, method)
                         self.gc.allocate(bound)
                         self.push(bound)
                    else:
                        print(f"Undefined property '{name}'.")
                        return InterpretResult.RUNTIME_ERROR
                else:
                    print(f"Only instances have properties. Got {obj}.")
                    return InterpretResult.RUNTIME_ERROR

            elif instruction == OpCode.OP_SET_FIELD:
                name_idx = self.read_byte()
                name = self.frames[-1].closure.function.chunk.constants[name_idx]
                val = self.pop()
                obj = self.pop()
                if isinstance(obj, object.ObjInstance):
                    obj.fields[name] = val
                    self.push(val)
                else:
                    print("Only instances have properties.")
                    return InterpretResult.RUNTIME_ERROR
            
            elif instruction == OpCode.OP_CALL:
                arg_count = self.read_byte()
                callee = self.peek(arg_count)
                if not self.call_value(callee, arg_count):
                    return InterpretResult.RUNTIME_ERROR

            elif instruction == OpCode.OP_CLASS:
                name_idx = self.read_byte()
                name = self.frames[-1].closure.function.chunk.constants[name_idx]
                klass = object.ObjClass(name)
                self.gc.allocate(klass)
                self.push(klass)
                
            elif instruction == OpCode.OP_METHOD:
                name_idx = self.read_byte()
                name = self.frames[-1].closure.function.chunk.constants[name_idx]
                method = self.peek(0)
                klass = self.peek(1)
                klass.methods[name] = method
                self.pop()
    
            elif instruction == OpCode.OP_STRUCT:
                name_idx = self.read_byte()
                name = self.frames[-1].closure.function.chunk.constants[name_idx]
                struct_obj = object.ObjStruct(name)
                self.gc.allocate(struct_obj)
                self.push(struct_obj)
            
            elif instruction == OpCode.OP_BUILD_ARRAY:
                count = self.read_byte()
                elements = []
                for _ in range(count):
                    elements.append(self.pop())
                elements.reverse()
                arr = object.ObjArray(elements)
                self.gc.allocate(arr)
                self.push(arr)
            
            elif instruction == OpCode.OP_GET_INDEX:
                index = self.pop()
                arr = self.pop()
                if isinstance(arr, object.ObjArray):
                    if isinstance(index, (int, float)):
                        idx = int(index)
                        if 0 <= idx < len(arr.elements):
                            self.push(arr.elements[idx])
                        else:
                            print(f"Index {idx} out of bounds for array of length {len(arr.elements)}.")
                            return InterpretResult.RUNTIME_ERROR
                    else:
                        print(f"Array index must be a number, got {type(index).__name__}.")
                        return InterpretResult.RUNTIME_ERROR
                else:
                    print(f"Can only index arrays, got {type(arr).__name__}.")
                    return InterpretResult.RUNTIME_ERROR
            

            elif instruction == OpCode.OP_CLOSURE:
                fn = self.read_constant()
                closure = object.ObjClosure(fn)
                self.gc.allocate(closure)
                self.push(closure)
                
                for i in range(fn.upvalue_count):
                    is_local = self.read_byte()
                    index = self.read_byte()
                    if is_local:
                         closure.upvalues.append(self.capture_upvalue(self.frames[-1].slots + index))
                    else:
                         closure.upvalues.append(self.frames[-1].closure.upvalues[index]) 

            elif instruction == OpCode.OP_INHERIT:
                superclass = self.peek(0)
                subclass = self.peek(1)
                
                if not isinstance(superclass, object.ObjClass):
                    print("Superclass must be a class.")
                    return InterpretResult.RUNTIME_ERROR
                
                subclass.methods.update(superclass.methods)
                # Keep superclass on stack for 'super' local variable scope usage.
                # Do NOT pop.
             
            elif instruction == OpCode.OP_GET_SUPER:
                name_idx = self.read_byte()
                name = self.frames[-1].closure.function.chunk.constants[name_idx]
                superclass = self.pop()
                receiver = self.pop()
                
                if not isinstance(superclass, object.ObjClass):
                    print(f"Error in OP_GET_SUPER: Expected ObjClass, got {type(superclass).__name__} ({superclass})")
                    return InterpretResult.RUNTIME_ERROR
                
                if name in superclass.methods:
                    method = superclass.methods[name]
                    bound = object.ObjBoundMethod(receiver, method)
                    self.gc.allocate(bound)
                    self.push(bound)
                else:
                    print(f"Undefined property '{name}' in superclass.")
                    return InterpretResult.RUNTIME_ERROR

            elif instruction == OpCode.OP_GET_UPVALUE:
                slot = self.read_byte()
                frame = self.frames[-1]
                upvalue = frame.closure.upvalues[slot]
                if upvalue.location is not None:
                     self.push(self.stack[upvalue.location])
                else:
                     self.push(upvalue.closed)

            elif instruction == OpCode.OP_SET_UPVALUE:
                slot = self.read_byte()
                frame = self.frames[-1]
                val = self.peek(0) # Assignment expression evaluates to value
                upvalue = frame.closure.upvalues[slot]
                if upvalue.location is not None:
                     self.stack[upvalue.location] = val
                else:
                     upvalue.closed = val
            
            elif instruction == OpCode.OP_CLOSE_UPVALUE:
                self.close_upvalues(len(self.stack) - 1)
                self.pop()

            elif instruction == OpCode.OP_TRY_BEGIN:
                # Read offset to catch block
                catch_offset = self.read_short()
                catch_ip = self.frames[-1].ip + catch_offset - 2  # Adjust for already read bytes
                handler = ExceptionHandler(catch_ip, len(self.stack), len(self.frames))
                self.exception_handlers.append(handler)

            elif instruction == OpCode.OP_TRY_END:
                # Successfully completed try block, pop handler
                if self.exception_handlers:
                    self.exception_handlers.pop()

            elif instruction == OpCode.OP_THROW:
                exception = self.pop()
                if not self.exception_handlers:
                    # No handler, runtime error
                    print(f"Uncaught exception: {exception}")
                    return InterpretResult.RUNTIME_ERROR
                
                # Find handler and unwind
                handler = self.exception_handlers.pop()
                
                # Unwind call stack
                while len(self.frames) > handler.frame_depth:
                    self.frames.pop()
                
                # Unwind value stack
                while len(self.stack) > handler.stack_depth:
                    self.pop()
                
                # Push exception value for catch variable
                self.push(exception)
                
                # Jump to catch block
                self.frames[-1].ip = handler.catch_ip

    def capture_upvalue(self, local_idx):
        for up in self.open_upvalues:
            if up.location == local_idx: return up
        created = object.ObjUpvalue(local_idx)
        self.open_upvalues.append(created)
        return created

    def close_upvalues(self, last):
        i = 0
        while i < len(self.open_upvalues):
            up = self.open_upvalues[i]
            if up.location >= last:
                up.closed = self.stack[up.location]
                up.location = None
                self.open_upvalues.pop(i)
            else:
                 i += 1

    def call_value(self, callee, arg_count):
        if isinstance(callee, object.ObjBoundMethod):
             self.stack[-arg_count - 1] = callee.receiver
             return self.call(callee.method, arg_count)
             
        elif isinstance(callee, object.ObjClass):
             instance = object.ObjInstance(callee)
             self.gc.allocate(instance)
             
             # Check for init
             if "init" in callee.methods:
                  initializer = callee.methods["init"]
                  # Setup call
                  # Replace callee (ObjClass) with Instance for 'this'
                  self.stack[-arg_count - 1] = instance
                  return self.call(initializer, arg_count)
             elif arg_count != 0:
                  print(f"Expected 0 arguments but got {arg_count}.")
                  return False
             
             self.stack[-arg_count - 1] = instance
             return True
             
        elif isinstance(callee, object.ObjClosure):
            return self.call(callee, arg_count)
            
        elif isinstance(callee, object.ObjStruct):
            if arg_count != 0:
                 print(f"Struct constructor expects 0 args.")
                 return False
            instance = object.ObjInstance(callee)
            self.gc.allocate(instance)
            # Remove Struct from stack, replace with Instance
            # Struct is at stack[-1] since arg_count=0
            self.stack[-1] = instance
            return True
        elif isinstance(callee, object.ObjNative):
            args = self.stack[-arg_count:]
            result = callee.fn(args)
            self.stack = self.stack[:-arg_count-1]
            self.push(result)
            return True
        else:
             print(f"Runtime Error: Can only call functions or structs, got {callee}.")
             return False

    def call(self, closure, arg_count):
        if arg_count != closure.function.arity:
             print(f"Expected {closure.function.arity} arguments but got {arg_count}.")
             return False
        
        slots = len(self.stack) - arg_count - 1
        frame = CallFrame(closure, 0, slots)
        self.frames.append(frame)
        return True

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        return self.stack.pop()
    
    def peek(self, distance):
        return self.stack[-1 - distance]

    def is_truthy(self, value):
        if value is None: return False
        if isinstance(value, bool): return value
        if value == 0: return False
        return True








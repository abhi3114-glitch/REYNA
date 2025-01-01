import time
import sys
from reyna_vals import ObjNative
import reyna_vals as object

def unwrap_val(x):
    if hasattr(x, 'value'): return x.value
    return x

def clock_native(*args):
    return time.time()

def input_native(*args):
    prompt = ""
    if len(args) > 0:
        prompt = str(unwrap_val(args[0]))
    return object.ObjString(input(prompt))

def read_file_native(*args):
    if len(args) < 1: return object.ObjString("Error: path required")
    path = str(unwrap_val(args[0]))
    try:
        with open(path, 'r') as f:
            return object.ObjString(f.read())
    except Exception as e:
        return object.ObjString(f"Error: {e}")

def write_file_native(*args):
    if len(args) < 2: return False
    path = str(unwrap_val(args[0]))
    content = str(unwrap_val(args[1]))
    try:
        with open(path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        return False

def exec_native(*args):
    if len(args) < 1: return False
    code = str(unwrap_val(args[0]))
    try:
        exec(code, globals()) # Use globals mainly for imports if needed
        return True
    except Exception as e:
        print(f"Python Error: {e}")
        return False

def register_stdlib(vm):
    vm.globals['clock'] = ObjNative(clock_native, 'clock')
    vm.globals['input'] = ObjNative(input_native, 'input')
    vm.globals['read_file'] = ObjNative(read_file_native, 'read_file')
    vm.globals['write_file'] = ObjNative(write_file_native, 'write_file')
    vm.globals['python'] = ObjNative(exec_native, 'python')
    
    # Type conversions
    # Type conversions
    vm.globals['str'] = ObjNative(lambda args: object.ObjString(str(unwrap_val(args[0]))) if len(args) > 0 else object.ObjString(""), 'str')
    
    def int_conv(args):
        if len(args) == 0: return 0
        val = unwrap_val(args[0])
        try: return int(float(str(val)))
        except: return 0
        
    vm.globals['int'] = ObjNative(int_conv, 'int')
    
    def float_conv(args):
         if len(args) == 0: return 0.0
         val = unwrap_val(args[0])
         try: return float(str(val))
         except: return 0.0
         
    vm.globals['float'] = ObjNative(float_conv, 'float')





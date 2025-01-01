import reyna_vals as object

class GC:
    def __init__(self, vm):
        self.vm = vm
        self.heap = [] # List of Obj
        self.gray_stack = []
        self.bytes_allocated = 0
        self.next_gc = 1024 * 1024 # 1MB threshold start

    def allocate(self, obj):
        # In a real C implementation, size matters. Here mostly count.
        self.heap.append(obj)
        # Check GC trigger
        if len(self.heap) > 1000: # Simple threshold for Python prototype
             # self.collect()
             pass
        return obj

    def collect(self):
        print("-- gc begin")
        before = len(self.heap)
        
        self.mark_roots()
        self.trace_references()
        self.sweep()
        
        after = len(self.heap)
        print(f"-- gc end. collected {before - after} objects, {after} remain.")

    def mark_roots(self):
        # Stack
        for value in self.vm.stack:
            self.mark_value(value)
        
        # Globals
        for name, value in self.vm.globals.items():
            self.mark_value(value)
        
        # Locals (if any tracked outside stack)
        pass

    def mark_value(self, value):
        if isinstance(value, object.Obj):
            self.mark_object(value)
    
    def mark_object(self, obj):
        if obj.marked: return
        obj.marked = True
        self.gray_stack.append(obj)

    def trace_references(self):
        while len(self.gray_stack) > 0:
            obj = self.gray_stack.pop()
            self.blacken_object(obj)

    def blacken_object(self, obj):
        if isinstance(obj, object.ObjInstance):
            for field in obj.fields.values():
                self.mark_value(field)
        elif isinstance(obj, object.ObjFunction):
             # Mark upvalues or constants? 
             pass
        # Strings have no outgoing refs

    def sweep(self):
        # Remove unmarked objects
        # In Python list, efficient removal is tricky. Rebuild list?
        survivors = []
        for obj in self.heap:
            if obj.marked:
                obj.marked = False # Unmark for next cycle
                survivors.append(obj)
        self.heap = survivors



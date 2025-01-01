class NativeFunction:
    def __init__(self, func, name="<native>"):
        self.func = func
        self.name = name

    def __call__(self, *args):
        return self.func(*args)
    
    def __repr__(self):
        return f"<native fn {self.name}>"

    def arity(self):
        # Allow variadic simply by failing at runtime if mismatch, 
        # or checking code object in python 
        return self.func.__code__.co_argcount

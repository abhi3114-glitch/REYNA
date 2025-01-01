class ClassDecl(Stmt):
    def __init__(self, name, superclass, methods):
        self.name = name
        self.superclass = superclass
        self.methods = methods
    def accept(self, visitor): return visitor.visit_class_decl(self)

class This(Expr):
    def __init__(self, keyword):
        self.keyword = keyword
    def accept(self, visitor): return visitor.visit_this_expr(self)
    
class Super(Expr):
    def __init__(self, keyword, method):
        self.keyword = keyword
        self.method = method
    def accept(self, visitor): return visitor.visit_super_expr(self)




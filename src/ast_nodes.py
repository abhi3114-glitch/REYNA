from abc import ABC, abstractmethod

class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor): pass

class Expr(ABC):
    @abstractmethod
    def accept(self, visitor): pass

# --- Declarations ---

class FnDecl(Stmt):
    def __init__(self, name, params, return_type, body, is_async=False):
        self.name = name
        self.params = params # List of (name_token, type_token)
        self.return_type = return_type
        self.body = body # BlockStmts
        self.is_async = is_async  # True for async fn
    def accept(self, visitor): return visitor.visit_fn_decl(self)

class StructDecl(Stmt):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields # List of (name_token, type_token)
    def accept(self, visitor): return visitor.visit_struct_decl(self)

class LetStmt(Stmt): # Replaces Var
    def __init__(self, name, type_token, initializer):
        self.name = name
        self.type_token = type_token
        self.initializer = initializer
    def accept(self, visitor): return visitor.visit_let_stmt(self)

class ClassDecl(Stmt):
    def __init__(self, name, superclass, methods):
        self.name = name
        self.superclass = superclass
        self.methods = methods
    def accept(self, visitor): return visitor.visit_class_decl(self)

class ImportStmt(Stmt):
    def __init__(self, path, names=None):
        self.path = path  # String path to module
        self.names = names  # List of names to import, None = import all
    def accept(self, visitor): return visitor.visit_import_stmt(self)

# --- Statements ---

class Block(Stmt):
    def __init__(self, statements):
        self.statements = statements
    def accept(self, visitor): return visitor.visit_block_stmt(self)

class IfStmt(Stmt):
    def __init__(self, condition, then_branch, else_branch):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
    def accept(self, visitor): return visitor.visit_if_stmt(self)

class WhileStmt(Stmt):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
    def accept(self, visitor): return visitor.visit_while_stmt(self)

class ReturnStmt(Stmt):
    def __init__(self, keyword, value):
        self.keyword = keyword
        self.value = value
    def accept(self, visitor): return visitor.visit_return_stmt(self)

class ExprStmt(Stmt):
    def __init__(self, expression):
        self.expression = expression
    def accept(self, visitor): return visitor.visit_expression_stmt(self)

class Print(Stmt): 
    def __init__(self, expression):
        self.expression = expression
    def accept(self, visitor): return visitor.visit_print_stmt(self)

class TryStmt(Stmt):
    def __init__(self, try_block, catch_var, catch_block, finally_block=None):
        self.try_block = try_block
        self.catch_var = catch_var  # Variable to bind exception
        self.catch_block = catch_block
        self.finally_block = finally_block
    def accept(self, visitor): return visitor.visit_try_stmt(self)

class ThrowStmt(Stmt):
    def __init__(self, keyword, value):
        self.keyword = keyword
        self.value = value  # Expression to throw
    def accept(self, visitor): return visitor.visit_throw_stmt(self)

# --- Expressions ---

class Binary(Expr):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
    def accept(self, visitor): return visitor.visit_binary_expr(self)

class Unary(Expr):
    def __init__(self, operator, right):
        self.operator = operator
        self.right = right
    def accept(self, visitor): return visitor.visit_unary_expr(self)

class Literal(Expr):
    def __init__(self, value):
        self.value = value
    def accept(self, visitor): return visitor.visit_literal_expr(self)

class Variable(Expr):
    def __init__(self, name):
        self.name = name
    def accept(self, visitor): return visitor.visit_variable_expr(self)

class Assign(Expr):
    def __init__(self, name, value):
        self.name = name
        self.value = value
    def accept(self, visitor): return visitor.visit_assign_expr(self)

class Grouping(Expr):
    def __init__(self, expression):
        self.expression = expression
    def accept(self, visitor): return visitor.visit_grouping_expr(self)

class Call(Expr):
    def __init__(self, callee, paren, arguments):
        self.callee = callee
        self.paren = paren
        self.arguments = arguments
    def accept(self, visitor): return visitor.visit_call_expr(self)

class Get(Expr):
    def __init__(self, obj, name):
        self.obj = obj
        self.name = name
    def accept(self, visitor): return visitor.visit_get_expr(self)

class Set(Expr):
    def __init__(self, obj, name, value):
        self.obj = obj
        self.name = name
        self.value = value
    def accept(self, visitor): return visitor.visit_set_expr(self)

class This(Expr):
    def __init__(self, keyword):
        self.keyword = keyword
    def accept(self, visitor): return visitor.visit_this_expr(self)

class Super(Expr):
    def __init__(self, keyword, method):
        self.keyword = keyword
        self.method = method
    def accept(self, visitor): return visitor.visit_super_expr(self)

class ArrayLiteral(Expr):
    def __init__(self, elements):
        self.elements = elements
    def accept(self, visitor): return visitor.visit_array_literal(self)

class IndexGet(Expr):
    def __init__(self, obj, index):
        self.obj = obj
        self.index = index
    def accept(self, visitor): return visitor.visit_index_get(self)

# Alias for parser compatibility
class Index(Expr):
    def __init__(self, target, index):
        self.target = target
        self.index = index
    def accept(self, visitor): return visitor.visit_index_get(self)

class IndexSet(Expr):
    def __init__(self, obj, index, value):
        self.obj = obj
        self.index = index
        self.value = value
    def accept(self, visitor): return visitor.visit_index_set(self)

class Logical(Expr):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
    def accept(self, visitor): return visitor.visit_logical_expr(self)

# For Statement (syntactic sugar for while)
class ForStmt(Stmt):
    def __init__(self, initializer, condition, increment, body):
        self.initializer = initializer
        self.condition = condition
        self.increment = increment
        self.body = body
    def accept(self, visitor): return visitor.visit_for_stmt(self)

# Pattern matching
class MatchCase:
    """A single case in a match expression."""
    def __init__(self, pattern, guard, body):
        self.pattern = pattern  # Expression to match against
        self.guard = guard      # Optional guard condition (if clause)
        self.body = body        # Expression or block to execute

class MatchExpr(Expr):
    def __init__(self, subject, cases):
        self.subject = subject  # The value being matched
        self.cases = cases      # List of MatchCase
    def accept(self, visitor): return visitor.visit_match_expr(self)

# Async/Await
class AwaitExpr(Expr):
    def __init__(self, keyword, value):
        self.keyword = keyword  # The await token
        self.value = value      # The promise/future to await
    def accept(self, visitor): return visitor.visit_await_expr(self)







import ast_nodes
from token_type import TokenType

class TypeCheckError(Exception):
    pass

class TypeChecker:
    def __init__(self):
        # symbol_table: [ {name: type_str} ] (stack of scopes)
        self.scopes = [{}] 
        # func_signatures: name -> (params_types, return_type)
        self.functions = {}
        # struct_defs: name -> {field: type}
        self.structs = {}
        self.classes = set()
        self.current_return_type = None
        self.current_class = None

    def check(self, statements):
        try:
            for stmt in statements:
                self.visit(stmt)
            return True
        except TypeCheckError as e:
            print(f"Type Error: {e}")
            return False
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False

    def visit(self, node):
        return node.accept(self)

    # --- Scopes ---
    def begin_scope(self):
        self.scopes.append({})

    def end_scope(self):
        self.scopes.pop()

    def declare(self, name, type_str):
        scope = self.scopes[-1]
        if name in scope:
            raise TypeCheckError(f"Variable '{name}' already declared in this scope.")
        scope[name] = type_str

    def resolve(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    # --- Visitor Methods ---

    def visit_fn_decl(self, stmt):
        name = stmt.name.lexeme
        param_types = []
        for p_name, p_type in stmt.params:
             param_types.append(p_type.lexeme) # Using string representation of type for now
        
        ret_type = stmt.return_type.lexeme if stmt.return_type else "void"
        
        self.functions[name] = (param_types, ret_type)
        
        self.begin_scope()
        self.current_return_type = ret_type
        for (p_name, p_type) in stmt.params:
            self.declare(p_name.lexeme, p_type.lexeme)
        
        self.visit(stmt.body) # Block
        self.end_scope()
        self.current_return_type = None

    def visit_struct_decl(self, stmt):
        name = stmt.name.lexeme
        fields = {}
        for f_name, f_type in stmt.fields:
            fields[f_name.lexeme] = f_type.lexeme
        self.structs[name] = fields

    def visit_class_decl(self, stmt):
        name = stmt.name.lexeme
        self.classes.add(name)
        
        previous_class = self.current_class
        self.current_class = name
        
        for method in stmt.methods:
             self.begin_scope()
             self.declare("this", name)
             for p_name, p_type in method.params:
                  self.declare(p_name.lexeme, p_type.lexeme)
             self.visit(method.body)
             self.end_scope()
             
        self.current_class = previous_class
        
    def visit_this_expr(self, expr):
        if not self.current_class:
            raise TypeCheckError("'this' used outside of class.")
        return self.current_class

    def visit_let_stmt(self, stmt):
        name = stmt.name.lexeme
        declared_type = stmt.type_token.lexeme if stmt.type_token else None
        
        if stmt.initializer:
            init_type = self.visit(stmt.initializer)
            if declared_type and init_type != declared_type:
                 # Auto-casting or error? Strict for now.
                 if declared_type == "float64" and init_type == "int64": return # Allow int->float
                 raise TypeCheckError(f"Variable '{name}' expects {declared_type}, got {init_type}")
            if not declared_type:
                declared_type = init_type # Inference
        
        self.declare(name, declared_type)

    def visit_block_stmt(self, stmt):
        self.begin_scope()
        for s in stmt.statements:
            self.visit(s)
        self.end_scope()

    def visit_if_stmt(self, stmt):
        cond_type = self.visit(stmt.condition)
        if cond_type != "bool":
            raise TypeCheckError(f"If condition must be bool, got {cond_type}")
        self.visit(stmt.then_branch)
        if stmt.else_branch:
            self.visit(stmt.else_branch)

    def visit_while_stmt(self, stmt):
        cond_type = self.visit(stmt.condition)
        if cond_type != "bool":
             raise TypeCheckError(f"While condition must be bool, got {cond_type}")
        self.visit(stmt.body)

    def visit_return_stmt(self, stmt):
        val_type = "void"
        if stmt.value:
            val_type = self.visit(stmt.value)
        
        if self.current_return_type and val_type != self.current_return_type:
             raise TypeCheckError(f"Return expects {self.current_return_type}, got {val_type}")

    def visit_expression_stmt(self, stmt):
        self.visit(stmt.expression)

    def visit_print_stmt(self, stmt): 
        # Print accepts anything?
        self.visit(stmt.expression)

    def visit_try_stmt(self, stmt):
        # Type check try block
        self.visit(stmt.try_block)
        
        # Catch block: declare the exception variable
        self.begin_scope()
        self.declare(stmt.catch_var.lexeme, "any")  # Exception can be any type
        self.visit(stmt.catch_block)
        self.end_scope()
        
        # Finally block (if present)
        if stmt.finally_block:
            self.visit(stmt.finally_block)

    def visit_throw_stmt(self, stmt):
        # Can throw anything
        self.visit(stmt.value)

    def visit_import_stmt(self, stmt):
        # Load and type-check the imported module
        import os
        
        # Use base path (examples directory or current)
        base_path = "."
        module_path = os.path.join(base_path, stmt.path)
        
        try:
            with open(module_path, 'r') as f:
                source = f.read()
        except FileNotFoundError:
            # Import error - will be caught at compile time
            return
        
        from lexer import Lexer
        from parser import Parser
        
        lexer = Lexer(source)
        tokens = lexer.scan_tokens()
        parser = Parser(tokens)
        statements = parser.parse()
        
        if statements:
            # Type check the module statements to register its definitions
            for mod_stmt in statements:
                self.visit(mod_stmt)

    def visit_match_expr(self, expr):
        # Type check subject and all cases
        self.visit(expr.subject)
        for case in expr.cases:
            self.visit(case.pattern)
            if case.guard:
                self.visit(case.guard)
            if hasattr(case.body, 'accept'):
                self.visit(case.body)
        return "any"  # Match can return any type

    def visit_array_literal(self, expr):
        for el in expr.elements:
            self.visit(el)
        return "array"

    def visit_await_expr(self, expr):
        # Await resolves to the inner value type
        return self.visit(expr.value)

    # Expressions return their type
    def visit_binary_expr(self, expr):
        left_type = self.visit(expr.left)
        right_type = self.visit(expr.right)
        op = expr.operator.type
        
        if left_type == "any" or right_type == "any":
             if op in [TokenType.GREATER, TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL, TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL]:
                 return "bool"
             return "any"
        
        # Numeric
        if left_type in ["int64", "float64"] and right_type in ["int64", "float64"]:
            if op in [TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH]:
                if left_type == "float64" or right_type == "float64": return "float64"
                return "int64"
            if op in [TokenType.GREATER, TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL, TokenType.EQUAL_EQUAL]:
                return "bool"
        
        # String concat
        if (left_type == "string" or right_type == "string") and op == TokenType.PLUS:
            return "string"

        raise TypeCheckError(f"Binary operator {expr.operator.lexeme} not supported for {left_type} and {right_type}")

    def visit_unary_expr(self, expr):
        right_type = self.visit(expr.right)
        op = expr.operator.type
        if op == TokenType.BANG:
            if right_type != "bool": raise TypeCheckError("! expects bool")
            return "bool"
        if op == TokenType.MINUS:
            if right_type not in ["int64", "float64"]: raise TypeCheckError("- expects number")
            return right_type
        return right_type

    def visit_literal_expr(self, expr):
        if isinstance(expr.value, bool): return "bool"
        if isinstance(expr.value, int): return "int64"
        if isinstance(expr.value, float): return "float64"
        if isinstance(expr.value, str): return "string"
        return "nil"

    def visit_variable_expr(self, expr):
        t = self.resolve(expr.name.lexeme)
        if t: return t
        
        # Check if it is a function
        if expr.name.lexeme in self.functions:
            return "function" # Special type for now
        
        if expr.name.lexeme in self.structs:
            return expr.name.lexeme
            
        # Check globals or stdlib?
        if expr.name.lexeme in ["clock", "input", "read_file", "write_file", "python"]:
            return "any" 
            
        raise TypeCheckError(f"Undefined variable '{expr.name.lexeme}'")

    def visit_assign_expr(self, expr):
        var_type = self.resolve(expr.name.lexeme)
        val_type = self.visit(expr.value)
        if var_type and val_type != var_type:
             raise TypeCheckError(f"Cannot assign {val_type} to variable of type {var_type}")
        return val_type

    def visit_call_expr(self, expr):
        if isinstance(expr.callee, ast_nodes.Variable):
            name = expr.callee.name.lexeme
            # Check functions
            if name in self.functions:
                params, ret = self.functions[name]
                if len(expr.arguments) != len(params):
                    raise TypeCheckError(f"Function {name} expects {len(params)} args, got {len(expr.arguments)}")
                for i, arg in enumerate(expr.arguments):
                    t = self.visit(arg)
                    if t != params[i] and not (params[i] == "float64" and t == "int64"):
                         raise TypeCheckError(f"Argument {i} expected {params[i]}, got {t}")
                return ret
            # Check Struct/Class Instantiation
            if name in self.structs or name in self.classes:
                if name in self.classes:
                     # Check if init exists in functions (hack because methods are visited there too?)
                     # No, methods are local scopes... wait. 
                     # I need to track class methods in TypeChecker.
                     # But visit_class_decl only adds name to self.classes.
                     # It does visit method bodies.
                     # I need to store method signatures for classes too.
                     pass 
                
                # For now permissive check for classes, strict for structs
                if name in self.structs and len(expr.arguments) > 0:
                     raise TypeCheckError(f"Constructor {name} takes no arguments.")
                
                return name
            
            # Stdlib
            if name in ["print", "clock", "str", "int", "float", "input", "write_file", "read_file", "python"]:
                for arg in expr.arguments: self.visit(arg)
                if name in ["str", "input", "read_file"]: return "string"
                if name in ["int"]: return "int64"
                if name in ["float", "clock"]: return "float64"
                return "void"

        return "any"

    def visit_get_expr(self, expr):
        obj_type = self.visit(expr.obj)
        
        if obj_type in self.classes:
             return "any" # Dynamic access on classes
             
        if obj_type not in self.structs:
             raise TypeCheckError(f"Only structs/classes have properties. Got {obj_type}")
        
        fields = self.structs[obj_type]
        name = expr.name.lexeme
        if name not in fields:
             raise TypeCheckError(f"Struct {obj_type} has no property '{name}'")
        return fields[name]

    def visit_super_expr(self, expr):
        if not self.current_class:
             raise TypeCheckError("'super' used outside of class.")
        # TODO: Check if current class actually has a superclass? 
        return "any"

    def visit_set_expr(self, expr):
        obj_type = self.visit(expr.obj)
        val_type = self.visit(expr.value)
        
        if obj_type in self.classes:
             return val_type # Dynamic set on classes
             
        if obj_type not in self.structs:
             raise TypeCheckError(f"Only structs/classes have properties.")
        
        fields = self.structs[obj_type]
        name = expr.name.lexeme
        if name not in fields:
             raise TypeCheckError(f"Struct {obj_type} has no property '{name}'")
        
        expected = fields[name]
        if val_type != expected:
             raise TypeCheckError(f"Field {name} expects {expected}, got {val_type}")
        return val_type

    def visit_grouping_expr(self, expr):
        return self.visit(expr.expression)
    
    def visit_array_expr(self, expr):
        for el in expr.elements: self.visit(el)
        return "array"

    def visit_index_get(self, expr):
        # Handle Index node that uses .target attribute
        target = getattr(expr, 'target', None) or getattr(expr, 'obj', None)
        if target:
            self.visit(target)
        self.visit(expr.index)
        return "any" 

    def visit_index_set_expr(self, expr):
        self.visit(expr.target)
        self.visit(expr.index)
        return self.visit(expr.value)
    
    def visit_logical_expr(self, expr):
        l = self.visit(expr.left)
        r = self.visit(expr.right)
        if l != "bool" or r != "bool": raise TypeCheckError("Logical ops expect bool")
        return "bool"





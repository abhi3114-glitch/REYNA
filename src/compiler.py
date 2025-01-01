from reyna_chunk import OpCode, Chunk
from token_type import TokenType, Token
import ast_nodes
import reyna_vals as object

class Compiler:
    # Module cache to prevent re-importing
    _module_cache = {}
    _base_path = "."  # Base path for resolving imports
    
    def __init__(self, parent=None, function_type="script"):
        self.chunk = None
        self.locals = []
        self.scope_depth = 0
        self.parent = parent
        self.function_type = function_type
        self.upvalues = [] 
        
        # Reserve slot 0 (Receiver)
        # For script/function: empty/function name
        # For method/initializer: 'this'
        receiver_name = "this" if function_type in ["method", "initializer"] else ""
        self.locals.append({'name': receiver_name, 'depth': 0, 'is_captured': False})

    def compile(self, statements):
        self.chunk = Chunk()
        for stmt in statements:
            self.compile_statement(stmt)
            # REPL mode might simplify this, but generally top level is a script fn
        self.emit_byte(OpCode.OP_RETURN)
        return self.chunk

    def compile_statement(self, stmt):
        if isinstance(stmt, ast_nodes.Print):
            self.compile_expression(stmt.expression)
            self.emit_byte(OpCode.OP_PRINT)
        elif isinstance(stmt, ast_nodes.ExprStmt):
            self.compile_expression(stmt.expression)
            self.emit_byte(OpCode.OP_POP)
        elif isinstance(stmt, ast_nodes.ImportStmt):
            # Module import - compile the imported module inline
            self.handle_import(stmt)
        elif isinstance(stmt, ast_nodes.LetStmt):
            # v2 LetStmt: name, type_token, initializer
            if self.scope_depth > 0:
                self.declare_local(stmt.name)
                if stmt.initializer:
                    self.compile_expression(stmt.initializer)
                else:
                    self.emit_byte(OpCode.OP_NIL)
                self.add_local(stmt.name) 
            else:
                if stmt.initializer:
                    self.compile_expression(stmt.initializer)
                else:
                    self.emit_byte(OpCode.OP_NIL)
                name_idx = self.make_constant(stmt.name.lexeme)
                self.emit_bytes(OpCode.OP_DEFINE_GLOBAL, name_idx)
        elif isinstance(stmt, ast_nodes.Block):
            self.begin_scope()
            for s in stmt.statements:
                self.compile_statement(s)
            self.end_scope()
        elif isinstance(stmt, ast_nodes.FnDecl):
            self.compile_function(stmt, "function")
            # Define name
            if self.scope_depth > 0:
                self.declare_local(stmt.name)
                self.add_local(stmt.name)
            else:
                name_idx = self.make_constant(stmt.name.lexeme)
                self.emit_bytes(OpCode.OP_DEFINE_GLOBAL, name_idx)
        elif isinstance(stmt, ast_nodes.IfStmt):
            self.compile_expression(stmt.condition)
            
            self.emit_byte(OpCode.OP_JUMP_IF_FALSE)
            self.emit_byte(0xff) 
            self.emit_byte(0xff)
            jump_if_offset = len(self.chunk.code) - 2

            self.emit_byte(OpCode.OP_POP) # Pop condition

            self.compile_statement(stmt.then_branch)

            self.emit_byte(OpCode.OP_JUMP)
            self.emit_byte(0xff)
            self.emit_byte(0xff)
            else_jump_offset = len(self.chunk.code) - 2

            self.patch_jump(jump_if_offset)
            self.emit_byte(OpCode.OP_POP) 

            if stmt.else_branch:
                self.compile_statement(stmt.else_branch)
            
        elif isinstance(stmt, ast_nodes.StructDecl):
            name_idx = self.make_constant(stmt.name.lexeme)
            self.emit_bytes(OpCode.OP_STRUCT, name_idx)
            self.emit_bytes(OpCode.OP_DEFINE_GLOBAL, name_idx)

        elif isinstance(stmt, ast_nodes.WhileStmt):
            loop_start = len(self.chunk.code)
            self.compile_expression(stmt.condition)
            
            self.emit_byte(OpCode.OP_JUMP_IF_FALSE)
            self.emit_byte(0xff)
            self.emit_byte(0xff)
            exit_jump = len(self.chunk.code) - 2
            
            self.emit_byte(OpCode.OP_POP) 
            self.compile_statement(stmt.body)
            
            self.emit_byte(OpCode.OP_LOOP)
            
            offset = len(self.chunk.code) - loop_start + 2
            self.emit_byte((offset >> 8) & 0xff)
            self.emit_byte(offset & 0xff)
            
            self.patch_jump(exit_jump)
            self.emit_byte(OpCode.OP_POP)

        elif isinstance(stmt, ast_nodes.TryStmt):
            # Emit OP_TRY_BEGIN with offset to catch block
            self.emit_byte(OpCode.OP_TRY_BEGIN)
            self.emit_byte(0xff)
            self.emit_byte(0xff)
            try_jump = len(self.chunk.code) - 2
            
            # Compile try block
            self.compile_statement(stmt.try_block)
            
            # If try succeeds, skip catch block
            self.emit_byte(OpCode.OP_TRY_END)
            self.emit_byte(OpCode.OP_JUMP)
            self.emit_byte(0xff)
            self.emit_byte(0xff)
            skip_catch = len(self.chunk.code) - 2
            
            # Patch try_jump to here (start of catch)
            self.patch_jump(try_jump)
            
            # Catch block: exception is on stack
            self.begin_scope()
            self.add_local(stmt.catch_var)  # Bind exception to variable
            self.compile_statement(stmt.catch_block)
            self.end_scope()
            
            # Patch skip_catch to here
            self.patch_jump(skip_catch)
            
            # Finally block (if present)
            if stmt.finally_block:
                self.compile_statement(stmt.finally_block)
        
        elif isinstance(stmt, ast_nodes.ThrowStmt):
            self.compile_expression(stmt.value)
            self.emit_byte(OpCode.OP_THROW)

        elif isinstance(stmt, ast_nodes.ClassDecl):
            name_idx = self.make_constant(stmt.name.lexeme)
            self.emit_bytes(OpCode.OP_CLASS, name_idx)
            self.emit_bytes(OpCode.OP_DEFINE_GLOBAL, name_idx)
            
            # Push subclass for method binding and inheritance
            self.emit_bytes(OpCode.OP_GET_GLOBAL, name_idx)
            
            if stmt.superclass:
                if stmt.name.lexeme == stmt.superclass.name.lexeme:
                    print("Error: A class cannot inherit from itself.")
                
                # Create scope for 'super' local
                self.begin_scope()
                
                # Track subclass on stack with dummy local to align indices
                self.add_local(Token(TokenType.IDENTIFIER, "", None, 0))
                
                # Push superclass
                self.compile_expression(stmt.superclass)
                
                # Track superclass as 'super' local
                self.add_local(Token(TokenType.SUPER, "super", None, 0))
                
                self.emit_byte(OpCode.OP_INHERIT)
            
            for method in stmt.methods:
                self.emit_bytes(OpCode.OP_GET_GLOBAL, name_idx)
                method_name_idx = self.make_constant(method.name.lexeme)
                type = "initializer" if method.name.lexeme == "init" else "method"
                self.compile_function(method, type)
                self.emit_bytes(OpCode.OP_METHOD, method_name_idx)
                self.emit_byte(OpCode.OP_POP)
            
            if stmt.superclass:
                self.end_scope() # Pops 'super' and dummy local
            else:
                self.emit_byte(OpCode.OP_POP) # Pop subclass

        elif isinstance(stmt, ast_nodes.ReturnStmt):
            if self.function_type == "initializer":
                 if stmt.value:
                      print("Error: Can't return a value from an initializer.")
                 self.emit_bytes(OpCode.OP_GET_LOCAL, 0)
                 self.emit_byte(OpCode.OP_RETURN)
            else:
                if stmt.value:
                    self.compile_expression(stmt.value)
                else:
                    self.emit_byte(OpCode.OP_NIL)
                self.emit_byte(OpCode.OP_RETURN)

    def compile_function(self, stmt, type):
        func_compiler = Compiler(parent=self, function_type=type)
        func_compiler.chunk = Chunk()
        func_compiler.begin_scope()
        
        # Params
        for p_name, p_type in stmt.params:
            func_compiler.declare_local(p_name)
            func_compiler.add_local(p_name)
        
        func_compiler.compile_statement(stmt.body)
        
        if func_compiler.function_type == "initializer":
             func_compiler.emit_bytes(OpCode.OP_GET_LOCAL, 0)
             func_compiler.emit_byte(OpCode.OP_RETURN)
        else:
             func_compiler.emit_byte(OpCode.OP_NIL) 
             func_compiler.emit_byte(OpCode.OP_RETURN)
        
        function_obj = object.ObjFunction(stmt.name.lexeme, len(stmt.params), func_compiler.chunk, len(func_compiler.upvalues))
        const_idx = self.make_constant(function_obj)
        self.emit_bytes(OpCode.OP_CLOSURE, const_idx)
        
        for upvalue in func_compiler.upvalues:
            is_local = 1 if upvalue['is_local'] else 0
            self.emit_byte(is_local)
            self.emit_byte(upvalue['index'])

    def compile_expression(self, expr):
        if isinstance(expr, ast_nodes.Binary):
            self.compile_expression(expr.left)
            self.compile_expression(expr.right)
            dtype = expr.operator.type
            if dtype == TokenType.PLUS: self.emit_byte(OpCode.OP_ADD)
            elif dtype == TokenType.MINUS: self.emit_byte(OpCode.OP_SUBTRACT)
            elif dtype == TokenType.STAR: self.emit_byte(OpCode.OP_MULTIPLY)
            elif dtype == TokenType.SLASH: self.emit_byte(OpCode.OP_DIVIDE)
            elif dtype == TokenType.EQUAL_EQUAL: self.emit_byte(OpCode.OP_EQUAL)
            elif dtype == TokenType.GREATER: self.emit_byte(OpCode.OP_GREATER)
            elif dtype == TokenType.LESS: self.emit_byte(OpCode.OP_LESS) 
            # ... others
        elif isinstance(expr, ast_nodes.Literal):
            if expr.value is None: self.emit_byte(OpCode.OP_NIL)
            elif expr.value is True: self.emit_byte(OpCode.OP_TRUE)
            elif expr.value is False: self.emit_byte(OpCode.OP_FALSE)
            else:
                val = expr.value
                if isinstance(val, str):
                    val = object.ObjString(val)
                const = self.make_constant(val)
                self.emit_bytes(OpCode.OP_CONSTANT, const)
        elif isinstance(expr, ast_nodes.Super):
             # Stack order for OP_GET_SUPER: [receiver (this)], [superclass (super)]
             # VM pops super first, then this/receiver.
             # 1. Push this
             self.load_variable(Token(TokenType.THIS, "this", None, 0))
             # 2. Push super (the ObjClass)
             self.load_variable(Token(TokenType.SUPER, "super", None, 0))
             # 3. Emit OP_GET_SUPER with method name index
             method_name_idx = self.make_constant(expr.method.lexeme)
             self.emit_bytes(OpCode.OP_GET_SUPER, method_name_idx)
             
        elif isinstance(expr, ast_nodes.Grouping):
            self.compile_expression(expr.expression)
        elif isinstance(expr, ast_nodes.This):
            idx = self.resolve_local(expr.keyword)
            if idx != -1:
                self.emit_bytes(OpCode.OP_GET_LOCAL, idx)
            else:
                idx = self.resolve_upvalue(expr.keyword)
                if idx != -1:
                    self.emit_bytes(OpCode.OP_GET_UPVALUE, idx)
                else:
                    print("Error: 'this' not found (are you in a class method?)")
        elif isinstance(expr, ast_nodes.Variable):
            # Check local
            idx = self.resolve_local(expr.name)
            if idx != -1:
                self.emit_bytes(OpCode.OP_GET_LOCAL, idx)
            else:
                idx = self.resolve_upvalue(expr.name)
                if idx != -1:
                    self.emit_bytes(OpCode.OP_GET_UPVALUE, idx)
                else:
                    idx = self.make_constant(expr.name.lexeme)
                    self.emit_bytes(OpCode.OP_GET_GLOBAL, idx)
        elif isinstance(expr, ast_nodes.Assign):
             # Right side
             self.compile_expression(expr.value)
             
             idx = self.resolve_local(expr.name)
             if idx != -1:
                 self.emit_bytes(OpCode.OP_SET_LOCAL, idx)
             else:
                 idx = self.resolve_upvalue(expr.name)
                 if idx != -1:
                     self.emit_bytes(OpCode.OP_SET_UPVALUE, idx)
                 else:
                     idx = self.make_constant(expr.name.lexeme)
                     self.emit_bytes(OpCode.OP_SET_GLOBAL, idx)
        elif isinstance(expr, ast_nodes.Call):
            self.compile_expression(expr.callee)
            arg_count = 0
            for arg in expr.arguments:
                self.compile_expression(arg)
                arg_count += 1
            self.emit_bytes(OpCode.OP_CALL, arg_count)
        elif isinstance(expr, ast_nodes.Get):
            self.compile_expression(expr.obj)
            name_idx = self.make_constant(expr.name.lexeme)
            self.emit_bytes(OpCode.OP_GET_FIELD, name_idx)
        elif isinstance(expr, ast_nodes.Set):
            self.compile_expression(expr.obj)
            self.compile_expression(expr.value)
            name_idx = self.make_constant(expr.name.lexeme)
            self.emit_bytes(OpCode.OP_SET_FIELD, name_idx)

        elif isinstance(expr, ast_nodes.ArrayLiteral):
            count = 0
            for el in expr.elements:
                self.compile_expression(el)
                count += 1
            if count > 255: print("Tool many array elements"); return
            self.emit_bytes(OpCode.OP_BUILD_ARRAY, count)

        elif isinstance(expr, ast_nodes.Index):
            self.compile_expression(expr.target)
            self.compile_expression(expr.index)
            self.emit_byte(OpCode.OP_GET_INDEX)

        elif isinstance(expr, ast_nodes.IndexSet):
            self.compile_expression(expr.target)
            self.compile_expression(expr.index)
            self.compile_expression(expr.value)
            self.emit_byte(OpCode.OP_SET_INDEX)

        elif isinstance(expr, ast_nodes.ArrayLiteral):
            count = 0
            for el in expr.elements:
                self.compile_expression(el)
                count += 1
            if count > 255: print("Too many array elements"); return
            self.emit_bytes(OpCode.OP_BUILD_ARRAY, count)

        elif isinstance(expr, ast_nodes.MatchExpr):
            # Compile match as a series of if-else checks
            # First, compile subject and store as temp
            self.compile_expression(expr.subject)
            
            end_jumps = []  # List of jumps to patch at end
            
            for case in expr.cases:
                # Duplicate subject for comparison
                self.emit_byte(OpCode.OP_NIL)  # Placeholder for dup
                # TODO: Add OP_DUP opcode for proper implementation
                # For now, use a simpler approach: recompile subject
                self.compile_expression(expr.subject)
                
                # Compile pattern as value
                self.compile_expression(case.pattern)
                
                # Compare: subject == pattern
                self.emit_byte(OpCode.OP_EQUAL)
                
                # Optional guard
                if case.guard:
                    # If pattern matched, also check guard
                    self.emit_byte(OpCode.OP_JUMP_IF_FALSE)
                    self.emit_byte(0xff)
                    self.emit_byte(0xff)
                    guard_skip = len(self.chunk.code) - 2
                    
                    self.emit_byte(OpCode.OP_POP)  # Pop true from pattern match
                    self.compile_expression(case.guard)
                    
                    # Patch guard skip to here
                    self.patch_jump(guard_skip)
                
                # Jump if false (pattern didn't match)
                self.emit_byte(OpCode.OP_JUMP_IF_FALSE)
                self.emit_byte(0xff)
                self.emit_byte(0xff)
                next_case = len(self.chunk.code) - 2
                
                self.emit_byte(OpCode.OP_POP)  # Pop true
                self.emit_byte(OpCode.OP_POP)  # Pop placeholder
                
                # Compile body
                if isinstance(case.body, ast_nodes.Block):
                    self.compile_statement(case.body)
                    self.emit_byte(OpCode.OP_NIL)  # Block needs to leave a value
                else:
                    self.compile_expression(case.body)
                
                # Jump to end
                self.emit_byte(OpCode.OP_JUMP)
                self.emit_byte(0xff)
                self.emit_byte(0xff)
                end_jumps.append(len(self.chunk.code) - 2)
                
                # Patch next_case to here
                self.patch_jump(next_case)
                self.emit_byte(OpCode.OP_POP)  # Pop false
            
            # Pop placeholder at end
            self.emit_byte(OpCode.OP_POP)
            
            # Default: nil
            self.emit_byte(OpCode.OP_NIL)
            
            # Patch all end jumps to here
            for jump in end_jumps:
                self.patch_jump(jump)

        elif isinstance(expr, ast_nodes.AwaitExpr):
            # For demo: await just evaluates the expression
            # Real implementation would integrate with event loop
            self.compile_expression(expr.value)

    def emit_byte(self, byte):
        self.chunk.write(byte, 1) # TODO: Line numbers

    def emit_bytes(self, b1, b2):
        self.emit_byte(b1)
        self.emit_byte(b2)

    def make_constant(self, value):
        return self.chunk.add_constant(value)

    def begin_scope(self):
        self.scope_depth += 1

    def end_scope(self):
        self.scope_depth -= 1
        # Pop locals
        while len(self.locals) > 0 and self.locals[-1]['depth'] > self.scope_depth:
            if self.locals[-1]['is_captured']:
                self.emit_byte(OpCode.OP_CLOSE_UPVALUE)
            else:
                self.emit_byte(OpCode.OP_POP)
            self.locals.pop()

    def declare_local(self, name):
        # TODO: Check redefinition
        pass # Just parsing phase tracked in locals for resolution

    def add_local(self, name):
        self.locals.append({'name': name.lexeme, 'depth': self.scope_depth, 'is_captured': False})

    def load_variable(self, name_token):
        idx = self.resolve_local(name_token)
        if idx != -1:
            self.emit_bytes(OpCode.OP_GET_LOCAL, idx)
        else:
            idx = self.resolve_upvalue(name_token)
            if idx != -1:
                self.emit_bytes(OpCode.OP_GET_UPVALUE, idx)
            else:
                print(f"Variable {name_token.lexeme} not found.")

    def resolve_local(self, name):
        for i in range(len(self.locals)-1, -1, -1):
            if self.locals[i]['name'] == name.lexeme:
                return i
        return -1
    
    def resolve_upvalue(self, name):
        if self.parent is None: return -1
    
        local = self.parent.resolve_local(name)
        if local != -1:
            self.parent.locals[local]['is_captured'] = True
            return self.add_upvalue(local, True)
            
        upvalue = self.parent.resolve_upvalue(name)
        if upvalue != -1:
            return self.add_upvalue(upvalue, False)
            
        return -1
        
    def add_upvalue(self, index, is_local):
         # check if already exists
         for i, up in enumerate(self.upvalues):
             if up['index'] == index and up['is_local'] == is_local:
                 return i
         self.upvalues.append({'index': index, 'is_local': is_local})
         return len(self.upvalues) - 1

    def patch_jump(self, offset):
        jump =  len(self.chunk.code) - offset - 2
        
        self.chunk.code[offset] = (jump >> 8) & 0xff
        self.chunk.code[offset + 1] = jump & 0xff

    def handle_import(self, stmt):
        """Load and compile an external module file."""
        import os
        
        # Resolve path relative to base path
        module_path = os.path.join(Compiler._base_path, stmt.path)
        
        # Check cache
        if module_path in Compiler._module_cache:
            # Already imported, skip
            return
        
        # Mark as imported to prevent circular imports
        Compiler._module_cache[module_path] = True
        
        try:
            with open(module_path, 'r') as f:
                source = f.read()
        except FileNotFoundError:
            print(f"Error: Could not find module '{stmt.path}'")
            return
        
        # Import lexer and parser
        from lexer import Lexer
        from parser import Parser
        
        # Lex and parse module
        lexer = Lexer(source)
        tokens = lexer.scan_tokens()
        parser = Parser(tokens)
        statements = parser.parse()
        
        if not statements:
            print(f"Error: Failed to parse module '{stmt.path}'")
            return
        
        # Compile module statements into current chunk
        for mod_stmt in statements:
            self.compile_statement(mod_stmt)



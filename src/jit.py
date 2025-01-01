import llvmlite.ir as ir
import llvmlite.binding as llvm
from ast_nodes import *
import ctypes

class CodeGen:
    def __init__(self):
        self.module = ir.Module(name="reyna_jit")
        self.module.triple = llvm.get_process_triple()
        self.builder = None
        self.func = None
        self.named_values = {}
        
        # Declare printf
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")
        
        # Declare format string once
        c_str_val = ir.Constant(ir.ArrayType(ir.IntType(8), 4), bytearray(b"%f\n\0"))
        self.c_str = ir.GlobalVariable(self.module, c_str_val.type, name="fstr")
        self.c_str.linkage = 'internal'
        self.c_str.global_constant = True
        self.c_str.initializer = c_str_val

    def generate(self, statements):
        # Wrap top-level statements in a main function
        func_type = ir.FunctionType(ir.VoidType(), [])
        self.func = ir.Function(self.module, func_type, name="main")
        block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        
        for stmt in statements:
            self.visit(stmt)
            
        if not self.builder.block.is_terminated:
             self.builder.ret_void()
        return self.module

    def visit(self, node):
        return node.accept(self)

    def visit_expression_stmt(self, stmt):
        self.visit(stmt.expression)

    def visit_print_stmt(self, stmt):
        value = self.visit(stmt.expression)
        fmt_arg = self.builder.bitcast(self.c_str, ir.IntType(8).as_pointer())
        self.builder.call(self.printf, [fmt_arg, value])

    def visit_block_stmt(self, stmt):
        for s in stmt.statements:
            self.visit(s)

    def visit_if_stmt(self, stmt):
        # Create blocks
        then_bb = self.func.append_basic_block(name="then")
        else_bb = self.func.append_basic_block(name="else")
        merge_bb = self.func.append_basic_block(name="ifcont")
        
        # Condition
        cond_val = self.visit(stmt.condition)
        # Convert to bool (i1) if needed (assuming int/double 0 is false)
        if cond_val.type == ir.DoubleType():
            cond_val = self.builder.fcmp_ordered('!=', cond_val, ir.Constant(ir.DoubleType(), 0.0), 'ifcond')
        elif cond_val.type == ir.IntType(64):
            cond_val = self.builder.icmp_signed('!=', cond_val, ir.Constant(ir.IntType(64), 0), 'ifcond')
            
        self.builder.cbranch(cond_val, then_bb, else_bb)
        
        # Then
        self.builder.position_at_start(then_bb)
        self.visit(stmt.then_branch)
        if not self.builder.block.is_terminated:
             self.builder.branch(merge_bb)
        
        # Else
        self.builder.position_at_start(else_bb)
        if stmt.else_branch:
            self.visit(stmt.else_branch)
        if not self.builder.block.is_terminated:
             self.builder.branch(merge_bb)
             
        # Merge
        self.builder.position_at_start(merge_bb)

    def visit_while_stmt(self, stmt):
        cond_bb = self.func.append_basic_block(name="loopcond")
        body_bb = self.func.append_basic_block(name="loopbody")
        after_bb = self.func.append_basic_block(name="loopend")
        
        # Jump to condition
        self.builder.branch(cond_bb)
        
        # Condition
        self.builder.position_at_start(cond_bb)
        cond_val = self.visit(stmt.condition)
         # Convert to bool
        if cond_val.type == ir.DoubleType():
            cond_val = self.builder.fcmp_ordered('!=', cond_val, ir.Constant(ir.DoubleType(), 0.0), 'loopcond')
        elif cond_val.type == ir.IntType(64):
            cond_val = self.builder.icmp_signed('!=', cond_val, ir.Constant(ir.IntType(64), 0), 'loopcond')
            
        self.builder.cbranch(cond_val, body_bb, after_bb)
        
        # Body
        self.builder.position_at_start(body_bb)
        self.visit(stmt.body)
        self.builder.branch(cond_bb)
        
        # After
        self.builder.position_at_start(after_bb)

    def visit_let_stmt(self, stmt):
        # Determine type
        typ = ir.DoubleType()
        if stmt.type_token:
            if stmt.type_token.lexeme == "int64": typ = ir.IntType(64)
            elif stmt.type_token.lexeme == "float64": typ = ir.DoubleType()
            elif stmt.type_token.lexeme == "bool": typ = ir.IntType(1)
        
        ptr = self.builder.alloca(typ, name=stmt.name.lexeme)
        self.named_values[stmt.name.lexeme] = ptr
        
        if stmt.initializer:
            init_val = self.visit(stmt.initializer)
            # Basic cast if needed (extremely simple)
            if init_val.type != typ:
                if typ == ir.DoubleType() and init_val.type == ir.IntType(64):
                    init_val = self.builder.sitofp(init_val, typ)
                # TODO: more casts
            self.builder.store(init_val, ptr)

    # ... (binary expr etc as before) ...
    def visit_binary_expr(self, expr):
        lhs = self.visit(expr.left)
        rhs = self.visit(expr.right)
        
        op_str = expr.operator.lexeme
        
        # Float math (default)
        if lhs.type == ir.DoubleType() or rhs.type == ir.DoubleType():
             # Promo to double
             if lhs.type == ir.IntType(64): lhs = self.builder.sitofp(lhs, ir.DoubleType())
             if rhs.type == ir.IntType(64): rhs = self.builder.sitofp(rhs, ir.DoubleType())
             
             if op_str == '+': return self.builder.fadd(lhs, rhs, 'addtmp')
             elif op_str == '-': return self.builder.fsub(lhs, rhs, 'subtmp')
             elif op_str == '*': return self.builder.fmul(lhs, rhs, 'multmp')
             elif op_str == '/': return self.builder.fdiv(lhs, rhs, 'divtmp')
             elif op_str == '<': return self.builder.fcmp_ordered('<', lhs, rhs, 'cmptmp')
        else:
             # Int math
             if op_str == '+': return self.builder.add(lhs, rhs, 'addtmp')
             elif op_str == '-': return self.builder.sub(lhs, rhs, 'subtmp')
             elif op_str == '*': return self.builder.mul(lhs, rhs, 'multmp')
             elif op_str == '/': return self.builder.sdiv(lhs, rhs, 'divtmp') # signed div
             elif op_str == '<': return self.builder.icmp_signed('<', lhs, rhs, 'cmptmp')

        return lhs # Fallback


    def visit_literal_expr(self, expr):
        if isinstance(expr.value, bool):
             return ir.Constant(ir.IntType(1), 1 if expr.value else 0)
        if isinstance(expr.value, int):
             return ir.Constant(ir.IntType(64), expr.value)
        if isinstance(expr.value, float):
             return ir.Constant(ir.DoubleType(), expr.value)
        return ir.Constant(ir.DoubleType(), 0.0)

    def visit_variable_expr(self, expr):
        ptr = self.named_values.get(expr.name.lexeme)
        if ptr:
            return self.builder.load(ptr, expr.name.lexeme)
        return ir.Constant(ir.DoubleType(), 0.0)
        
    def visit_assign_expr(self, expr):
        val = self.visit(expr.value)
        ptr = self.named_values.get(expr.name.lexeme)
        if ptr:
            self.builder.store(val, ptr)
        return val

    def visit_struct_decl(self, stmt):
        pass # Structs ignored in JIT basics for now

    def visit_get_expr(self, expr): pass
    def visit_set_expr(self, expr): pass


class ReynaJIT:
    def __init__(self):
        try:
            llvm.initialize()
            llvm.initialize_native_target()
            llvm.initialize_native_asmprinter()
        except:
             # Fallback for newer versions or broken envs?
             try:
                 llvm.initialize_all_targets()
                 llvm.initialize_all_asmprinters()
             except Exception as e:
                 print(f"JIT Init Failed: {e}")
                 return
        
        # Load standard C library for printf
        try:
            llvm.load_library_permanently("msvcrt.dll")
        except:
            pass 
            
        self.codegen = CodeGen()
        self.target = llvm.Target.from_default_triple()
        self.target_machine = self.target.create_target_machine()

    def compile_and_run(self, statements):
        # Generate IR
        llvm_mod = self.codegen.generate(statements)
        
        # Verify
        print("Generated LLVM IR:")
        print(str(llvm_mod))
        
        try:
            # Convert IR module to LLVM binding module
            mod = llvm.parse_assembly(str(llvm_mod))
            mod.verify()
            
            # Create Engine
            engine = llvm.create_execution_engine()
            engine.add_module(mod)
            engine.finalize_object()
            engine.run_static_constructors()
            
            # Lookup main
            func_ptr = engine.get_function_address("main")
            
            # Cast and Call
            cfunc = ctypes.CFUNCTYPE(None)(func_ptr)
            cfunc()
        except Exception as e:
            print(f"JIT Execution Failed: {str(e)}")





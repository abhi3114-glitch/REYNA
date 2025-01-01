from ast_nodes import *

class AstPrinter:
    def print(self, expr):
        return expr.accept(self)

    def visit_binary_expr(self, expr):
        return self.parenthesize(expr.operator.lexeme, expr.left, expr.right)

    def visit_grouping_expr(self, expr):
        return self.parenthesize("group", expr.expression)

    def visit_literal_expr(self, expr):
        if expr.value is None: return "nil"
        return str(expr.value)

    def visit_unary_expr(self, expr):
        return self.parenthesize(expr.operator.lexeme, expr.right)

    def visit_variable_expr(self, expr):
        return f"var({expr.name.lexeme})"

    def visit_assign_expr(self, expr):
        return self.parenthesize(f"assign {expr.name.lexeme}", expr.value)

    def visit_logical_expr(self, expr):
        return self.parenthesize(expr.operator.lexeme, expr.left, expr.right)
    
    def visit_call_expr(self, expr):
        return self.parenthesize(f"call {self.print(expr.callee)}") # simplified

    def parenthesize(self, name, *exprs):
        builder = []
        builder.append(f"({name}")
        for expr in exprs:
            builder.append(" ")
            try:
                builder.append(expr.accept(self))
            except AttributeError:
                builder.append(str(expr))
        builder.append(")")
        return "".join(builder)




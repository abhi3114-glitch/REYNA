from token_type import TokenType
import ast_nodes

class ParseError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        statements = []
        while not self.is_at_end():
            decl = self.declaration()
            if decl: statements.append(decl)
        return statements

    def declaration(self):
        try:
            if self.match(TokenType.IMPORT):
                return self.import_statement()
            if self.match(TokenType.ASYNC):
                # async fn declaration
                self.consume(TokenType.FN, "Expect 'fn' after 'async'.")
                return self.fn_declaration(is_async=True)
            if self.match(TokenType.FN):
                return self.fn_declaration()
            if self.match(TokenType.CLASS):
                return self.class_declaration()
            if self.match(TokenType.STRUCT):
                return self.struct_declaration()
            if self.match(TokenType.LET):
                return self.let_declaration()
            return self.statement()
        except ParseError:
            self.synchronize()
            return None

    def import_statement(self):
        # import "path/to/module.reyna";
        # or: import { name1, name2 } from "path/to/module.reyna";
        if self.match(TokenType.LEFT_BRACE):
            # Named imports
            names = []
            while True:
                names.append(self.consume(TokenType.IDENTIFIER, "Expect import name."))
                if not self.match(TokenType.COMMA):
                    break
            self.consume(TokenType.RIGHT_BRACE, "Expect '}' after import names.")
            # Expect 'from' keyword - using IDENTIFIER for now since we don't have FROM token
            from_token = self.consume(TokenType.IDENTIFIER, "Expect 'from' keyword.")
            if from_token.lexeme != "from":
                raise self.error(from_token, "Expect 'from' keyword.")
            path = self.consume(TokenType.STRING, "Expect module path string.")
            self.consume(TokenType.SEMICOLON, "Expect ';' after import.")
            return ast_nodes.ImportStmt(path.literal, names)
        else:
            # Simple import
            path = self.consume(TokenType.STRING, "Expect module path string.")
            self.consume(TokenType.SEMICOLON, "Expect ';' after import.")
            return ast_nodes.ImportStmt(path.literal, None)

    def class_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expect class name.")
        superclass = None
        if self.match(TokenType.LESS):
            self.consume(TokenType.IDENTIFIER, "Expect superclass name.")
            superclass = ast_nodes.Variable(self.previous())
        
        self.consume(TokenType.LEFT_BRACE, "Expect '{' before class body.")
        methods = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            self.consume(TokenType.FN, "Expect 'fn' before method.")
            methods.append(self.function_body("method"))
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")
        return ast_nodes.ClassDecl(name, superclass, methods)

    def fn_declaration(self, is_async=False):
        return self.function_body("function", is_async=is_async)

    def function_body(self, kind, is_async=False):
        name = self.consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self.consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        params = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                param_name = self.consume(TokenType.IDENTIFIER, "Expect parameter name.")
                self.consume(TokenType.COLON, "Expect ':' after parameter name.")
                param_type = self.parse_type()
                params.append((param_name, param_type))
                if not self.match(TokenType.COMMA): break
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")
        
        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.parse_type()
            
        self.consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self.block()
        return ast_nodes.FnDecl(name, params, return_type, ast_nodes.Block(body), is_async=is_async)

    def struct_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expect struct name.")
        self.consume(TokenType.LEFT_BRACE, "Expect '{' before struct body.")
        fields = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            field_name = self.consume(TokenType.IDENTIFIER, "Expect field name.")
            self.consume(TokenType.COLON, "Expect ':' after field name.")
            field_type = self.parse_type()
            self.consume(TokenType.SEMICOLON, "Expect ';' after field declaration.")
            fields.append((field_name, field_type))
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after struct body.")
        return ast_nodes.StructDecl(name, fields)

    def let_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")
        type_token = None
        if self.match(TokenType.COLON):
            type_token = self.parse_type()
        
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()
        
        self.consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        # Map to LetStmt
        return ast_nodes.LetStmt(name, type_token, initializer)

    def parse_type(self):
        # Parses a type signature
        if self.match(TokenType.TYPE_INT64, TokenType.TYPE_FLOAT64, TokenType.TYPE_BOOL, TokenType.TYPE_STRING, TokenType.IDENTIFIER):
            return self.previous()
        raise self.error(self.peek(), "Expect type.")

    def statement(self):
        if self.match(TokenType.IF): return self.if_statement()
        if self.match(TokenType.IF): return self.if_statement()
        if self.match(TokenType.WHILE): return self.while_statement()
        if self.match(TokenType.FOR): return self.for_statement()
        if self.match(TokenType.RETURN): return self.return_statement()
        if self.match(TokenType.TRY): return self.try_statement()
        if self.match(TokenType.THROW): return self.throw_statement()
        if self.match(TokenType.LEFT_BRACE): return ast_nodes.Block(self.block())
        if self.match(TokenType.PRINT): 
            return self.print_statement() 
        return self.expression_statement()

    def try_statement(self):
        # try { ... } catch (e) { ... } finally { ... }
        self.consume(TokenType.LEFT_BRACE, "Expect '{' after 'try'.")
        try_block = ast_nodes.Block(self.block())
        
        self.consume(TokenType.CATCH, "Expect 'catch' after try block.")
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'catch'.")
        catch_var = self.consume(TokenType.IDENTIFIER, "Expect exception variable name.")
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after catch variable.")
        self.consume(TokenType.LEFT_BRACE, "Expect '{' after catch.")
        catch_block = ast_nodes.Block(self.block())
        
        finally_block = None
        if self.match(TokenType.FINALLY):
            self.consume(TokenType.LEFT_BRACE, "Expect '{' after 'finally'.")
            finally_block = ast_nodes.Block(self.block())
        
        return ast_nodes.TryStmt(try_block, catch_var, catch_block, finally_block)

    def throw_statement(self):
        keyword = self.previous()
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after throw value.")
        return ast_nodes.ThrowStmt(keyword, value)

    def if_statement(self):
        # Parens optional in v2 design, but keeping parser simple for now: Support both?
        # Let's enforce parens for now to keep it LL(1) clean or peek
        if self.check(TokenType.LEFT_PAREN):
            self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
            condition = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")
        else:
            condition = self.expression() # No parens

        # Expect Block
        if not self.check(TokenType.LEFT_BRACE):
             # Single stmt support? Stick to blocks for v2
             self.consume(TokenType.LEFT_BRACE, "Expect '{' after condition.")

        self.consume(TokenType.LEFT_BRACE, "Expect '{' after condition.")
        then_branch = ast_nodes.Block(self.block())
        else_branch = None
        if self.match(TokenType.ELSE):
            if self.match(TokenType.IF):
                else_branch = self.if_statement() # elif
            else:
                 self.consume(TokenType.LEFT_BRACE, "Expect '{' after else.")
                 else_branch = ast_nodes.Block(self.block())
        return ast_nodes.IfStmt(condition, then_branch, else_branch)

    def print_statement(self):
        value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return ast_nodes.Print(value)

    def while_statement(self):
        if self.check(TokenType.LEFT_PAREN):
            self.consume(TokenType.LEFT_PAREN, "Expect '('")
            condition = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')'")
        else:
            condition = self.expression()
            
        self.consume(TokenType.LEFT_BRACE, "Expect '{'")
        body = ast_nodes.Block(self.block())
        return ast_nodes.WhileStmt(condition, body)

    def for_statement(self):
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")
        
        # Initializer
        initializer = None
        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.LET):
            initializer = self.let_declaration()
        else:
            initializer = self.expression_statement()
        
        # Condition
        condition = None
        if not self.check(TokenType.SEMICOLON):
             condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")
        
        # Increment
        increment = None
        if not self.check(TokenType.RIGHT_PAREN):
             increment = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")
        
        # Body
        body = self.statement()
        # Ensure body is a Block if it isn't? Or standard logic is fine?
        # Desugar
        if increment:
             # If body is Block, append? Or wrap?
             # Wrap in block to ensure increment execution.
             # Note: standard Lox wraps.
             body = ast_nodes.Block([body, ast_nodes.ExprStmt(increment)])

        if not condition: condition = ast_nodes.Literal(True)
        
        body = ast_nodes.WhileStmt(condition, body)
        
        if initializer:
             body = ast_nodes.Block([initializer, body])
             
        return body

    def return_statement(self):
        keyword = self.previous()
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return ast_nodes.ReturnStmt(keyword, value)

    def block(self):
        statements = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def expression_statement(self):
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return ast_nodes.ExprStmt(expr)

    def expression(self):
        return self.assignment()

    def assignment(self):
        expr = self.or_expression()
        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()
            if isinstance(expr, ast_nodes.Variable):
                return ast_nodes.Assign(expr.name, value)
            elif isinstance(expr, ast_nodes.Get):
                return ast_nodes.Set(expr.obj, expr.name, value)
            elif isinstance(expr, ast_nodes.Index):
                return ast_nodes.IndexSet(expr.target, expr.index, value)
            self.error(equals, "Invalid assignment target.")
        return expr

    def or_expression(self):
        expr = self.and_expression()
        while self.match(TokenType.OR):
            op = self.previous()
            right = self.and_expression()
            expr = ast_nodes.Logic(expr, op, right)
        return expr

    def and_expression(self):
        expr = self.equality()
        while self.match(TokenType.AND):
            op = self.previous()
            right = self.equality()
            expr = ast_nodes.Logic(expr, op, right)
        return expr

    def equality(self):
        expr = self.comparison()
        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            op = self.previous()
            right = self.comparison()
            expr = ast_nodes.Binary(expr, op, right)
        return expr

    def comparison(self):
        expr = self.term()
        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            op = self.previous()
            right = self.term()
            expr = ast_nodes.Binary(expr, op, right)
        return expr

    def term(self):
        expr = self.factor()
        while self.match(TokenType.MINUS, TokenType.PLUS):
            op = self.previous()
            right = self.factor()
            expr = ast_nodes.Binary(expr, op, right)
        return expr

    def factor(self):
        expr = self.unary()
        while self.match(TokenType.SLASH, TokenType.STAR):
            op = self.previous()
            right = self.unary()
            expr = ast_nodes.Binary(expr, op, right)
        return expr

    def unary(self):
        if self.match(TokenType.BANG, TokenType.MINUS):
            op = self.previous()
            right = self.unary()
            return ast_nodes.Unary(op, right)
        return self.call()

    def call(self):
        expr = self.primary()
        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                name = self.consume(TokenType.IDENTIFIER, "Expect property name after '.'.")
                expr = ast_nodes.Get(expr, name)
            elif self.match(TokenType.LEFT_BRACKET):
                index = self.expression()
                self.consume(TokenType.RIGHT_BRACKET, "Expect ']' after index.")
                expr = ast_nodes.Index(expr, index)
            else:
                break
        return expr

    def finish_call(self, callee):
        args = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                args.append(self.expression())
                if not self.match(TokenType.COMMA): break
        paren = self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
        return ast_nodes.Call(callee, paren, args)

    def super_expression(self):
        keyword = self.previous()
        self.consume(TokenType.DOT, "Expect '.' after 'super'.")
        method = self.consume(TokenType.IDENTIFIER, "Expect superclass method name.")
        return ast_nodes.Super(keyword, method)

    def match_expression(self):
        # match subject { pattern => body, ... }
        subject = self.expression()
        self.consume(TokenType.LEFT_BRACE, "Expect '{' after match subject.")
        
        cases = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            # Pattern (underscore for wildcard, using IDENTIFIER for now)
            if self.match(TokenType.IDENTIFIER):
                pattern = ast_nodes.Variable(self.previous())
            else:
                pattern = self.expression()
            
            # Optional guard: if condition
            guard = None
            if self.match(TokenType.IF):
                guard = self.expression()
            
            # Arrow =>
            self.consume(TokenType.FAT_ARROW, "Expect '=>' in match case.")
            
            # Body (expression or block)
            if self.check(TokenType.LEFT_BRACE):
                self.consume(TokenType.LEFT_BRACE, "")
                body = ast_nodes.Block(self.block())
            else:
                body = self.expression()
            
            cases.append(ast_nodes.MatchCase(pattern, guard, body))
            
            # Optional comma between cases
            self.match(TokenType.COMMA)
        
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after match cases.")
        return ast_nodes.MatchExpr(subject, cases)


    def primary(self):
        if self.match(TokenType.FALSE): return ast_nodes.Literal(False)
        if self.match(TokenType.TRUE): return ast_nodes.Literal(True)
        if self.match(TokenType.NIL): return ast_nodes.Literal(None)
        if self.match(TokenType.NUMBER): return ast_nodes.Literal(self.previous().literal)
        if self.match(TokenType.FLOAT_NUMBER): return ast_nodes.Literal(self.previous().literal)
        if self.match(TokenType.STRING): return ast_nodes.Literal(self.previous().literal)
        if self.match(TokenType.SUPER): return self.super_expression()
        if self.match(TokenType.THIS): return ast_nodes.This(self.previous())
        if self.match(TokenType.IDENTIFIER): return ast_nodes.Variable(self.previous())
        
        if self.match(TokenType.MATCH):
            return self.match_expression()
        
        if self.match(TokenType.AWAIT):
            keyword = self.previous()
            value = self.expression()
            return ast_nodes.AwaitExpr(keyword, value)
        
        if self.match(TokenType.LEFT_BRACKET):
            elements = []
            if not self.check(TokenType.RIGHT_BRACKET):
                while True:
                    elements.append(self.expression())
                    if not self.match(TokenType.COMMA): break
            self.consume(TokenType.RIGHT_BRACKET, "Expect ']' after array elements.")
            return ast_nodes.ArrayLiteral(elements)


        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return ast_nodes.Grouping(expr)
        
        raise self.error(self.peek(), "Expect expression.")

    def match(self, *types):
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False

    def consume(self, type, message):
        if self.check(type): return self.advance()
        raise self.error(self.peek(), message)

    def check(self, type):
        if self.is_at_end(): return False
        return self.peek().type == type

    def advance(self):
        if not self.is_at_end(): self.current += 1
        return self.previous()

    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def error(self, token, message):
        print(f"[line {token.line}] Error at '{token.lexeme}': {message}")
        return ParseError()

    def synchronize(self):
        self.advance()
        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON: return
            if self.peek().type in [TokenType.FN, TokenType.LET, TokenType.FOR, TokenType.IF, TokenType.WHILE, TokenType.RETURN, TokenType.STRUCT]:
                return
            self.advance()






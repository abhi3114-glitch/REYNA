from token_type import TokenType, Token

class Lexer:
    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1
        
        self.keywords = {
            "and": TokenType.AND,
            "else": TokenType.ELSE,
            "false": TokenType.FALSE,
            "for": TokenType.FOR,
            "fn": TokenType.FN,
            "if": TokenType.IF,
            "nil": TokenType.NIL,
            "or": TokenType.OR,
            "print": TokenType.PRINT,
            "return": TokenType.RETURN,
            "true": TokenType.TRUE,
            "let": TokenType.LET,
            "while": TokenType.WHILE,
            "struct": TokenType.STRUCT,
            "import": TokenType.IMPORT,
            "int64": TokenType.TYPE_INT64,
            "float64": TokenType.TYPE_FLOAT64,
            "bool": TokenType.TYPE_BOOL,
            "string": TokenType.TYPE_STRING,
            "class": TokenType.CLASS,
            "this": TokenType.THIS,
            "super": TokenType.SUPER,
            # Error handling
            "try": TokenType.TRY,
            "catch": TokenType.CATCH,
            "throw": TokenType.THROW,
            "finally": TokenType.FINALLY,
            # Pattern matching
            "match": TokenType.MATCH,
            # Async/Await
            "async": TokenType.ASYNC,
            "await": TokenType.AWAIT,
        }

    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def scan_token(self):
        c = self.advance()
        if c == '(': self.add_token(TokenType.LEFT_PAREN)
        elif c == ')': self.add_token(TokenType.RIGHT_PAREN)
        elif c == '{': self.add_token(TokenType.LEFT_BRACE)
        elif c == '}': self.add_token(TokenType.RIGHT_BRACE)
        elif c == '[': self.add_token(TokenType.LEFT_BRACKET)
        elif c == ']': self.add_token(TokenType.RIGHT_BRACKET)
        elif c == ',': self.add_token(TokenType.COMMA)
        elif c == '.': self.add_token(TokenType.DOT)
        elif c == '-': 
            if self.match('>'): self.add_token(TokenType.ARROW)
            else: self.add_token(TokenType.MINUS)
        elif c == '+': self.add_token(TokenType.PLUS)
        elif c == ';': self.add_token(TokenType.SEMICOLON)
        elif c == '*': self.add_token(TokenType.STAR)
        elif c == ':': self.add_token(TokenType.COLON)
        elif c == '!': self.add_token(TokenType.BANG_EQUAL if self.match('=') else TokenType.BANG)
        elif c == '=': 
            if self.match('='):
                self.add_token(TokenType.EQUAL_EQUAL)
            elif self.match('>'):
                self.add_token(TokenType.FAT_ARROW)
            else:
                self.add_token(TokenType.EQUAL)
        elif c == '<': self.add_token(TokenType.LESS_EQUAL if self.match('=') else TokenType.LESS)
        elif c == '>': self.add_token(TokenType.GREATER_EQUAL if self.match('=') else TokenType.GREATER)
        elif c == '/':
            if self.match('/'):
                # comment goes until the end of the line
                while self.peek() != '\n' and not self.is_at_end():
                    self.advance()
            else:
                self.add_token(TokenType.SLASH)
        elif c in [' ', '\r', '\t']:
            pass
        elif c == '\n':
            self.line += 1
        elif c == '"':
            self.string()
        else:
            if self.is_digit(c):
                self.number()
            elif self.is_alpha(c):
                self.identifier()
            else:
                print(f"Unexpected character: {c} at line {self.line}")

    def identifier(self):
        while self.is_alpha_numeric(self.peek()):
            self.advance()
        
        text = self.source[self.start:self.current]
        type = self.keywords.get(text, TokenType.IDENTIFIER)
        self.add_token(type)

    def number(self):
        is_float = False
        while self.is_digit(self.peek()):
            self.advance()

        if self.peek() == '.' and self.is_digit(self.peek_next()):
            is_float = True
            self.advance() # consume dot
            while self.is_digit(self.peek()):
                self.advance()
        
        value = float(self.source[self.start:self.current]) if is_float else int(self.source[self.start:self.current])
        type = TokenType.FLOAT_NUMBER if is_float else TokenType.NUMBER
        self.add_token(type, value)

    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n': self.line += 1
            self.advance()
        
        if self.is_at_end():
            print("Unterminated string.")
            return

        self.advance() # The closing "
        value = self.source[self.start+1 : self.current-1]
        self.add_token(TokenType.STRING, value)

    def match(self, expected):
        if self.is_at_end(): return False
        if self.source[self.current] != expected: return False
        self.current += 1
        return True

    def peek(self):
        if self.is_at_end(): return '\0'
        return self.source[self.current]

    def peek_next(self):
        if self.current + 1 >= len(self.source): return '\0'
        return self.source[self.current + 1]

    def is_alpha(self, c):
        return (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z') or c == '_'

    def is_alpha_numeric(self, c):
        return self.is_alpha(c) or self.is_digit(c)

    def is_digit(self, c):
        return c >= '0' and c <= '9'

    def is_at_end(self):
        return self.current >= len(self.source)

    def advance(self):
        self.current += 1
        return self.source[self.current - 1]

    def add_token(self, type, literal=None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(type, text, literal, self.line))










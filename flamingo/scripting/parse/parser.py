from flamingo.scripting.interpreter import FlamingoScriptError
from flamingo.scripting.token.token_types import *
from flamingo.scripting.parse.ast import *


class Parser:
    __slots__ = ('tokens', 'pos', 'len')

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.len = len(tokens)

    def parse(self) -> Block:
        token = self.peek()
        statements = []
        while not self.is_at_end():
            stmt = self.declaration()
            if stmt:
                statements.append(stmt)
        return Block(token, tuple(statements))

    def declaration(self) -> Stmt:
        token = self.peek()

        if token.t_type == T_KEYWORD:
            text = token.value
            if text == "!set":
                return self.parse_set()
            if text == "!if":
                return self.parse_if()
            if text == "!while":
                return self.parse_while()
            if text == "!for":
                return self.parse_for()
            if text == "!macro":
                return self.parse_macro_def()
            if text == "!do":
                return self.parse_macro_call()

        if token.t_type == T_COMMAND:
            self.advance()
            return Command(token, token.value)

        self.advance()
        return None

    def parse_set(self) -> SetStmt:
        token = self.peek()
        self.advance()

        name_token = self.consume(T_IDENTIFIER, "Expect variable name after '!set'.")

        self.consume(T_EQUALS, "Expect '=' after variable name.")

        value = self.expression()

        return SetStmt(token, name_token.value, value)

    def parse_if(self) -> IfStmt:
        token = self.peek()
        self.advance()

        condition = self.expression()
        then_branch = self.parse_block()
        else_branch = None

        next_token = self.peek()
        if next_token.t_type == T_KEYWORD:
            if next_token.value == "!else":
                self.advance()
                if self.peek().value == "!if":
                    else_branch = self.parse_if()
                else:
                    else_branch = self.parse_block()

        return IfStmt(token, condition, then_branch, else_branch)

    def parse_while(self) -> WhileStmt:
        token = self.peek()
        self.advance()
        condition = self.expression()
        body = self.parse_block()
        return WhileStmt(token, condition, body)

    def parse_for(self) -> ForStmt:
        token = self.peek()
        self.advance()

        target = self.consume(T_IDENTIFIER, "Expect variable name after '!for'").value

        if self.peek().value != "in":
            raise FlamingoScriptError(self.peek(), "Expect 'in' after variable name.")
        self.advance()

        iterable = self.expression()
        body = self.parse_block()

        return ForStmt(token, target, iterable, body)

    def parse_macro_def(self) -> MacroDef:
        token = self.peek()
        self.advance()
        name = self.consume(T_IDENTIFIER, "Expect macro name").value

        params = []
        if self.match(T_OPEN_PARENS):
            if not self.check(T_CLOSE_PARENS):
                while True:
                    params.append(self.consume(T_IDENTIFIER, "Expect param name").value)
                    if not self.match(T_COMMA): break
            self.consume(T_CLOSE_PARENS, "Expect ')' after params")

        body = self.parse_block()
        return MacroDef(token, name, tuple(params), body)

    def parse_macro_call(self) -> MacroCall:
        token = self.peek()
        self.advance()
        name = self.consume(T_IDENTIFIER, "Expect macro name").value

        args = []
        if self.match(T_OPEN_PARENS):
            if not self.check(T_CLOSE_PARENS):
                while True:
                    args.append(self.expression())
                    if not self.match(T_COMMA): break
            self.consume(T_CLOSE_PARENS, "Expect ')' after args")

        return MacroCall(token, name, tuple(args))

    def parse_block(self) -> Block:
        self.consume(T_COLON, "Expect ':' before block")
        self.consume(T_NEWLINE, "Expect newline before block")
        self.consume(T_INDENT, "Expect indent start of block")
        token = self.peek()

        stmts = []
        while not self.check(T_DEDENT) and not self.is_at_end():
            stmt = self.declaration()
            if stmt: stmts.append(stmt)

        self.consume(T_DEDENT, "Expect dedent end of block")
        return Block(token, tuple(stmts))

    def expression(self) -> Expr:
        return self.logic_or()

    def logic_or(self) -> Expr:
        expr = self.logic_and()

        while self.match(T_DOUBLE_PIPES):
            operator = self.previous()
            right = self.logic_and()
            expr = Binary(operator, expr, T_DOUBLE_PIPES, right)

        return expr

    def logic_and(self) -> Expr:
        expr = self.equality()

        while self.match(T_DOUBLE_AMPERSAND):
            operator = self.previous()
            right = self.equality()
            expr = Binary(operator, expr, T_DOUBLE_AMPERSAND, right)

        return expr

    def equality(self) -> Expr:
        expr = self.comparison()

        while self.match(T_BANG_EQUALS, T_DOUBLE_EQUALS):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(operator, expr, operator.t_type, right)

        return expr

    def comparison(self) -> Expr:
        expr = self.term()

        while self.match(T_MORE_THAN, T_MORE_THAN_EQUALS,
                         T_LESS_THAN, T_LESS_THAN_EQUALS):
            operator = self.previous()
            right = self.term()
            expr = Binary(operator, expr, operator.t_type, right)

        return expr

    def term(self) -> Expr:
        expr = self.factor()

        while self.match(T_MINUS, T_PLUS):
            operator = self.previous()
            right = self.factor()
            expr = Binary(operator, expr, operator.t_type, right)

        return expr

    def factor(self) -> Expr:
        expr = self.unary()

        while self.match(T_SLASH, T_STAR, T_PERCENT):
            operator = self.previous()
            right = self.unary()
            expr = Binary(operator, expr, operator.t_type, right)

        return expr

    def unary(self) -> Expr:
        if self.match(T_BANG, T_MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, operator.t_type, right)

        return self.primary()

    def primary(self) -> Expr:
        token = self.peek()
        if self.match(T_INTEGER):
            return Literal(token, int(token.value))
        if self.match(T_FLOAT):
            return Literal(token, float(token.value))
        if self.match(T_STRING):
            return Literal(token, token.value)
        if self.match(T_KEYWORD):
            if token.value == "True":
                return Literal(token, True)
            if token.value == "False":
                return Literal(token, False)
            if token.value == "Nothing":
                return Literal(token, None)

        if self.match(T_IDENTIFIER):
            return Identifier(token, token.value)

        if self.match(T_VARIABLE):
            return Variable(token, token.value)

        if self.match(T_OPEN_BRACKETS):
            elements = []
            if not self.check(T_CLOSE_BRACKETS):
                while True:
                    elements.append(self.expression())
                    if not self.match(T_COMMA): break
            self.consume(T_CLOSE_BRACKETS, "Expect ']'")
            return ListExpr(token, tuple(elements))

        if self.match(T_OPEN_PARENS):
            expr = self.expression()
            if self.match(T_COMMA):
                elements = [expr]
                while True:
                    elements.append(self.expression())
                    if not self.match(T_COMMA): break
                self.consume(T_CLOSE_PARENS, "Expect ')'")
                return TupleExpr(token, tuple(elements))
            else:
                self.consume(T_CLOSE_PARENS, "Expect ')'")
                return expr

        raise FlamingoScriptError(self.peek(), f"Unexpected token {self.peek()}")

    def match(self, *t_type: int) -> bool:
        if any(map(self.check, t_type)):
            self.advance()
            return True
        return False

    def check(self, t_type: int) -> bool:
        if self.is_at_end(): return False
        return self.tokens[self.pos].t_type == t_type

    def advance(self):
        if not self.is_at_end(): self.pos += 1
        return self.tokens[self.pos - 1]

    def consume(self, t_type: int, msg: str):
        if self.check(t_type):
            return self.advance()
        raise FlamingoScriptError(self.peek(), msg)

    def peek(self, n: int = 0) -> Token:
        if self.pos + n < len(self.tokens):
            return self.tokens[self.pos + n]
        return self.tokens[-1]

    def previous(self):
        return self.peek(-1)

    def is_at_end(self):
        return self.pos >= self.len or self.tokens[self.pos].t_type == T_END_OF_FILE

from typing import Callable

from plox.tokens import Token, TokenType
from plox import expressions as expr, statements as stmt


class Parser:
    def __init__(
        self, tokens: list[Token], error_callback: Callable[[Token, str], None]
    ):
        self._tokens = tokens
        self._error_callback = error_callback
        self._current = 0

    def parse(self) -> list[stmt.Stmt]:
        statements = []
        while not self._is_at_end():
            statements.append(self._declaration())
        return statements

    def _declaration(self) -> stmt.Stmt | None:
        try:
            if self._match(TokenType.FUN):
                return self._function("function")
            if self._match(TokenType.VAR):
                return self._var_declaration()
            return self._statement()
        except ParseError:
            self._synchronize()
            return None

    def _synchronize(self):
        print("SYNC")

    def _var_declaration(self) -> stmt.Stmt:
        name = self._consume(TokenType.IDENTIFIER, "Expect variable name.")

        initializer = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()

        self._consume(TokenType.SEMICOLON, "Expect ';' after variable declaration.")
        return stmt.Var(name, initializer)

    def _statement(self) -> stmt.Stmt:
        if self._match(TokenType.FOR):
            return self._for_statement()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        if self._match(TokenType.WHILE):
            return self._while_statement()
        if self._match(TokenType.LEFT_BRACE):
            return stmt.Block(self._block())
        return self._expression_statement()

    def _if_statement(self) -> stmt.Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")

        then_branch = self._statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._statement()

        return stmt.If(condition, then_branch, else_branch)

    def _print_statement(self) -> stmt.Stmt:
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmt.Print(value)

    def _return_statement(self) -> stmt.Stmt:
        keyword = self._previous()
        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()

        self._consume(TokenType.SEMICOLON, "Expect ';' after return value.")
        return stmt.Return(keyword, value)

    def _while_statement(self) -> stmt.Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after condition.")
        body = self._statement()

        return stmt.While(condition, body)

    def _for_statement(self) -> stmt.Stmt:
        self._consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        if self._match(TokenType.SEMICOLON):
            initializer = None
        elif self._match(TokenType.VAR):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()

        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()

        self._consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()

        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")
        body = self._statement()

        if increment:
            body = stmt.Block([body, stmt.Expression(increment)])

        if not condition:
            condition = expr.Literal(True)
        body = stmt.While(condition, body)

        if initializer:
            body = stmt.Block([initializer, body])

        return body

    def _expression_statement(self) -> stmt.Stmt:
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return stmt.Expression(value)

    def _function(self, kind: str) -> stmt.Function:
        name = self._consume(TokenType.IDENTIFIER, f"Expect {kind} name.")
        self._consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        parameters = []
        if not self._check(TokenType.RIGHT_PAREN):
            parameters.append(
                self._consume(TokenType.IDENTIFIER, "Expect parameter name.")
            )
            while self._match(TokenType.COMMA):
                if len(parameters) >= 255:
                    self._error(self._peek(), "Can't have more than 255 parameters.")
                parameters.append(
                    self._consume(TokenType.IDENTIFIER, "Expect parameter name.")
                )
        self._consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        self._consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self._block()
        return stmt.Function(name, parameters, body)

    def _block(self) -> list[stmt.Stmt]:
        statements = []

        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            statements.append(self._declaration())

        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def _expression(self) -> expr.Expr:
        return self._assignment()

    def _assignment(self) -> expr.Expr:
        expression = self._or()

        if self._match(TokenType.EQUAL):
            equals = self._previous()
            value = self._assignment()

            if isinstance(expression, expr.Variable):
                name = expression.name
                return expr.Assign(name, value)

            self._error(equals, "Invalid assignment target.")

        return expression

    def _or(self) -> expr.Expr:
        expression = self._and()

        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._and()
            expression = expr.Logical(expression, operator, right)

        return expression

    def _and(self) -> expr.Expr:
        expression = self._equality()

        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._equality()
            expression = expr.Logical(expression, operator, right)

        return expression

    def _equality(self) -> expr.Expr:
        expression = self._comparison()

        while self._match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self._previous()
            right = self._comparison()
            expression = expr.Binary(expression, operator, right)

        return expression

    def _comparison(self) -> expr.Expr:
        expression = self._term()

        while self._match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            operator = self._previous()
            right = self._term()
            expression = expr.Binary(expression, operator, right)

        return expression

    def _term(self) -> expr.Expr:
        expression = self._factor()

        while self._match(TokenType.MINUS, TokenType.PLUS):
            operator = self._previous()
            right = self._factor()
            expression = expr.Binary(expression, operator, right)

        return expression

    def _factor(self) -> expr.Expr:
        expression = self._unary()

        while self._match(TokenType.SLASH, TokenType.STAR):
            operator = self._previous()
            right = self._unary()
            expression = expr.Binary(expression, operator, right)

        return expression

    def _unary(self) -> expr.Expr:
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            right = self._unary()
            return expr.Unary(operator, right)

        return self._call()

    def _call(self) -> expr.Expr:
        expression = self._primary()

        while True:
            if self._match(TokenType.LEFT_PAREN):
                expression = self._finish_call(expression)
            else:
                break

        return expression

    def _finish_call(self, callee: expr.Expr) -> expr.Expr:
        arguments = []
        if not self._check(TokenType.RIGHT_PAREN):
            arguments.append(self._expression())
            while self._match(TokenType.COMMA):
                if len(arguments) >= 255:
                    self._error(self._peek(), "Can't have more than 255 arguments.")
                arguments.append(self._expression())

        paren = self._consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")

        return expr.Call(callee, paren, arguments)

    def _primary(self) -> expr.Expr:
        if self._match(TokenType.FALSE):
            return expr.Literal(False)
        if self._match(TokenType.TRUE):
            return expr.Literal(True)
        if self._match(TokenType.NIL):
            return expr.Literal(None)

        if self._match(TokenType.NUMBER, TokenType.STRING):
            return expr.Literal(self._previous().literal)

        if self._match(TokenType.LEFT_PAREN):
            expression = self._expression()
            self._consume(TokenType.RIGHT_PAREN, "Expect ')' after expression")
            return expr.Grouping(expression)

        if self._match(TokenType.IDENTIFIER):
            return expr.Variable(self._previous())

        raise self._error(self._peek(), "Expect expression.")

    def _match(self, *types: TokenType) -> bool:
        for type_ in types:
            if self._check(type_):
                self._advance()
                return True

        return False

    def _consume(self, type_: TokenType, message: str) -> Token:
        if self._check(type_):
            return self._advance()

        raise self._error(self._peek(), message)

    def _error(self, token: Token, message: str) -> Exception:
        self._error_callback(token, message)
        return ParseError()

    def _check(self, type_: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == type_

    def _advance(self) -> Token:
        if not self._is_at_end():
            self._current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self._tokens[self._current]

    def _previous(self) -> Token:
        return self._tokens[self._current - 1]


class ParseError(Exception):
    pass

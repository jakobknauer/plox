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
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.LEFT_BRACE):
            return stmt.Block(self._block())
        return self._expression_statement()

    def _print_statement(self) -> stmt.Stmt:
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after value.")
        return stmt.Print(value)

    def _expression_statement(self) -> stmt.Stmt:
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expect ';' after expression.")
        return stmt.Expression(value)

    def _block(self) -> list[stmt.Stmt]:
        statements = []

        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            statements.append(self._declaration())

        self._consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def _expression(self) -> expr.Expr:
        return self._assignment()

    def _assignment(self) -> expr.Expr:
        expression = self._equality()

        if self._match(TokenType.EQUAL):
            equals = self._previous()
            value = self._assignment()

            if isinstance(expression, expr.Variable):
                name = expression.name
                return expr.Assign(name, value)

            self._error(equals, "Invalid assignment target.")

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

        return self._primary()

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

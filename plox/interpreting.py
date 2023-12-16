# pylint: disable=function-redefined
# mypy: disable-error-code="no-redef"

from typing import Callable

from plox.expression import Binary, Unary, Grouping, Literal
from plox import statement as stmt
from plox.token import Token, TokenType
from plox.visitor import visitor


class InterpreterError(RuntimeError):
    def __init__(self, token: Token, message: str, *args, **kwargs):
        super().__init__(args, kwargs)
        self.token = token
        self.message = message


class Interpreter:
    def __init__(self, error_callback: Callable[[InterpreterError], None]):
        self._error_callback = error_callback

    def interpret(self, statements: list[stmt.Stmt]) -> None:
        try:
            for statement in statements:
                self.execute(statement)
        except InterpreterError as e:
            self._error_callback(e)

    @visitor(stmt.Expression)
    def execute(self, statement: stmt.Expression) -> None:
        self.evaluate(statement.expression)

    @visitor(stmt.Print)
    def execute(self, statement: stmt.Print) -> None:
        value = self.evaluate(statement.expression)
        print(self._stringify(value))

    @visitor(Literal)
    def evaluate(self, literal: Literal) -> object:
        return literal.value

    @visitor(Grouping)
    def evaluate(self, grouping: Grouping) -> object:
        return self.evaluate(grouping.expression)

    @visitor(Unary)
    def evaluate(self, unary: Unary) -> object:
        right = self.evaluate(unary.right)

        match unary.operator.type:
            case TokenType.MINUS:
                self._check_number_operand(unary.operator, right)
                return -float(right)
            case TokenType.BANG:
                return not self._is_truthy(right)
            case _:
                return None

    @visitor(Binary)
    def evaluate(self, binary: Binary) -> object:
        left = self.evaluate(binary.left)
        right = self.evaluate(binary.right)

        match binary.operator.type:
            # Arithmetic
            case TokenType.MINUS:
                self._check_number_operands(binary, left, right)
                return left - right
            case TokenType.SLASH:
                self._check_number_operands(binary, left, right)
                return left / right
            case TokenType.STAR:
                self._check_number_operands(binary, left, right)
                return left * right
            case TokenType.PLUS if isinstance(left, float) and isinstance(right, float):
                return left + right

            # String concatenation
            case TokenType.PLUS if isinstance(left, str) and isinstance(right, str):
                return left + right

            # Fallback for plus with incompatible operands
            case TokenType.PLUS:
                raise InterpreterError(
                    binary.operator, "Operands must be two numbers or two strings."
                )

            # Comparison
            case TokenType.GREATER:
                self._check_number_operands(binary, left, right)
                return left > right
            case TokenType.GREATER_EQUAL:
                self._check_number_operands(binary, left, right)
                return left >= right
            case TokenType.LESS:
                self._check_number_operands(binary, left, right)
                return left < right
            case TokenType.LESS_EQUAL:
                self._check_number_operands(binary, left, right)
                return left <= right

            # Equality
            case TokenType.BANG_EQUAL:
                return left != right
            case TokenType.EQUAL_EQUAL:
                return left == right

            case _:
                return None

    def _is_truthy(self, object_: object) -> bool:
        match object_:
            case None:
                return False
            case bool():
                return object_
            case _:
                return False

    def _check_number_operand(self, operator: Token, operand: object) -> None:
        if isinstance(operand, float):
            return
        raise InterpreterError(operator, "Operand must be a number")

    def _check_number_operands(
        self, operator: Token, left: object, right: object
    ) -> None:
        if isinstance(left, float) and isinstance(right, float):
            return
        raise InterpreterError(operator, "Operands must be numbers")

    def _stringify(self, object_: object) -> str:
        match object_:
            case None:
                return "nil"
            case float():
                text = str(object_)
                if text.endswith(".0"):
                    text = text[:-2]
                return text
            case _:
                return str(object_)
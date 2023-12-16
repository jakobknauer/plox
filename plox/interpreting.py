# pylint: disable=function-redefined
# mypy: disable-error-code="no-redef"

from abc import ABC, abstractmethod
import time
from typing import Callable

from plox import expressions as expr, statements as stmt
from plox.tokens import Token, TokenType
from plox.visitor import visitor

from plox.environments import Environment


class LoxCallable(ABC):
    @abstractmethod
    def call(self, interpreter: "Interpreter", arguments: list[object]) -> object:
        pass

    @abstractmethod
    def arity(self) -> int:
        pass


class AnonymousCallable(LoxCallable):
    def __init__(
        self, callable_: Callable[["Interpreter", list[object]], object], arity: int
    ):
        self._callable = callable_
        self._arity = arity

    def arity(self) -> int:
        return self._arity

    def call(self, interpreter: "Interpreter", arguments: list[object]) -> object:
        return self._callable(interpreter, arguments)


class LoxFunction(LoxCallable):
    def __init__(self, declaration: stmt.Function, closure: Environment):
        self._declaration = declaration
        self._closure = closure

    def arity(self) -> int:
        return len(self._declaration.params)

    def call(self, interpreter: "Interpreter", arguments: list[object]) -> object:
        environment = Environment(self._closure)
        for parameter, argument in zip(self._declaration.params, arguments):
            environment.define(parameter.lexeme, argument)

        try:
            interpreter.execute_block(self._declaration.body, environment)
        except Return as return_value:
            return return_value.value
        return None

    def __str__(self) -> str:
        return f"<fn {self._declaration.name.lexeme}>"


class InterpreterError(RuntimeError):
    def __init__(self, token: Token, message: str, *args, **kwargs):
        super().__init__(args, kwargs)
        self.token = token
        self.message = message


class Return(RuntimeError):
    def __init__(self, value: object):
        self.value = value


class Interpreter:
    def __init__(self, error_callback: Callable[[InterpreterError], None]):
        self._error_callback = error_callback

        self.globals = Environment()
        self.globals.define(
            "clock",
            AnonymousCallable(
                callable_=lambda interpreter, arguments: (time.time() / 1000.0),
                arity=0,
            ),
        )

        self._environment = self.globals
        self._locals: dict[expr.Expr, int] = {}

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

    @visitor(stmt.Var)
    def execute(self, statement: stmt.Var) -> None:
        value = None
        if statement.initializer is not None:
            value = self.evaluate(statement.initializer)
        self._environment.define(statement.name.lexeme, value)

    @visitor(stmt.Block)
    def execute(self, statement: stmt.Block) -> None:
        self.execute_block(statement.statements, Environment(self._environment))

    @visitor(stmt.While)
    def execute(self, statement: stmt.While) -> None:
        while self._is_truthy(self.evaluate(statement.condition)):
            self.execute(statement.body)

    @visitor(stmt.Function)
    def execute(self, statement: stmt.Function) -> None:
        function = LoxFunction(statement, self._environment)
        self._environment.define(statement.name.lexeme, function)

    @visitor(stmt.Return)
    def execute(self, statement: stmt.Return) -> None:
        value = None
        if statement.value is not None:
            value = self.evaluate(statement.value)

        raise Return(value)

    def execute_block(
        self, statements: list[stmt.Stmt], environment: Environment
    ) -> None:
        previous = self._environment
        try:
            self._environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self._environment = previous

    @visitor(stmt.If)
    def execute(self, statement: stmt.If) -> None:
        if self._is_truthy(self.evaluate(statement.condition)):
            self.execute(statement.then_branch)
        elif statement.else_branch is not None:
            self.execute(statement.else_branch)

    def resolve(self, expression: expr.Expr, depth: int) -> None:
        self._locals[expression] = depth

    @visitor(expr.Literal)
    def evaluate(self, literal: expr.Literal) -> object:
        return literal.value

    @visitor(expr.Grouping)
    def evaluate(self, grouping: expr.Grouping) -> object:
        return self.evaluate(grouping.expression)

    @visitor(expr.Unary)
    def evaluate(self, unary: expr.Unary) -> object:
        right = self.evaluate(unary.right)

        match unary.operator.type:
            case TokenType.MINUS:
                self._check_number_operand(unary.operator, right)
                return -float(right)
            case TokenType.BANG:
                return not self._is_truthy(right)
            case _:
                return None

    @visitor(expr.Binary)
    def evaluate(self, binary: expr.Binary) -> object:
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

    @visitor(expr.Variable)
    def evaluate(self, variable: expr.Variable) -> object:
        return self._look_up_variable(variable.name, variable)

    @visitor(expr.Assign)
    def evaluate(self, assign: expr.Assign) -> object:
        value = self.evaluate(assign.value)

        distance = self._locals.get(assign)
        if distance is not None:
            self._environment.assign_at(distance, assign.name, value)
        else:
            self.globals.assign(assign.name, value)

        return value

    @visitor(expr.Logical)
    def evaluate(self, logical: expr.Logical) -> object:
        left = self.evaluate(logical.left)

        if logical.operator.type == TokenType.OR:
            if self._is_truthy(left):
                return left
        else:
            if not self._is_truthy(left):
                return left

        return self.evaluate(logical.right)

    @visitor(expr.Call)
    def evaluate(self, call: expr.Call) -> object:
        callee = self.evaluate(call.callee)

        arguments = []
        for argument in call.arguments:
            arguments.append(self.evaluate(argument))

        if not isinstance(callee, LoxCallable):
            raise InterpreterError(call.paren, "Can only call functions and classes.")

        function: LoxCallable = callee

        if len(arguments) != function.arity():
            raise InterpreterError(
                call.paren,
                "Expected {function.arity()} arguments but got {len(arguments)}.",
            )
        return function.call(self, arguments)

    def _is_truthy(self, object_: object) -> bool:
        match object_:
            case None:
                return False
            case bool():
                return object_
            case _:
                return True

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

    def _look_up_variable(self, name: Token, expression: expr.Expr) -> object:
        distance = self._locals.get(expression)
        if distance is not None:
            return self._environment.get_at(distance, name.lexeme)
        else:
            return self.globals.get(name)

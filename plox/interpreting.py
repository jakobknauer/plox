# pylint: disable=function-redefined
# mypy: disable-error-code="no-redef"

from abc import ABC, abstractmethod
import time
from typing import Callable, Self

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
    def __init__(
        self, declaration: stmt.Function, closure: Environment, is_initializer: bool
    ):
        self._declaration = declaration
        self._closure = closure
        self._is_initializer = is_initializer

    def arity(self) -> int:
        return len(self._declaration.params)

    def call(self, interpreter: "Interpreter", arguments: list[object]) -> object:
        environment = Environment(self._closure)
        for parameter, argument in zip(self._declaration.params, arguments):
            environment.define(parameter.lexeme, argument)

        try:
            interpreter.execute_block(self._declaration.body, environment)
        except Return as return_value:
            if self._is_initializer:
                return self._closure.get_at(0, "this")
            return return_value.value

        if self._is_initializer:
            return self._closure.get_at(0, "this")
        return None

    def __str__(self) -> str:
        return f"<fn {self._declaration.name.lexeme}>"

    def bind(self, instance: "LoxInstance") -> Self:
        environment = Environment(self._closure)
        environment.define("this", instance)
        return LoxFunction(self._declaration, environment, self._is_initializer)


class LoxClass(LoxCallable):
    def __init__(
        self, name: str, superclass: Self | None, methods: dict[str, LoxFunction]
    ):
        self._name = name
        self._superclass = superclass
        self._methods = methods

    def __str__(self) -> str:
        return self._name

    def call(self, interpreter: "Interpreter", arguments: list[object]) -> object:
        instance = LoxInstance(self)
        initializer = self.find_method("init")
        if initializer:
            initializer.bind(instance).call(interpreter, arguments)

        return instance

    def arity(self) -> int:
        initializer = self.find_method("init")
        if not initializer:
            return 0
        return initializer.arity()

    def find_method(self, name: str) -> LoxFunction | None:
        if name in self._methods:
            return self._methods[name]

        if self._superclass:
            return self._superclass.find_method(name)

        return None


class LoxInstance:
    def __init__(self, class_: LoxClass):
        self._class = class_
        self._fields: dict[str, object] = {}

    def __str__(self) -> str:
        return f"{self._class._name} instance"

    def get(self, name: Token) -> object:
        if name.lexeme in self._fields:
            return self._fields[name.lexeme]

        method = self._class.find_method(name.lexeme)
        if method:
            return method.bind(self)

        raise InterpreterError(name, f"Undefined property '{name.lexeme}'.")

    def set(self, name: Token, value: object) -> None:
        self._fields[name.lexeme] = value


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
        function = LoxFunction(statement, self._environment, False)
        self._environment.define(statement.name.lexeme, function)

    @visitor(stmt.Return)
    def execute(self, statement: stmt.Return) -> None:
        value = None
        if statement.value is not None:
            value = self.evaluate(statement.value)

        raise Return(value)

    @visitor(stmt.If)
    def execute(self, statement: stmt.If) -> None:
        if self._is_truthy(self.evaluate(statement.condition)):
            self.execute(statement.then_branch)
        elif statement.else_branch is not None:
            self.execute(statement.else_branch)

    @visitor(stmt.Class)
    def execute(self, statement: stmt.Class) -> None:
        superclass = None
        if statement.superclass:
            superclass = self.evaluate(statement.superclass)
            if not isinstance(superclass, LoxClass):
                raise InterpreterError(
                    statement.superclass.name, "Superclass must be a class."
                )

        self._environment.define(statement.name.lexeme, None)

        if statement.superclass:
            self._environment = Environment(self._environment)
            self._environment.define("super", superclass)

        methods = {}
        for method in statement.methods:
            function = LoxFunction(
                method, self._environment, method.name.lexeme == "this"
            )
            methods[method.name.lexeme] = function

        class_ = LoxClass(statement.name.lexeme, superclass, methods)

        if statement.superclass:
            self._environment = self._environment._enclosing

        self._environment.assign(statement.name, class_)

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

    @visitor(expr.Get)
    def evaluate(self, get: expr.Get) -> object:
        object_ = self.evaluate(get.object_)
        if isinstance(object_, LoxInstance):
            return object_.get(get.name)

        raise InterpreterError(get.name, "Only instances have properties.")

    @visitor(expr.Set)
    def evaluate(self, set_: expr.Set) -> object:
        object_ = self.evaluate(set_.object_)

        if not isinstance(object_, LoxInstance):
            raise InterpreterError(set_.name, "Only instances have fields.")

        value = self.evaluate(set_.value)
        object_.set(set_.name, value)
        return value

    @visitor(expr.This)
    def evaluate(self, this: expr.This) -> object:
        return self._look_up_variable(this.keyword, this)

    @visitor(expr.Super)
    def evaluate(self, super_: expr.Super) -> object:
        distance = self._locals[super_]
        superclass = self._environment.get_at(distance, "super")
        object_ = self._environment.get_at(distance - 1, "this")

        method = superclass.find_method(super_.method.lexeme)

        if method is None:
            raise InterpreterError(super_.method, f"Undefined property '{super_.method.lexeme}'.")

        return method.bind(object_)

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

# pylint: disable=function-redefined
# mypy: disable-error-code="no-redef"

from typing import Callable
from enum import Enum, auto

from plox.interpreting import Interpreter
from plox.visitor import visitor
import plox.statements as stmt
import plox.expressions as expr
from plox.tokens import Token


class _FunctionType(Enum):
    NONE = auto()
    FUNCTION = auto()
    INITIALIZER = auto()
    METHOD = auto()


class _ClassType(Enum):
    NONE = auto()
    CLASS = auto()
    SUBCLASS = auto()


class Resolver:
    def __init__(
        self, interpreter: Interpreter, error_callback: Callable[[Token, str], None]
    ) -> None:
        self._interpreter = interpreter
        self._scopes: list[dict[str, bool]] = []
        self._error_callback = error_callback
        self._current_function = _FunctionType.NONE
        self._current_class = _ClassType.NONE

    @visitor(list)
    def resolve(self, statements: list[stmt.Stmt]) -> None:
        for statement in statements:
            self.resolve(statement)

    @visitor(stmt.Block)
    def resolve(self, statement: stmt.Block) -> None:
        self._begin_scope()
        self.resolve(statement.statements)
        self._end_scope()

    @visitor(stmt.Var)
    def resolve(self, statement: stmt.Var) -> None:
        self._declare(statement.name)
        if statement.initializer is not None:
            self.resolve(statement.initializer)
        self._define(statement.name)

    @visitor(expr.Variable)
    def resolve(self, expression: expr.Variable) -> None:
        if self._scopes and self._scopes[-1].get(expression.name.lexeme) is False:
            self._error_callback(
                expression.name, "Can't read local variable in its own initializer."
            )

        self._resolve_local(expression, expression.name)

    @visitor(expr.Assign)
    def resolve(self, expression: expr.Assign) -> None:
        self.resolve(expression.value)
        self._resolve_local(expression, expression.name)

    @visitor(stmt.Function)
    def resolve(self, statement: stmt.Function) -> None:
        self._declare(statement.name)
        self._define(statement.name)

        self._resolve_function(statement, _FunctionType.FUNCTION)

    @visitor(stmt.Expression)
    def resolve(self, statement: stmt.Expression) -> None:
        self.resolve(statement.expression)

    @visitor(stmt.If)
    def resolve(self, statement: stmt.If) -> None:
        self.resolve(statement.condition)
        self.resolve(statement.then_branch)
        if statement.else_branch:
            self.resolve(statement.else_branch)

    @visitor(stmt.Print)
    def resolve(self, statement: stmt.Print) -> None:
        self.resolve(statement.expression)

    @visitor(stmt.Return)
    def resolve(self, statement: stmt.Return) -> None:
        if self._current_function == _FunctionType.NONE:
            self._error_callback(statement.keyword, "Can't return from top-level code.")

        if statement.value:
            if self._current_function == _FunctionType.INITIALIZER:
                self._error_callback(
                    statement.keyword, "Can't return a value from an initializer."
                )
            self.resolve(statement.value)

    @visitor(stmt.While)
    def resolve(self, statement: stmt.While) -> None:
        self.resolve(statement.condition)
        self.resolve(statement.body)

    @visitor(stmt.Class)
    def resolve(self, statement: stmt.Class) -> None:
        enclosing_class, self._current_class = self._current_class, _ClassType.CLASS

        self._declare(statement.name)
        self._define(statement.name)

        if statement.superclass:
            if statement.name.lexeme == statement.superclass.name.lexeme:
                self._error_callback("A class can't inherit from itself.")

        if statement.superclass:
            self._current_class = _ClassType.SUBCLASS
            self.resolve(statement.superclass)

        if statement.superclass:
            self._begin_scope()
            self._scopes[-1]["super"] = True

        self._begin_scope()
        self._scopes[-1]["this"] = True

        for method in statement.methods:
            declaration = (
                _FunctionType.INITIALIZER
                if method.name.lexeme == "init"
                else _FunctionType.METHOD
            )
            self._resolve_function(method, declaration)

        self._end_scope()

        if statement.superclass:
            self._end_scope()

        self._current_class = enclosing_class

    @visitor(expr.Binary)
    def resolve(self, expression: expr.Binary) -> None:
        self.resolve(expression.left)
        self.resolve(expression.right)

    @visitor(expr.Call)
    def resolve(self, expression: expr.Call) -> None:
        self.resolve(expression.callee)

        for argument in expression.arguments:
            self.resolve(argument)

    @visitor(expr.Grouping)
    def resolve(self, expression: expr.Grouping) -> None:
        self.resolve(expression.expression)

    @visitor(expr.Literal)
    def resolve(self, expression: expr.Literal) -> None:
        pass

    @visitor(expr.Logical)
    def resolve(self, expression: expr.Logical) -> None:
        self.resolve(expression.left)
        self.resolve(expression.right)

    @visitor(expr.Unary)
    def resolve(self, expression: expr.Unary) -> None:
        self.resolve(expression.right)

    @visitor(expr.Get)
    def resolve(self, expression: expr.Get) -> None:
        self.resolve(expression.object_)

    @visitor(expr.Set)
    def resolve(self, expression: expr.Set) -> None:
        self.resolve(expression.value)
        self.resolve(expression.object_)

    @visitor(expr.This)
    def resolve(self, expression: expr.This) -> None:
        if self._current_class == _ClassType.NONE:
            self._error_callback(
                expression.keyword, "Can't use 'this' outside of a class."
            )
            return

        self._resolve_local(expression, expression.keyword)

    @visitor(expr.Super)
    def resolve(self, expression: expr.Super) -> None:
        if self._current_class == _ClassType.NONE:
            self._error_callback(
                expression.keyword, "Can't use 'super' outside of a class."
            )
        elif self._current_class != _ClassType.SUBCLASS:
            self._error_callback(
                expression.keyword, "Can't use 'super' in a class with no superclass."
            )

        self._resolve_local(expression, expression.keyword)

    def _begin_scope(self) -> None:
        self._scopes.append({})

    def _end_scope(self) -> None:
        del self._scopes[-1]

    def _declare(self, name: Token) -> None:
        if not self._scopes:
            return

        scope = self._scopes[-1]
        if name.lexeme in scope:
            self._error_callback(
                name, "Already a variable with this name in this scope."
            )
        scope[name.lexeme] = False

    def _define(self, name: Token) -> None:
        if not self._scopes:
            return
        self._scopes[-1][name.lexeme] = True

    def _resolve_local(self, expression: expr.Expr, name: Token) -> None:
        for i, scope in reversed(list(enumerate(self._scopes))):
            if name.lexeme in scope:
                self._interpreter.resolve(expression, len(self._scopes) - 1 - i)
                return

    def _resolve_function(self, function: stmt.Function, type_: _FunctionType) -> None:
        enclosing_function, self._current_function = self._current_function, type_

        self._begin_scope()
        for param in function.params:
            self._declare(param)
            self._define(param)
        self.resolve(function.body)
        self._end_scope()
        self._current_function = enclosing_function

from dataclasses import dataclass

from plox.tokens import Token


@dataclass(eq=False)
class Expr:
    pass


@dataclass(eq=False)
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass(eq=False)
class Grouping(Expr):
    expression: Expr


@dataclass(eq=False)
class Literal(Expr):
    value: object


@dataclass(eq=False)
class Unary(Expr):
    operator: Token
    right: Expr


@dataclass(eq=False)
class Variable(Expr):
    name: Token


@dataclass(eq=False)
class Assign(Expr):
    name: Token
    value: Expr


@dataclass(eq=False)
class Logical(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass(eq=False)
class Call(Expr):
    callee: Expr
    paren: Token
    arguments: list[Expr]


@dataclass(eq=False)
class Get(Expr):
    object_: Expr
    name: Token


@dataclass(eq=False)
class Set(Expr):
    object_: Expr
    name: Token
    value: Expr


@dataclass(eq=False)
class This(Expr):
    keyword: Token

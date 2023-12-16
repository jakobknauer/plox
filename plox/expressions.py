from dataclasses import dataclass

from plox.tokens import Token


@dataclass
class Expr:
    pass


@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass
class Grouping(Expr):
    expression: Expr


@dataclass
class Literal(Expr):
    value: object


@dataclass
class Unary(Expr):
    operator: Token
    right: Expr


@dataclass
class Variable(Expr):
    name: Token


@dataclass
class Assign(Expr):
    name: Token
    value: Expr

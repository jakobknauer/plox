from dataclasses import dataclass

from plox.expressions import Expr
from plox.tokens import Token


@dataclass
class Stmt:
    pass


@dataclass
class Expression(Stmt):
    expression: Expr


@dataclass
class Print(Stmt):
    expression: Expr


@dataclass
class Var(Stmt):
    name: Token
    initializer: Expr | None
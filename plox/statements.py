from dataclasses import dataclass

from plox.expressions import Expr
from plox import expressions as expr
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


@dataclass
class Block(Stmt):
    statements: list[Stmt]


@dataclass
class If(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt | None


@dataclass
class While(Stmt):
    condition: Expr
    body: Stmt


@dataclass
class Function(Stmt):
    name: Token
    params: list[Token]
    body: list[Stmt]


@dataclass
class Return(Stmt):
    keyword: Token
    value: Expr | None


@dataclass
class Class(Stmt):
    name: Token
    superclass: expr.Variable | None
    methods: list[Function]

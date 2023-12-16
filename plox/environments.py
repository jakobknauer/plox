from typing import Self

import plox.interpreting
from plox.tokens import Token


class Environment:
    def __init__(self, enclosing: Self | None = None):
        self._values: dict[str, object] = {}
        self._enclosing = enclosing

    def define(self, name: str, value: object) -> None:
        self._values[name] = value

    def assign(self, name: Token, value: object) -> None:
        if name.lexeme in self._values:
            self._values[name.lexeme] = value
            return

        if self._enclosing:
            self._enclosing.assign(name, value)
            return

        raise plox.interpreting.PloxRuntimeError(
            name, f"Undefined variable '{name.lexeme}'."
        )

    def assign_at(self, distance: int, name: Token, value: object) -> None:
        self._ancestor(distance)._values[name.lexeme] = value

    def get(self, name: Token) -> object:
        if name.lexeme in self._values:
            return self._values[name.lexeme]

        if self._enclosing:
            return self._enclosing.get(name)

        raise plox.interpreting.PloxRuntimeError(
            name, f"Undefined variable '{name.lexeme}'."
        )

    def get_at(self, distance: int, name: str) -> object:
        return self._ancestor(distance)._values.get(name)

    def _ancestor(self, distance: int) -> Self:
        environment = self
        for _ in range(distance):
            environment = environment._enclosing
        return environment

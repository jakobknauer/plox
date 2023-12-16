import plox.interpreting
from plox.tokens import Token


class Environment:
    def __init__(self):
        self._values = {}

    def define(self, name: str, value: object) -> None:
        self._values[name] = value

    def assign(self, name: Token, value: object) -> None:
        if name.lexeme in self._values:
            self._values[name.lexeme] = value
            return

        raise plox.interpreting.InterpreterError(
            name, f"Undefined variable '{name.lexeme}'."
        )

    def get(self, name: Token) -> object:
        if name.lexeme in self._values:
            return self._values[name.lexeme]

        raise plox.interpreting.InterpreterError(
            name, f"Undefined variable '{name.lexeme}'."
        )

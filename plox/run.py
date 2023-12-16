#!/usr/bin/env python3

import sys

from plox.interpreting import Interpreter, PloxRuntimeError
from plox.parsing import Parser
from plox.resolving import Resolver
from plox.scanning import Scanner
from plox.tokens import Token, TokenType
from plox.standard_library import STANDARD_LIBRARY


def main():
    if len(sys.argv) > 2:
        print("Usage: plox [script]")
        sys.exit(64)
    elif len(sys.argv) == 2:
        Application().run_file(sys.argv[1])
    else:
        Application().run_prompt()


class Application:
    def __init__(self):
        self._had_error = False
        self._had_runtime_error = False
        self._interpreter = Interpreter(globals_=STANDARD_LIBRARY, error_callback=self._interpreter_error)

    def run_file(self, path: str):
        with open(path) as file:
            source = file.read()

        self.run(source)

        if self._had_error:
            sys.exit(65)
        if self._had_runtime_error:
            sys.exit(70)

    def run_prompt(self):
        while True:
            line = input("> ")

            if not line:
                break

            self.run(line)
            self._had_error = False

    def run(self, source: str) -> None:
        scanner = Scanner(source, self._error)
        tokens = scanner.scan_tokens()

        parser = Parser(tokens, self._error2)
        statements = parser.parse()

        if self._had_error:
            return

        resolver = Resolver(self._interpreter, self._error2)
        resolver.resolve(statements)

        if self._had_error:
            return

        self._interpreter.interpret(statements)

    def _error(self, line: int, message: str):
        self._report(line, "", message)

    def _error2(self, token: Token, message: str):
        if token.type == TokenType.EOF:
            self._report(token.line, " at end", message)
        else:
            self._report(token.line, f" at '{token.lexeme}'", message)

    def _interpreter_error(self, ie: PloxRuntimeError):
        print(f"{ie.message}\n[line {ie.token.line}]")
        self._had_runtime_error = True

    def _report(self, line: int, where: str, message: str):
        print(f"[line {line}] Error{where}: {message}")
        self._had_error = True


if __name__ == "__main__":
    main()

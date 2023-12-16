#!/usr/bin/env python3

import sys

from plox.scanning import Scanner
from plox.parsing import Parser
from plox.interpreting import Interpreter, InterpreterError
from plox.token import Token, TokenType


had_error = False
had_interpreter_error = False


def main():
    if len(sys.argv) > 2:
        print("Usage: plox [script]")
        sys.exit(64)
    elif len(sys.argv) == 2:
        run_file(sys.argv[1])
    else:
        run_prompt()


def run_file(path: str):
    with open(path) as file:
        source = file.read()

    run(source)

    if had_error:
        sys.exit(65)
    if had_interpreter_error:
        sys.exit(70)


def run_prompt():
    global had_error

    while True:
        line = input("> ")

        if not line:
            break

        run(line)
        had_error = False


def run(source: str):
    scanner = Scanner(source, error)
    tokens = scanner.scan_tokens()

    parser = Parser(tokens, error2)
    expression = parser.parse()

    if had_error:
        return

    assert expression is not None
    Interpreter(interpreter_error).interpret(expression)


def error(line: int, message: str):
    report(line, "", message)


def error2(token: Token, message: str):
    if token.type == TokenType.EOF:
        report(token.line, " at end", message)
    else:
        report(token.line, f" at '{token.lexeme}'", message)


def interpreter_error(ie: InterpreterError):
    global had_interpreter_error
    print(f"{ie.message}\n[line {ie.token.line}]")
    had_interpreter_error = True


def report(line: int, where: str, message: str):
    global had_error
    print(f"[line {line}] Error{where}: {message}")
    had_error = True


if __name__ == "__main__":
    main()

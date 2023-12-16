import math
import time

from plox.environments import Environment
from plox.interpreting import (
    AnonymousCallable,
    Interpreter,
    LoxClass,
    AnonymousLoxFunction,
    LoxInstance,
)


def _to_str(interpreter: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], (str, float)):
        raise Exception(
            "Built-in function 'str' expects arguments of type string or float."
        )
    return str(arguments[0])


def _to_float(interpreter: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], (str, float)):
        raise Exception(
            "Built-in function 'float' expects arguments of type string or float."
        )
    return float(arguments[0])


def _floor(interpreter: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise Exception("Built-in function 'floor' expects arguments of type float.")
    return float(math.floor(arguments[0]))


def _ceil(interpreter: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise Exception("Built-in function 'ceil' expects arguments of type float.")
    return float(math.ceil(arguments[0]))


def _sin(interpreter: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise Exception("Built-in function 'sin' expects arguments of type float.")
    return math.sin(arguments[0])


def _cos(interpreter: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise Exception("Built-in function 'cos' expects arguments of type float.")
    return math.cos(arguments[0])


def _exp(interpreter: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise Exception("Built-in function 'exp' expects arguments of type float.")
    return math.exp(arguments[0])


def _log(interpreter: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise Exception("Built-in function 'log' expects arguments of type float.")
    return math.log(arguments[0])


_functions = [
    ("clock", lambda interpreter, arguments: (time.time() / 1000.0), 0),
    ("input", lambda interpreter, arguments: input(), 0),
    ("str", _to_str, 1),
    ("float", _to_float, 1),
    ("floor", _floor, 1),
    ("ceil", _ceil, 1),
    ("sin", _sin, 1),
    ("cos", _cos, 1),
    ("exp", _exp, 1),
    ("log", _log, 1),
]


STANDARD_LIBRARY = Environment()

for identifier, callable_, arity in _functions:
    STANDARD_LIBRARY.define(identifier, AnonymousCallable(callable_, arity))


def _lox_list_init(interpreter: Interpreter, environment: Environment):
    instance = environment.get_by_name("this")
    assert isinstance(instance, LoxInstance)
    instance._items = []


_lox_list_init_func = AnonymousLoxFunction(
    callable_=_lox_list_init,
    params=[],
    closure=Environment(),
)


def _lox_list_append(interpreter: Interpreter, environment: Environment, item: object):
    instance = environment.get_by_name("this")
    assert isinstance(instance, LoxInstance)
    instance._items.append(item)


_lox_list_append_func = AnonymousLoxFunction(
    callable_=_lox_list_append,
    params=["item"],
    closure=Environment(),
)


def _lox_list_at(interpreter: Interpreter, environment: Environment, index: object):
    instance = environment.get_by_name("this")
    assert isinstance(instance, LoxInstance)
    assert isinstance(index, float)
    return instance._items[int(index)]


_lox_list_at_func = AnonymousLoxFunction(
    callable_=_lox_list_at,
    params=["index"],
    closure=Environment(),
)

_lox_list = LoxClass(
    name="list",
    superclass=None,
    methods={
        "init": _lox_list_init_func,
        "append": _lox_list_append_func,
        "at": _lox_list_at_func,
    },
)

STANDARD_LIBRARY.define("list", _lox_list)

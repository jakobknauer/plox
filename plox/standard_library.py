import math
import time
import inspect

from plox.environments import Environment
from plox.interpreting import (
    AnonymousCallable,
    AnonymousLoxFunction,
    Interpreter,
    LoxCallable,
    LoxClass,
    LoxInstance,
)


def _to_str(_: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], (str, float)):
        raise ValueError(
            "Built-in function 'str' expects arguments of type string or float."
        )
    return str(arguments[0])


def _to_float(_: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], (str, float)):
        raise ValueError(
            "Built-in function 'float' expects arguments of type string or float."
        )
    return float(arguments[0])


def _floor(_: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise ValueError("Built-in function 'floor' expects arguments of type float.")
    return float(math.floor(arguments[0]))


def _ceil(_: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise ValueError("Built-in function 'ceil' expects arguments of type float.")
    return float(math.ceil(arguments[0]))


def _sin(_: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise ValueError("Built-in function 'sin' expects arguments of type float.")
    return math.sin(arguments[0])


def _cos(_: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise ValueError("Built-in function 'cos' expects arguments of type float.")
    return math.cos(arguments[0])


def _exp(_: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise ValueError("Built-in function 'exp' expects arguments of type float.")
    return math.exp(arguments[0])


def _log(_: Interpreter, arguments: list[object]) -> object:
    if not isinstance(arguments[0], float):
        raise ValueError("Built-in function 'log' expects arguments of type float.")
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


def lox_function(function) -> AnonymousLoxFunction:
    parameters = inspect.getfullargspec(function).args
    return AnonymousLoxFunction(function, parameters[2:], STANDARD_LIBRARY)


@lox_function
def _lox_list_init(_: Interpreter, environment: Environment):
    instance = environment.get_by_name("this")
    assert isinstance(instance, LoxInstance)
    instance.metafields["items"] = []


@lox_function
def _lox_list_append(_: Interpreter, environment: Environment, item: object):
    instance = environment.get_by_name("this")
    assert isinstance(instance, LoxInstance)
    items = instance.metafields["items"]
    assert isinstance(items, list)
    items.append(item)


@lox_function
def _lox_list_at(_: Interpreter, environment: Environment, index: object):
    instance = environment.get_by_name("this")
    assert isinstance(instance, LoxInstance)
    assert isinstance(index, float)
    items = instance.metafields["items"]
    assert isinstance(items, list)
    return items[int(index)]


@lox_function
def _lox_list_size(_: Interpreter, environment: Environment):
    instance = environment.get_by_name("this")
    assert isinstance(instance, LoxInstance)
    items = instance.metafields["items"]
    assert isinstance(items, list)
    return float(len(items))


@lox_function
def _lox_list_iterate(interpreter: Interpreter, environment: Environment):
    instance = environment.get_by_name("this")
    assert isinstance(instance, LoxInstance)
    iterator_class = environment.get_by_name("ListIterator")
    assert isinstance(iterator_class, LoxClass)
    iterator = LoxInstance(iterator_class)
    iterator_initializer = iterator_class.find_method("init")
    assert isinstance(iterator_initializer, LoxCallable)
    iterator_initializer.bind(iterator).call(interpreter, [instance])
    return iterator


_lox_list = LoxClass(
    name="List",
    superclass=None,
    methods={
        "init": _lox_list_init,
        "append": _lox_list_append,
        "at": _lox_list_at,
        "size": _lox_list_size,
        "iterate": _lox_list_iterate,
    },
)
STANDARD_LIBRARY.define("List", _lox_list)

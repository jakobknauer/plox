# Plox

Plox is an interpreter for the Lox programming language described in the book [Crafting Interpreters](https://craftinginterpreters.com/) by Robert Nystrom.


## Features

The program is a relatively direct translation of the tree-walk interpreter developed in the first part of the book from Java to Python, with a number of extensions:

#### Standard Library

We introduce a standard library that defines a number of functions and classes that are added to the global scope before executing user programs.
Part of the standard library is [implemented in Python](plox/standard_library.py), and part is implemented [directly in Lox](plox/standard_library.lox). 
The standard library includes functions for conversion between strings and numbers, a number of mathematical functions such as `floor` or trigonometric functions, the `input` function for prompting user input, as well as lists, linked lists, and ranges (see below).

#### List Syntax

As a part of the of the standard library, we add a `List` class implemented using Python's `list`.
As a more compact way to create lists, we add list syntax similar to Python: `var myList = [1, 2, 3]`.

#### Foreach Loops and Iterators

We add `foreach` loops to the language that, similar to `for` loops, are converted to `while` loops upon parsing. The newly introduced syntax

    foreach(i; list)
    {
        print i;
    }

is equivalent to:

    var it = list.iterate();
    while(it.hasItems())
    {
        var i = it.get();
        print i;
        it.move();
    }

That is, the object `list` must have a method `iterate` that returns an *iterator*, which is an object implementing methods called `hasItems`, `get`, and `move`.
The standard library implements iterators for `List`, `LinkedList` and `Range`.
The latter is a lazy iterable over an evenly spaced list of integers, similar to Python's `range`.


## Usage

Plox has no dependencies beyond the Python standard library.

Run in interactive mode:

    python -m plox.run

Run a Lox source file:

    python -m plox.run example.lox

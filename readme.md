# A minimal Python interpreter in Python with runtime AST definition and edit-and-continue

# Running

python_terp depends on [pymetaterp](https://github.com/asrp/pymetaterp).

    pip install -r requirements
    python test/python_repl.py

At the prompt, first run

    p>> simport simple_ast

to use advanced features such as the `for` statement or boolean `and`. See [lib/simple_ast.py](lib/simple_ast.py). Then type in commands as usual.

    p>> x = 3
    p>> print x
    3
    p>> [x*x for x in [1,2,3,4,5] if x%2 == 1]
    [1, 9, 25]

To run source from a file

    python test/python_terp_test.py test/python_terp_ex.py

See [test/python_terp_ex.py](test/python_terp_ex.py) and [test/parse_ex.py](test/parse_ex.py) for some things the current version can handle.

# Highlights

## Runtime AST node semantics

This allows defining, modifying (by redefining functions) and debugging the semantics of if statements, for statements and others at run time. For example, `for_stmt` is a function in [lib/simple_ast.py](lib/simple_ast.py) defined as

    def for_stmt(index_var, iterable, block, else_block=None):
        iterator = iter(evaluate(iterable))
        while_true:
            try:
                assignment(index_var, iterator.next())
            except StopIteration:
                return
            __caller__['__continue__'] = __continue__
            __caller__['__break__'] = __break__
            evaluate(block)

See [lib/boot.py](lib/boot.py), [lib/globals.py](lib/globals.py) and [lib/simple_ast.py](lib/simple_ast.py) for more examples.

## Edit and continue

Examine [test/buggy_ex.py](test/buggy_ex.py) and run

    python -i test/python_terp_test.py test/buggy_ex.py

Get an error

    i is 1
    1
    i is 2
    3
    i is 3
    6
    i is 4
    Traceback (most recent call last):
      File "test/python_terp_test.py", line 35, in <module>
        output = pyterp.run(pyi_tree, filename=filename)
      File "./python_terp/python_terp.py", line 198, in run
        return self._run(root)
      File "./python_terp/python_terp.py", line 206, in _run
        self.one_step()
      File "./python_terp/python_terp.py", line 256, in one_step
        raise output
    KeyError: 'ii'
    >>>

Do not exit the CPython interpreter! Examine the stack

    >>> pyterp.st()
    [...]
    34 In file lib/simple_ast.py line 142 function aug_assign (evaluate)
        assignment(names, __binary__(operation[0][0], evaluate(names), evaluate(values)))
    35 In file test/buggy_ex.py line 7 function __main__ (NAME)
            total += ii

find the error

    >>> pyterp.last_stack[-1].root.pprint()
    NAME
      str 'ii'

fix it

    >>> pyterp.last_stack[-1].root[0] = 'i'

and continue execution

    >>> pyterp.continue_()
    Printing total
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "./python_terp/python_terp.py", line 226, in continue_
        self.one_step()
      File "./python_terp/python_terp.py", line 256, in one_step
        raise output
    KeyError: 'tootal'

fix the second bug and continue

    >>> pyterp.last_stack[-1].root[0] = 'total'
    >>> pyterp.continue_()
    10
    i is 5
    Printing total
    15
    Loop complete

This would make it easier to debug long computations without explicit pickling or debug rare bugs such as requests to a webserver.

## Low complexity

Current line counts are

    Parsing
       48 pymetaterp/boot_grammar.py
      177 pymetaterp/boot_stackless.py
      233 pymetaterp/boot_tree.py
       69 pymetaterp/util.py
      171 pymetaterp/python_grammar.py
      182 pymetaterp/python.py
    -------------------------
      880 total

    Running
      629 python_terp/python_terp.py
       76 python_terp/debugger.py
    -------------------------
      705 total

    Library
      198 lib/simple_ast.py
       52 lib/global.py
      422 lib/objects.py
    -------------------------
      672 total

## CPython interoperability

To access CPython objects, just make them available in the namespace. For example adding

    pyterp = python_terp.Interpreter(pyi)
    import foo
    pyterp.scope['foo'] = foo

before running `pyterp.run`  will make `foo` available as a global variable.

## Python compatibility

python_terp is intended to make language modification to Python easier to preview changes more quickly and is not intended for full CPython compatibility. However, a large subset of Python is already included. In particular, enough to run the first stage of its parser.

    python test/python_terp_test.py test/parse_ex.py

# Caveats

- Slow, as expected from running an interpreter inside another interpreter.
- Still uses quite a bit of CPython features (so its not easy to port to another language) such as dicts and boolean operations.

# Todo

Pull requests welcome.

- Reduce dependency on Python dict and use objects.Dict. Troublesome for now because all scope depend on Python dicts.
- Add nicer interface for edit and continue (diff the two versions of the source).
- Add more AST node semantics like `yield` (make just take a portion of the call stack and pass it around).
- Runtime grammar modifications so new AST nodes can be added (just need to chain existing tools together).
- Document internals some more.

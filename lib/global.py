def len(iterable):
    return iterable.__len__()

def str(var):
    return var.__str__()

def repr(var):
    return var.__repr__()

def iter(iterable):
    if type(iterable).__name__ == "str":
        return _iter(iterable)
    return iterable.__iter__()

def hash(var):
    return var.__hash__()

def bool(var):
    return var.__nonzero__()

def getattr(instance, key, default=None):
    if type(instance) != Instance:
        return default
    return instance.getattr(key, default)

def hasattr(instance, key):
    if type(instance) != Instance:
        return False
    return instance.hasattr(key)

# Should be made into a generator?
def enumerate(iterable):
    result = []
    i = 0
    for item in iterable:
        result.append((i, item))
        i += 1
    return result

def pglobals():
    return __caller__

def peval(expr, globals=None, locals=None):
    print "evaluating", expr
    if globals is None:
        globals = __caller__
    if locals is None:
        scope = globals
    if locals is not None:
        scope = Scope(locals)
        scope['__parent__'] = globals
    return evaluate(ast(expr), scope)

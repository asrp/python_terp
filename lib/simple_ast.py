def break_stmt():
    raise __caller__['__break__']

def continue_stmt():
    raise __caller__['__continue__']

def simple_for_stmt(index_var, iterable, block):
    index = 0
    iterable = evaluate(iterable)
    length = len(iterable)
    while_true:
        assignment(index_var, iterable[index])
        evaluate(block)
        index = index + 1
        if index == length:
            return None

def print_stmt(node):
    simple_for child in node:
        _print(str(evaluate(child)))
    _print("\n")

def parents(node):
    if len(node.node) == 0:
        return None
    return evaluate(node[0])

def classdef(name, parents, block):
    class_name = get_name(name)
    params = {"__parents__": evaluate(parents),
              "__parent__": __caller__,
              "__type__": "Class",
              "__dict__": {"__name__": class_name,
                           "__module__": __caller__['__module__'],
                           "__parent__": __caller__,
                           "__path__": (__caller__['__module__'], class_name)}}
    class_dict = Instance("Class", params)
    __caller__[class_name] = class_dict
    evaluate(block, class_dict['__dict__'])

def reload_module(module):
    load_module(module.__module__)

def and_test(param1, param2):
    if evaluate(param1):
        if evaluate(param2):
            return True
    return False

def or_test(param1, param2):
    if evaluate(param1):
        return True
    if evaluate(param2):
        return True
    return False

def not_test(param):
    return __unary__("not", param)

def unpack_assign(names, values):
    # Problem: if_stmt calls regular assign!
    if names.node.name not in ["testlist", "listmaker", "exprlist"]:
        return assignment(names, values)
    if len(names) == 1 and len(values) == 1:
        return unpack_assign(names[0], values[0])
    if len(names) == 1:
        return unpack_assign(names[0], values)
    if len(values) == 1:
        return unpack_assign(names, values[0])
    if len(names) != len(values):
        bpoint()
    simple_for name_value in zip(names, values):
        unpack_assign(name_value[0], name_value[1])

def gen_true():
    return True

def if_stmt(*condition_and_blocks):
    simple_for condition, block in condition_and_blocks:
        if evaluate(condition):
            return evaluate(block)

def try_stmt(block, handling):
    error = eval_error(block)
    if error is not None:
        simple_for clause, except_block in handling:
            if len(clause) == 0 or type(error) == evaluate(clause[0]):
                evaluate(except_block)
                # Should also handle finally...
                return
        raise error

def for_stmt(index_var, iterable, block, else_block=None):
    iterator = iter(evaluate(iterable))
    while_true:
        try:
            assignment(index_var, iterator.next())
        except StopIteration:
            #Variable not even set if not passed
            #if else_block is not None:
            #    evaluate(else_block)
            return
        __caller__['__continue__'] = __continue__
        __caller__['__break__'] = __break__
        evaluate(block)

def listcomp(expression, *values):
    __caller__["__list_comp_result"] = []
    __caller__["__expression__"] = expression
    root = `__list_comp_result.append(evaluate(__expression__))`.node
    # Skips first value which is the expression
    for node in reversed(values):
        node = node.node
        if node.name == "list_for":
            root = Node("for_stmt", node + [root])
            root.pos=node.pos
        if node.name == "list_if":
            root = Node("single_if", node + [root])
            root.pos=node.pos
    evaluate(root, __caller__)
    return __caller__["__list_comp_result"]

listcomp_arg = listcomp

def dictcomp(key_expr, value_expr, *loops):
    __caller__["__dict_comp_result"] = {}
    __caller__["__key__"] = key_expr
    __caller__["__value__"] = value_expr
    root = `__dict_comp_result[evaluate(__key__)] = evaluate(__value__)`.node
    # Skips first value which is the expression
    for node in reversed(loops):
        node = node.node
        if node.name == "list_for":
            root = Node("for_stmt", node + [root])
            root.pos=node.pos
        if node.name == "list_if":
            root = Node("single_if", node + [root])
            root.pos=node.pos
    evaluate(root, __caller__)
    return __caller__["__dict_comp_result"]

def aug_assign(names, operation, values):
    assignment(names, __binary__(operation[0][0], evaluate(names), evaluate(values)))

def while_stmt(condition, block, else_block=None):
    while_true:
        if not evaluate(condition):
            return None
        evaluate(block)
    if else_block is not None:
        evaluate(else_block)

def del_stmt(obj_and_key):
    evaluate(obj_and_key[0]).__delitem__(evaluate(obj_and_key[1]))

def start(value=0):
    return value

def stop(value=None):
    return value

def slice(start, stop, step=None):
    return _slice(start, stop, step)

def test(expr, cond, else_value):
    if evaluate(cond):
        return evaluate(expr)
    return evaluate(else_value)

def assert_stmt(condition):
    if evaluate(condition):
        return
    raise AssertionError()

def import_from(module, names):
    import_names(module)
    module_scope = modules[get_name(module)]
    if names.node.name == 'import_all':
        simple_for name in module_scope.keys():
            if name not in ['__module__', '__source__', '__parent__']:
                __caller__[name] = module_scope[name]
        return
    for name in names:
        name = name[0]
        __caller__[name] = module_scope[name]

def import_names(module_name):
    if module_name.node.name == "NAME":
        module_name_s = get_name(module_name)
        local_name = module_name_s
    if module_name.node.name == "dotted_as_name":
        module_name_s = get_name(module_name[0])
        local_name = get_name(module_name[1])

    # var_name = module_name if var_name is None else get_name(var_name)
    if module_name_s not in modules:
        load_module(module_name_s)
    __caller__[local_name] = modules[module_name_s]

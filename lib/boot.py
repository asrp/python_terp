def __getitem__(var, param):
    return var.__getitem__(param)

def __setitem__(var, param, value):
    return evaluate(var).__setitem__(evaluate(param), value)

def subscriptlist(subscript):
    return subscript

def subscript(value):
    return value

def pair(value1, value2):
    return (value1, value2)

def single_if(condition, block):
    if_true = {True: block, False: `pass`}
    evaluate(if_true[bool(evaluate(condition))])

# import single name: no dots, no as, no from
def simport_stmt(module_name):
    module_name = get_name(module_name)
    # var_name = module_name if var_name is None else get_name(var_name)
    if module_name not in modules:
        load_module(module_name)
    __caller__[module_name] = modules[module_name]

# Also the reload builtin
def load_module(module_name):
    filename = "lib/" + module_name + ".py"
    node = ast(filename, True)
    if node.name not in ["And", "file_input", "suite"]:
        pos = node.pos
        node = Node("suite", [node])
        node.pos = pos
    # Should set up __doc__, __file__, __name__, __package__, __path__
    if module_name in modules:
        module = modules[module_name]
        module.clear()
        module['__module__'] = module_name
        module['__source__'] = filename
        module['__parent__'] = modules['boot']
        # Loses parent pointers. Should only mark them for deletion once nothing else points to them.
        #del modules[module_name][:]
    if module_name not in modules:
        # Should parent be the root scope?
        module = Scope({'__module__': module_name, '__source__': module_name,
                        '__parent__': modules['boot']})
        modules[module_name] = module
        sources[module_name] = tag_file("lib/" + module_name + ".py")
    evaluate(node, module)

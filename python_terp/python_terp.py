from pymetaterp.util import Node, MatchError
import operator, __builtin__
from bisect import bisect_left as bisect
import sys
from pdb import set_trace as bp
import ctypes
import debugger

def c_array(value):
    return (ctypes.py_object * value)()

class Continuation(Exception):
    pass

class Eval(Exception):
    pass

class Instance(dict):
    def __init__(self, name, value=None):
        dict.__init__(self, value if value is not None else {"__dict__":{}})
        self.name = name

    def getattr(self, key, default):
        return self['__dict__'].get(key, default)

    def hasattr(self, key):
        return key in self['__dict__']

class Name(str):
    pass

class Source(object):
    pass

def tag_file(filename, lines=None):
    node = Source()
    node.filename = filename
    node.lines = open(node.filename).readlines() if lines is None else lines
    line_len = [len(l) for l in node.lines]
    node.line_num = [sum(line_len[:i+1]) for i in xrange(len(line_len))]
    return node

class Frame:
    def __init__(self, root, scope):
        self.root = root
        self.calls = []
        self.scope = scope
        self.outputs = []
        self.step = "new"

    def __repr__(self):
        return repr(self.calls)

class Thunk(object):
    def __init__(self, node, scope):
        self.node = node
        self.scope = scope
        self.name = "thaw"
        self.pos = self.node.pos

    def __iter__(self):
        return iter([Thunk(child, self.scope) for child in self.node])

    def __getitem__(self, key):
        child = self.node[key]
        return Thunk(child, self.scope) if type(child) == Node else child

    def __len__(self):
        return self.node.__len__()

def get_name(node):
    if type(node) == Thunk:
        node, scope = node.node, node.scope
    assert(len(node) == 1 and type(node[0]) == str)
    return Name(node[0])

def raised(value, _raised=True):
    value._raised = _raised
    return value

def constant(value=""):
    return value

def _print(s):
    if s == "\n":
        print
    else:
        print s,

def bpoint(value=None):
    bp()

def __unary__(operation, param):
    ops = {'not': lambda x: not x,
           '+': lambda x: x,
           '-': lambda x: -x}
    return ops[operation](param)

def __binary__(operation, param1, param2):
    ops = {'+': operator.add,
           '-': operator.sub,
           '*': operator.mul,
           '/': operator.div,
           '%': operator.mod,
           '^': operator.xor,
           '>': operator.gt,
           '<': operator.lt,
           '>=': operator.ge,
           '<=': operator.le,
           '==': operator.eq,
           '!=': operator.ne,
           'in': lambda x, y: x in y,
           'not in': lambda x, y: x not in y,
           'and': operator.and_,
           'or': operator.or_,
           'is': lambda x, y: x is y,
           'is not': lambda x, y: x is not y}
    return ops[operation](param1, param2)

def no_op(*args):
    pass

def lookup(name, scope):
    if type(name) in [Name, str]:
        name = [name]
    while scope is not None:
        try:
            value = scope
            for part in name:
                value = value[part]
            return value
        except KeyError:
            scope = scope["__parent__"]
    raise

# Using dict because attribs can clash with python attributes!
class Scope(dict):
    pass

node_calls = ["file_input", "suite", "And", "STRINGS", "thaw", "print_stmt", "_print", "Function", "parents"]
no_thunk_calls = ['break_stmt', 'continue_stmt', 'not_test', 'slice', 'start', 'stop']
handles_errors = ["__call__", "while_true", "evaluate", "eval_error"]
native_functions = ["function", "builtin_function_or_method", "method-wrapper",
                    "method_descriptor", "instancemethod", "wrapper_descriptor",
                    "type"]

class Interpreter:
    def __init__(self, parser=None):
        self.parser = parser
        self.debug = False
        self.debugger = debugger.Debugger()
        self.repl_count = 0
        self.root_scope = self.scope = Scope()
        self.modules = {"boot": self.root_scope}
        self.sources = {"boot": ""}
        self.scope["__module__"] = "boot"
        self.scope["__func__"] = None
        self.scope["__func_name__"] = "__main__"
        self.scope["__parent__"] = None
        self.scope["None"] = None
        self.scope["_slice"] = slice
        self.scope["_iter"] = iter
        self.scope["inf"] = float('inf')
        self.scope["int"] = int
        self.scope["cpy_str"] = str
        self.scope["list_append"] = list.append

        for varname in ["Exception", "True", "False", "IndexError", "StopIteration", "AssertionError",
                        "bool", "xrange", "type", "zip", "reversed"]:
            self.scope[varname] = getattr(__builtin__, varname)

        for varname in ["Instance", "Name", "Node", "Thunk", "Scope",
                        "self.lookup", "_print", "bpoint",
                        "no_op", "self.evaluate", "self.eval_error",
                        "get_name", "__binary__", "__unary__",
                        "self.modules", "self.sources", "self.ast", "tag_file",
                        "self.assignment", "c_array"]:
            if "." in varname:
                name = varname.split(".")[-1]
                self.scope[name] = getattr(self, name)
            else:
                self.scope[varname] = globals()[varname]

        self.functions = {"NUMBER": constant, "STRING": constant,
                          "thaw": constant,
                          "EMPTY_LINE": no_op, "comment": no_op, "pass_stmt": no_op,
                          "__getattr__": self.getattrib,}

    def run(self, root, filename="<console>", modname=None, lines=None):
        modname = filename if modname is None else modname
        if modname in self.modules:
            self.scope = self.modules[modname]
        else:
            self.scope = self.modules[modname] = Scope(__parent__=self.root_scope)
        self.scope['__source__'] = filename
        self.scope['__module__'] = modname
        self.sources[filename] = tag_file(filename, lines)
        return self._run(root)

    def _run(self, root):
        self.stack = [Frame(root, self.scope)]
        self.last_stack = []
        self.call_stack = []
        self.last_call_stack = []
        while self.stack:
            self.one_step()
        return self.output

    def continue_(self, stack=None, call_stack=None, n=1):
        """ Continue after error."""
        stack = self.last_stack if stack is None else stack
        call_stack = self.last_call_stack if call_stack is None else call_stack
        self.stack = stack[:-n]
        self.call_stack = call_stack[:]
        # Need to also undo things like step changes!
        # Alters input stack...
        for frame in self.stack:
            frame.outputs.pop()
        #self.stack[-1].step = "new"
        self.last_stack = []
        self.last_call_stack = []
        self.scope = self.last_scope
        root = self.stack[-1].calls[len(self.stack[-1].outputs)]
        self.stack.append(Frame(root, self.scope))
        while self.stack:
            self.one_step()

    def save():
        self.saved_stack = self.last_stack[:]
        self.saved_call_stack = self.last_call_stack[:]

    def pm(self):
        self.debug = True
        self.debugger.waitlen = None
        self.continue_()

    def one_step(self):
        try:
            output = self.run_step()
        except Eval:
            output = Eval
        if output is Eval:
            root = self.stack[-1].calls[len(self.stack[-1].outputs)]
            self.last_stack = []
            self.stack.append(Frame(root, self.scope))
            self.last_scope = self.scope
        else:
            if self.debug:
                self.debugger.callback(self, True, output)
                #print " "*len(self.stack), "-->", repr(output)[:30]
            self.last_stack.insert(0, self.stack.pop())
            if not self.stack:
                self.output = output
                if getattr(output, "_raised", False):
                    # !import pdb; pdb.post_mortem(output.traceback[-1])
                    raise output
                else:
                    return output
            self.stack[-1].outputs.append(output)

    def run_step(self):
        self.frame = self.stack[-1]
        self.root = self.frame.root
        self.name = self.root.name
        self.pos = self.root.pos
        if self.name != "__call__":
            if self.debug:
                self.debugger.callback(self)
                #print " "*len(self.stack), self.name, self.frame.step, str(self.frame.outputs[-1])[:20] if self.frame.outputs else ""
        if self.frame.step != "new":
            self.outputs = self.frame.outputs
            self.output = self.outputs[-1] if self.outputs else None
            self.is_error = getattr(self.output, "_raised", False)
            self.finished = len(self.outputs) == len(self.frame.calls)
            if self.is_error:
                if self.name not in handles_errors:
                    return self.output
            elif not self.finished:
                return Eval
        if self.name in self.modules['boot'] and type(self.modules['boot'][self.name]) == Node and self.modules['boot'][self.name].name == "Function":
            child = self.root if self.name not in ['single_if', 'simport_stmt',
                                                   'import_names']\
                    else Thunk(self.root, self.scope)
            child = [child] if self.name in node_calls else child
            return self.out(["__call__", self.modules['boot'][self.name], child, True],
                            tree=True)
        elif self.name in self.modules.get('simple_ast', []):
            child = self.root if self.name in no_thunk_calls\
                    else Thunk(self.root, self.scope)
            child = [child] if self.name in node_calls else child
            return self.out(["__call__", self.modules['simple_ast'][self.name], child, True],
                            tree=True)
        elif self.name in self.functions:
            f = self.functions[self.name]
            return f(self.root) if self.name in node_calls else f(*self.root)
        else:
            f = getattr(self, self.name, None)
        if f:
            try:
                output = f(self.root) if self.name in node_calls else f(*self.root)
            except Eval:
                return Eval
            except Exception as e:
                output = raised(e)
                output.traceback = sys.exc_info()
            return output
        not_yet_implemented

    def node_tree(self, lst):
        if type(lst) != list or type(lst[0]) != str:
            return lst
        return Node(lst[0], (self.node_tree(c) for c in lst[1:]), pos=self.pos)

    def out(self, nodes, step="next", tree=False):
        if self.frame.step == "new":
            return self.calls(nodes, step, tree)
        else:
            return self.output

    def outs(self, nodes, step="next", tree=False):
        if self.frame.step == "new":
            return self.calls(nodes, step, tree)
        else:
            return self.outputs

    def calls(self, nodes, step="next", tree=False):
        if not nodes:
            return []
        if tree:
            nodes = [self.node_tree(nodes)]
        if not self.frame.calls:
            self.frame.calls = nodes
        else:
            self.frame.calls.extend(nodes)
        self.frame.step = step
        raise Eval()

    def regular_assign(self, name, value):
        if self.is_error:
            return self.output
        if self.frame.step in ["new", "next"]:
            value = self.out([value])
            self.calls([Node("assignment", [name, value], pos=self.pos)],
                       step="finished")

    def assignment(self, name, value):
        """ Assign a single variable to a single already evaluated value. """
        if self.is_error:
            return self.output
        elif name.name == "__getattr__" or name.name == "thaw" and name.node.name == "__getattr__":
            return self.setattrib(name[0], name[1], value)
        elif name.name == "__getitem__" or name.name == "thaw" and name.node.name == "__getitem__":
            if name.name != "thaw":
                name = self.thunk(name)
            self.out(['__call__', self.modules['boot']['__setitem__'],
                                  [name[0], name[1], value], True, True], tree=True)
        elif name.name == "thaw" and name.node.name == "NAME":
            name.scope[Name(name.node[0])] = value
        elif name.name == "NAME":
            self.scope[Name(name[0])] = value
        else:
            thunk = self.thunk(name) if type(name) != Thunk else name
            assert(thunk.node.name in ["testlist", "listmaker", "exprlist"])
            self.out(["__call__", self.modules["simple_ast"]["unpack_assign"],
                                  [thunk, value], True, True], tree=True)

    def file_input(self, node):
        outputs = self.outs(node)
        return outputs if node.name in ["And", "subscript", "file_output"]\
            else None

    And = suite = STRINGS = file_input

    def NAME(self, aname):
        return self.lookup(Name(aname))

    def lookup(self, name):
        return lookup(name, self.scope)

    def __binary__(self, operation, param1, param2):
        param1, param2 = self.outs([param1, param2])
        return __binary__(operation, param1, param2)

    def factor(self, operation, param):
        return __unary__(operation, self.out([param]))

    def while_true(self, block):
        if self.frame.step == "new":
            self.scope["__continue__"] = Continuation("continue")
            self.scope["__break__"] = Continuation("break")
            self.calls([block])
        else:
            if self.is_error and self.output != self.scope["__continue__"]:
                return self.output if self.output != self.scope["__break__"]\
                       else None
            if self.output == self.scope["__continue__"]:
                self.scope["__continue__"]._raised = False
            self.outputs.pop()
        return Eval

    # Only simple arguments for now. No default value evaluation.
    def funcdef(self, name, args, block):
        func_name = Name(name[0])
        normal = [arg for arg in args if arg.name != "fpdef_opt"]
        optional = [arg for arg in args if arg.name == "fpdef_opt"]
        defaults = self.outs([arg[1] for arg in optional])
        args = Node("parameters", normal + [Node("optional", [opt[0], value])
                                            for opt, value in zip(optional, defaults)])
        self.scope[func_name] = Node("Function", [args, block], scope=self.scope, source=self.lookup('__source__'),
                                     pos=self.pos, func_name=func_name)

    def __call__(self, func_node, args, skip_func=False, skip_value=False):
        func_name = func_node.func_name if func_node.name == "Function" else\
            'not yet known method' if func_node.name == "__getattr__" else func_node[0]
        assert(type(func_name) in [Name, str])
        if self.debug:
            self.debugger.callback(self, func_name=func_name)
            #print " "*len(self.stack), "call", func_name, self.frame.step, str(self.frame.outputs[-1])[:20] if self.frame.outputs else ""
        if self.frame.step in ["new", "call"]:
            star_args = (args and args[0].name == "remaining_args")
            if star_args:
                args = args[0]
            # Should possibly change scope for func_node!
            if skip_func and skip_value:
                func, args_value = func_node, args
                self.frame.step = "call"
            elif skip_func:
                func, args_value = func_node, self.outs(list(args), step="call")
            elif skip_value:
                func, args_value = func_node, self.out([func_node], step="call")
            else:
                self.out([func_node] + list(args), step="call")
                func, args_value = self.outputs[0], self.outputs[1:]
            if self.is_error: # Not new step (is_error may not be reset then)
                return self.output
            if star_args:
                args_value = args_value[0]
            if hasattr(func, "_self"):
                args_value = [func._self] + args_value
            if func in [self.evaluate, self.assignment, self.eval_error]:
                self.calls([Node(func_name, args_value,
                                 pos=self.pos)], step="node_call")
            elif type(func).__name__ in native_functions:
                return func(*args_value)
            if isinstance(func, Instance):
                if func.name == "Class":
                    args_value = [func] + args_value
                    func = self.get_method(func, '__pnew__')
                    assert(func is not None)
                    #if func is None:
                    #    func = self.modules['objects']['pobject']['__dict__']['__pnew__']
                else:
                    bp()
            func_args, func_body = func
            assert(func_name in [func.func_name, 'not yet known method'] or\
                       func.func_name == '__pnew__')
            func_name = func.func_name
            self.frame.scope = self.scope
            self.scope = Scope(__func__=func, __return__=Continuation("return"),
                               __parent__=func.scope, __func_name__=func_name,
                               __caller__=self.scope)
            self.setup_args(func_args, args_value)
            self.call_stack.append(func)
            self.calls([func_body], step="finished")
        elif self.frame.step == "finished":
            result = self.output.value if self.is_error and self.output == self.scope["__return__"] else\
                     self.output if self.is_error else\
                     None
            self.last_call_stack.append(self.call_stack.pop())
            self.scope = self.frame.scope
            return result
        elif self.frame.step == "node_call":
            return self.output

    def setup_args(self, func_args, args_value):
        i = -1
        for i, (name, value) in enumerate(zip(func_args, args_value)):
            if name.name == "remaining_args":
                i -= 1
                break
            var_name = Name(name[0] if name.name == "NAME" else name[0][0])
            self.scope[var_name] = value
        i += 1
        if i < len(func_args) and func_args[i].name == "remaining_args":
            self.scope[Name(func_args[i][0][0])] = args_value[i:]
        else:
            for default in func_args[i:]:
                assert(default.name == "optional")
                self.scope[Name(default[0][0])] = default[1]

    def return_stmt(self, node=None):
        output = self.out([node]) if node is not None else None
        cont = self.lookup("__return__")
        cont.value = output
        return raised(cont)

    def raise_stmt(self, error=None):
        if error is None:
            not_yet_implemented
        else:
            return raised(self.out([error]))

    def get_method(self, instance, method_name):
        if instance.get('__type__') == "Class" and method_name in ["__getitem__", "__setitem__"]:
            return None
        mod_name, classname = instance['__dict__']['__path__']
        cls = self.modules[mod_name][classname]
        # In the class-parent tree, find the first ancestor of cls
        # whose __dict__ contains method_name
        while True:
            if method_name in cls['__dict__']:
                return cls['__dict__'][method_name]
            elif cls['__parents__'] is not None:
                cls = cls['__parents__']
            else:
                return None

    def getattrib(self, var, param):
        try:
            param_value = Name(param[0])
        except:
            var_value, param_value = self.outs([var, params])
        else:
            var_value = self.out([var])
        if type(var_value) == Instance and param_value in var_value['__dict__']:
            return var_value['__dict__'][param_value]
        elif type(var_value) == Instance and self.get_method(var_value, param_value) is not None:
            func = self.get_method(var_value, param_value)
            if var_value.get('__type__') == "Class":
                return func
            return Node("Function", func, _self=var_value, scope=func.scope,
                        source=func.source, func_name=func.func_name)
        elif type(var_value) == Scope and param_value in var_value and param_value not in ["__getitem__", "__setitem__"]:
            return var_value[param_value]
        else:
            return getattr(var_value, param_value)

    def setattrib(self, obj_node, attrib, value):
        if obj_node.name == "thaw":
            obj = self.out(["evaluate", obj_node], tree=True)
        else:
            obj = self.out([obj_node])
        if type(obj) == Instance:
            obj['__dict__'][Name(attrib[0])] = value
        elif type(obj) == Scope and value not in ["__getitem__", "__setitem__"]:
            obj[Name(attrib[0])] = value
        else:
            setattr(obj, Name(attrib[0]), value)

    def thunk(self, node):
        return Thunk(node, self.scope)

    def listmaker(self, *values):
        if values and values[0].name == "listcomp":
            return self.out(values)
        return self.outs(values)

    def dictmaker(self, *key_value_pairs):
        if key_value_pairs and key_value_pairs[0].name == "dictcomp":
            return self.out(key_value_pairs)
        return dict(self.outs(key_value_pairs))
        #return Instance("Dict", self.outs(key_value_pairs))

    def tuple(self, *values):
        return tuple(self.outs(values))
        #return Instance("List", self.outs(values))

    def evaluate(self, thunk, scope=None):
        if self.frame.step == "new":
            self.frame.scope = self.scope
            self.scope = thunk.scope if scope is None else scope
        self.out([thunk.node if thunk.name == "thaw" else thunk])
        self.scope = self.frame.scope
        return self.output

    def stack_trace(self, stack=None):
        stack = stack if stack is not None else self.stack + self.last_stack
        #for frame in reversed(self.last_call_stack):
        for i, frame in enumerate(stack):
            if frame.scope.get('__func__'):
                #mod_name = lookup("__module__", frame.scope['__func__'].scope)
                mod_name = frame.scope['__func__'].source
            else:
                mod_name = lookup("__source__", frame.scope)
            func_name = lookup("__func_name__", frame.scope)
            if mod_name not in self.sources:
                print "** Stack frame error, skipping **"
                continue
            source = self.sources[mod_name]
            line_num = [bisect(source.line_num, p) for p in frame.root.pos]
            rel_pos = [p - (source.line_num[line_num[0]-1] if line_num[0] else 0)
                       for p in frame.root.pos]
            lines = "".join(source.lines[line_num[0]: line_num[1]+1])
            print str(i).ljust(2) + " In file " + '\033[92m' + source.filename + '\033[0m' + " line " + str(line_num[0]) + " function " + '\033[92m' + str(func_name) + " (" + frame.root.name + ")" + '\033[0m'
            print lines[:rel_pos[0]] + '\033[91m' + lines[rel_pos[0]: rel_pos[1]] + '\033[0m' + lines[rel_pos[1]:-1]

    st = stack_trace

    def eval_error(self, block):
        output = self.evaluate(block) # Dangerous
        #output = self.out(["evaluate", block], tree=True)
        return raised(output, False) if self.is_error else None

    def ast(self, expr, is_filename=False):
        return self.parser.parse('grammar', expr+'\n' if not is_filename else
                                 open(expr).read())

    def repl(self):
        prev = ""
        while True:
            try:
                new_cmd = raw_input("p>> " if not prev else "... ")
            except EOFError:
                break
            command = prev + new_cmd + '\n'
            # print "command %s" % repr(command)
            output = self.parser.parse("single_input", command)
            if type(output) == MatchError:
                # Doesn't work. Need EOL to raise a special error
                output = self.parser.parse("compound_stmt", command)
                if type(output) == MatchError or new_cmd.strip():
                    prev = command
                    continue
            prev = ""
            self.repl_count += 1
            returned = self.run(output, "<console-%s>" % self.repl_count,
                                self.scope['__module__'], command.split("\n"))
            if returned is not None:
                print returned

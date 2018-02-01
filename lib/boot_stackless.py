from objects import object, all, any, zip, List, isinstance
from util import Node, MatchError
NAME, FLAGS, ARGS, BODY = [0, 1, 2, 3]
# input is a pair (container, pos)

class Eval(object):
    pass

class Frame(object):
    def __pinit__(self, root, input):
        self.root = root
        self.calls = List()
        self.input = input[:]
        self.outputs = List()

    def __repr__(self):
        return repr(self.calls)

def pop(input):
    input[1] += 1
    try:
        return input[0][input[1]]
    except IndexError:
        return MatchError("EOF")

def to_list(output):
    return output  if getattr(output, "name", None) == "And" else\
           []      if output is None else\
           [output]

def to_node(outputs, join_str):
    outputs = [elem for output in outputs
               for elem in to_list(output)]
    if len(outputs) == 1:
        return outputs[0]
    elif len(outputs) == 0:
        return None
    else:
        if join_str and all(type(output) == cpy_str for output in outputs):
            return "".join(outputs)
        return Node("And", outputs)

class Interpreter(object):
    def __pinit__(self, grammar_tree):
        self.rules = {rule[NAME][0]:rule for rule in grammar_tree}
        self.join_str = True

    def dbg(self):
        print len(self.input[0]), self.input[1]
        if len(self.input[0]) == self.input[1] + 1:
            return
        print self.input[0][self.input[1]: self.input[1] + 200]

    def parse(self, rule_name, input):
        output = self.match(self.rules[rule_name][-1], input)
        if isinstance(output, MatchError) or len(self.input[0]) == self.input[1] + 1:
            return output
        return MatchError("Not all input read")

    def match(self, root, input=None, pos=-1):
        """ >>> g.match(g.rules['grammar'][-1], "x='y'") """
        self.input = [input, pos]
        self.stack = [Frame(root, self.input)]
        output = self.new_step()
        #self.memoizer = {}
        while True:
            #print [c.root.name for c in self.stack]
            #bpoint()
            if output is Eval:
                root = self.stack[-1].calls[len(self.stack[-1].outputs)]
                self.stack.append(Frame(root, self.input))
                output = self.new_step()
            else:
                if isinstance(output, Node) and not hasattr(output, "pos"):
                    output.pos = (self.stack[-1].input[1]+1, self.input[1]+1)
                self.stack.pop()
                if not self.stack:
                    return output
                #print len(self.stack)*" ", "returned", output
                self.stack[-1].outputs.append(output)
                output = self.next_step()

    def new_step(self):
        root = self.stack[-1].root
        name = root.name
        calls = self.stack[-1].calls
        #print [c for c in root]
        #p [c['__dict__']['root']['__dict__']['name'] for c in self.scope['self']['__dict__']['stack']]
        print len(self.stack)*" ", "matching", name, self.input[1]
        if name in ["and", "args", "output", "or"]:
            calls.extend(root)
        elif name in ["bound", "negation", "quantified"]:
            calls.append(root[0])
        elif name == "apply":
            print " "*len(self.stack), "matching", name, root[NAME], self.input[1], self.input[0][self.input[1]+1:self.input[1]+11]
            if root[NAME] == "anything":
                return pop(self.input)
            #key = (root[NAME], id(self.input[0]), self.input[1])
            #if key in self.memoizer:
            #    self.input = self.memoizer[key][1][:]
            #    return self.memoizer[key][0]
            #self.stack[-1].key = key
            calls.append(self.rules[root[NAME]][BODY])
        elif name in ["exactly", "token"]:
            print " "*len(self.stack), name, root[0]
            if name == "token":
                while pop(self.input) in ['\t', '\n', '\r', ' ']:
                    pass
                if self.input[1] == len(self.input[0]):
                    return MatchError("EOF")
                self.input[1] -= 1
            for char in root[0]:
                if pop(self.input) != char:
                    return MatchError("Not exactly %s" % root[0])
            return root[0]
        return Eval

    def next_step(self):
        frame = self.stack[-1]
        root = frame.root
        name = root.name
        outputs = frame.outputs
        output = outputs[-1] if outputs else None
        is_error = isinstance(output, MatchError)
        finished = len(outputs) == len(frame.calls)
        if is_error and name not in ["quantified", "or", "negation"]:
            return output
        elif not (finished or name in ["or", "quantified"]):
            return Eval
        if name in ["and", "args", "output"]:
            if any(child.name == "output" for child in root):
                outputs = [output for child, output in zip(root, outputs)
                           if child.name == "output"]
            return to_node(outputs, self.join_str)
        elif name == "quantified":
            assert(root[1].name == "quantifier")
            lower, upper = {"*": (0, inf), "+": (1, inf), "?": (0, 1)}[root[1][0]]
            if is_error:
                self.input = frame.input[:]
                outputs.pop()
            #print("output len", len(outputs))
            if is_error or len(outputs) == upper or frame.input == self.input:
                if lower > len(outputs):
                    return MatchError("Matched %s < %s times" % (len(outputs), lower))
                else:
                    return to_node(outputs, self.join_str)
            else:
                frame.input = self.input[:]
                self.stack[-1].calls.append(root[0])
        elif name == "or":
            if is_error:
                self.input = frame.input[:]
                if finished:
                    return MatchError("All Or matches failed")
            else:
                return output
        elif name == "apply":
            if root[NAME] == "escaped_char" and not is_error:
                chars = {'"': '"', "'": "'", 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t', 'b': '\b', '\\': '\\'}
                return chars[output]
            and_node = getattr(output, "name", None) == "And"
            make_node = "!" in self.rules[root[NAME]][FLAGS] or\
                        (and_node and len(output) > 1)
            #print len(self.stack)*" ", "returned", output
            if make_node:
                output = Node(root[NAME], to_list(output))
            #self.memoizer[frame.key] = (output, self.input[:])
            return output

        elif name in "bound":
            return Node(root[1][0], to_list(output))
        elif name == "negation":
            if is_error:
                self.input = frame.input
                return None
            else:
                return MatchError("Negation true")
        else:
            raise Exception("Unknown operator %s" % name)
        return Eval

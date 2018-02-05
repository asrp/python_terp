simport simple_ast
import util
import boot_tree

def getattr(instance, key, default=None):
    return instance.getattr(key, default)

wrapped = util.simple_wrap_tree(boot_tree.tree)

import boot_stackless
i1 = boot_stackless.Interpreter(wrapped)
import boot_grammar
import python_grammar
grammar = boot_grammar.bootstrap + boot_grammar.extra
match_tree = i1.match(i1.rules['grammar'][-1], grammar)
match_tree.pprint()
# Not tested beyond this point.

i2 = boot_stackless.Interpreter(match_tree)
match_tree2 = i2.match(i2.rules['grammar'][-1], grammar + boot_grammar.diff)
i3 = boot_terp.Interpreter(match_tree2)
match_tree3 = i3.match(i3.rules['grammar'][-1], python_grammar.full_definition + python_grammar.extra)

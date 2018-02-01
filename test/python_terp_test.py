# Test all features of the interpreter using the test file python_terp_ex.py.
# Also try python test/python_terp_test.py test/parse_ex.py

import sys
sys.path.append('.')
sys.setrecursionlimit(5000)
from pymetaterp.util import simple_wrap_tree
from pymetaterp import boot_grammar, boot_tree, boot_stackless as boot_terp, python, python_grammar, boot
from python_terp import python_terp


grammar = boot_grammar.bootstrap + boot_grammar.extra
i1 = boot_terp.Interpreter(simple_wrap_tree(boot_tree.tree))
# Not needed, just double checking
match_tree = i1.match(i1.rules['grammar'][-1], grammar)
i2 = boot_terp.Interpreter(match_tree)
match_tree2 = i2.match(i2.rules['grammar'][-1], grammar + boot_grammar.diff)
i3 = boot_terp.Interpreter(match_tree2)
match_tree3 = i3.match(i3.rules['grammar'][-1], python_grammar.full_definition + python_grammar.extra)
pyi = python.Interpreter(match_tree3)
#pyi_tree = pyi.match(pyi.rules['grammar'][-1], open("python_ex2.py").read())

filename = "test/python_terp_ex.py" if len(sys.argv) == 1 else sys.argv[-1]
print "Parsing and running file %s" % filename
pyi_tree = pyi.match(pyi.rules['grammar'][-1], open(filename).read())
if hasattr(pyi_tree, "pprint"):
    pyi_tree.pprint()
else:
    print pyi_tree
pyterp = python_terp.Interpreter(pyi)
pyterp.run(pyi.match(pyi.rules['grammar'][-1], open("lib/boot.py").read()),
           filename="lib/boot.py", modname="boot")
pyterp.run(pyi.match(pyi.rules['grammar'][-1], open("lib/global.py").read()),
           filename="lib/global.py", modname="boot")
output = pyterp.run(pyi_tree, filename=filename)

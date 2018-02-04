# Run this file with python -i test/python_terp_test.py test/buggy_ex.py
simport simple_ast
total = 0
for i in [1, 2, 3, 4, 5]:
    print "i is", i
    if i >= 4:
        # Bug 1
        total += ii
        print "Printing total"
        # Bug 2
        print tootal
    else:
        total += i
        print total
print "Loop complete"

# Fix the bug at runtime by running these in the CPython interpreter
# pyterp.st()
# pyterp.last_stack[-1].root.pprint()
# pyterp.last_stack[-1].root[0]
# pyterp.last_stack[-1].root[0] = 'i'
# pyterp.continue_()
# pyterp.last_stack[-1].root[0]
# pyterp.last_stack[-1].root[0] = 'total'
# pyterp.continue_()
